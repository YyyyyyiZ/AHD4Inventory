import os
import json
from datetime import datetime

from ...llm.interface_LLM import InterfaceLLM
from .utils import *


class Evolution:

    def __init__(self, api_endpoint, api_key, model_LLM, llm_use_local, llm_local_url, debug_mode, prompts,
                 analyzer, external_optimizer, param_loc, exp_output_path, **kwargs):

        # set prompt interface
        # getprompts = GetPrompts()
        self.prompt_task = prompts.get_task() + analyzer.param
        self.prompt_func_name = prompts.get_func_name()
        self.prompt_func_inputs = prompts.get_func_inputs()
        self.prompt_func_outputs = prompts.get_func_outputs()
        self.prompt_inout_inf = prompts.get_inout_inf()
        self.prompt_other_inf = prompts.get_other_inf()
        if len(self.prompt_func_inputs) > 1:
            self.joined_inputs = ", ".join("'" + s + "'" for s in self.prompt_func_inputs)
        else:
            self.joined_inputs = "'" + self.prompt_func_inputs[0] + "'"

        if len(self.prompt_func_outputs) > 1:
            self.joined_outputs = ", ".join("'" + s + "'" for s in self.prompt_func_outputs)
        else:
            self.joined_outputs = "'" + self.prompt_func_outputs[0] + "'"

        # set LLMs
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode  # close prompt checking
        self.exp_output_path = exp_output_path
        self.init_base_prompt()
        self.analyzer = analyzer

        self.interface_llm = InterfaceLLM(self.api_endpoint, self.api_key, self.model_LLM, llm_use_local, llm_local_url,
                                          self.debug_mode)
        self.external_optimizer = external_optimizer
        self.param_loc = param_loc

    def init_base_prompt(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(self.current_dir)

        self.prompt_i1 = file_to_string(f'{self.file_path}/operator/prompt_i1.txt')
        self.prompt_e1 = file_to_string(f'{self.file_path}/operator/prompt_e1.txt')
        self.prompt_e2 = file_to_string(f'{self.file_path}/operator/prompt_e2.txt')
        self.prompt_m1 = file_to_string(f'{self.file_path}/operator/prompt_m1.txt')
        self.prompt_m2 = file_to_string(f'{self.file_path}/operator/prompt_m2.txt')
        self.prompt_temp = file_to_string(f'{self.file_path}/operator/prompt_temp.txt')
        self.prompt_m2plural = file_to_string(f'{self.file_path}/operator/prompt_m2plural.txt')
        self.prompt_m3 = file_to_string(f'{self.file_path}/operator/prompt_m3.txt')

    def external_optimizer_prompt(self):
        if self.param_loc == 'start':
            prompt_content = """When providing code, follow these requirements for optimizable parameters:
                        1. DECLARE ALL OPTIMIZABLE PARAMETERS AT THE BEGINNING:
                           - Group all optimizable parameters in a dedicated section at the start
                           - Each declaration must use this format:
                             param_name = initial_value  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'float'}"

                        2. PARAMETER USAGE IN CODE:
                           - After declaration section, only reference parameters by name
                           - Never use hard-coded numeric values that should be parameters
                           - Example correct usage:
                             order_quantity = base_stock * 2  # NOT: order_quantity = 100

                        3. REQUIREMENTS:
                           - All optimizable parameters must be continuous variables
                           - Include these attributes for each parameter:
                             * initial: Starting value
                             * min: Minimum allowed value
                             * max: Maximum allowed value
                             * type: Data type ('int' or 'float')
                           - No function parameters may be marked as optimizable. Only mark parameters that are assigned within the code body.

                        Example structure:
                        # --- OPTIMIZABLE PARAMETERS ---
                        base_stock = 50  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'int'}
                        reorder_point = 30  # OPT_PARAM: {'initial': 30, 'min': 5, 'max': 150, 'type': 'int'}

                        # --- MAIN CODE ---
                        if inventory < reorder_point:
                            order = base_stock - current_inventory

                        DON'T mark more than 10 optimizable parameters.
                        DON'T mark any optimizable parameters in the main code.
                        """

        else:  # default parameter location
            prompt_content = "1. Mark optimizable parameters in the code with `# OPT_PARAM: ` comments, like this:" \
                             + "\n" + "base_stock = 50  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'float'}" \
                             + "\n" + "2. comments should follow the parameter in the same line." \
                             + "\n" + "3. Only mark parameters that are assigned within the code body (not function inputs)" \
                             + "\n" + "4. Only mark continuous parameters assigned with an equals sign (`=`)" \
                             + "\n" + "5. DON'T mark more than 10 optimizable parameters." \
                             + "\n" + "6. "

        return prompt_content

    def op_prompt(self, operator):
        if operator == 'm1' or operator == 'm2' or operator == 'm3':
            op_prompt_content = "\n\nGiven a policy and the demand trajectories, your task is to change the policy to produce an improved implementation that achieves a lower average cumulative total cost on the training demand trajectories.\n\n"
        elif operator == 'm2plural':
            op_prompt_content = "\n\nGiven some policies and the demand trajectories, your task is to change the policies to produce an improved implementation that achieves a lower average cumulative total cost on the training demand trajectories.\n\n"
        elif operator == 'e1':
            op_prompt_content = "\n\nGiven some policies and the demand trajectories, your task is to change the policies to produce a different implementation.\n\n"
        elif operator == 'e2':
            op_prompt_content = "\n\nGiven some policies and the demand trajectories, your task is to change the policies to produce a similar implementation.\n\n"
        elif operator == 'i1':
            op_prompt_content = "\n\nGiven the demand trajectories, your task is to design policies for the above problem.\n\n"
        else:
            raise ValueError(f"Operator {operator} not recognized")
        return op_prompt_content

    def get_prompt_i1(self):
        prompt_content = self.prompt_i1.format(
            prompt_task=self.prompt_task,
            data_summary=self.analyzer.get_data_summary(),
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/i1_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_e1(self, indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = prompt_indiv + "No." + str(i + 1) + " policy code: \n" + indivs[i]['code'] + "\n" + "\n"
        prompt_content = self.prompt_e1.format(
            prompt_task=self.prompt_task,
            num_indivs=str(len(indivs)),
            code_indivs=prompt_indiv,
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance(indivs),
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/e1_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_e2(self, indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = prompt_indiv + "No." + str(i + 1) + " policy code: \n" + indivs[i]['code'] + "\n" + "\n"
        prompt_content = self.prompt_e2.format(
            prompt_task=self.prompt_task,
            num_indivs=str(len(indivs)),
            code_indivs=prompt_indiv,
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance(indivs),
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/e2_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_m1(self, indiv1):
        prompt_content = self.prompt_m1.format(
            prompt_task=self.prompt_task + self.op_prompt('m1'),
            # algo_decsr=indiv1['algorithm'],
            algo_code=indiv1['code'],
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance([indiv1]),
            # prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/m1_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_m2(self, indiv1):
        # Extract optimizable parameters from the parent code
        optimizable_params_text = self._extract_optimizable_params_info(indiv1)

        prompt_content = self.prompt_m2.format(
            prompt_task=self.prompt_task,
            algo_code=indiv1['code'],
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance([indiv1]),
            optimizable_params=optimizable_params_text,
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/m2_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_m2plural(self, indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = prompt_indiv + "No." + str(i + 1) + " policy code: \n" + indivs[i]['code'] + "\n" + "\n"
        prompt_content = self.prompt_m2plural.format(
            prompt_task=self.prompt_task,
            num_indivs=str(len(indivs)),
            algo_code=prompt_indiv,
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance(indivs),
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/m2plural_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_temp_task(self):
        task = """
ROLE:
You are a research engineer specializing in inventory control (lost-sales, deterministic lead time).
Your job is to write a STRICTLY STATIONARY Python policy.

TASK:
Given the simulator definition and historical demand trajectories, propose a modified policy
```compute_order_amount(on_hand_inventory, pipeline_orders)    return order_amount``` that achieves a LOWER average cost
than the incumbent.

HARD CONSTRAINTS (must satisfy ALL):
- Strict stationarity: output depends ONLY on current inputs.
- No hidden state: no globals, no function attributes, no caching, no mutation across calls.
- Return a NON-NEGATIVE INT.
- Use only Python built-ins (and math if needed). Keep it fast and deterministic.
- Mark <= 10 tunable parameters using EXACT inline format:
  x = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.0, "max": 10.0, "type": "float"}
  (Only parameters assigned with "=" inside function body; no more than 10.)

OUTPUT FORMAT (STRICT):
1) Output only ONE Python function named compute_order_amount (no extra helper functions).
2) After the function, output exactly one line:
   {{concise explanation of what changed and why it should reduce cost}}
No other text.

SIMULATOR + DATA

Inventory control, single item, finite horizon.
- Selling horizon: T = 50 periods
- Deterministic delivery lead time: L = 6 periods
- Total periods per trajectory: L+T = 56 (t = 1..56)
- Two phases:
  (1) Planning phase (t = 1..L): D_t = 0 (NO demand; zeros are placeholders), and NO costs are incurred.
  (2) Selling phase  (t = L+1..L+T): demand occurs and costs are incurred.

State observed at the START of period t:
- On-hand inventory I_t >= 0 (pre-arrival inventory)
- Pipeline orders Q_t = [q_{t,1}, q_{t,2}, ..., q_{t,L}] (length L, FIFO oldest->newest)
  * pipeline_orders[0] = q_{t,1} arrives at the beginning of the CURRENT period t
  * pipeline_orders[-1] = q_{t,L} arrives at the beginning of period t+L-1

Within each period t (evaluator dynamics):
1) Arrival of oldest pipeline order:
   q_arrive = q_{t,1} = Q_t[0]
   Available before demand = I_t + q_arrive
2) Order placement:
   a_t = policy(I_t, Q_t)   # a_t >= 0, arrives at beginning of period t+L
3) Demand realization:
   D_t is exogenous (historical). For t<=L, D_t=0.
4) Cost (ONLY for selling phase t > L):
   holding = h * max(0, I_t + q_arrive - D_t)
   lost    = p * max(0, D_t - I_t - q_arrive)
   cost_t  = holding + lost
5) State transition:
   I_{t+1} = max(0, I_t + q_arrive - D_t)
   Q_{t+1} = [q_{t,2}, q_{t,3}, ..., q_{t,L}, a_t]

Initial state (for every trajectory):
- I_1 = 0
- Q_1 = [0, 0, 0, 0, 0, 0]  # length L

Objective (how you are evaluated):
Given N historical demand trajectories, minimize the average total cost over the selling phase:
avg_cost = (1/N) * sum_{n=1..N} sum_{t=L+1..L+T} cost_t^{(n)}

Equivalent evaluator pseudocode:
total_cost = 0
for each trajectory n in 1..N:
  I = 0
  Q = [0]*L
  for t in 1..L+T:
    q_arrive = Q[0]
    a = policy(I, Q)
    D = 0 if t<=L else SELLING_DEMANDS[n-1][t-L-1]
    if t > L:
      total_cost += h*max(0, I + q_arrive - D) + p*max(0, D - I - q_arrive)
    I = max(0, I + q_arrive - D)
    Q = Q[1:] + [a]
avg_cost_per_period = total_cost / (N*T)

Problem parameters:
- L = 6
- T = 50
- h = 1
- p = 2
- N = 50
        """
        return task

    def get_prompt_temp(self, indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = prompt_indiv + "No." + str(i + 1) + " policy code: \n" + indivs[i]['code'] + "\n" + "\n"
        prompt_content = self.prompt_temp.format(
            prompt_task=self.get_temp_task(),
            algo_code=prompt_indiv,
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance(indivs),
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/temp_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_m3(self, indiv1):
        # Extract optimizable parameters from the parent code
        optimizable_params_text = self._extract_optimizable_params_info(indiv1)

        prompt_content = self.prompt_m3.format(
            prompt_task=self.prompt_task + self.op_prompt('m3'),
            algo_code=indiv1['code'],
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance([indiv1]),
            optimizable_params=optimizable_params_text,
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt(),
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/m3_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def _get_alg(self, prompt_content):

        response = self.interface_llm.get_response(prompt_content)

        algorithm = re.findall(r"\{\{(.*?)\}\}", response, re.DOTALL)
        # cost = re.findall(r"\[\[\[(.*?)\]\]\]", response, re.DOTALL)
        if len(algorithm) == 0:
            if 'python' in response:
                algorithm = re.findall(r'^.*?(?=python)', response, re.DOTALL)
            elif 'import' in response:
                algorithm = re.findall(r'^.*?(?=import)', response, re.DOTALL)
            else:
                algorithm = re.findall(r'^.*?(?=def)', response, re.DOTALL)

        code = re.findall(r"import.*return", response, re.DOTALL)
        if len(code) == 0:
            code = re.findall(r"def.*return", response, re.DOTALL)

        optim_params = {}
        if self.external_optimizer:
            for line in code[0].split('\n'):
                if "OPT_PARAM:" in line:
                    param_name = self._extract_param_name(line)
                    param_str = line.split("OPT_PARAM:")[1].strip()
                    param_str = param_str.replace("'", '"')
                    param_config = json.loads(param_str)
                    optim_params[param_name] = param_config

        n_retry = 1
        while len(algorithm) == 0:
            if self.debug_mode:
                print("Error: algorithm or code not identified, wait 1 seconds and retrying ... ")

            response = self.interface_llm.get_response(prompt_content)

            algorithm = re.findall(r"\{\{(.*?)\}\}", response, re.DOTALL)
            if len(algorithm) == 0:
                if 'python' in response:
                    algorithm = re.findall(r'^.*?(?=python)', response, re.DOTALL)
                elif 'import' in response:
                    algorithm = re.findall(r'^.*?(?=import)', response, re.DOTALL)
                else:
                    algorithm = re.findall(r'^.*?(?=def)', response, re.DOTALL)

            code = re.findall(r"import.*return", response, re.DOTALL)
            if len(code) == 0:
                code = re.findall(r"def.*return", response, re.DOTALL)

            if self.external_optimizer:
                for line in code[0].split('\n'):
                    if "OPT_PARAM:" in line:
                        param_name = self._extract_param_name(line)
                        param_str = line.split("OPT_PARAM:")[1].strip()
                        param_str = param_str.replace("'", '"')
                        param_config = json.loads(param_str)
                        optim_params[param_name] = param_config
            if n_retry > 3:
                break
            n_retry += 1

        algorithm = algorithm[0]
        code = code[0]
        # cost = cost[0]
        cost = None

        code_all = code + " " + ", ".join(s for s in self.prompt_func_outputs)
        # print("llm response:", code_all)
        return [code_all, algorithm, optim_params, cost]

    def _extract_param_name(self, oneline) -> str:
        match = re.match(r'^\s*(\w+)\s*(?:==|>=|<=|=|>|<)', oneline)
        return match.group(1) if match else oneline.strip()

    def _extract_optimizable_params_info(self, indiv):
        """Extract optimizable parameters from the parent code and format them for the prompt."""
        code = indiv['code']
        opt_params = {}
        simple_params = {}

        # Extract parameters marked with OPT_PARAM
        for line in code.split('\n'):
            if "OPT_PARAM:" in line:
                param_name = self._extract_param_name(line)
                param_str = line.split("OPT_PARAM:")[1].strip()
                param_str = param_str.replace("'", '"')
                try:
                    param_config = json.loads(param_str)
                    opt_params[param_name] = param_config
                except:
                    pass
            else:
                # Try to extract simple numeric assignments (e.g., base_stock = 20)
                # Skip function definitions and returns
                if 'def ' not in line and 'return ' not in line and '=' in line:
                    # Simple pattern: variable_name = numeric_value
                    import re
                    match = re.match(r'^\s*(\w+)\s*=\s*([0-9.]+)\s*(?:#.*)?$', line.strip())
                    if match:
                        param_name = match.group(1)
                        param_value = match.group(2)
                        # Convert to appropriate type
                        if '.' in param_value:
                            simple_params[param_name] = float(param_value)
                        else:
                            simple_params[param_name] = int(param_value)

        # Format the parameters for the prompt
        if opt_params:
            params_text = "The current algorithm has the following optimizable parameters:\n"
            for param_name, config in opt_params.items():
                params_text += f"- {param_name}: current value = {config.get('initial', 'N/A')}, "
                params_text += f"min = {config.get('min', 'N/A')}, max = {config.get('max', 'N/A')}, "
                params_text += f"type = {config.get('type', 'N/A')}\n"
            params_text += "\nIf you choose Option 1 (Parameter Adjustment), you should focus on adjusting these parameters."
        elif simple_params:
            params_text = "The current algorithm has the following numerical parameters that could be adjusted:\n"
            for param_name, value in simple_params.items():
                param_type = 'float' if isinstance(value, float) else 'int'
                params_text += f"- {param_name}: current value = {value} (type: {param_type})\n"
            params_text += "\nIf you choose Option 1 (Parameter Adjustment), you should focus on adjusting these parameters."
        else:
            params_text = "No explicit optimizable parameters were identified in the current algorithm.\nIf you choose Option 1 (Parameter Adjustment), identify which numerical values in the code should be treated as adjustable parameters."

        return params_text

    def _get_reflection(self, prompt_content):
        response = self.interface_llm.get_response(prompt_content)
        return response

    def i1(self):

        prompt_content = self.get_prompt_i1()

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ i1 ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]

    def e1(self, parents):

        prompt_content = self.get_prompt_e1(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ e1 ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]

    def e2(self, parents):

        prompt_content = self.get_prompt_e2(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ e2 ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]

    def m1(self, parents):

        prompt_content = self.get_prompt_m1(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m1 ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]

    def m2(self, parents):

        prompt_content = self.get_prompt_m2(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m2 ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]

    def m2plural(self, parents):

        prompt_content = self.get_prompt_m2plural(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m2plural ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]

    def op_temp(self, parents):

        prompt_content = self.get_prompt_temp(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ temp ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]

    def m3(self, parents):

        prompt_content = self.get_prompt_m3(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m3 ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params, cost]
