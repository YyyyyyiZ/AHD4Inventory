# Matched DeepSeek Train Policies, m2-only, 1pct

Scope:
- train rows only from `final results - S 3.csv`
- same distribution only
- relative error <= 1%
- DeepSeek only
- exact m2 folders only: `deepseek-chat_*_50_plain_processed_scipy_15_default_m2_*_r*`
- m2 files only: `prompt_for_code/m2_*.txt`

Counts:
- target train repeat cells: 29601
- matched train cells: 18247
- matched ratio: 61.643188%
- unique normalized policies: 1240
- unique source prompt files: 1323
- source parse failures: 211

Files:
- `manifest.csv`: one row per unique policy.
- `matches.csv`: one row per matched train cell.
- `unmatched_train_cells.csv`: train cells with no m2-only match within 1%.
- `summary_by_distribution.csv`: match ratio by distribution.
- `policies/`: flat policy `.py` files by hash.
- `policies_by_distribution/`: policy `.py` files copied under each matched distribution.
- `policies.jsonl`: policy code plus metadata.
