AG2 Routing Layer
=================

ag2_router.py
    RouterAG2 class. Deterministic dispatcher that mirrors the LangChain /
    LlamaIndex / CrewAI routers: uses shared_lib.query_classification to
    pick which specialized agents to run, then executes them in parallel
    with asyncio.gather. Used by src/main.py.

(See ../ag2_agent.py for the AG2-native demo using ConversableAgent and
GroupChat. The router is preferred at runtime for predictable latency
and cost; the AG2-native flow is illustrative.)
