from ..llm.api_general import InterfaceAPI
import os
# from ..llm.api_local_llm import InterfaceLocalLLM

class InterfaceLLM:
    def __init__(self, api_endpoint, api_key, model_LLM,llm_use_local,llm_local_url, debug_mode):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode
        self.llm_use_local = False
        self.llm_local_url = llm_local_url

        print("- check LLM API")

        if self.llm_use_local:
            # print('local llm delopyment is used ...')
            raise ValueError("local llm delopyment is used ...")
            
            # if self.llm_local_url == None or self.llm_local_url == 'xxx' :
            #     print(">> Stop with empty url for local llm !")
            #     exit()
            #
            # self.interface_llm = InterfaceLocalLLM(
            #     self.llm_local_url
            # )

        else:
            print('remote llm api is used ...')

            # Unified routing via OpenRouter.
            env_openrouter_key = os.getenv("OPENROUTER_API_KEY")
            if env_openrouter_key:
                self.api_key = env_openrouter_key

            if self.api_key == None or self.api_key == 'xxx':
                print(">> Stop with wrong API setting: set OPENROUTER_API_KEY (or llm_api_key) for OpenRouter access!")
                exit()

            self.interface_llm = InterfaceAPI(
                self.api_endpoint,
                self.api_key,
                self.model_LLM,
                self.debug_mode,
            )

            
        res = self.interface_llm.get_response("1+1=?")

        if res == None:
            print(">> Error in LLM API, wrong endpoint, key, model or local deployment!")
            exit()

    def get_response(self, prompt_content):
        response = self.interface_llm.get_response(prompt_content)

        return response
