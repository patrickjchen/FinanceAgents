# FinanceAgents - CrewAI Implementation

The CrewAI-flavoured shell around the shared FinanceAgents core: a FastAPI server, an interactive CLI, a deterministic router, and a reference `Crew` definition that wraps each shared agent as a CrewAI tool.

For the system overview, agent list, routing rules, environment setup, and the web UI see the [root README](../README.md). This file covers only what is specific to this directory.

## What is here

```
crewai_agents/
├── src/
│   ├── main.py                # FastAPI app + CLI loop (port 8000); uses RouterCrew
│   ├── crew_agent.py          # CrewAI Agents/Tasks/Crew over the shared agents (reference)
│   └── agents/
│       ├── crewai_router.py   # RouterCrew: classify -> dispatch shared agents concurrently
│       └── router.py          # older router, superseded by crewai_router.py, not imported
├── tests/
│   ├── test_agents.py         # import smoke script
│   └── sample_outputs/
├── working_dir/               # generated, gitignored: vector_db/chroma_index, logs
├── requirements.txt           # ../requirements.txt + crewai, langchain, langchain-core
└── dockerfile                 # not maintained, see root README
```

## Two orchestration paths

**`main.py` uses `RouterCrew`** (`src/agents/crewai_router.py`). It is the same shape as the LangChain, LlamaIndex, and AG2 routers: pick agents with `shared_lib/query_classification`, run them with `asyncio.gather`, hand the results to the shared LLM post-processing. This is the path behind `POST /query` and the CLI.

**`crew_agent.py` is the CrewAI-native reference.** Each shared agent (`RAGAgent`, `FinanceAgent`, `YahooAgent`, `SECAgent`, `RedditAgent`, `GeneralAgent`) is exposed as a `@tool`, and a CrewAI `Agent` with a role and backstory owns each tool. `build_crew()` assembles them and `run_crew()` kicks off one task per agent. It is not wired into `main.py`.

## Run

From this directory, with `env.all` filled in at the repository root:

```bash
cd crewai_agents
env $(cat ../env.all) python src/main.py
```

You get the API on `http://localhost:8000` and a prompt in the same terminal (`Enter your question:`; `exit` or `quit` to stop).

## API

`POST /query` with `{"query": "..."}` returns `{"response": {AgentName: {"summary": markdown}}}` as documented in the root README. Swagger UI is at `/docs`. This implementation has no `/health` or `/agents` endpoint.

## RAG storage

`RAGAgent` persists its Chroma index at `working_dir/vector_db/chroma_index`, relative to this directory, and adds new `../raw_data/` files on startup.

## Notes

- `run_crew()` in `crew_agent.py` reads `task.agent.name`, which recent CrewAI `Agent` versions do not expose. The router path used by `main.py` is unaffected.
- `redis` is listed in `requirements.txt` but nothing imports it.
