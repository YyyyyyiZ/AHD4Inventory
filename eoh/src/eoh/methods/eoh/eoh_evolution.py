import os
import json
from datetime import datetime

from ...llm.interface_LLM import InterfaceLLM
from .utils import *


class Evolution:

    def __init__(self, api_endpoint, api_key, model_LLM, llm_use_local, llm_local_url, debug_mode, prompts,
                 analyzer, external_optimizer, param_loc, exp_output_path, **kwargs):

        self.prompt_task = prompts.get_task()
        self.prompt_func_outputs = prompts.get_func_outputs()

        # set LLMs
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode  # close prompt checking
        self.exp_output_path = exp_output_path
        self.external_optimizer = external_optimizer

        self.analyzer = analyzer
        self.problem_spec = analyzer.get_problem_spec()
        self.init_base_prompt()
        self.interface_llm = InterfaceLLM(self.api_endpoint, self.api_key, self.model_LLM, llm_use_local, llm_local_url,
                                          self.debug_mode)

    def init_base_prompt(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(self.current_dir)

        # Demand Agent is not used (using template-based calculation instead)
        # self.demandAgent_sys = self._format_system_prompt(
        #     file_to_string(f'{self.file_path}/prompt/demandAgent_sys.txt')
        # )
        # self.demandAgent_user = file_to_string(f'{self.file_path}/prompt/demandAgent_user.txt')

        self.EvaluatorA_user = file_to_string(f'{self.file_path}/prompt/EvaluatorA_user.txt')
        self.EvaluatorA_sys = self._format_system_prompt(
            file_to_string(f'{self.file_path}/prompt/EvaluatorA_sys.txt')
        )
        self.EvaluatorB_user = file_to_string(f'{self.file_path}/prompt/EvaluatorB_user.txt')
        self.EvaluatorB_sys = self._format_system_prompt(
            file_to_string(f'{self.file_path}/prompt/EvaluatorB_sys.txt')
        )
        self.EvaluatorC_user = file_to_string(f'{self.file_path}/prompt/EvaluatorC_user.txt')
        self.EvaluatorC_sys = self._format_system_prompt(
            file_to_string(f'{self.file_path}/prompt/EvaluatorC_sys.txt')
        )

        # Insight Aggregator is not used (evaluator outputs go directly to policy creator)
        # self.insightAgg_sys = self._format_system_prompt(
        #     file_to_string(f'{self.file_path}/prompt/insightAgg_sys.txt')
        # )
        # self.insightAgg_user = file_to_string(f'{self.file_path}/prompt/insightAgg_user.txt')

        self.instructions = file_to_string(f'{self.file_path}/prompt/instructions.txt')
        self.policyCreator_sys = self._format_system_prompt(
            file_to_string(f'{self.file_path}/prompt/policyCreator_sys.txt')
        )
        self.policyCreator_user = file_to_string(f'{self.file_path}/prompt/policyCreator_user.txt')
        self._save_system_prompts()

    def _save_system_prompts(self):
        # self.save_txt(self.demandAgent_sys, 'prompt_for_code', 'system_demandAgent')  # Demand Agent not used
        self.save_txt(self.EvaluatorA_sys, 'prompt_for_code', 'system_evaluatorA')
        self.save_txt(self.EvaluatorB_sys, 'prompt_for_code', 'system_evaluatorB')
        self.save_txt(self.EvaluatorC_sys, 'prompt_for_code', 'system_evaluatorC')
        # self.save_txt(self.insightAgg_sys, 'prompt_for_code', 'system_insightAgg')  # Insight Aggregator not used
        self.save_txt(self.policyCreator_sys, 'prompt_for_code', 'system_policyCreator')

    def _format_system_prompt(self, template):
        try:
            spec = json.loads(self.problem_spec)
        except Exception:
            return template

        replacements = {
            "__L__": spec.get("L", ""),
            "__T__": spec.get("T", ""),
            "__H__": spec.get("h", ""),
            "__P__": spec.get("p", ""),
        }

        formatted = template
        for key, value in replacements.items():
            formatted = formatted.replace(key, str(value))
        return formatted

    def workflow(self, parents):
        # try:
        #     data = self.interface_llm.get_response(self.demandAgent_sys, self.get_prompt_data())
        #     self.save_txt(data, 'response', 'data')
        # except Exception as exc:
        #     data = f"[demandAgent_error] {exc}"
        #     self.save_txt(data, 'response', 'data_error')

        data = self.analyzer.get_demand_stats()
        self.save_txt(data, 'response', 'data')

        # Evaluate each parent policy individually
        eval_all = []
        for i, parent in enumerate(parents):
            eval_userA = self.get_prompt_evalA(parent, data)
            evalA = self.interface_llm.get_response(self.EvaluatorA_sys, eval_userA)
            self.save_txt(evalA, 'response', f'evalA_policy{i+1}')
            eval_all.append(evalA)
            # eval_userB = self.get_prompt_evalB(parent, data)
            # evalB = self.interface_llm.get_response(self.EvaluatorB_sys, eval_userB)
            # self.save_txt(evalB, 'response', f'evalB_policy{i+1}')
            # eval_userC = self.get_prompt_evalC(parent, data)
            # evalC = self.interface_llm.get_response(self.EvaluatorC_sys, eval_userC)
            # self.save_txt(evalC, 'response', f'evalC_policy{i+1}')
            # eval_all.append([evalA, evalB, evalC])

        # Insight Aggregator is not used - evaluator outputs go directly to policy creator
        # insight = self.interface_llm.get_response(self.insightAgg_sys, self.get_prompt_insight(parents, eval_all, data))
        # self.save_txt(insight, 'response', 'insight')

        [code_all, algorithm, optim_params, cost] = self._get_alg(
            self.policyCreator_sys,
            self.get_prompt_creator(eval_all, parents, data)
        )
        return [code_all, algorithm, optim_params, cost]

    def get_prompt_data(self):
        prompt_content = self.demandAgent_user.format(
            PROBLEM_SPEC_JSON=self.problem_spec,
            HISTORICAL_DEMANDS_JSON=self.analyzer.get_demand_data(),
        )
        self.save_txt(prompt_content, 'prompt_for_code', 'data')
        return prompt_content

    def get_prompt_evalA(self, indiv, data):
        # Get algorithm performance for single policy (returns None if algo_performance is 'no')
        algo_performance = self.analyzer.get_algo_performance([indiv])
        if algo_performance is None:
            algo_performance = "Performance data not available."

        prompt_content = self.EvaluatorA_user.format(
            HISTORICAL_DEMANDS_JSON=self.analyzer.get_demand_data(),
            DEMAND_BATCH_JSON=data,
            POLICY_ARTIFACT_JSON=indiv['code'],
            ALGO_PERFORMANCE_JSON=algo_performance,
        )
        self.save_txt(prompt_content, 'prompt_for_code', 'evaluatorA')
        return prompt_content

    def get_prompt_evalB(self, indiv, data):
        # Get algorithm performance for single policy (returns None if algo_performance is 'no')
        algo_performance = self.analyzer.get_algo_performance([indiv])
        if algo_performance is None:
            algo_performance = "Performance data not available."

        prompt_content = self.EvaluatorB_user.format(
            HISTORICAL_DEMANDS_JSON=self.analyzer.get_demand_data(),
            DEMAND_BATCH_JSON=data,
            POLICY_ARTIFACT_JSON=indiv['code'],
            ALGO_PERFORMANCE_JSON=algo_performance,
        )
        self.save_txt(prompt_content, 'prompt_for_code', 'evaluatorB')
        return prompt_content

    def get_prompt_evalC(self, indiv, data):
        # Get algorithm performance for single policy (returns None if algo_performance is 'no')
        algo_performance = self.analyzer.get_algo_performance([indiv])
        if algo_performance is None:
            algo_performance = "Performance data not available."

        prompt_content = self.EvaluatorC_user.format(
            HISTORICAL_DEMANDS_JSON=self.analyzer.get_demand_data(),
            DEMAND_BATCH_JSON=data,
            POLICY_ARTIFACT_JSON=indiv['code'],
            ALGO_PERFORMANCE_JSON=algo_performance,
        )
        self.save_txt(prompt_content, 'prompt_for_code', 'evaluatorC')
        return prompt_content

    # Insight Aggregator is not used - commenting out this method
    # def get_prompt_insight(self, indivs, evaluation, data):
    #     prompt_indiv = ""
    #     for i in range(len(indivs)):
    #         prompt_indiv = prompt_indiv + "No." + str(i + 1) + " policy code: \n" + indivs[i]['code'] + "\n\n"
    #     prompt_content = self.insightAgg_user.format(
    #         DEMAND_BATCH_JSON=data,
    #         CANDIDATE_POLICIES_JSON=prompt_indiv,
    #         EVAL_REPORTS_JSON=evaluation,
    #     )
    #     self.save_txt(prompt_content, 'prompt_for_code', 'insight')
    #     return prompt_content

    def get_prompt_creator(self, evaluator_outputs, indivs, data):
        """Generate prompt for policy creator with direct evaluator outputs."""
        prompt_indiv = ""
        for i in range(len(indivs)):
            prompt_indiv = prompt_indiv + "No." + str(i + 1) + " policy code: \n" + indivs[i]['code'] + "\n" + "\n"

        # Format evaluator outputs
        eval_text = ""
        for i, eval_output in enumerate(evaluator_outputs):
            eval_text += f"Evaluation of Policy No.{i+1}:\n{eval_output}\n\n"

        prompt_content = self.policyCreator_user.format(
            DEMAND_STATS_JSON=data,
            SEED_POLICIES_JSON=prompt_indiv,
            EVALUATOR_OUTPUTS_JSON=eval_text,
            INSTRUCTIONS=self.instructions
        )
        self.save_txt(prompt_content, 'prompt_for_code', 'create')
        return prompt_content

    def save_txt(self, content, folder, prefix):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.exp_output_path}/{folder}/{prefix}_{timestamp}.txt"
        with open(file_name, 'w') as file:
            file.writelines(content + '\n')

    def _get_alg(self, system, user):

        response = self.interface_llm.get_response(system, user)

        # algorithm = re.findall(r"\{\{(.*?)\}\}", response, re.DOTALL)
        # # cost = re.findall(r"\[\[\[(.*?)\]\]\]", response, re.DOTALL)
        # if len(algorithm) == 0:
        #     if 'python' in response:
        #         algorithm = re.findall(r'^.*?(?=python)', response, re.DOTALL)
        #     elif 'import' in response:
        #         algorithm = re.findall(r'^.*?(?=import)', response, re.DOTALL)
        #     else:
        #         algorithm = re.findall(r'^.*?(?=def)', response, re.DOTALL)

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
        while len(code) == 0:
            if self.debug_mode:
                print("Error: algorithm or code not identified, wait 1 seconds and retrying ... ")

            response = self.interface_llm.get_response(system, user)
            # algorithm = re.findall(r"\{\{(.*?)\}\}", response, re.DOTALL)
            # if len(algorithm) == 0:
            #     if 'python' in response:
            #         algorithm = re.findall(r'^.*?(?=python)', response, re.DOTALL)
            #     elif 'import' in response:
            #         algorithm = re.findall(r'^.*?(?=import)', response, re.DOTALL)
            #     else:
            #         algorithm = re.findall(r'^.*?(?=def)', response, re.DOTALL)

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

        # algorithm = algorithm[0]
        algorithm = ""
        code = code[0]
        # cost = cost[0]
        cost = None

        code_all = code + " " + ", ".join(s for s in self.prompt_func_outputs)
        # print("llm response:", code_all)
        return [code_all, algorithm, optim_params, cost]

    def _extract_param_name(self, oneline) -> str:
        match = re.match(r'^\s*(\w+)\s*(?:==|>=|<=|=|>|<)', oneline)
        return match.group(1) if match else oneline.strip()
