"""Provider-aware LlamaIndex LLM factory.

LlamaIndex's ``OpenAI`` class validates model names against OpenAI's catalogue,
so it cannot be pointed at OpenRouter model ids like ``deepseek/deepseek-chat``.
When ``LLM_PROVIDER=openrouter`` we use ``OpenAILike`` (any OpenAI-compatible
endpoint) instead. All key / base_url / model resolution lives in
``shared_lib.llm_config`` so this stays in sync with the other implementations.
"""

import os
from shared_lib.llm_config import get_llm_settings


def make_llm(temperature: float = 0.1):
    settings = get_llm_settings()
    if settings.provider == "openrouter":
        from llama_index.llms.openai_like import OpenAILike

        return OpenAILike(
            model=settings.model,
            api_key=settings.api_key,
            api_base=settings.base_url,
            temperature=temperature,
            is_chat_model=True,
            is_function_calling_model=False,
            context_window=int(os.getenv("LLM_CONTEXT_WINDOW", "16384")),
            default_headers=settings.default_headers or None,
        )

    from llama_index.llms.openai import OpenAI

    kwargs = {"model": settings.model, "temperature": temperature}
    if settings.api_key:
        kwargs["api_key"] = settings.api_key
    if settings.base_url:
        kwargs["api_base"] = settings.base_url
    return OpenAI(**kwargs)
