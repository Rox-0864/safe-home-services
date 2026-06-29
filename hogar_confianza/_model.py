import logging
import os
from typing import AsyncGenerator

from google.adk.models import LLMRegistry
from google.adk.models.base_llm import BaseLlm

logger = logging.getLogger(__name__)

FALLBACK_MODEL_DEFAULT = "ollama_chat/qwen2.5:3b"


def _create_llm(model_name: str) -> BaseLlm:
    if model_name.startswith("openai/") or model_name.startswith("ollama_chat/"):
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(model=model_name)
    return LLMRegistry.new_llm(model_name)


def resolve_model() -> BaseLlm:
    model_name = os.getenv("ADK_MODEL", "gemini-3.1-flash-lite")
    return _create_llm(model_name)


class FallbackLlm(BaseLlm):
    """Wrapper que intenta el modelo primario y cae al secundario si falla."""

    def __init__(self, primary: BaseLlm, fallback: BaseLlm, **kwargs):
        super().__init__(model=primary.model, **kwargs)
        self._primary = primary
        self._fallback = fallback
        self._has_failed = False

    async def generate_content_async(
        self, llm_request, stream: bool = False
    ) -> AsyncGenerator:
        if self._has_failed:
            async for response in self._fallback.generate_content_async(
                llm_request, stream=stream
            ):
                yield response
            return

        try:
            async for response in self._primary.generate_content_async(
                llm_request, stream=stream
            ):
                yield response
        except Exception as e:
            logger.warning(
                "Modelo primario %s falló: %s. Cambiando a fallback %s",
                self._primary.model,
                e,
                self._fallback.model,
            )
            self._has_failed = True
            async for response in self._fallback.generate_content_async(
                llm_request, stream=stream
            ):
                yield response


def resolve_model_with_fallback() -> FallbackLlm:
    primary = resolve_model()
    fallback_name = os.getenv("ADK_FALLBACK_MODEL", FALLBACK_MODEL_DEFAULT)
    fallback = _create_llm(fallback_name)
    return FallbackLlm(primary, fallback)
