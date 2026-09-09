# FinanceAgents - LlamaIndex Implementation

The LlamaIndex-flavoured implementation of FinanceAgents. Unlike the other three directories, this one replaces several shared agents with LlamaIndex-native versions: retrieval runs on a persisted `VectorStoreIndex`, the Yahoo agent can export CSVs, and the Reddit agent uses `asyncpraw`.

For the system overview, routing rules, environment setup, and the web UI see the [root README](../README.md). This file covers only what is specific to this directory.

## What is here

```
llamaindex_agents/
├── src/
│   ├── main.py                    # FastAPI app + CLI loop (port 8000)
│   ├── rag_agent.py               # RAGAgent on a persisted VectorStoreIndex
│   ├── finance_agent.py           # FinanceAgent: query engine over RAGAgent's index
│   ├── yahoo_agent_enhanced.py    # YahooAgentEnhanced: yfinance stats + CSV export + index
│   ├── reddit_agent.py            # RedditAgent on asyncpraw
│   ├── llm_settings.py            # builds the LlamaIndex LLM for the configured provider
│   └── agents/
│       └── router.py              # RouterAgent: classify -> dispatch agents concurrently
├── tests/                         # standalone scripts, see below
├── working_dir/                   # generated, gitignored
│   ├── vector_db/llamaindex_storage/   # RAG index
│   ├── financial_data/csv/             # Yahoo exports
│   └── financial_data/yahoo_index/
├── requirements.txt               # ../requirements.txt + llama-index-* packages, asyncpraw
```

`SECAgent` and `GeneralAgent` come from `shared_lib/`.

## Agents specific to this directory

| Agent | File | Notes |
|-------|------|-------|
| `RAGAgent` | `src/rag_agent.py` | Owns the `VectorStoreIndex`. Builds it from `../raw_data/` on first run, persists to `working_dir/vector_db/llamaindex_storage`, and inserts any new raw file on later startups. `retrieve(query, company, k)` returns passages; `query_engine` does retrieval plus synthesis. |
| `FinanceAgent` | `src/finance_agent.py` | Runs `RAGAgent.query_engine` per company, extracts revenue/income/asset figures with regex, returns the synthesized answer plus source snippets. |
| `YahooAgentEnhanced` | `src/yahoo_agent_enhanced.py` | 30-day statistics via `yfinance`, optional CSV export under `working_dir/financial_data/csv/`. |
| `RedditAgent` | `src/reddit_agent.py` | Async Reddit search with `asyncpraw`. |

The chat LLM comes from `src/llm_settings.py`, which reads the shared provider settings (`shared_lib/llm_config.py`). With `LLM_PROVIDER=openrouter` it uses `OpenAILike`, since LlamaIndex's `OpenAI` class rejects non-OpenAI model ids. The embedding model is the shared cached `all-MiniLM-L6-v2` (`shared_lib/embeddings.py`).

## Run

From this directory, with `env.all` filled in at the repository root:

```bash
cd llamaindex_agents
env $(cat ../env.all) python src/main.py
```

You get the API on `http://localhost:8000` and a prompt in the same terminal (`Enter your question:`; `exit` or `quit` to stop).

The first start builds the index from every filing in `../raw_data/`. With the five bundled 10-Q/10-K filings that takes a few minutes; later starts load it in seconds.

## API

- `POST /query` `{"query": "..."}` returns `{"response": {AgentName: {"summary": markdown}}}` as documented in the root README.
- `GET /health` returns status and version.
- `GET /agents` lists the agents.
- Swagger UI at `/docs`.

## Tests

The files under `tests/` are standalone scripts, not pytest cases. Run them from this directory:

```bash
env $(cat ../env.all) python tests/test_implementation.py   # imports + schema smoke test
env $(cat ../env.all) python tests/test_workflow.py         # end to end, calls the LLM
env $(cat ../env.all) python tests/test_yahoo_enhanced.py
python tests/debug_agents.py                                 # per-agent isolation
python tests/debug_router.py
```

## Notes

- Orchestration is the same deterministic router as the other three implementations. An earlier LlamaIndex Workflow design was replaced; there are no `@step` workflows in this directory.
- The retrieval similarity cutoff in `RAGAgent` defaults to 0.3. `all-MiniLM-L6-v2` cosine scores for good matches sit around 0.4 to 0.65, so a higher cutoff filters everything out.
