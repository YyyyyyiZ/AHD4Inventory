import json
import re
from pathlib import Path
from typing import Optional


BASE_DIR = Path("/home/yfenghua/research/AHD4Inventory/examples/inventory")
UNIQUE_DIR = BASE_DIR / "unique_interesting_policies"
DISTRIBUTIONS = ["normal_std30", "poisson", "exponential"]


def needs_repair(code: str) -> bool:
    if not isinstance(code, str):
        return False
    if "def compute_order_amount" not in code:
        return False
    return re.search(r"\breturn\b", code) is None


def extract_historical_policy_code(prompt_text: str) -> Optional[str]:
    marker = "I have one policy with its code as follows:"
    marker_idx = prompt_text.find(marker)
    search_start = marker_idx + len(marker) if marker_idx >= 0 else 0

    def_idx = prompt_text.find("def compute_order_amount", search_start)
    if def_idx < 0:
        return None

    tail = prompt_text[def_idx:]
    stop_patterns = [
        "\nBelow is the cost statistics",
        "\n    Below is the cost statistics",
        "\nNo.1 policy:",
        "\n    No.1 policy:",
    ]
    stops = [tail.find(p) for p in stop_patterns if tail.find(p) >= 0]
    end_idx = min(stops) if stops else len(tail)

    code = tail[:end_idx].strip()
    if "def compute_order_amount" not in code:
        return None
    if re.search(r"\breturn\b", code) is None:
        return None
    return code


def repair_single_policy(policy_path: Path) -> bool:
    with policy_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    code = data.get("code")
    if not needs_repair(code):
        return False

    source_experiment = data.get("source_experiment")
    source_txt_file = data.get("source_txt_file")
    if not source_experiment or not source_txt_file:
        return False

    prompt_path = BASE_DIR / source_experiment / "prompt_for_code" / source_txt_file
    if not prompt_path.exists():
        return False

    prompt_text = prompt_path.read_text(encoding="utf-8")
    repaired_code = extract_historical_policy_code(prompt_text)
    if not repaired_code:
        return False

    data["code"] = repaired_code
    with policy_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)
        f.write("\n")
    return True


def sync_merged_file(distribution: str) -> int:
    merged_path = UNIQUE_DIR / f"{distribution}_merged_policies.json"
    with merged_path.open("r", encoding="utf-8") as f:
        merged = json.load(f)

    file_to_code = {}
    for policy_file in sorted((UNIQUE_DIR / distribution).glob("*.json")):
        with policy_file.open("r", encoding="utf-8") as f:
            policy_data = json.load(f)
        file_to_code[policy_file.name] = policy_data.get("code")

    repaired_count = 0
    for policy in merged.get("policies", []):
        filename = policy.get("filename")
        if filename in file_to_code and policy.get("code") != file_to_code[filename]:
            policy["code"] = file_to_code[filename]
            repaired_count += 1

    merged["policy_count"] = len(merged.get("policies", []))
    with merged_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=True, indent=2)
        f.write("\n")

    return repaired_count


def main() -> None:
    repaired_by_dist = {d: 0 for d in DISTRIBUTIONS}
    merged_sync_by_dist = {d: 0 for d in DISTRIBUTIONS}

    for dist in DISTRIBUTIONS:
        for policy_file in sorted((UNIQUE_DIR / dist).glob("*.json")):
            if repair_single_policy(policy_file):
                repaired_by_dist[dist] += 1
        merged_sync_by_dist[dist] = sync_merged_file(dist)

    print("Repair summary:")
    for dist in DISTRIBUTIONS:
        print(
            f"  {dist}: repaired source files={repaired_by_dist[dist]}, "
            f"updated merged entries={merged_sync_by_dist[dist]}"
        )


if __name__ == "__main__":
    main()
