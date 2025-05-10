## Inventory

### Dataset Preparation

- **Script**: `examples/inventory/evaluation/gen_data.py` 
  Generates training and testing datasets
- **Output Location**: `examples/inventory/evaluation/data/`
- **File Naming Pattern**: `{train/test}_{demand}_{volatility}.json` 

### Train

#### Execution Script
`examples/inventory/runEoH.py`

```python
# Set parameters #
paras.set_paras(method = "eoh",
                problem = "inventory",
                demand = 80,  # 50, 60, 70, 80
                volatility = 'low',  # low, median, high
                llm_api_endpoint = "<LLM ENDPOINT>", 
                llm_api_key = "<YOUR API KEY>", 
                llm_model = "<LLM MODEL>", 
                ecc_pop_size = 30,  # number of samples in each population
                ec_n_pop= 10,  # number of populations
                exp_n_proc = 4,  # multi-core parallel
                exp_debug_mode = False,
                exp_use_continue = True,
                create_initial = False,
                load_pop_path ="results/pops/population_generation_0.json",
                load_pop_id = 0)
```

#### Dataset Selection Parameters
- **`demand`**: Integer value or `None` (wildcard)
- **`volatility`**: String ('low', 'medium', 'high')

##### Examples:
| demand | volatility | Training File       | Testing File        |
|--------|------------|---------------------|---------------------|
| 80     | 'low'      | `train_80_low.json` | `test_80_low.json`  |
| None   | 'low'      | `train_*_low.json`  | `test_*_low.json`   |

#### Initial Population Configuration

##### Options:
1. **LLM-Generated Population**  
   - Set `create_initial=True` to generate initial heuristics via LLM

2. **Predefined Heuristics**
   
   - Set `load_pop_path` to your heuristics file path
   - File format requirements for `load_pop_path`:
     ```json
     {
       "algorithm": "your_algorithm_name",
       "code": "your_implementation",
       "objective": null,	\\ This field will be auto-calculated
       "other_inf": null
     }
     ```
   
   ⚠️*Note1*: You can use both methods simultaneously (LLM generation + predefined heuristics)
   
   ⚠️*Note2*: You cannot set both `create_initial=False` AND `load_pop_path=None`, as this would result in having no initial heuristics available.


### Evaluate

#### Manual Evaluation (`runEval`)
1. Copy your heuristic implementation to `heuristic.py` 
   **Important**: Ensure the function name, inputs, and outputs exactly match the evaluation block's requirements.

#### Automated Tools

For easier processing and evaluation of LLM outputs:

1. **Formatting LLM Outputs**  
   - LLM outputs are stored as JSON files (hard to read directly)  
   - Run: `examples/inventory/extract_code.py`  
   - Output: Formatted code in `examples/inventory/evaluation/code_extracted.txt`

2. **Automatic Evaluation**  
   - Run: `examples/inventory/evaluation/autoEval.py` 
   - This evaluates all code in `code_extracted.txt` 
   - Results saved to: `examples/inventory/evaluation/eval_results.txt`
   
   ⚠️*Note3*:  Ensure `runEval.py` is correctly configured because `autoEval.py` directly executes `runEval.py` and depends on its proper functioning

### Core Implementation Files

#### Problem Definition
`eoh/src/eoh/problems/optimization/inventory/prompts.py`  

- Problem description
- Function signature specifications
- LLM prompt engineering templates

#### Training Pipeline Configuration
`eoh/src/eoh/problems/optimization/inventory/run.py`  

1. **Training Data Loading**  
   - Dataset selection logic  
   - Preprocessing routines  

2. **Heuristic Evaluation**  
   - Performance metrics calculation  
   - Training set evaluation methodology
