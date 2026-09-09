"""Single place that decides which LLM backend every implementation talks to.

Two providers are supported, both through the OpenAI-compatible chat API:

    LLM_PROVIDER=openai      (default)  -> api.openai.com, key from OPENAI_API_KEY
    LLM_PROVIDER=openrouter             -> openrouter.ai,  key from OPENROUTER_API_KEY

If LLM_PROVIDER is unset, "openrouter" is chosen automatically when only
OPENROUTER_API_KEY is present; otherwise "openai".

Other knobs (all optional):

    LLM_MODEL             model id; default gpt-3.5-turbo (openai) or
                          openai/gpt-3.5-turbo (openrouter, note the vendor prefix)
    OPENAI_BASE_URL       override base URL for the openai provider
    OPENROUTER_BASE_URL   default https://openrouter.ai/api/v1
    OPENROUTER_SITE_URL   optional HTTP-Referer sent to OpenRouter (dashboard attribution)
    OPENROUTER_APP_NAME   optional X-Title sent to OpenRouter (default "FinanceAgents")

Every agent should obtain its client via get_llm_client() and its model name via
get_llm_model() instead of constructing openai.OpenAI(...) directly, so that a
provider switch is a pure environment change.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

_DEFAULT_MODELS = {
    "openai": "gpt-3.5-turbo",
    "openrouter": "deepseek/deepseek-chat",
    #"openrouter": "openai/gpt-3.5-turbo",
}


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    api_key: Optional[str]
    base_url: Optional[str]
    model: str
    default_headers: Dict[str, str] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def client_kwargs(self) -> Dict[str, object]:
        """Keyword arguments for openai.OpenAI(...)."""
        kwargs: Dict[str, object] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        if self.default_headers:
            kwargs["default_headers"] = dict(self.default_headers)
        return kwargs

    def ag2_config_entry(self) -> Dict[str, object]:
        """One entry for an AG2 / autogen ``config_list``."""
        entry: Dict[str, object] = {
            "model": self.model,
            "api_key": self.api_key,
            "api_type": "openai",
        }
        if self.base_url:
            entry["base_url"] = self.base_url
        if self.default_headers:
            entry["default_headers"] = dict(self.default_headers)
        return entry


def get_llm_provider() -> str:
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if provider in _DEFAULT_MODELS:
        return provider
    if provider:
        raise ValueError(
            f"Unsupported LLM_PROVIDER={provider!r}; expected one of {sorted(_DEFAULT_MODELS)}"
        )
    if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        return "openrouter"
    return "openai"


def get_llm_settings() -> LLMSettings:
    provider = get_llm_provider()
    model = os.getenv("LLM_MODEL") or _DEFAULT_MODELS[provider]

    if provider == "openrouter":
        headers = {"X-Title": os.getenv("OPENROUTER_APP_NAME", "FinanceAgents")}
        site = os.getenv("OPENROUTER_SITE_URL")
        if site:
            headers["HTTP-Referer"] = site
        return LLMSettings(
            provider=provider,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL", OPENROUTER_DEFAULT_BASE_URL),
            model=model,
            default_headers=headers,
        )

    return LLMSettings(
        provider=provider,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        model=model,
    )


def get_llm_model() -> str:
    return get_llm_settings().model


def llm_available() -> bool:
    return get_llm_settings().available


def missing_key_message() -> str:
    provider = get_llm_provider()
    var = "OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY"
    return f"{var} not set (LLM_PROVIDER={provider})"


def get_llm_client():
    """Return a configured ``openai.OpenAI`` client, or None when no key is set."""
    settings = get_llm_settings()
    if not settings.available:
        return None
    import openai

    return openai.OpenAI(**settings.client_kwargs())


def require_llm_client():
    """Like get_llm_client() but raises a descriptive ValueError when unconfigured."""
    client = get_llm_client()
    if client is None:
        raise ValueError(missing_key_message())
    return client
