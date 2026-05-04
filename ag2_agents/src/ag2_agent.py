"""AG2-native multi-agent flow for FinanceAgents.

This module shows how to wire the shared specialized agents (Finance, Yahoo,
SEC, Reddit, General) into AG2's ConversableAgent + GroupChat pattern.

The router in src/agents/ag2_router.py is what main.py uses at runtime
(deterministic, parallel, fast). This file is the AG2-flavored
demonstration — it lets a coordinator LLM decide which tools to call,
which is closer to AG2's idiomatic style.

Run directly:
    python src/ag2_agent.py "Tell me about Tesla stock"
"""
from __future__ import annotations

import os
import sys
import json
from datetime import datetime
from typing import Any, Dict

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", ".."))

from shared_lib.schemas import MCPRequest, MCPResponse, MCPContext
from shared_lib.agents.finance_agent import FinanceAgent
from shared_lib.agents.general_agent import GeneralAgent
from shared_lib.agents.reddit_agent import RedditAgent
from shared_lib.agents.yahoo_agent import YahooAgent
from shared_lib.agents.sec_agent import SECAgent

# AG2 (formerly AutoGen). The package was renamed; the imports below match
# the post-rebrand layout. If using legacy autogen, the same symbols are
# re-exported under `autogen`.
try:
    from autogen import ConversableAgent, GroupChat, GroupChatManager, UserProxyAgent
except ImportError as e:
    raise ImportError(
        "ag2 is required for ag2_agent.py. Install via: pip install ag2"
    ) from e


def _wrap_response(payload: Any) -> str:
    """Coerce an MCPResponse / dict / str into a JSON string for AG2 tool output."""
    if isinstance(payload, MCPResponse):
        payload = payload.data
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        return str(payload)


def _make_request(user_query: str, request_id: str) -> MCPRequest:
    return MCPRequest(
        request_id=request_id,
        context=MCPContext(user_query=user_query),
    )


# ---- Tool functions registered on AG2 agents ---------------------------------
# Each tool delegates to the corresponding shared agent's run().

def finance_tool(user_query: str) -> str:
    """Analyze internal financial PDFs (RAG) for the given query."""
    return _wrap_response(FinanceAgent().run(_make_request(user_query, "ag2-finance")))


def yahoo_tool(user_query: str) -> str:
    """Fetch and summarize 30-day Yahoo Finance stock statistics."""
    return _wrap_response(YahooAgent().run(_make_request(user_query, "ag2-yahoo")))


def sec_tool(user_query: str) -> str:
    """Summarize SEC filings relevant to the query."""
    return _wrap_response(SECAgent().run(_make_request(user_query, "ag2-sec")))


def reddit_tool(user_query: str) -> str:
    """Analyze Reddit sentiment for the query (sync wrapper around async agent)."""
    import asyncio
    coro = RedditAgent().run(_make_request(user_query, "ag2-reddit"), None)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from within a running loop, run on a fresh one.
            return _wrap_response(asyncio.run_coroutine_threadsafe(coro, loop).result())
    except RuntimeError:
        pass
    return _wrap_response(asyncio.run(coro))


def general_tool(user_query: str) -> str:
    """Answer non-financial / general questions."""
    return _wrap_response(GeneralAgent().run(_make_request(user_query, "ag2-general")))


# ---- AG2 agent definitions ---------------------------------------------------

def _llm_config() -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    return {
        "config_list": [
            {"model": "gpt-3.5-turbo", "api_key": api_key},
        ],
        "temperature": 0.1,
        "cache_seed": None,
    }


def build_finance_agents() -> Dict[str, ConversableAgent]:
    """Construct the cast of AG2 ConversableAgents wrapping the shared agents."""
    cfg = _llm_config()

    finance = ConversableAgent(
        name="finance",
        system_message=(
            "You analyze internal financial documents (10-K/10-Q PDFs) via RAG. "
            "Call the finance_tool with the user's query and report findings."
        ),
        llm_config=cfg,
        human_input_mode="NEVER",
    )
    yahoo = ConversableAgent(
        name="yahoo",
        system_message=(
            "You report real-time stock statistics from Yahoo Finance. "
            "Call yahoo_tool with the user's query."
        ),
        llm_config=cfg,
        human_input_mode="NEVER",
    )
    sec = ConversableAgent(
        name="sec",
        system_message=(
            "You summarize SEC filings. Call sec_tool with the user's query."
        ),
        llm_config=cfg,
        human_input_mode="NEVER",
    )
    reddit = ConversableAgent(
        name="reddit",
        system_message=(
            "You assess social-media sentiment. Call reddit_tool with the user's query."
        ),
        llm_config=cfg,
        human_input_mode="NEVER",
    )
    general = ConversableAgent(
        name="general",
        system_message=(
            "You answer general (non-financial) questions. Call general_tool."
        ),
        llm_config=cfg,
        human_input_mode="NEVER",
    )

    coordinator = ConversableAgent(
        name="coordinator",
        system_message=(
            "You are the routing coordinator. Decide which specialized agents "
            "should be consulted (finance, yahoo, sec, reddit, general) for the "
            "user query, ask each in turn, then synthesize a final report. "
            "When the analysis is complete, end your message with TERMINATE."
        ),
        llm_config=cfg,
        human_input_mode="NEVER",
    )

    # Tool execution is delegated to a UserProxyAgent so AG2 can actually
    # invoke the registered functions.
    executor = UserProxyAgent(
        name="executor",
        human_input_mode="NEVER",
        code_execution_config=False,
        is_termination_msg=lambda m: isinstance(m, dict)
        and "TERMINATE" in (m.get("content") or ""),
    )

    # Register tools: caller side declares the schema; executor side runs them.
    for agent, fn in (
        (finance, finance_tool),
        (yahoo, yahoo_tool),
        (sec, sec_tool),
        (reddit, reddit_tool),
        (general, general_tool),
    ):
        agent.register_for_llm(name=fn.__name__, description=fn.__doc__ or "")(fn)
        executor.register_for_execution(name=fn.__name__)(fn)

    return {
        "coordinator": coordinator,
        "executor": executor,
        "finance": finance,
        "yahoo": yahoo,
        "sec": sec,
        "reddit": reddit,
        "general": general,
    }


def run_groupchat(user_query: str, max_round: int = 12) -> MCPResponse:
    """Run an AG2 GroupChat over the shared agents and return an MCPResponse."""
    cast = build_finance_agents()
    members = [
        cast["coordinator"],
        cast["executor"],
        cast["finance"],
        cast["yahoo"],
        cast["sec"],
        cast["reddit"],
        cast["general"],
    ]
    groupchat = GroupChat(
        agents=members,
        messages=[],
        max_round=max_round,
        speaker_selection_method="auto",
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=_llm_config())

    chat_result = cast["executor"].initiate_chat(
        manager,
        message=user_query,
        clear_history=True,
    )

    return MCPResponse(
        request_id="ag2-groupchat",
        data={"groupchat": str(chat_result.summary if hasattr(chat_result, "summary") else chat_result)},
        context_updates=None,
        status="success",
        timestamp=datetime.now(),
    )


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Tell me about Apple stock"
    response = run_groupchat(query)
    print(json.dumps(response.data, indent=2, ensure_ascii=False, default=str))
