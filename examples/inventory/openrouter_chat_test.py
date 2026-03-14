"""Minimal OpenRouter chat-completions test script."""
import os
from openai import OpenAI


def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "say ok"}],
    )
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
