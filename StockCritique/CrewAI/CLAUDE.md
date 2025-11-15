# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BankerAI is a FastAPI-based backend that provides financial analysis through multiple specialized agents. The system routes user queries to different agents based on query content and company mentions, then aggregates responses to provide comprehensive financial insights.

## Common Commands

### Development
- Start the server: `python main.py` (runs both FastAPI server on port 8000 and CLI interface)
- Install dependencies: `pip install -r requirements.txt`
- Docker build: `docker build -t bankerai-backend .`
- Docker run: `docker run -p 8000:8000 bankerai-backend`

### Testing
- Run tests: `pytest` (pytest is included in requirements.txt)

## Architecture

### Core Components

**Main Application (`main.py`)**
- FastAPI server with `/query` endpoint
- Dual interface: HTTP API + CLI loop
- Response improvement via OpenAI GPT-3.5-turbo
- CORS middleware for cross-origin requests

**Router System (`agents/crewai_router.py`)**
- `RouterCrew` class handles query routing and agent orchestration
- Determines which agents to run based on query analysis
- Extracts companies/tickers from queries using regex patterns
- Runs agents concurrently using asyncio.gather()

**MCP Protocol (`mcp/schemas.py`)**
- Standardized request/response format across all agents
- `MCPRequest`: Contains context with user_query, companies, tickers
- `MCPResponse`: Contains agent data, context updates, status
- `MCPContext`: Shared context passed between agents

### Agent Architecture

**Agent Types:**
- `GeneralAgent`: Handles non-finance queries
- `FinanceAgent`: Analyzes internal financial documents using RAG (ChromaDB + HuggingFace embeddings)
- `YahooAgent`: Fetches real-time stock data
- `SECAgent`: Processes SEC financial filings
- `RedditAgent`: Performs sentiment analysis on Reddit posts
- `MonitorAgent`: Logs health/status across all agents

**Agent Selection Logic:**
- Non-finance queries → GeneralAgent only
- Finance queries with tickers → All financial agents + GeneralAgent
- Finance queries without tickers → RedditAgent, FinanceAgent, GeneralAgent

### Key Patterns

**Document Processing:**
- PDFs stored in `./backend/raw_data/`
- ChromaDB vector database in `vector_db/chroma_index/`
- HuggingFace embeddings model: "all-MiniLM-L6-v2"

**Error Handling:**
- Comprehensive try/catch blocks in all agents
- Graceful fallbacks when agents fail
- JSON logging to `monitor_logs.json`

**Company/Ticker Mapping:**
- Hardcoded mapping in `COMPANY_TICKER_MAP`
- Dynamic extraction from PDF filenames in raw_data directory
- Finance keywords list for query classification

## Environment Setup

Required environment variables in `.env`:
- `OPENAI_API_KEY`: For GPT-3.5-turbo response improvement
- `REDDIT_CLIENT_ID`: For Reddit API access
- `REDDIT_CLIENT_SECRET`: For Reddit API access

## File Structure Notes

- `agents/`: All agent implementations
- `mcp/`: MCP protocol schemas and context management
- `vector_db/`: ChromaDB persistence directory
- `backend/raw_data/`: PDF documents for FinanceAgent RAG
- `monitor_logs.json`: Centralized logging output
- `dockerfile`: Production container setup

## Development Notes

- The system uses both sync and async patterns - agents run in thread pools when needed
- Response formatting happens in main.py via `improve_agent_response()`
- All agents follow the MCP protocol for consistency
- Vector database is built on first run if not present