import re
import time
import os
import json


from ...llm.interface_LLM import InterfaceLLM
from .reflection.utils import *


class Evolution():

    def __init__(self, api_endpoint, api_key, model_LLM,llm_use_local,llm_local_url, debug_mode,prompts,
                 reflect, external_optimizer, **kwargs):

        # set prompt interface
        #getprompts = GetPrompts()
        self.prompt_task         = prompts.get_task()
        self.prompt_func_name    = prompts.get_func_name()
        self.prompt_func_inputs  = prompts.get_func_inputs()
        self.prompt_func_outputs = prompts.get_func_outputs()
        self.prompt_inout_inf    = prompts.get_inout_inf()
        self.prompt_other_inf    = prompts.get_other_inf()
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
        self.debug_mode = debug_mode # close prompt checking
        self.init_base_prompt()


        self.interface_llm = InterfaceLLM(self.api_endpoint, self.api_key, self.model_LLM,llm_use_local,llm_local_url, self.debug_mode)
        self.reflect = reflect
        if self.reflect:
            self.short_term_reflection_str = ""
            self.long_term_reflection_str = ""
            # self.init_reevo_prompt()
        self.external_optimizer = external_optimizer


    def init_base_prompt(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(self.current_dir, 'reflection')

        self.prompt_i1 = file_to_string(f'{self.file_path}/common/prompt_i1.txt')
        self.prompt_e1 = file_to_string(f'{self.file_path}/common/prompt_e1.txt')
        self.prompt_e2 = file_to_string(f'{self.file_path}/common/prompt_e2.txt')
        self.prompt_m1 = file_to_string(f'{self.file_path}/common/prompt_m1.txt')
        self.prompt_m2 = file_to_string(f'{self.file_path}/common/prompt_m2.txt')
        self.prompt_m3 = file_to_string(f'{self.file_path}/common/prompt_m3.txt')

        self.prompt_mimic_best_sample = file_to_string(f'{self.file_path}/common/mimic_best_sample.txt')
        self.prompt_correct_worst_sample = file_to_string(f'{self.file_path}/common/correct_worst_sample.txt')
        self.prompt_hybrid = file_to_string(f'{self.file_path}/common/hybrid.txt')
        self.prompt_multi_comparative_reflection = file_to_string(f'{self.file_path}/common/multi_comparative_reflection.txt')

    def external_optimizer_prompt(self):
        prompt_content = "Finally, Mark optimizable parameters in the code with `# OPT_PARAM: ` comments, like this:" \
                          + "\n" + "base_stock = 50  # OPT_PARAM: {'initial': 50, 'min': 10, 'max': 200, 'type': 'int'}" \
                          + "\n" + "Follow these requirements: 1. comments should follow the parameter in the same line." \
                          + "\n" + "2. Only mark parameters that are assigned within the code body (not function inputs)" \
                          + "\n" + "3. Only mark continuous parameters assigned with an equals sign (`=`)"
        return prompt_content
        
    def get_prompt_i1(self):
        prompt_content = self.prompt_i1.format(
            prompt_task=self.prompt_task,
            prompt_func_name = self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs = self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf
        )
        return prompt_content

        
    def get_prompt_e1(self,indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv=prompt_indiv+"No."+str(i+1) +" algorithm and the corresponding code are: \n" + indivs[i]['algorithm']+"\n" +indivs[i]['code']+"\n"

        prompt_content = self.prompt_e1.format(
            prompt_task=self.prompt_task,
            num_indivs = str(len(indivs)),
            code_indivs = prompt_indiv,
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
            reflection_content=self.short_term_reflection_str if self.reflect else '',
            # reflection_content=self.short_term_reflection_prompt(indivs) if self.reflect else '',
        )

        return prompt_content
    
    def get_prompt_e2(self,indivs):
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv=prompt_indiv+"No."+str(i+1) +" algorithm and the corresponding code are: \n" + indivs[i]['algorithm']+"\n" +indivs[i]['code']+"\n"

        prompt_content = self.prompt_e2.format(
            prompt_task=self.prompt_task,
            num_indivs=str(len(indivs)),
            code_indivs=prompt_indiv,
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
            reflection_content=self.short_term_reflection_str if self.reflect else '',
            # reflection_content=self.short_term_reflection_prompt(indivs) if self.reflect else '',
        )
        return prompt_content
    
    def get_prompt_m1(self,indiv1):
        prompt_content = self.prompt_m1.format(
            prompt_task=self.prompt_task,
            algo_decsr=indiv1['algorithm'],
            algo_code=indiv1['code'],
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
            reflection_content=self.short_term_reflection_str if self.reflect else '',
            # reflection_content=self.long_term_reflection_str if self.reflect else '',
        )
        return prompt_content
    
    def get_prompt_m2(self,indiv1):
        prompt_content = self.prompt_m1.format(
            prompt_task=self.prompt_task,
            algo_descr=indiv1['algorithm'],
            algo_code=indiv1['code'],
            prompt_func_name=self.prompt_func_name,
            prompt_func_num_inputs=str(len(self.prompt_func_inputs)),
            prompt_func_inputs=self.joined_inputs,
            prompt_func_num_outputs=str(len(self.prompt_func_outputs)),
            prompt_func_outputs=self.joined_outputs,
            prompt_inout_inf=self.prompt_inout_inf,
            prompt_other_inf=self.prompt_other_inf,
            external_optimizer=self.external_optimizer_prompt() if self.external_optimizer else '',
            reflection_content=self.short_term_reflection_str if self.reflect else '',
            # reflection_content=self.long_term_reflection_str if self.reflect else '',
        )
        return prompt_content
    
    def get_prompt_m3(self,indiv1):
        prompt_content = self.prompt_m3.format(
            algo_code=indiv1['code'],
            prompt_inout_inf=self.prompt_inout_inf,
            reflection_content=self.long_term_reflection_str if self.reflect else '',
        )
        return prompt_content


    def _get_alg(self,prompt_content):

        response = self.interface_llm.get_response(prompt_content)

        algorithm = re.findall(r"\{\{(.*?)\}\}", response, re.DOTALL)
        if len(algorithm) == 0:
            if 'python' in response:
                algorithm = re.findall(r'^.*?(?=python)', response,re.DOTALL)
            elif 'import' in response:
                algorithm = re.findall(r'^.*?(?=import)', response,re.DOTALL)
            else:
                algorithm = re.findall(r'^.*?(?=def)', response,re.DOTALL)

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
                    algorithm = re.findall(r'^.*?(?=python)', response,re.DOTALL)
                elif 'import' in response:
                    algorithm = re.findall(r'^.*?(?=import)', response,re.DOTALL)
                else:
                    algorithm = re.findall(r'^.*?(?=def)', response,re.DOTALL)

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
            n_retry +=1

        algorithm = algorithm[0]
        code = code[0] 

        code_all = code+" "+", ".join(s for s in self.prompt_func_outputs)
        return [code_all, algorithm, optim_params]

    def _extract_param_name(self, oneline) -> str:
        match = re.match(r'^\s*(\w+)\s*(?:==|>=|<=|=|>|<)', oneline)
        return match.group(1) if match else oneline.strip()

    def _get_reflection(self, prompt_content):
        response = self.interface_llm.get_response(prompt_content)
        return response

    def i1(self):

        prompt_content = self.get_prompt_i1()

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ i1 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm, optim_params] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]
    
    def e1(self,parents):
      
        prompt_content = self.get_prompt_e1(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ e1 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm, optim_params] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params]
    
    def e2(self,parents):
      
        prompt_content = self.get_prompt_e2(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ e2 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm, optim_params] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params]
    
    def m1(self,parents):
      
        prompt_content = self.get_prompt_m1(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m1 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm, optim_params] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params]
    
    def m2(self,parents):
      
        prompt_content = self.get_prompt_m2(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m2 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm, optim_params] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm, optim_params]
    
    def m3(self,parents):
      
        prompt_content = self.get_prompt_m3(parents)

        if self.debug_mode:
            print("\n >>> check prompt for creating algorithm using [ m3 ] : \n", prompt_content )
            print(">>> Press 'Enter' to continue")
            input()
      
        [code_all, algorithm, optim_params] = self._get_alg(prompt_content)

        if self.debug_mode:
            print("\n >>> check designed algorithm: \n", algorithm)
            print("\n >>> check designed code: \n", code_all)
            print(">>> Press 'Enter' to continue")
            input()

        return [code_all, algorithm]

    def mimic_best_sample(self, population, iteration):
        best_ind = population[0]

        best_code = filter_code(best_ind["code"])

        user = self.prompt_mimic_best_sample.format(
            prompt_task=self.prompt_task,
            best_code=best_code
        )
        short_term_reflection = self._get_reflection(user)
        file_name = f"{self.file_path}/content/reflection_{iteration}.txt"
        with open(file_name, 'a') as file:
            file.writelines(short_term_reflection + '\n')
        self.short_term_reflection_str = short_term_reflection

    def correct_worst_sample(self, population, iteration):
        worst_ind = population[-1]
        worst_code = filter_code(worst_ind["code"])

        user = self.prompt_correct_worst_sample.format(
            prompt_task=self.prompt_task,
            worst_code=worst_code
        )
        short_term_reflection = self._get_reflection(user)
        file_name = f"{self.file_path}/content/reflection_{iteration}.txt"
        with open(file_name, 'a') as file:
            file.writelines(short_term_reflection + '\n')
        self.short_term_reflection_str = short_term_reflection

    def hybrid(self, population, iteration):
        best_ind, worst_ind = population[0], population[-1]

        worst_code = filter_code(worst_ind["code"])
        best_code = filter_code(best_ind["code"])

        user = self.prompt_hybrid.format(
            prompt_task=self.prompt_task,
            worst_code=worst_code,
            best_code=best_code
        )
        short_term_reflection = self._get_reflection(user)
        file_name = f"{self.file_path}/content/reflection_{iteration}.txt"
        with open(file_name, 'a') as file:
            file.writelines(short_term_reflection + '\n')
        self.short_term_reflection_str = short_term_reflection

    def multi_comparative_reflection(self, population, iteration, K1=5, K2=5):
        worst_group = population[-K1:]  # Take last K1 elements (worst performers)
        best_group = population[:K2]  # Take first K2 elements (best performers)

        # Prepare code sections for the prompt
        worst_sections = []
        for i, ind in enumerate(worst_group, 1):
            rank = "Worst" if i == 1 else f"{ordinal(i)} Worst"  # "Worst", "Second Worst", etc.
            worst_sections.append(f"[{rank}]\n{filter_code(ind['code'])}\n")

        best_sections = []
        for i, ind in enumerate(best_group, 1):
            rank = "Best" if i == 1 else f"{ordinal(i)} Best"  # "Best", "Second Best", etc.
            best_sections.append(f"[{rank}]\n{filter_code(ind['code'])}\n")

        user = self.prompt_multi_comparative_reflection.format(
            prompt_task=self.prompt_task,
            worst="".join(worst_sections),
            best="".join(best_sections)
        )

        short_term_reflection = self._get_reflection(user)
        file_name = f"{self.file_path}/content/reflection_{iteration}.txt"
        with open(file_name, 'a') as file:
            file.writelines(short_term_reflection + '\n')
        self.short_term_reflection_str = short_term_reflection


    def init_reevo_prompt(self):
        problem_prompt_path = 'inventory'
        self.problem_desc = file_to_string(f'{self.file_path}/{problem_prompt_path}/problem_desc.txt')
        self.seed_func = file_to_string(f'{self.file_path}/{problem_prompt_path}/seed_func.txt')
        self.func_name = file_to_string(f'{self.file_path}/{problem_prompt_path}/func_name.txt')
        self.func_signature = file_to_string(f'{self.file_path}/{problem_prompt_path}/func_signature.txt')
        self.func_desc = file_to_string(f'{self.file_path}/{problem_prompt_path}/func_desc.txt')

        self.user_reflector_st_prompt = file_to_string(f'{self.file_path}/common/user_reflector_st.txt')
        self.user_reflector_lt_prompt = file_to_string(f'{self.file_path}/common/user_reflector_lt.txt')

    def short_term_reflection_prompt_reevo(self, indivs):
        ind1, ind2 = indivs[0], indivs[1]
        # if ind1["objective"] == ind2["objective"]:
        #     raise ValueError("Two individuals to crossover have the same objective value!")
        # Determine which individual is better or worse
        if ind1["objective"] <= ind2["objective"]:
            better_ind, worse_ind = ind1, ind2
        elif ind1["objective"] > ind2["objective"]:
            better_ind, worse_ind = ind2, ind1

        worse_code = filter_code(worse_ind["code"])
        better_code = filter_code(better_ind["code"])

        system = self.system_reflector_prompt
        user = self.user_reflector_st_prompt.format(
            func_name=self.func_name,
            func_desc=self.func_desc,
            problem_desc=self.problem_desc,
            worse_code=worse_code,
            better_code=better_code
        )
        short_term_reflection = self._get_reflection(system+user)
        file_name = f"{self.file_path}/content/temp_short_term_reflection.txt"
        with open(file_name, 'a') as file:
            file.writelines(short_term_reflection + '\n')
        # self.short_term_reflection_str += "\n" + short_term_reflection

        return short_term_reflection

    def long_term_reflection_reevo(self, iteration):
        """
        Long-term reflection before mutation.
        """
        file_name = f"{self.file_path}/content/temp_short_term_reflection.txt"
        with open(file_name, 'r') as file:
            self.short_term_reflection_str = file.read()
        with open(file_name, 'w') as file:
            pass
        system = self.system_reflector_prompt
        user = self.user_reflector_lt_prompt.format(
            problem_desc=self.problem_desc,
            prior_reflection=self.long_term_reflection_str,
            new_reflection=self.short_term_reflection_str,
        )

        self.long_term_reflection_str = self._get_reflection(system+user)
        # Write reflections to file
        file_name = f"{self.file_path}/content/problem_iter{iteration}_short_term_reflections.txt"
        with open(file_name, 'w') as file:
            file.writelines(self.short_term_reflection_str + '\n')


        file_name = f"{self.file_path}/content/problem_iter{iteration}_long_term_reflection.txt"
        with open(file_name, 'w') as file:
            file.writelines(self.long_term_reflection_str + '\n')
        self.short_term_reflection_str = ''