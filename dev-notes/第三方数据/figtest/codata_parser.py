"""Minimal, verified parser for nist_codata2022_constants.txt.

The file is a fixed-width layout, NOT pipe-delimited despite the README's
'Quantity | Value | Uncertainty | Unit' shorthand (there are no literal '|'
characters in the actual file). Reliable structural cues:
- thousands separators inside a number are SINGLE spaces (e.g. '6.644 657 3450')
- field boundaries between value/uncertainty/unit are runs of 5+ spaces, though
  a few long-number rows happen to have only 4 spaces at one boundary and are
  skipped (counted, not silently dropped)
- very-precise values are truncated with a trailing '...' which must be stripped
  before float() parsing
- uncertainty '(exact)' means a defined constant with no uncertainty

Only rows with a parseable value are returned; caller filters by unit etc.
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_num(s):
    s = s.strip()
    if not s or "exact" in s.lower() or s.startswith("(e"):
        return None
    s = s.replace(" ", "")
    if s.endswith("..."):
        s = s[:-3]
    try:
        return float(s)
    except ValueError:
        return None


def parse_constants(path):
    """Return (entries, skipped_count) where entries is a list of
    (line_no, quantity_name, value, uncertainty_or_None, unit_or_empty_str)."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    entries = []
    skipped = 0
    for i, line in enumerate(lines, start=1):
        raw = line.rstrip("\n")
        if not raw.strip() or raw.lstrip().startswith("-") or raw.strip().startswith("Quantity") \
                or "CODATA" in raw or raw.strip().startswith("From:") or "listing" in raw.lower() \
                or raw.strip().lower().startswith("fundamental"):
            continue
        parts = re.split(r" {5,}", raw.strip())
        if len(parts) < 2:
            continue
        qty = parts[0].strip()
        val_str = parts[1].strip()
        unc_str = parts[2].strip() if len(parts) > 2 else ""
        unit = " ".join(parts[3:]).strip() if len(parts) > 3 else ""
        val = parse_num(val_str)
        unc = parse_num(unc_str)
        if val is None:
            skipped += 1
            continue
        entries.append((i, qty, val, unc, unit))
    return entries, skipped


def kg_constants_with_real_uncertainty(path):
    """Convenience wrapper: pull out kg-unit constants whose uncertainty is a
    real number (not '(exact)', not None)."""
    entries, skipped = parse_constants(path)
    kg = [(i, q, v, u) for (i, q, v, u, unit) in entries if unit == "kg" and u is not None]
    return kg, skipped


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "..", "nist_codata2022_constants.txt")
    kg, skipped = kg_constants_with_real_uncertainty(path)
    print(f"kg constants with real uncertainty: {len(kg)}; rows skipped (no parseable value / non-data row): {skipped}")
    for row in kg:
        print(row)
