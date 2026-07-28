import json
import litellm

from src.config import settings
from src.core.exceptions import LLMError


class LLMClient:
    def __init__(self):
        litellm.api_key = settings.llm_api_key

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await litellm.acompletion(
                model=model or settings.llm_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(f"LLM call failed: {e}")

    async def json(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
    ) -> dict:
        full_prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
        response = await self.complete(full_prompt, system_prompt, model, temperature=0.3)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise LLMError(f"Failed to parse LLM response as JSON: {response[:200]}")


llm_client = LLMClient()
