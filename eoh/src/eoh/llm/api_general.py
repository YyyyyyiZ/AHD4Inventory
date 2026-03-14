import json
import urllib.error
import urllib.request
from typing import Any, Dict


class InterfaceAPIError(RuntimeError):
    pass


class InterfaceAPI:
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    CHAT_COMPLETIONS_PATH = "/chat/completions"

    MODEL_ID_MAP = {
        "gpt-4o": "openai/gpt-4o",
        "gpt-5.2": "openai/gpt-5.2",
        "deepseek-chat": "deepseek/deepseek-chat",
        "deepseek-chat-v3-0324": "deepseek/deepseek-chat-v3-0324",
    }

    def __init__(self, api_endpoint, api_key, model_LLM, debug_mode):
        # Keep constructor signature for caller compatibility.
        self.api_endpoint = self.OPENROUTER_BASE_URL
        self.api_key = api_key
        self.model_LLM = self._resolve_openrouter_model_id(model_LLM)
        self.debug_mode = debug_mode
        self.request_path = self.CHAT_COMPLETIONS_PATH

    def _resolve_openrouter_model_id(self, model_name: str) -> str:
        model_name = (model_name or "").strip()
        if not model_name:
            raise ValueError("Resolved model is empty.")

        if "/" in model_name:
            return model_name

        return self.MODEL_ID_MAP.get(model_name, model_name)

    def startup_validation_log(self):
        print("[LLM Startup] resolved base_url=", self.api_endpoint)
        print("[LLM Startup] resolved model=", self.model_LLM)
        print("[LLM Startup] api key present=", bool(self.api_key))
        print("[LLM Startup] final request endpoint path=", self.request_path)

    def _request_chat_completion(self, messages) -> Dict[str, Any]:
        payload = json.dumps({"model": self.model_LLM, "messages": messages}).encode("utf-8")
        endpoint = f"{self.api_endpoint}{self.request_path}"
        request = urllib.request.Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "eoh-openrouter-client/1.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body_bytes = response.read()
                body_text = body_bytes.decode("utf-8", errors="replace")
                status_code = response.getcode()
                if status_code >= 400:
                    raise InterfaceAPIError(
                        f"HTTP {status_code} from OpenRouter. body={body_text}; "
                        f"resolved_base_url={self.api_endpoint}; resolved_model={self.model_LLM}"
                    )
                return json.loads(body_text)
        except urllib.error.HTTPError as err:
            error_body = err.read().decode("utf-8", errors="replace")
            raise InterfaceAPIError(
                f"HTTP {err.code} from OpenRouter. body={error_body}; "
                f"resolved_base_url={self.api_endpoint}; resolved_model={self.model_LLM}"
            ) from err
        except urllib.error.URLError as err:
            raise InterfaceAPIError(
                f"Network error calling OpenRouter: {err}; "
                f"resolved_base_url={self.api_endpoint}; resolved_model={self.model_LLM}"
            ) from err

    def health_check(self):
        return self._request_chat_completion(messages=[{"role": "user", "content": "say ok"}])

    def get_response(self, prompt_content):
        response_json = self._request_chat_completion(
            messages=[{"role": "user", "content": prompt_content}]
        )
        return response_json["choices"][0]["message"]["content"]
