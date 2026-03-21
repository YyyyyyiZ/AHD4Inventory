# AHD4Inventory: Evolutionary Heuristic Design for Inventory Control

AHD4Inventory provides the **Evolution of Heuristics (EoH)** pipeline that couples evolutionary computation with large language models (LLMs) to automatically design inventory-control policies. The system targets single-product, lost-sales settings with fixed lead times and supports multiple demand distributions through configurable datasets and prompts.

## Key Features
- **LLM-informed search** that iteratively refines candidate ordering policies using curated prompt templates (classic `v1` and expanded `v2`).【F:eoh/src/eoh/problems/optimization/inventory/prompts.py†L1-L118】
- **Evolutionary optimization** with configurable selection and population management, external optimizers, and optional warm-start from existing heuristics.【F:eoh/src/eoh/methods/eoh/eoh.py†L12-L171】
- **Inventory-focused analyzers** that summarize training trajectories and guide reflection during search.【F:eoh/src/eoh/methods/eoh/eoh.py†L46-L60】
- **Ready-to-run example** for training and evaluating heuristics on synthetic inventory datasets, including tools for generating data and extracting/evaluating LLM-generated code.【F:examples/inventory/runEoH.py†L1-L87】【F:docs/inventory.md†L1-L78】

## Repository Layout
- `eoh/`: Python package implementing the EoH framework, including the main entry point (`eoh.py`), inventory prompts, evolutionary operators, and utilities.【F:eoh/src/eoh/eoh.py†L1-L36】【F:eoh/src/eoh/problems/optimization/inventory/prompts.py†L1-L118】
- `examples/inventory/`: Scripts and configuration templates for running EoH on inventory datasets; includes prebuilt heuristic pools and sanity checks.【F:examples/inventory/runEoH.py†L1-L87】
- `examples/inventory/evaluation/`: Data generation utilities and train/test trajectories used by the inventory example.【F:docs/inventory.md†L3-L15】【F:examples/inventory/evaluation/data/compute_opt.py†L1-L45】
- `docs/`: Task-specific guides outlining dataset preparation, training parameters, and evaluation helpers for the inventory tasks.【F:docs/inventory.md†L1-L78】【F:docs/inventory2.md†L1-L82】

## Requirements
- Python 3.10+
- NumPy, Numba, Joblib, Pandas, SciPy (installed automatically when installing the `eoh` package).【F:eoh/setup.py†L1-L24】

## Installation
Install the EoH package in editable mode from the repository root:

```bash
cd eoh
pip install -e .
```

This exposes the `eoh` module and installs required dependencies.

## Quickstart: Train Heuristics for Inventory Control
1. **Prepare LLM access**: provide an API endpoint, key, and model name (e.g., DeepSeek via `api.deepseek.com`).【F:examples/inventory/runEoH.py†L9-L32】
2. **Launch training** from the repository root:
   ```bash
   python examples/inventory/runEoH.py \
     --llm_api_endpoint <ENDPOINT> \
     --llm_api_key <API_KEY> \
     --llm_model <MODEL> \
     --operator e1 e2 m2 \
     --exp_continue_path base_stock.json \
     --exp_use_continue 1 \
     --ec_pop_size 4 --ec_n_pop 10 \
     --dist normal_std30_L6_c1_5 --n_train 50 --n_horizon 50
   ```
   Key options:
   - `--prompt_version {v1,v2}` selects the prompt template; `v2` is the new default.【F:examples/inventory/runEoH.py†L23-L33】
   - `--operator` chooses evolutionary operators; population size and generations are set via `ec_pop_size` and `ec_n_pop`.【F:examples/inventory/runEoH.py†L34-L47】
   - `--exp_use_continue/--exp_continue_path` load an initial heuristic pool (e.g., `base_stock.json`) and can be combined with `--exp_create_initial` to let the LLM generate additional starters.【F:examples/inventory/runEoH.py†L40-L54】【F:eoh/src/eoh/methods/eoh/eoh.py†L70-L116】
   - `--external_opt` and related arguments enable optional fine-tuning of heuristic parameters via external optimizers (e.g., SciPy).【F:examples/inventory/runEoH.py†L34-L41】【F:eoh/src/eoh/methods/eoh/eoh.py†L38-L54】

3. **Outputs**: Results (populations, reflections, and CSV summaries) are written under the `exp_output_path`, which is auto-generated from the provided configuration unless explicitly set.【F:examples/inventory/runEoH.py†L56-L64】【F:eoh/src/eoh/methods/eoh/eoh.py†L88-L116】

### OpenRouter Quick Tests (Fast / Non-Thinking)

`examples/inventory/runEoH.py` now includes OpenRouter presets for quick model switching:

- `openrouter-minimax-fast` -> `minimax/minimax-m2.5`
- `openrouter-deepseek-fast` -> `deepseek/deepseek-chat`
- `openrouter-gemini-2.5-fast` -> `google/gemini-2.5-flash`
- `openrouter-gpt-5-nano` -> `openai/gpt-5-nano`
- `openrouter-gpt-5-mini` -> `openai/gpt-5-mini`
- `openrouter-gemini-3.0-preview` -> `google/gemini-3-flash-preview`
- `openrouter-grok-4.1-fast` -> `x-ai/grok-4.1-fast`

All presets use endpoint `https://openrouter.ai/api/v1` and force `--llm_reasoning_effort low`.

Example:

```bash
export OPENROUTER_API_KEY=<YOUR_OPENROUTER_KEY>
python examples/inventory/runEoH.py \
  --llm_profile openrouter-grok-4.1-fast \
  --operator e1 e2 m2 \
  --exp_continue_path base_stock.json \
  --exp_use_continue 1 \
  --ec_pop_size 4 --ec_n_pop 10 \
  --dist normal_std30_L6_c1_5 --n_train 50 --n_horizon 50
```

## Dataset Preparation
Use the helper script to create training and testing trajectories:

```bash
python examples/inventory/evaluation/gen_data.py
```

Generated JSON files are stored in `examples/inventory/evaluation/data/` with names encoding demand distribution and cost parameters (e.g., `normal_std30_L6_c1_5_train.json`).【F:docs/inventory.md†L3-L15】 Adjust distribution, demand level, and volatility in the script to match your experiment.

## Evaluation Utilities
- **Manual evaluation**: integrate candidate heuristics into the evaluation harness to measure average costs on the selected dataset.【F:docs/inventory.md†L29-L48】
- **Automatic processing**: use `examples/inventory/extract_code.py` to collect LLM outputs and `examples/inventory/evaluation/autoEval.py` to batch-evaluate them, producing consolidated metrics in `examples/inventory/evaluation/eval_results.txt`.【F:docs/inventory.md†L48-L65】

## Extending the Framework
- Adapt prompt templates or problem definitions under `eoh/src/eoh/problems/optimization/inventory/` to target new inventory settings.【F:eoh/src/eoh/problems/optimization/inventory/prompts.py†L1-L118】
- Customize evolutionary operators and reflection strategies in `eoh/src/eoh/methods/eoh/` to experiment with alternative search dynamics.【F:eoh/src/eoh/methods/eoh/eoh.py†L12-L171】
- Swap or integrate different LLM providers by configuring the API endpoint/key or pointing to a locally hosted model URL in the parameter set (`Paras`).【F:eoh/src/eoh/utils/getParas.py†L38-L66】

## Licensing
This project is released under the MIT License. See [LICENSE](LICENSE) for details.
