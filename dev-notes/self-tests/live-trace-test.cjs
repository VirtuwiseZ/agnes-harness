// Minimal verification: read a LIVE session's tool calls from an external process.
// Protocol: JSON-RPC 2.0 over a Windows named pipe, one JSON object per line.
//
// Key insight: readToolDetail does a direct ledger row scan (session.scan),
// NOT an event-stream attach. So it should work even while the session is live.
//
// Usage: node live-trace-test.cjs <sessionId>

const fs = require('node:fs');
const { createHash } = require('node:crypto');

const DATA_DIR = process.env.AGNES_DATA_DIR || 'C:\\Users\\StanleyZ\\.agh\\data';
const SESSION_ID = process.argv[2];
if (!SESSION_ID) {
  console.error('usage: node live-trace-test.cjs <sessionId>');
  process.exit(1);
}

const hex = createHash('sha256').update(DATA_DIR).digest('hex').slice(0, 16);
const PIPE = '\\\\.\\pipe\\agnes-' + hex;
console.log('[pipe]', PIPE);

// --- open the pipe ---
let fd;
try {
  fd = fs.openSync(PIPE, 'r+');
} catch (e) {
  console.error('[pipe] cannot open:', e.message);
  process.exit(1);
}

const readBuf = Buffer.alloc(1 << 20); // 1 MiB
let msgBytes = []; // accumulated bytes across readSync calls

function readLine() {
  for (;;) {
    const nl = msgBytes.indexOf(0x0a);
    if (nl !== -1) {
      const line = Buffer.from(msgBytes.splice(0, nl + 1)).toString('utf-8').trimEnd();
      msgBytes.length = 0;
      return line || null;
    }
    const n = fs.readSync(fd, readBuf, 0, readBuf.length, null);
    if (n === 0) return null;
    for (let i = 0; i < n; i++) msgBytes.push(readBuf[i]);
  }
}

function sendRpc(obj) {
  fs.writeSync(fd, JSON.stringify(obj) + '\n');
}

// --- pending request map ---
let nextId = 0;
const pending = new Map();

// Background reader
(function readLoop() {
  try {
    const line = readLine();
    if (line !== null) {
      let msg;
      try { msg = JSON.parse(line); } catch { return setTimeout(readLoop, 1); }
      if (msg.id !== undefined && pending.has(msg.id)) {
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }
    }
  } catch (e) {
    console.error('[reader]', e.message);
    return;
  }
  setTimeout(readLoop, 0);
})();

function call(method, params, timeoutMs = 30000) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => { pending.delete(id); reject(new Error('timeout: ' + method)); }, timeoutMs);
    pending.set(id, (msg) => {
      clearTimeout(t);
      if (msg.error) reject(Object.assign(new Error(method + ': ' + JSON.stringify(msg.error)), { rpcError: msg.error }));
      else resolve(msg.result);
    });
    sendRpc({ jsonrpc: '2.0', id, method, params });
  });
}

async function main() {
  // 1. initialize (local auth: kind='local' passes unconditionally on pipe transport)
  const initData = {
    protocolVersion: 1,
    clientCapabilities: {
      fs: { readTextFile: false, writeTextFile: false },
      _meta: { 'ai.agnes.harness': { capabilities: { permission: true } } },
    },
    _meta: { 'ai.agnes.harness': { clientId: 'live-trace-test', auth: { kind: 'local' } } },
  };
  const init = await call('initialize', initData);
  console.log('[init] ok, version =', init && init.agnesVersion);

  // 2. read tool details: callSeq = 1, 2, 3, ... until call-not-found
  const results = [];
  let callSeq = 1;
  const MAX_SEQ = 10000;
  let notFound = false;

  while (!notFound && callSeq <= MAX_SEQ) {
    try {
      // readToolDetail returns pages of base64-encoded JSON
      let offset = 0;
      let totalBytes;
      const chunks = [];
      for (;;) {
        const resp = await call('_agnes/v1/session.readToolDetail', {
          sessionId: SESSION_ID,
          callSeq: callSeq,
          offset: offset,
        });
        const b64 = resp.data || '';
        chunks.push(Buffer.from(b64, 'base64'));
        totalBytes = resp.totalBytes !== undefined ? resp.totalBytes : totalBytes;
        if (resp.nextOffset === null || resp.nextOffset === undefined) break;
        offset = resp.nextOffset;
      }
      const raw = Buffer.concat(chunks).toString('utf-8');
      let detail = null;
      try { detail = JSON.parse(raw); } catch (e) { console.error('[seq ' + callSeq + '] parse err:', e.message); }
      results.push({ callSeq: callSeq, detail: detail });
      callSeq++;
    } catch (e) {
      const s = JSON.stringify(e.rpcError || e.message);
      if (s.includes('call-not-found') || s.includes('result-not-found')) {
        notFound = true;
      } else {
        throw e;
      }
    }
  }

  console.log('\n=== RESULTS ===');
  console.log('Session:', SESSION_ID);
  console.log('Tool calls found:', results.length);
  for (const r of results) {
    const c = r.detail && r.detail.call;
    if (!c) { console.log('  seq ' + r.callSeq + ': (parse failed)'); continue; }
    const status = r.detail.result && r.detail.result.isError ? 'ERR' : 'ok';
    console.log('  seq ' + r.callSeq + ': ' + c.name + ' [' + status + ']');
  }
  console.log('\n=== PASS: readToolDetail works on a live session without attach ===');
}

main().catch(e => {
  console.error('[FATAL]', e.message);
  if (e.rpcError) console.error('  rpcError:', JSON.stringify(e.rpcError));
  process.exitCode = 1;
});
