"""
audit_log.py
============
Append-only audit-log writer for `problem_state.json`, per project consensus
Section 2 ("Context management & single source of truth").

Purpose
-------
Every external-capability call (atmosphere data API, numerical solver run,
dimensional/boundary gate invocation) MUST leave a structured audit record:

    { "source": ..., "timestamp": ..., "args": ..., "artifact_id": ... }

This script is the *only* sanctioned way to write such records into
`problem_state.json` — no other code path may mutate the file's
`audit_logs` field. It exists so that:

  1. The audit trail is append-only and time-ordered (never edited in place).
  2. Each record gets a deterministic `artifact_id` (content-addressed hash),
     which is what the "quote constraint" report node uses to attach
     traceability badges to final conclusions.
  3. The file's concurrent-write safety relies on a simple exclusive
     (O_EXCL)-style lock: read-modify-write under an OS-level lock file.

Tool-priority note
------------------
This is a small, project-specific "state-file protocol" helper, not a
general-purpose logging framework. Python's stdlib `json`/`hashlib`/
`fcntl`-equivalent locking is used directly; no third-party dependency is
introduced. It deliberately keeps to the exact field names already fixed
by the consensus document (Section 2), so downstream readers (Node 3
report synthesis, Node 4 HTML renderer) can rely on a stable schema.

Usage (from a node / hook, in-process):
    import audit_log
    record = audit_log.append_record(
        state_path="problem_state.json",
        source="NRLMSIS_atmosphere_api",
        args={"altitude_span_km": [0, 150], "step_km": 1},
    )
    # -> {"artifact_id": "<sha256>", "record": {...}}

CLI — full, copy-paste-runnable command lines (do not flatten all flags
into one positional argument the way a one-off guess might; this script
is a subcommand-based CLI, not a flat-args one):
    python audit_log.py append --state <path-to-problem_state.json> \
        --source <source_name> --args-json '{"key": "value"}'
    python audit_log.py verify --state <path-to-problem_state.json>

  The subcommand word (append / verify) is mandatory and must come
  before the -- flags; running `python audit_log.py --state ... --source ...`
  with no subcommand is a usage error (exit code 2), not a write.

CLI exit codes: 0 = written OK / verify PASS, 1 = verify FAIL, 2 =
state file unreadable / write failed / usage error.
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time


def _artifact_id(payload: dict) -> str:
    """Content-addressed id for an audit record: stable across re-serialization
    of the same logical record, changes if any field actually differs.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _acquire_lock(state_path: str, timeout_s: float = 10.0):
    """Cross-platform simple lock: create `<state_path>.lock` with O_EXCL
    semantics, retrying briefly. Returns the lock file handle (held until
    explicit release).
    """
    lock_path = state_path + ".lock"
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            return lock_path, fd
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"could not acquire lock on {lock_path}")
            time.sleep(0.05)


def _release_lock(lock_path: str, fd: int):
    os.close(fd)
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass


def _load_state(state_path: str) -> dict:
    if not os.path.exists(state_path):
        return {}
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_state(state_path: str, state: dict):
    """Atomic write: write to a temp file in the same directory, then
    os.replace() over the target, so a crash never leaves a half-written
    state file behind.
    """
    directory = os.path.dirname(state_path) or "."
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, delete=False
    ) as tmp:
        json.dump(state, tmp, indent=2, ensure_ascii=False)
        tmp_path = tmp.name
    os.replace(tmp_path, state_path)


def append_record(state_path: str, source: str, args: dict | None = None,
                  extras: dict | None = None) -> dict:
    """Append one audit record to `state_path`'s `audit_logs` array (creating
    the key if absent) and return the record plus its artifact_id.
    """
    args = args or {}
    extras = extras or {}

    record = {
        "timestamp": time.time(),
        "source": source,
        "args": args,
        "artifact_id": "",  # filled in after hashing (excluding this field)
        **extras,
    }
    record["artifact_id"] = _artifact_id(
        {k: v for k, v in record.items() if k != "artifact_id"}
    )

    lock_path, lock_fd = _acquire_lock(state_path)
    try:
        state = _load_state(state_path)
        state.setdefault("audit_logs", []).append(record)
        _write_state(state_path, state)
    finally:
        _release_lock(lock_path, lock_fd)

    return {"artifact_id": record["artifact_id"], "record": record}


def verify_chain(state_path: str) -> dict:
    """Re-hash every record in `audit_logs` and confirm each stored
    `artifact_id` still matches — detects any out-of-band tampering with
    the audit trail. Returns per-record OK/FAIL and an overall verdict.
    """
    state = _load_state(state_path)
    logs = state.get("audit_logs", [])
    per_record = []
    all_ok = True
    for i, rec in enumerate(logs):
        stored_id = rec.get("artifact_id", "")
        recomputed = _artifact_id({k: v for k, v in rec.items() if k != "artifact_id"})
        ok = stored_id == recomputed
        per_record.append({"index": i, "ok": ok, "stored": stored_id, "recomputed": recomputed})
        all_ok = all_ok and ok
    return {"verdict": "PASS" if all_ok else "FAIL", "records": per_record}


def main():
    p = argparse.ArgumentParser(description="Append-only audit-log writer for problem_state.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("append", help="append one audit record")
    a.add_argument("--state", required=True)
    a.add_argument("--source", required=True)
    a.add_argument("--args-json", default="{}")

    v = sub.add_parser("verify", help="re-hash and verify the audit chain")
    v.add_argument("--state", required=True)

    args = p.parse_args()

    if args.cmd == "append":
        try:
            args_dict = json.loads(args.args_json)
        except json.JSONDecodeError as e:
            print(json.dumps({"verdict": "ERROR", "reason": f"bad --args-json: {e}"}))
            return 2
        out = append_record(args.state, args.source, args_dict)
        print(json.dumps(out, indent=2))
        return 0

    if args.cmd == "verify":
        out = verify_chain(args.state)
        print(json.dumps(out, indent=2))
        return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
