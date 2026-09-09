# FinanceAgents - LangChain Implementation

The LangChain-flavoured shell around the shared FinanceAgents core. The shared agents in `shared_lib/` are built on LangChain primitives (document loaders, `HuggingFaceEmbeddings`, `langchain-chroma`), and this directory adds the FastAPI server, the interactive CLI, and a deterministic router.

For the system overview, agent list, routing rules, environment setup, and the web UI see the [root README](../README.md). This file covers only what is specific to this directory.

## What is here

```
langchain_agents/
├── src/
│   ├── main.py            # FastAPI app + CLI loop (port 8000)
│   └── agents/
│       └── router.py      # RouterAgent: classify -> dispatch shared agents concurrently
├── tests/
│   └── sample_outputs/    # recorded responses, for reference only
├── working_dir/           # generated, gitignored: vector_db/chroma_index, logs
├── requirements.txt       # ../requirements.txt + langchain, langchain-core
└── dockerfile             # not maintained, see root README
```

`RouterAgent.route()` calls `shared_lib/query_classification` to pick agents, instantiates each from `shared_lib/agents/`, and runs them with `asyncio.gather`. Sync agents are wrapped in `loop.run_in_executor`; `RedditAgent` is awaited directly. Routing is keyword based; no embedding model or LLM is involved in choosing agents.

## Run

From this directory, with `env.all` filled in at the repository root:

```bash
cd langchain_agents
env $(cat ../env.all) python src/main.py
```

You get the API on `http://localhost:8000` and a prompt in the same terminal:

```
============================================================
  FinanceAgents CLI (LangChain)
============================================================
Supported tickers for financial queries:
  AAPL, AMZN, GOOG, IBM, INTC, META, MSFT, NFLX, NVDA, TSLA

Enter your question: MSFT
```

Type `exit` or `quit` to stop.

## API

`POST /query` with `{"query": "..."}` returns `{"response": {AgentName: {"summary": markdown}}}` as documented in the root README. Swagger UI is at `/docs`. This implementation has no `/health` or `/agents` endpoint.

## RAG storage

`RAGAgent` persists its Chroma index at `working_dir/vector_db/chroma_index`, relative to this directory. On startup it adds any file in `../raw_data/` that is not yet indexed. Delete the directory to force a full rebuild.

## Notes

- `redis` and `secedgar` are listed in `requirements.txt` but nothing imports them.
- `src/agents/router.py` is the only orchestration code; everything it dispatches lives in `shared_lib/`, so behaviour changes usually belong there.
