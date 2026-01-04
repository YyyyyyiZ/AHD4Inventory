"""
extract_code.py  (Pro version)

Scan pops_best/*.json and extract policy code into pops_best/extracted/*.py.

Expected JSON format:
- key "code" exists and is a string containing a function definition:
    def compute_order_amount(...):
        ...

We also write pops_best/extracted/_manifest.csv.
"""

import json
from pathlib import Path
from datetime import datetime


def main():
    base_dir = Path(__file__).resolve().parent
    pops_dir = base_dir / "pops_best"
    if not pops_dir.exists():
        raise FileNotFoundError(f"pops_best/ not found under {base_dir}")

    out_dir = pops_dir / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_paths = sorted(pops_dir.glob("*.json"))
    if not json_paths:
        raise FileNotFoundError(f"No *.json found under {pops_dir}")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manifest = []

    for jp in json_paths:
        try:
            obj = json.loads(jp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] Skip {jp.name}: JSON parse error: {e}")
            continue

        code = obj.get("code", "")
        if not isinstance(code, str) or not code.strip():
            print(f"[WARN] Skip {jp.name}: missing/empty 'code' field")
            continue

        # Basic sanity check
        if "def compute_order_amount" not in code:
            print(f"[WARN] {jp.name}: 'compute_order_amount' not found; still extracting.")

        out_path = out_dir / f"{jp.stem}.py"
        header = (
            "# Auto-extracted policy code\n"
            f"# Source JSON: {jp.name}\n"
            f"# Extracted at: {ts}\n\n"
        )
        out_path.write_text(header + code.rstrip() + "\n", encoding="utf-8")
        manifest.append((jp.name, str(out_path.relative_to(base_dir))))
        print(f"[OK] {jp.name} -> {out_path}")

    mf = out_dir / "_manifest.csv"
    mf.write_text("source_json,extracted_py\n" + "\n".join([f"{a},{b}" for a, b in manifest]) + "\n", encoding="utf-8")
    print(f"Done. Extracted {len(manifest)} policies. Manifest: {mf}")


if __name__ == "__main__":
    main()
