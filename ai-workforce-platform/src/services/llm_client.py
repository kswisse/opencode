import json
import time

import litellm
from opentelemetry import trace

from src.config import settings
from src.core.exceptions import LLMError
from src.observability.logging import get_logger

tracer = trace.get_tracer("llm_client")


class LLMClient:
    def __init__(self):
        litellm.api_key = settings.llm_api_key
        self.log = get_logger("llm_client")

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        with tracer.start_as_current_span("llm.complete") as span:
            span.set_attribute("model", model or settings.llm_model)
            span.set_attribute("temperature", temperature)

            start = time.monotonic()

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

                duration_ms = (time.monotonic() - start) * 1000
                self.log.info(
                    "llm_call_completed",
                    model=model or settings.llm_model,
                    duration_ms=round(duration_ms, 2),
                    prompt_length=len(prompt),
                )

                return response.choices[0].message.content
            except Exception as e:
                duration_ms = (time.monotonic() - start) * 1000
                self.log.error(
                    "llm_call_failed",
                    model=model or settings.llm_model,
                    error=str(e),
                    duration_ms=round(duration_ms, 2),
                )
                raise LLMError(f"LLM call failed: {e}")

    async def json(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
    ) -> dict:
        with tracer.start_as_current_span("llm.json"):
            full_prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
            response = await self.complete(full_prompt, system_prompt, model, temperature=0.3)
            try:
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    cleaned = cleaned.rsplit("```", 1)[0]
                return json.loads(cleaned)
            except json.JSONDecodeError:
                self.log.error(
                    "llm_json_parse_failed",
                    response_preview=response[:200],
                )
                raise LLMError(f"Failed to parse LLM response as JSON: {response[:200]}")


llm_client = LLMClient()
