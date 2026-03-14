from ..llm.api_general import InterfaceAPI
import os


class InterfaceLLM:
    def __init__(self, api_endpoint, api_key, model_LLM, llm_use_local, llm_local_url, debug_mode):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode
        self.llm_use_local = False
        self.llm_local_url = llm_local_url

        print("- check LLM API")

        if self.llm_use_local:
            raise ValueError("local llm delopyment is used ...")

        print('remote llm api is used ...')

        env_openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if env_openrouter_key:
            self.api_key = env_openrouter_key

        if self.api_key is None or self.api_key == 'xxx' or self.api_key == '':
            raise ValueError("Set OPENROUTER_API_KEY (or llm_api_key) for OpenRouter access.")

        self.interface_llm = InterfaceAPI(
            self.api_endpoint,
            self.api_key,
            self.model_LLM,
            self.debug_mode,
        )

        self.interface_llm.startup_validation_log()
        self.interface_llm.health_check()

    def get_response(self, prompt_content):
        response = self.interface_llm.get_response(prompt_content)
        return response
