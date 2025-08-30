import http.client
import json


class InterfaceAPI:
    def __init__(self, api_endpoint, api_key, model_LLM, debug_mode):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode
        self.n_trial = 5

    def get_response(self, prompt_content, role='data'):
        if role == 'code':
            payload_explanation = json.dumps(
                {
                    "model": self.model_LLM,
                    "messages": [
                        {"role": "system",
                         "content": (
                             "You are Agent A, a helpful code generator. "
                             "Your primary responsibility is to design and implement algorithms "
                             "based on the problem description provided by the user. "
                             "You may interact with another agent B who has access "
                             "to the demand data. "
                             "If you need information about the data, you must explicitly "
                             "ask Agent B by starting your response with 'QUESTION'. "
                             "If you are ready to provide code, you must start your response "
                             "with 'GENERATION' and follow the specified output format. "
                             "Do not mix questions and Generated code in the same response. "
                             "Always stay within your role as an algorithm/code designer."
                         ),
                         },
                        {"role": "user",
                         "content": prompt_content
                         }
                    ],
                }
            )
        elif role == 'data':
            payload_explanation = json.dumps(
                {
                    "model": self.model_LLM,
                    "messages": [
                        {"role": "system",
                         "content": (
                             "You are Agent B, a helpful data analyst. "
                             "You have full access to the demand data, which consists of "
                             "a 2D dataset with multiple scenarios across different time periods. "
                             "Your primary responsibility is to answer questions about the data "
                             "from Agent A, such as descriptive statistics, possible distributions, "
                             "Always stay within your role as a data expert."
                         ),
                         },
                        {"role": "user",
                         "content": prompt_content
                         }
                    ],
                }
            )
        else:
            raise ValueError("Role must be either 'code' or 'data'")

        headers = {
            "Authorization": "Bearer " + self.api_key,
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "Content-Type": "application/json",
            "x-api2d-no-cache": 1,
        }

        response = None
        n_trial = 1
        while True:
            n_trial += 1
            if n_trial > self.n_trial:
                return response
            try:
                conn = http.client.HTTPSConnection(self.api_endpoint)
                conn.request("POST", "/v1/chat/completions", payload_explanation, headers)
                res = conn.getresponse()
                data = res.read()
                json_data = json.loads(data)
                response = json_data["choices"][0]["message"]["content"]
                break
            except:
                if self.debug_mode:
                    print("Error in API. Restarting the process...")
                continue

        return response
