# FinanceAgents — AG2 Implementation

A FastAPI-based financial analysis system that uses [AG2](https://github.com/ag2ai/ag2) (formerly AutoGen) to orchestrate specialized agents over financial documents, SEC filings, real-time stock data, and Reddit sentiment.

This is one of four parallel implementations in the FinanceAgents repository (alongside LlamaIndex, CrewAI, and LangChain).

## Architecture

### Core Components

**Router** (`src/agents/ag2_router.py`)
- `RouterAG2` analyzes the query, picks the relevant agents, and runs them concurrently with `asyncio.gather`.
- Uses the same `shared_lib/query_classification.py` helpers as the other implementations, so routing decisions are consistent.

**AG2-native flow** (`src/ag2_agent.py`)
- Demonstrates AG2's idiomatic style: each shared agent is wrapped as a tool registered on a `ConversableAgent`, and a coordinator `ConversableAgent` + `GroupChatManager` decides which tools to call.
- Useful as a reference; main.py uses the deterministic router for predictable latency.

**Specialized agents** (from `shared_lib/agents/`)
- `FinanceAgent` — RAG over internal PDFs (ChromaDB + HuggingFace embeddings).
- `YahooAgent` — 30-day stock statistics from Yahoo Finance.
- `SECAgent` — SEC filing summaries.
- `RedditAgent` — Reddit sentiment via PRAW.
- `GeneralAgent` — Non-financial queries.

**MCP protocol** (`shared_lib/schemas.py`)
- `MCPRequest` / `MCPResponse` / `MCPContext` shared across all four implementations.

## Quick Start

### Prerequisites
- Python 3.8+
- `pip`
- (Optional) Docker

### Install

```bash
cd ag2_agents
pip install -r requirements.txt
```

### Environment

Create a `.env` file (or use the project-root `.env`):

```env
OPENAI_API_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

### Run

```bash
# Local: starts FastAPI on :8002 and an interactive CLI
env $(cat ../.env) python src/main.py

# Or run the AG2-native group-chat demo directly
python src/ag2_agent.py "Tell me about Tesla stock"
```

### Docker

```bash
docker build -t financeagents-ag2 .
docker run -p 8002:8002 financeagents-ag2
```

## API

`POST /query`

```json
{ "query": "What is Apple's revenue trend?" }
```

`GET /health`, `GET /agents` — service introspection.

Swagger UI: `http://localhost:8002/docs`

## Project Structure

```
ag2_agents/
├── src/
│   ├── main.py                # FastAPI server + CLI (port 8002)
│   ├── ag2_agent.py           # AG2-native ConversableAgent + GroupChat demo
│   └── agents/
│       ├── ag2_router.py      # Deterministic router + APIRouter
│       └── readme.txt
├── tests/
├── working_dir/               # gitignored
├── requirements.txt
├── dockerfile
└── README.md
```

## How AG2 fits in

The deterministic `RouterAG2` is identical in shape to `RouterCrew` / `RouterAgent` — same parallel `asyncio.gather` over the shared agents — to keep behavior comparable across frameworks.

The framework-specific code lives in `ag2_agent.py`:
- `ConversableAgent` instances per specialty, each with a tool that proxies to the corresponding shared agent.
- A `coordinator` `ConversableAgent` plus a `UserProxyAgent` executor.
- `GroupChat` + `GroupChatManager` for multi-turn LLM-driven orchestration.

This mirrors how `crewai_agents/src/crew_agent.py` demonstrates CrewAI patterns while `crewai_router.py` does the work in main.

## Ports

| Implementation | HTTP port |
|----------------|-----------|
| LangChain      | 8000      |
| CrewAI         | 8001      |
| LlamaIndex     | 8001      |
| **AG2**        | **8002**  |

## Disclaimer

For educational/research use only. Not financial advice.
