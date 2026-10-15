import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

root = pathlib.Path(r"E:\agnes-harness\dev-notes\reference-solutions\例题\2025AB")
mineru_dir = root / "mineru_output"

pdfs = [
    "2025-GM-A-112.pdf",
    "2025-GM-A-182.pdf",
    "2025-GM-B-127.pdf",
    "2025-GM-B-765.pdf",
    "2025-GM-B-796.pdf",
]

LATEX_RE = re.compile(r"\\(frac|sqrt|sum|int\b|alpha|beta|theta|rho|pi|mu|sigma|cdot|times|mathrm|quad|left|right|begin|end)")


def stats(text):
    return {
        "chars": len(text),
        "latex_hits": len(LATEX_RE.findall(text)),
        "display_math": len(re.findall(r"\$\$|\\\\\[|\\\\\]", text)),
        "inline_math": len(re.findall(r"\$[^\$]+\$", text)),
        "pipe_table_rows": len(re.findall(r"^\|.*\|$", text, re.M)),
        "inline_image_refs": len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text)),
        "base64_img_blobs": len(re.findall(r"data:image/[a-z]+;base64,", text)),
        "mojibake": len(re.findall(r"[鈥爙]|锟", text)),
    }


for f in pdfs:
    md_path = mineru_dir / f.replace(".pdf", ".md")
    text = md_path.read_text(encoding="utf-8", errors="replace")
    s = stats(text)
    s["size_kb"] = round(md_path.stat().st_size / 1024)
    print(f, json.dumps(s, indent=2))
    print()
