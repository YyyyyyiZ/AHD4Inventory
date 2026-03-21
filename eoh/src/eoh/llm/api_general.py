import http.client
import json
from urllib.parse import urlparse


class InterfaceAPI:
    def __init__(self, api_endpoint, api_key, model_LLM, debug_mode, reasoning_effort=None):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.model_LLM = model_LLM
        self.debug_mode = debug_mode
        self.reasoning_effort = reasoning_effort
        self.n_trial = 5

        # Set timeout based on reasoning effort
        # Higher reasoning effort requires more thinking time
        timeout_map = {
            "low": 600,      # 10 minutes for faster responses
            "medium": 900,   # 15 minutes (default)
            "high": 4500     # 75 minutes for deep reasoning
        }
        self.timeout = timeout_map.get(reasoning_effort, 900)

        if debug_mode:
            print(f"API timeout set to {self.timeout}s for reasoning_effort='{reasoning_effort}'")

        # Parse the endpoint URL to separate host and path
        parsed = urlparse(api_endpoint)
        self.host = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]
        self.base_path = parsed.path if parsed.netloc else ''
        # Remove trailing slash from base_path if present
        if self.base_path.endswith('/'):
            self.base_path = self.base_path[:-1]

    def _is_gemini_endpoint(self):
        return "generativelanguage.googleapis.com" in self.api_endpoint

    def _is_openrouter_endpoint(self):
        return "openrouter.ai" in self.host

    def _build_chat_completions_path(self, is_gemini, is_openrouter):
        if is_gemini:
            return f"{self.base_path}/chat/completions"
        if is_openrouter:
            # OpenRouter canonical path is /api/v1/chat/completions.
            if not self.base_path:
                return "/api/v1/chat/completions"
            if self.base_path.endswith("/v1"):
                return f"{self.base_path}/chat/completions"
            return f"{self.base_path}/v1/chat/completions"

        # Most OpenAI-compatible providers expect /v1/chat/completions.
        # If users already provide an endpoint ending in /v1 (e.g., MiniMax),
        # avoid appending /v1 twice.
        if not self.base_path:
            return "/v1/chat/completions"
        if self.base_path.endswith("/v1"):
            return f"{self.base_path}/chat/completions"
        return f"{self.base_path}/v1/chat/completions"

    def get_response(self, prompt_content):
        # Check endpoint families.
        is_gemini = self._is_gemini_endpoint()
        is_openrouter = self._is_openrouter_endpoint()
        is_minimax = (
            "api.minimax.io" in self.api_endpoint
            or "api.minimaxi.com" in self.api_endpoint
            or "api.minimax.chat" in self.api_endpoint
            or (self.model_LLM or "").lower().startswith("minimax-")
        )
        # Avoid re-sending long prompts to MiniMax; each retry burns tokens.
        max_trials = 1 if is_minimax else self.n_trial

        payload_dict = {
            "model": self.model_LLM,
            "messages": [
                # {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_content}
            ],
        }

        # Only newer Gemini reasoning-capable models accept reasoning_effort.
        # gemini-2.0-flash can fail if this field is sent.
        model_name = (self.model_LLM or "").lower()
        supports_reasoning_effort = (
            "gemini-2.5" in model_name
            or "gemini-3" in model_name
            or "thinking" in model_name
        )
        if is_gemini and supports_reasoning_effort and self.reasoning_effort:
            payload_dict["reasoning_effort"] = self.reasoning_effort
        elif is_minimax and self.debug_mode and self.reasoning_effort:
            # MiniMax M2.5 supports interleaved thinking/reasoning_split,
            # but not OpenAI-style reasoning_effort levels.
            print("MiniMax model detected: ignoring reasoning_effort (not supported by MiniMax API).")

        payload_explanation = json.dumps(payload_dict)

        headers = {
            "Authorization": "Bearer " + self.api_key,
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "Content-Type": "application/json",
        }
        if is_openrouter:
            # Optional attribution headers recommended by OpenRouter.
            headers["HTTP-Referer"] = "https://github.com/yfenghua/AHD4Inventory"
            headers["X-Title"] = "AHD4Inventory"

        # Add x-api2d-no-cache only for API2D-like endpoints.
        if (not is_gemini) and (not is_openrouter):
            headers["x-api2d-no-cache"] = "1"
        
        response = None
        n_trial = 0
        while n_trial < max_trials:
            n_trial += 1
            conn = None
            data = b""
            full_path = ""
            try:
                # Add timeout based on reasoning effort
                conn = http.client.HTTPSConnection(self.host, timeout=self.timeout)
                full_path = self._build_chat_completions_path(is_gemini, is_openrouter)
                conn.request("POST", full_path, payload_explanation, headers)
                res = conn.getresponse()
                data = res.read()
                json_data = json.loads(data)

                # Normalize error shapes returned by some Gemini responses.
                if isinstance(json_data, list) and json_data:
                    if isinstance(json_data[0], dict) and "error" in json_data[0]:
                        err = json_data[0]["error"]
                        raise RuntimeError(f"{err.get('status', 'ERROR')}: {err.get('message', err)}")

                if isinstance(json_data, dict) and "error" in json_data:
                    err = json_data["error"]
                    raise RuntimeError(f"{err.get('status', 'ERROR')}: {err.get('message', err)}")

                # OpenAI-compatible response parsing, plus fallback for content-part arrays.
                response = json_data["choices"][0]["message"]["content"]
                if isinstance(response, list):
                    text_parts = []
                    for part in response:
                        if isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                    response = "\n".join(text_parts).strip()
                break
            except Exception as e:
                # Always print the first failure (even on single-try MiniMax) to avoid silent None.
                try:
                    status = res.status
                except Exception:
                    status = "unknown"
                print(f"API Error: {e}")
                print(f"Host: {self.host}, Path: {full_path}, Status: {status}")
                try:
                    print(f"Raw response: {data[:500].decode('utf-8', errors='replace')}")
                except Exception:
                    pass
                print(f"Model: {self.model_LLM}")

                if self.debug_mode:
                    import traceback
                    traceback.print_exc()

                # Do not loop silently; break so caller knows we failed.
                break
            finally:
                if conn is not None:
                    conn.close()


        return response
