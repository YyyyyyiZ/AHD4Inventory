# Nested-logit cardinality correction (September 2026)

The source benchmark uses `ceil(n * cap_rate)` for the per-nest cardinality
limit. The earlier loader used Python's `round`, giving limits 2 and 12 instead
of 3 and 13 when `n=25` and the cap rate is 0.1 or 0.5. This affected 233 of
the 971 released nested-logit instances and 12 of the 48 L1 queries per model.

The corrected experiment keeps the original prompts, API settings, query
budgets, instance sets, and artifact-selection rule. The L2 programs are
unchanged. Only their evaluations on the 233 affected instances are replaced;
the other 738 evaluations per program are retained exactly. Twelve L1 queries
per model are replaced because the original queries received incorrect input
caps. The other 36 queries per model are retained exactly.
The new logs explicitly record `web_search: false`; the original main L1 logs
predate that optional feature and omit the flag. Neither set of queries used it.

## Records and reproducibility

- `original/`: immutable gzip copies of every original JSONL file. These are
  historical wrong-cap experiments, not additional draws or current scores.
- `l2/`: corrected decisions, feasibility, revenues, runtime, source-file hash,
  artifact-code hash, and source index. Source indices distinguish repeated
  `rep` labels in the stability file.
- `l1/`: full replacement query transcripts, decisions, usage, and provenance.
- `failed_attempts/`: an authentication failure with no model response. It is
  not an additional experimental draw.
- `baselines.json`: all 971 instances' corrected classical heuristic revenues.

Canonical `../l1_nl_*.jsonl`, `../l2_nl_*.jsonl`, and the Sol zero-compute,
stability, and web-search JSONLs contain the merged corrected experiment.
The originally defective stability artifact remains preserved and excluded;
it is not replaced with a new draw. Table and figure scripts read these
canonical files, never the original archives or partial checkpoints.

From the repository root, with the released benchmark data installed:

```bash
python assortment/repair_nl_caps.py l2        # local evaluation only
python assortment/repair_nl_caps.py baselines # local evaluation only
python assortment/repair_nl_caps.py verify    # read-only integrity audit
```

Only `python assortment/repair_nl_caps.py l1 --model MODEL` can call an LLM.
Completed query checkpoints are reused on resume; a recorded generation error
stops the worker for inspection rather than silently spending another query.
The repair script validates the original prompt and API settings before a
replacement query. It replaces a canonical file only when all of that file's
required corrections have completed.

Use Python 3.10 or newer for replays: some frozen artifacts use
`int.bit_count()`. The corrected L2 replays used Python 3.10.9, NumPy 1.24.2,
and SciPy 1.10.0. An initial Python 3.9 replay was invalid for one artifact and
was discarded; all L2 corrections were rerun under Python 3.10. No generated
solver was patched to accommodate the wrong runtime.

The OpenAI L1 replacement queries used Python 3.9.6, NumPy 1.24.2, and SciPy
1.10.0; the Fable replacements used Python 3.10.9 with the same numerical
library versions. Runtime provenance is recorded in the replacement query
records. Original query transcripts and runtimes are unchanged.

The paper's comparator excludes LLM solutions. Rebuild it with
`assortment/make_vs_published_table.py` when the authors' private results are
available; the corrected `../best_existing.json` cache is included for users
without those files. The cap change does not affect the synthetic nested-logit
holdout, whose caps are explicit integers.

## Completed results and validation

All 48 replacement queries completed successfully. These results combine each
model's 12 replacement queries with its 36 unchanged original queries.

| Model | L1 mean, % of best existing | L1 within 0.1%, % | L2 mean, % of best existing | L2 within 0.1%, % |
|---|---:|---:|---:|---:|
| gpt-5.6-sol | 100.00 | 100.0 | 100.00 | 100.0 |
| claude-fable-5 | 100.00 | 100.0 | 100.00 | 100.0 |
| gpt-5.4 | 99.85 | 97.9 | 100.00 | 99.1 |
| gpt-5.1 | 99.88 | 87.5 | 99.72 | 59.9 |

L1 uses 48 instances; L2 uses all 971. The revenue-ordered baseline has mean
97.58%, minimum 72.86%, and a 67.5% within-0.1% share. On the same 48-instance
subset, GPT-5.1's within-0.1% share is 60.4% for L2 and 87.5% for L1.

All nine valid Sol stability draws have identical mean revenue (100.00060295%)
and a 100% within-0.1% share. The zero-compute and web-search programs also
match on every instance. Values slightly above 100% reflect the best-known
comparator and its recorded precision; LLM solutions never enter the comparator.

The [validation report](validation.json) records all 20 valid replayed L2
artifacts and four completed L1 models. All 4,660 corrected L2 decisions and
48 replacement L1 decisions passed feasibility and independent scalar revenue
checks. Original artifact code and unaffected records are unchanged. Eighty
additional old-cap controls, four per valid artifact, reproduce the original
revenues. The original defective stability draw remains excluded.

## Public-release path redaction

The original gzip archives retain their original bytes and source hashes. The
public builder shortens local paths in traceback logs in canonical JSONL records.
The release manifest declares this transformation. The verifier permits only
these path substitutions inside cell output logs when comparing unchanged L1
queries with their archives; code, prompts, decisions, revenues and all other
fields remain strict. This changes no experiment or numerical result.
