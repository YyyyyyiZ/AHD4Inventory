import numpy as np
import os
import json
from datetime import datetime

from ...llm.interface_LLM import InterfaceLLM
from .reflection.utils import *


class Evolution:

    def __init__(self, api_endpoint, api_key, model_LLM, llm_use_local, llm_local_url, debug_mode, prompts,
                 analyzer, external_optimizer, param_loc, exp_output_path, **kwargs):

        # set prompt interface
        #getprompts = GetPrompts()
        self.prompt_task = prompts.get_task()+analyzer.param
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
        self.file_path = os.path.join(self.current_dir, 'reflection')

        self.prompt_i1 = file_to_string(f'{self.file_path}/common/prompt_i1.txt')
        self.prompt_e1 = file_to_string(f'{self.file_path}/common/prompt_e1.txt')
        self.prompt_e2 = file_to_string(f'{self.file_path}/common/prompt_e2.txt')
        self.prompt_m1 = file_to_string(f'{self.file_path}/common/prompt_m1.txt')
        self.prompt_m2 = file_to_string(f'{self.file_path}/common/prompt_m2.txt')
        self.prompt_data_summary = file_to_string(f'{self.file_path}/common/prompt_data_summary.txt')

    def external_optimizer_prompt(self):
        if self.param_loc == 'start':
            prompt_content = """When providing code, follow these requirements for optimizable parameters:
                        1. DECLARE ALL OPTIMIZABLE PARAMETERS AT THE BEGINNING:
                           - Group all optimizable parameters in a dedicated section at the start
                           - Each declaration must use this format:
                             param_name = initial_value  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'int'}"

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
            prompt_content = "Then, Mark optimizable parameters in the code with `# OPT_PARAM: ` comments, like this:" \
                             + "\n" + "base_stock = 50  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'int'}" \
                             + "\n" + "Follow these requirements: 1. comments should follow the parameter in the same line." \
                             + "\n" + "2. Only mark parameters that are assigned within the code body (not function inputs)" \
                             + "\n" + "3. Only mark continuous parameters assigned with an equals sign (`=`)" \
                             + "\n" + "4. DON'T mark more than 10 optimizable parameters."

        return prompt_content

    def get_prompt_i1(self):
        prompt_content = self.prompt_i1.format(
            prompt_task=self.prompt_task,
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf
        )
        return prompt_content

    def get_prompt_e1(self, indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = prompt_indiv + "No." + str(i + 1) + " algorithm: \n" + indivs[i]['code'] + "\n"
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
            prompt_indiv = prompt_indiv + "No." + str(i + 1) + " algorithm: \n" + indivs[i]['code'] + "\n"
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
            prompt_task=self.prompt_task,
            # algo_decsr=indiv1['algorithm'],
            algo_code=indiv1['code'],
            data_summary=self.analyzer.get_data_summary(),
            # algo_performance=self.analyzer.get_algo_performance([indiv1]),
            # prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            # external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/prompt_for_code/m1_{timestamp}.txt"
        with open(file_name, 'a') as file:
            file.writelines(prompt_content + '\n')
        return prompt_content

    def get_prompt_m2(self, indiv1):
        prompt_content = self.prompt_m2.format(
            prompt_task=self.prompt_task,
            algo_code=indiv1['code'],
            data_summary=self.analyzer.get_data_summary(),
            algo_performance=self.analyzer.get_algo_performance([indiv1]),
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
        while len(algorithm) == 0 or len(code) == 0:
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
        return [code_all, algorithm, optim_params, cost]

    def _extract_param_name(self, oneline) -> str:
        match = re.match(r'^\s*(\w+)\s*(?:==|>=|<=|=|>|<)', oneline)
        return match.group(1) if match else oneline.strip()

    def _get_reflection(self, prompt_content):
        response = self.interface_llm.get_response(prompt_content)
        return response

    def i1(self):

        prompt_content = self.get_prompt_i1()

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ i1 ] : \n", prompt_content)
            print(">>> Press 'Enter' to continue")
            input()

        [code_all, algorithm, optim_params] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]

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
