# Inventory2

## Dataset Preparation

- **Script**: `examples/inventory2/evaluation/gen_data.py` 
  Generates training and testing datasets
- **Output Location**: `examples/inventory2/evaluation/data/`
- **File Naming Pattern**: `{distribution}_{train/test}_{demand}_{volatility}.json` 

## Train

### Execution Script
`examples/inventory2/runEoH.py`

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

paras.set_paras(method = "eoh",
                problem = "inventory2",
                dist = 'poisson',
                demand = 80,
                volatility = 'low',
                llm_api_endpoint = "<LLM ENDPOINT>", 
                llm_api_key = "<YOUR API KEY>", 
                llm_model = "<LLM MODEL>", 
                ecc_pop_size = 10,  # number of samples in each population
                ec_n_pop= 2,  # number of populations
                exp_n_proc = 4,  # multi-core parallel
                exp_use_continue = 1,    # load existing heuristics
                exp_continue_path ="results/pops/initial_pool.json",   # path to existing heuristics
                exp_create_initial = 0,
                exp_output_path = 'unknown',
                K1=0,
                K2=1,   # 'mimic_best_sample', 'correct_worst_sample', 'hybrid', 'multi_comparative_reflection'
                external_optimizer='scipy',
                background_info='exactdata',
                background_type='nofix',
                data_sep='sepp',
                cal_cost='no',
                prompt_type='flow30',  # llm, tool
                repeat=3,
                filename='res_new_design'
                )
```

### Param Ⅰ---Dataset Selection
- `dist`: String ('poison', 'normal')
- **`demand`**: Integer value or `None` (wildcard)
- **`volatility`**: String ('low', 'medium', 'high')

#### Examples:
| dist    | demand | volatility | Training File               | Testing File               |
| ------- | ------ | ---------- | --------------------------- | -------------------------- |
| poisson | 80     | 'low'      | `poisson_train_80_low.json` | `poisson_test_80_low.json` |
| poisson | None   | 'low'      | `poisson_train_*_low.json`  | `poisson_test_*_low.json`  |

### Param Ⅱ---Initial Population

#### Options:
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

### Param Ⅲ---Reflection Type

- `K1`: # good performers
- `K2`: # bad performers
- `prompt_type`: which reflection prompt pattern to use,  must be a subfolder of `\AHD4Inventory\eoh\src\eoh\methods\eoh\reflection\common`

```python
if K1==0 and K2==0:
    reflect = None		# No reflection
elif K1==0 and K2==1:
    reflect = 'correct_worst_sample'
elif K1==1 and K2==0:
    reflect = 'mimic_best_sample'
elif K1==1 and K2==1:
    reflect = 'hybrid'
else:
    reflect = 'multi_comparative_reflection'
```

### Param Ⅳ---Background Information

* `data_sep`: whether to use a separate data reflector or not
  * `sep`: independent data reflector without performance $\to$ *data reflection*, second reflector background information will be None $\to$ *code reflection*. Concatenate *data reflection* and *code reflection* as the *final reflection*

  ⚠️*Note3*: In this case, *data reflection* and *code reflection* are independent and parallel

  * `sepp`: independent data reflector with performance on specified code and all trajectories $\to$ *data reflection*, second reflector info depends on `background_info` $\to$ *final reflection*
  * `no`: no independent data reflector

* `background_info`: which type of background information to use
  * when `data_sep`='sepp' $\to$ available choices: ['no', 'exactdata', 'refonly', 'exactdataref']
  * when `data_sep`='sep' $\to$ all choices are invalid. 
    * Provide all demand trajectories to generate *data reflection*, which will later be concatenated with *code reflection* to generate *final reflection*
    * `background_type`: fix data reflection or not, only valid when `data_sep`='sep'
  * when `data_sep`='no' → available choices: ['no', 'avg', 'interval', 'dataonly', 'data', 'explicit']

* `cal_cost`: include how to compute cost (performance metric)
  * 'no': don't include
  * 'code': provide the pseudocode


### Param Ⅴ---External Optimizer

* `external_opt`: type of external optimizer to use
  * 'no': no external optimizer
  * 'scipy': Scipy optimizer, `AHD4Inventory\eoh\src\eoh\methods\eoh\external_scipy.py`

### Param Ⅵ---Save Results

- `repeat`: Experiment index. For experiments with completely same configurations, use `repeat` to distinguish different runs
- **`filename`**: result storage path, `{filename}.csv


## Evaluate

### Manual Evaluation (`runEval`)
1. Copy your heuristic implementation to `heuristic.py` 
   **Important**: Ensure the function name, inputs, and outputs exactly match the evaluation block's requirements.

### Automated Tools

For easier processing and evaluation of LLM outputs:

1. **Formatting LLM Outputs**  
   - LLM outputs are stored as JSON files (hard to read directly)  
   - Run: `examples/inventory2/extract_code.py`  
   - Output: Formatted code in `examples/inventory2/evaluation/code_extracted.txt`

2. **Automatic Evaluation**  
   - Run: `examples/inventory2/evaluation/autoEval.py` 
   - This evaluates all code in `code_extracted.txt` 
   - Results saved to: `examples/inventory2/evaluation/eval_results.txt`
   
   ⚠️*Note4*:  Ensure `runEval.py` is correctly configured because `autoEval.py` directly executes `runEval.py` and depends on its proper functioning

## Core Implementation Files

### Problem Definition
`eoh/src/eoh/problems/optimization/inventory2/prompts.py`  

- Problem description
- Function signature specifications
- LLM prompt engineering templates

### Training Pipeline Configuration
`eoh/src/eoh/problems/optimization/inventory2/run.py`  

1. **Training Data Loading**  
   - Dataset selection logic  
   - Preprocessing routines  

2. **Heuristic Evaluation**  
   - Performance metrics calculation  
   - Training set evaluation methodology
