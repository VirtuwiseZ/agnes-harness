#!/usr/bin/env node
// trace_capture.cjs — Node 4's automatic trace-source tool.
//
// What it is: a stand-alone, zero-dependency (Node stdlib only) script that
// (1) discovers the live AGH named pipe on this machine without hardcoding
// any hash, (2) connects and performs the AGH initialize + session/load
// handshake for a given session key, and (3) captures every session/update
// notification the daemon streams back as the session's full history is
// replayed — converting each one, on the fly, into the JSONL event schema
// ({seq, ts, type, data}) that program-design/hooks/trace_visualizer.py
// expects for its --trace argument. The output file is directly usable as
// that argument; no further transformation is needed.
//
// Why it exists: the governance protocol's Node 4 step needs to cross-check
// the report's claims against the run's actual AGH execution trace. This
// script makes that possible entirely automatically — the agent's own
// session key (written into problem_state.json's `session_key` field at
// Node 0/1, per SKILL.md §0) is the only input a human never has to supply.
// No `agh export`, no manual file handoff.
//
// Platform note (known limitation, not a bug to fix around silently): the
// pipe-discovery step uses `Get-ChildItem \\.\pipe\`, which is a Windows
// named-pipe enumeration. On non-Windows AGH installations (Unix-domain
// socket daemons), this discovery mechanism will not find anything usable
// and the script will report "no agnes-* pipes found". This is expected to
// be revisited if/when the project needs cross-platform Node 4 execution;
// for now the project's demo/test environment is Windows-only, matching
// where the AGH daemon socket actually lives.
//
// Usage:
//   node trace_capture.cjs <sessionId> [outputFile]
//     <sessionId>   the AGH session key to capture; typically read from
//                   problem_state.json's `session_key` field for the current
//                   task, not hand-typed.
//     [outputFile]  optional; defaults to program-design/runtime/
//                   trace_capture_converted_<short-session-id>.jsonl.
//   Env overrides (for testing / pinning, not for normal Node 4 use):
//     AGH_SESSION_ID  fallback source for <sessionId> if the positional arg
//                     is omitted.
//     PIPE_NAME       pin a specific pipe name instead of auto-discovering.
//
// Exit codes: 0 = capture succeeded; 1 = no reachable pipe / capture
// error; 2 = usage error (no sessionId given).
//
// Output is a JSONL file, one event per line, in the same shape
// trace_visualizer.py's load_trace() expects (see that file's docstring).
// A first "_capture_meta" line records which sessionId was captured and
// when, for auditability; the remaining lines are pure trace events.

const net = require('net');
const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const META_KEY = 'agnes';
const OUT_DEFAULT_BASE = path.join(__dirname, '..', 'runtime');

function discoverPipes() {
  const ps = `Get-ChildItem '\\.\\pipe\\' | Where-Object Name -like 'agnes*' | Select-Object -ExpandProperty Name`;
  const out = execSync(`powershell -NoProfile -Command ${JSON.stringify(ps)}`, { encoding: 'utf8' });
  return out.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
}

function handshake(pipeName) {
  return new Promise((resolve) => {
    let buf = Buffer.alloc(0);
    let seq = 0;
    let settled = false;
    const finish = (ok) => {
      if (!settled) { settled = true; resolve(ok); }
    };
    const conn = net.connect('\\\\?\\pipe\\' + pipeName, () => {
      const send = (obj) => { obj.jsonrpc = '2.0'; obj.id = ++seq; conn.write(JSON.stringify(obj) + '\n'); return obj.id; };
      const initId = send({
        method: 'initialize',
        params: {
          protocolVersion: 1,
          clientCapabilities: {
            fs: { readTextFile: false, writeTextFile: false },
            _meta: { [META_KEY]: { capabilities: { permission: true } } },
          },
          _meta: { [META_KEY]: { clientId: 'trace-capture' } },
        },
      });
      conn.on('data', (chunk) => {
        buf = Buffer.concat([buf, chunk]);
        let idx;
        while ((idx = buf.indexOf('\n')) !== -1) {
          const line = buf.slice(0, idx).toString('utf8').trim();
          buf = buf.slice(idx + 1);
          if (!line) continue;
          let msg;
          try { msg = JSON.parse(line); } catch { continue; }
          if (msg.id === initId) {
            finish(!msg.error);
            conn.end();
          }
        }
      });
      conn.on('error', () => finish(false));
      setTimeout(() => finish(false), 5000);
    });
    conn.on('error', () => finish(false));
  });
}

function captureAndConvert(sessionId, pipeName, outPath) {
  return new Promise((resolve) => {
    let buf = Buffer.alloc(0);
    let seq = 0;
    let toolCallCount = 0;
    let toolResultCount = 0;
    let placeholderCount = 0;
    const out = fs.createWriteStream(outPath, { encoding: 'utf8' });

    const writeConverted = (obj) => out.write(JSON.stringify(obj) + '\n');
    writeConverted({ _capture_meta: { sessionId, startedAt: new Date().toISOString(), source: 'session/load stream' } });

    const convertLine = (obj) => {
      if (obj._capture_meta) return;
      const es = obj._meta && obj._meta['ai.agnes.harness'] ? obj._meta['ai.agnes.harness'].eventSequence : null;
      const upd = obj.update || {};
      const su = upd.sessionUpdate;
      if (su === 'tool_call') {
        toolCallCount++;
        writeConverted({
          seq: es, ts: null, type: 'tool/call',
          data: { toolUseId: upd.toolCallId, name: upd.title, args: upd.rawInput || {} },
        });
      } else if (su === 'tool_call_update') {
        toolResultCount++;
        const status = upd.status;
        const contentBlocks = upd.content || [];
        const textParts = [];
        for (const b of contentBlocks) {
          const c = b && b.content;
          if (c && c.type === 'text') textParts.push(c.text || '');
        }
        writeConverted({
          seq: es, ts: null, type: 'tool/result',
          data: {
            toolUseId: upd.toolCallId,
            content: [{ type: 'text', text: textParts.join('\n') }],
            isError: status === 'failed',
          },
        });
      } else {
        placeholderCount++;
        writeConverted({
          seq: es, ts: null, type: 'session/start',
          data: { key: obj.sessionId, placeholder: su },
        });
      }
    };

    const conn = net.connect('\\\\?\\pipe\\' + pipeName, () => {
      const send = (obj) => { obj.jsonrpc = '2.0'; obj.id = ++seq; conn.write(JSON.stringify(obj) + '\n'); return obj.id; };
      send({
        method: 'initialize',
        params: {
          protocolVersion: 1,
          clientCapabilities: {
            fs: { readTextFile: false, writeTextFile: false },
            _meta: { [META_KEY]: { capabilities: { permission: true } } },
          },
          _meta: { [META_KEY]: { clientId: 'trace-capture' } },
        },
      });
      send({
        method: 'session/load',
        params: { sessionId, cwd: '', mcpServers: [] },
      });

      conn.on('data', (chunk) => {
        buf = Buffer.concat([buf, chunk]);
        let idx;
        while ((idx = buf.indexOf('\n')) !== -1) {
          const line = buf.slice(0, idx).toString('utf8').trim();
          buf = buf.slice(idx + 1);
          if (!line) continue;
          let msg;
          try { msg = JSON.parse(line); } catch { continue; }
          if (msg.method === 'session/update') {
            convertLine(msg.params || {});
          }
        }
      });

      conn.on('close', () => {
        out.end(() => {
          resolve({ toolCallCount, toolResultCount, placeholderCount, outPath });
        });
      });
      setTimeout(() => {
        try { conn.destroy(); } catch { /* ignore */ }
      }, 20000);
    });
    conn.on('error', (e) => {
      out.end();
      resolve({ error: e.message, outPath });
    });
  });
}

(async () => {
  const sessionId = process.argv[2] || process.env.AGH_SESSION_ID;
  if (!sessionId) {
    console.error('usage: node trace_capture.cjs <sessionId> [outputFile]  (or set AGH_SESSION_ID)');
    process.exit(2);
  }
  const outArg = process.argv[3];
  const outPath = outArg || path.join(
    OUT_DEFAULT_BASE,
    `trace_capture_converted_${sessionId.replace(/[^a-z0-9]/gi, '').slice(0, 8)}.jsonl`);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });

  const pinned = process.env.PIPE_NAME;
  let pipeNames = pinned ? [pinned] : discoverPipes();
  if (!pipeNames.length) {
    console.error('no agnes-* pipes found on this machine (see the script header for the Windows-specific discovery mechanism)');
    process.exit(1);
  }
  console.log('candidate pipes:', pipeNames);
  let chosen = null;
  for (const p of pipeNames) {
    const ok = await handshake(p);
    console.log(`handshake ${p}: ${ok ? 'OK' : 'rejected'}`);
    if (ok) { chosen = p; break; }
  }
  if (!chosen) {
    console.error('none of the candidate pipes accepted an initialize handshake');
    process.exit(1);
  }
  const result = await captureAndConvert(sessionId, chosen, outPath);
  if (result.error) {
    console.error('capture failed:', result.error);
    process.exit(1);
  }
  console.log(`captured: tool/call=${result.toolCallCount} tool/result=${result.toolResultCount} other=${result.placeholderCount}`);
  console.log('wrote:', outPath);
})();
