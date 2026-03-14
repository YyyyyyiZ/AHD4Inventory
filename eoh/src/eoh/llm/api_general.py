import http.client
import json


class InterfaceAPI:
    def __init__(self, api_endpoint, api_key, model_LLM, debug_mode):
        # Route all remote model calls through OpenRouter's OpenAI-compatible API.
        # Keep the constructor signature for caller compatibility.
        self.api_endpoint = "openrouter.ai"
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode
        self.n_trial = 5

    def get_response(self, prompt_content):
        payload_explanation = json.dumps(
            {
                "model": self.model_LLM,
                "messages": [
                    # {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt_content}
                ],
            }
        )

        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "eoh-openrouter-client/1.0",
        }
        
        response = None
        n_trial = 1
        while True:
            n_trial += 1
            if n_trial > self.n_trial:
                return response
            try:
                # Add timeout to prevent hanging indefinitely
                conn = http.client.HTTPSConnection(self.api_endpoint, timeout=180)
                conn.request("POST", "/api/v1/chat/completions", payload_explanation, headers)
                res = conn.getresponse()
                data = res.read()
                json_data = json.loads(data)
                response = json_data["choices"][0]["message"]["content"]
                break
            except Exception as e:
                if self.debug_mode:
                    print(f"Error in API: {e}. Restarting the process...")
                continue
            finally:
                conn.close()
            

        return response
