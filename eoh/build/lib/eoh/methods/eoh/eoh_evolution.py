import os
import json
from datetime import datetime

from ...llm.interface_LLM import InterfaceLLM
from .utils import *


class Evolution:

    def __init__(self, api_endpoint, api_key, model_LLM, llm_use_local, llm_local_url, debug_mode, prompts,
                 analyzer, external_optimizer, param_loc, param_num, exp_output_path, **kwargs):

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
        self.prompt_with_explanations = kwargs.get("prompt_with_explanations", False)
        self.init_base_prompt()
        self.analyzer = analyzer

        self.interface_llm = InterfaceLLM(self.api_endpoint, self.api_key, self.model_LLM, llm_use_local, llm_local_url,
                                          self.debug_mode)
        self.external_optimizer = external_optimizer
        self.param_loc = param_loc
        self.param_num = param_num

    def init_base_prompt(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(self.current_dir)

        self.prompt_i1 = file_to_string(f'{self.file_path}/operator/prompt_i1.txt')
        self.prompt_e1 = file_to_string(f'{self.file_path}/operator/prompt_e1.txt')
        self.prompt_e2 = file_to_string(f'{self.file_path}/operator/prompt_e2.txt')
        self.prompt_m1 = file_to_string(f'{self.file_path}/operator/prompt_m1.txt')
        if self.prompt_with_explanations:
            self.prompt_m2 = file_to_string(f'{self.file_path}/operator/prompt_m2.txt')
            self.prompt_m2plural = file_to_string(f'{self.file_path}/operator/prompt_m2plural.txt')
        else:
            self.prompt_m2 = file_to_string(f'{self.file_path}/operator/prompt_m2_legacy.txt')
            self.prompt_m2plural = file_to_string(f'{self.file_path}/operator/prompt_m2plural_legacy.txt')
        self.prompt_m3 = file_to_string(f'{self.file_path}/operator/prompt_m3.txt')

    def external_optimizer_prompt(self):
        if self.param_loc == 'start':
            prompt_content = f"""When providing code, follow these requirements for optimizable parameters:
                            1. DECLARE ALL OPTIMIZABLE PARAMETERS AT THE BEGINNING:
                               - Group all optimizable parameters in a dedicated section at the start
                               - Each declaration must use this format:
                                 param_name = initial_value  # OPT_PARAM: {{'initial': 50, 'min': 10, 'max': 200, 'type': 'float'}}

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
                            base_stock = 50  # OPT_PARAM: {{'initial': 50, 'min': 10, 'max': 200, 'type': 'int'}}
                            reorder_point = 30  # OPT_PARAM: {{'initial': 30, 'min': 5, 'max': 150, 'type': 'int'}}

                            # --- MAIN CODE ---
                            if inventory < reorder_point:
                                order = base_stock - current_inventory

                            DON'T mark more than 10 optimizable parameters.
                            DON'T mark any optimizable parameters in the main code.
                            """

        else:  # default parameter location
            prompt_content = (
                    "1. Mark optimizable parameters in the code with `# OPT_PARAM: ` comments, like this:"
                    + "\n" + "base_stock = 50  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'float'}"
                    + "\n" + "2. comments should follow the parameter in the same line."
                    + "\n" + "3. Only mark parameters that are assigned within the code body (not function inputs)"
                    + "\n" + "4. Only mark continuous parameters assigned with an equals sign (`=`)"
                    + "\n" + f"5. DON'T mark more than 10 optimizable parameters."
                    + "\n" + f"6. The generated code must contain at most {self.param_num} parameters that satisfy the criteria for optimizable parameters. Do not merely leave extra eligible parameters unmarked; instead, structure the code so that no more than {self.param_num} parameters are eligible to be marked."
                    + "\n" + "7. "
            )

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
        with open(file_name, 'w') as file:
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
        with open(file_name, 'w') as file:
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
        with open(file_name, 'w') as file:
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
        with open(file_name, 'w') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def _clean_reasoning_markers(self, text):
        """Remove any {{{{}}}} or {{}} reasoning markers from text to ensure they don't appear in prompts."""
        if not text:
            return text
        # Remove quadruple brace content {{{{...}}}}
        cleaned = re.sub(r'\{\{\{\{.*?\}\}\}\}', '', text, flags=re.DOTALL)
        # Also remove double brace content {{...}} (for backward compatibility)
        cleaned = re.sub(r'\{\{.*?\}\}', '', cleaned, flags=re.DOTALL)
        return cleaned.strip()

    def _extract_reasoning_block(self, text):
        """Extract reasoning wrapped in {{{{...}}}} or {{...}} for m2-style operators."""
        if not text:
            return ""
        match = re.search(r"\{\{\{\{(.*?)\}\}\}\}", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"\{\{(.*?)\}\}", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def get_prompt_m2(self, indiv1):
        # Extract optimizable parameters from the parent code
        optimizable_params_text = self._extract_optimizable_params_info(indiv1)

        # Clean any reasoning markers from fields before showing in prompt
        clean_description = self._clean_reasoning_markers(indiv1.get('description', 'Not provided'))
        clean_code = self._clean_reasoning_markers(indiv1['code'])
        clean_intuition = self._clean_reasoning_markers(indiv1.get('intuition', 'Not provided'))

        prompt_content = self.prompt_m2.format(
            prompt_task=self.prompt_task,
            algo_code=clean_code,
            algo_description=clean_description,
            algo_intuition=clean_intuition,
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
            reasoning_braces="{{}}",
            reasoning_block="{{Your step-by-step reasoning process here.}}",
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/m2_{timestamp}.txt"
        with open(file_name, 'w') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_m2plural(self, indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            # Clean any reasoning markers from fields before showing in prompt
            clean_description = self._clean_reasoning_markers(indivs[i].get('description', 'Not provided'))
            clean_code = self._clean_reasoning_markers(indivs[i]['code'])
            clean_intuition = self._clean_reasoning_markers(indivs[i].get('intuition', 'Not provided'))

            prompt_indiv += f"No.{i + 1} policy:\n\n"
            prompt_indiv += f"Description: {clean_description}\n\n"
            prompt_indiv += f"Code:\n{clean_code}\n\n"
            prompt_indiv += f"Intuition: {clean_intuition}\n\n"
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
            reasoning_braces="{{}}",
            reasoning_block="{{Your step-by-step reasoning process here.}}",
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/m2plural_{timestamp}.txt"
        with open(file_name, 'w') as file:
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
        with open(file_name, 'w') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def _get_alg_with_metadata(self, prompt_content):
        """
        Parse LLM response that includes DESCRIPTION, CODE, and INTUITION sections.
        Returns: [code, algorithm, description, intuition, optim_params, cost]
        """
        response = self.interface_llm.get_response(prompt_content)

        # Extract description
        description_match = re.search(r'DESCRIPTION:\s*(.*?)(?=CODE:|$)', response, re.DOTALL | re.IGNORECASE)
        description = description_match.group(1).strip() if description_match else ""

        # Extract intuition (stop at quadruple braces {{{{)
        intuition_match = re.search(r'INTUITION:\s*(.*?)(?=\{\{\{\{|\{\{|$)', response, re.DOTALL | re.IGNORECASE)
        intuition = intuition_match.group(1).strip() if intuition_match else ""

        # Extract algorithm explanation (from quadruple curly braces {{{{...}}}}) - this is for storage only, not for next gen prompts
        algorithm = [self._extract_reasoning_block(response) or ""]

        # Extract code - stop before {{}} to exclude reasoning from code
        # First try to extract from CODE: section until INTUITION: or {{
        code_match = re.search(r'CODE:\s*(.*?)(?=INTUITION:|$)', response, re.DOTALL | re.IGNORECASE)
        if code_match:
            code_section = code_match.group(1)
            # Now extract actual Python code from this section
            code = re.findall(r"(?:import.*?return|def.*?return)", code_section, re.DOTALL)
        else:
            # Fallback: extract code the old way but stop before {{
            code = re.findall(r"import.*?(?=\{\{)", response, re.DOTALL)
            if len(code) == 0:
                code = re.findall(r"def.*?(?=\{\{)", response, re.DOTALL)
            if len(code) == 0:
                code = re.findall(r"import.*return", response, re.DOTALL)
            if len(code) == 0:
                code = re.findall(r"def.*return", response, re.DOTALL)

        # Extract optimizable parameters
        optim_params = {}
        if self.external_optimizer and len(code) > 0:
            for line in code[0].split('\n'):
                if "OPT_PARAM:" in line:
                    param_name = self._extract_param_name(line)
                    param_str = line.split("OPT_PARAM:")[1].strip()
                    param_str = param_str.replace("'", '"')
                    try:
                        param_config = json.loads(param_str)
                        optim_params[param_name] = param_config
                    except:
                        pass

        # Retry logic if parsing fails
        n_retry = 1
        while len(code) == 0 and n_retry <= 3:
            if self.debug_mode:
                print("Error: code not identified, wait 1 seconds and retrying ... ")

            response = self.interface_llm.get_response(prompt_content)

            # Re-extract all components
            description_match = re.search(r'DESCRIPTION:\s*(.*?)(?=CODE:|$)', response, re.DOTALL | re.IGNORECASE)
            description = description_match.group(1).strip() if description_match else ""

            intuition_match = re.search(r'INTUITION:\s*(.*?)(?=\{\{\{\{|\{\{|$)', response, re.DOTALL | re.IGNORECASE)
            intuition = intuition_match.group(1).strip() if intuition_match else ""

            algorithm = [self._extract_reasoning_block(response) or ""]

            # Extract code - stop before {{}} to exclude reasoning from code
            code_match = re.search(r'CODE:\s*(.*?)(?=INTUITION:|$)', response, re.DOTALL | re.IGNORECASE)
            if code_match:
                code_section = code_match.group(1)
                code = re.findall(r"(?:import.*?return|def.*?return)", code_section, re.DOTALL)
            else:
                code = re.findall(r"import.*?(?=\{\{)", response, re.DOTALL)
                if len(code) == 0:
                    code = re.findall(r"def.*?(?=\{\{)", response, re.DOTALL)
                if len(code) == 0:
                    code = re.findall(r"import.*return", response, re.DOTALL)
                if len(code) == 0:
                    code = re.findall(r"def.*return", response, re.DOTALL)

            if self.external_optimizer and len(code) > 0:
                optim_params = {}
                for line in code[0].split('\n'):
                    if "OPT_PARAM:" in line:
                        param_name = self._extract_param_name(line)
                        param_str = line.split("OPT_PARAM:")[1].strip()
                        param_str = param_str.replace("'", '"')
                        try:
                            param_config = json.loads(param_str)
                            optim_params[param_name] = param_config
                        except:
                            pass

            n_retry += 1

        algorithm = algorithm[0] if len(algorithm) > 0 else ""
        code = code[0] if len(code) > 0 else ""
        cost = None

        code_all = code + " " + ", ".join(s for s in self.prompt_func_outputs)

        return [description, code_all, intuition, algorithm, optim_params, cost]

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

        if self.prompt_with_explanations:
            [description, code_all, intuition, algorithm, optim_params, cost] = self._get_alg_with_metadata(
                prompt_content)
        else:
            [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)
            description = ""
            intuition = ""

        if self.debug_mode:
            if self.prompt_with_explanations:
                print("\n >>> check description: \n", description)
                print("\n >>> check designed code: \n", code_all)
                print("\n >>> check intuition: \n", intuition)
                print("\n >>> check designed algorithm: \n", algorithm)
            else:
                print("\n >>> check designed code: \n", code_all)
                print("\n >>> check designed algorithm: \n", algorithm)
            print(">>> Press 'Enter' to continue")
            input()

        return [description, code_all, intuition, algorithm, optim_params, cost]

    def m2plural(self, parents):

        prompt_content = self.get_prompt_m2plural(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m2plural ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        if self.prompt_with_explanations:
            [description, code_all, intuition, algorithm, optim_params, cost] = self._get_alg_with_metadata(
                prompt_content)
        else:
            [code_all, algorithm, optim_params, cost] = self._get_alg(prompt_content)
            description = ""
            intuition = ""

        if self.debug_mode:
            if self.prompt_with_explanations:
                print("\n >>> check description: \n", description)
                print("\n >>> check designed code: \n", code_all)
                print("\n >>> check intuition: \n", intuition)
                print("\n >>> check designed algorithm: \n", algorithm)
            else:
                print("\n >>> check designed code: \n", code_all)
                print("\n >>> check designed algorithm: \n", algorithm)
            print(">>> Press 'Enter' to continue")
            input()

        return [description, code_all, intuition, algorithm, optim_params, cost]

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
