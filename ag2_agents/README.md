# FinanceAgents - AG2 Implementation

The [AG2](https://github.com/ag2ai/ag2) (formerly AutoGen) shell around the shared FinanceAgents core: a FastAPI server, an interactive CLI, a deterministic router, and a standalone AG2 `GroupChat` demo in which an LLM coordinator decides which agents to consult.

For the system overview, agent list, routing rules, environment setup, and the web UI see the [root README](../README.md). This file covers only what is specific to this directory.

## What is here

```
ag2_agents/
├── src/
│   ├── main.py                # FastAPI app + CLI loop (port 8000); uses RouterAG2
│   ├── ag2_agent.py           # AG2-native ConversableAgent + GroupChat demo
│   └── agents/
│       └── ag2_router.py      # RouterAG2: classify -> dispatch shared agents concurrently
├── tests/                     # empty
├── working_dir/               # generated, gitignored: vector_db/chroma_index, logs
├── requirements.txt           # ../requirements.txt + ag2>=0.9,<1.0
└── dockerfile                 # not maintained, see root README
```

## Two orchestration paths

**`main.py` uses `RouterAG2`.** Same shape as the other three routers: `shared_lib/query_classification` picks the agents, they run under `asyncio.gather`, and the shared LLM passes produce the summaries. This is what serves `POST /query` and the CLI. Latency and cost are predictable.

**`ag2_agent.py` is the AG2-native demo.** Each shared agent (`RAGAgent`, `FinanceAgent`, `YahooAgent`, `SECAgent`, `RedditAgent`, `GeneralAgent`) is registered as a tool on its own `ConversableAgent`; a `coordinator` `ConversableAgent` plus a `UserProxyAgent` executor sit in a `GroupChat` run by `GroupChatManager` with automatic speaker selection. The coordinator's LLM decides who speaks and which tools run, then ends with `TERMINATE`. Run it directly:

```bash
env $(cat ../env.all) python src/ag2_agent.py "Tell me about Tesla stock"
```

Expect several LLM calls per round for up to 12 rounds; it costs far more tokens than the router.

## Run the server

From this directory, with `env.all` filled in at the repository root:

```bash
cd ag2_agents
env $(cat ../env.all) python src/main.py
```

You get the API on `http://localhost:8000` and a prompt in the same terminal (`Enter your question:`; `exit` or `quit` to stop).

## API

- `POST /query` `{"query": "..."}` returns `{"response": {AgentName: {"summary": markdown}}}` as documented in the root README.
- `GET /health`, `GET /agents`.
- Swagger UI at `/docs`.

## AG2 version

`requirements.txt` pins `ag2>=0.9,<1.0`. On that line the package installs as `ag2` and imports as `from autogen import ConversableAgent, GroupChat, ...`. AG2 1.0 is a different framework (`ag2.Agent`, no `ConversableAgent`, no `autogen` module) and will not run `ag2_agent.py`. If you built the shared conda env before the pin was added, downgrade with:

```bash
pip install "ag2>=0.9,<1.0"
```

## RAG storage

`RAGAgent` persists its Chroma index at `working_dir/vector_db/chroma_index`, relative to this directory, and adds new `../raw_data/` files on startup.
