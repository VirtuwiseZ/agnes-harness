import json
import os
import pathlib
import re
import time

import pdfplumber
import pypdf
import pymupdf4llm

import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

root = pathlib.Path(r"E:\agnes-harness\dev-notes\reference-solutions\例题\2025AB")
out_dir = root / "pypdf_pymupdf4llm_plumber_output"
out_dir.mkdir(exist_ok=True)

pdfs = [
    "2025-GM-A-112.pdf",
    "2025-GM-A-182.pdf",
    "2025-GM-B-127.pdf",
    "2025-GM-B-765.pdf",
    "2025-GM-B-796.pdf",
]

LATEX_RE = re.compile(r"\\(frac|sqrt|sum|int\b|alpha|beta|theta|rho|pi|mu|sigma|cdot|times|mathrm)")


def clean_surrogates(text):
    """Strip lone/unpaired UTF-16 surrogates (U+D800–U+DFFF) so the result is
    always a valid Python str that can be written to a utf-8 file. Replaces
    each lone surrogate with '?' — we never want to silently drop content,
    and we don't want to crash either."""
    return re.sub(r"[\ud800-\udfff]", "?", text)


def stats(text):
    return {
        "chars": len(text),
        "latex_hits": len(LATEX_RE.findall(text)),
        "pipe_table_rows": len(re.findall(r"^\|.*\|$", text, re.M)),
        "mojibake": len(re.findall(r"[鈥爙]|锟", text)),
        "lines": text.count("\n"),
    }


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


results = []
for f in pdfs:
    path = root / f
    row = {"file": f, "size_kb": round(path.stat().st_size / 1024)}

    t0 = time.time()
    try:
        reader = pypdf.PdfReader(str(path))
        text = clean_surrogates("\n".join((p.extract_text() or "") for p in reader.pages))
        row["pypdf"] = {"ok": True, "seconds": round(time.time() - t0, 2), **stats(text)}
        write_text(out_dir / (f.replace(".pdf", "_pypdf.txt")), text)
    except Exception as e:
        row["pypdf"] = {"ok": False, "error": str(e)}

    t0 = time.time()
    try:
        tables = []
        with pdfplumber.open(str(path)) as pdf:
            texts = [clean_surrogates(pg.extract_text() or "") for pg in pdf.pages]
            for pg in pdf.pages:
                for t in (pg.find_tables() or []):
                    tables.append(t.extract())
        text = "\n".join(texts)
        table_cells = sum(len(r) for tbl in tables for r in tbl if r)
        row["pdfplumber"] = {
            "ok": True, "seconds": round(time.time() - t0, 2), **stats(text),
            "tables_found": len(tables), "table_cells": table_cells,
        }
        write_text(out_dir / (f.replace(".pdf", "_plumber_tables.json")),
                   json.dumps(tables, ensure_ascii=False, default=str))
    except Exception as e:
        row["pdfplumber"] = {"ok": False, "error": str(e)}

    t0 = time.time()
    try:
        md = clean_surrogates(pymupdf4llm.to_markdown(str(path)))
        row["pymupdf4llm"] = {"ok": True, "seconds": round(time.time() - t0, 2), **stats(md)}
        write_text(out_dir / (f.replace(".pdf", "_pymupdf4llm.md")), md)
    except Exception as e:
        row["pymupdf4llm"] = {"ok": False, "error": str(e)}

    results.append(row)
    print("done:", f, flush=True)

summary = out_dir / "_summary.json"
with open(summary, "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=2, ensure_ascii=False)
print()
print(json.dumps(results, indent=2))
