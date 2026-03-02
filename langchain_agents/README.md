# FinanceAgents - LangChain Implementation

A FastAPI-based financial analysis system that uses LangChain and semantic similarity routing to provide comprehensive investment insights through specialized AI agents.

## 🎯 What Makes This Implementation Unique?

This LangChain implementation features:

- **Semantic Query Classification**: Uses sentence transformers to determine if queries are finance-related
- **Intelligent Router**: Similarity-based routing with configurable threshold (0.4)
- **LangChain Framework**: Built on the LangChain ecosystem for agent orchestration
- **Parallel Execution**: Async execution of multiple agents concurrently
- **Shared Schemas**: Standardized communication via shared_lib

## 🏗️ Architecture

### Core Components

**RouterAgent** (`src/agents/router.py`)
- Central orchestrator using semantic similarity for query classification
- Extracts company names and maps them to stock tickers
- Calculates similarity score against finance keywords
- Dispatches queries to appropriate agents in parallel

**Routing Logic:**
- Non-finance queries (similarity < 0.4) → GeneralAgent only
- Finance + tickers → All agents (Reddit, Finance, Yahoo, SEC, General)
- Finance + companies (no tickers) → Reddit, Finance, General
- Finance (no companies) → Reddit, General

### Specialized Agents

| Agent | Purpose | Implementation |
|-------|---------|----------------|
| **FinanceAgent** | RAG-based document analysis | ChromaDB + HuggingFace embeddings |
| **YahooAgent** | Real-time stock data (30-day) | yfinance + GPT-3.5 analysis |
| **SECAgent** | SEC filing analysis | SEC EDGAR API (mock data for now) |
| **RedditAgent** | Social sentiment analysis | PRAW (r/stocks scraping) |
| **GeneralAgent** | Non-finance queries | GPT-3.5-turbo |
| **MonitorAgent** | System logging | JSON-based health monitoring |

### Shared Schemas

Standardized communication schemas from `shared_lib/schemas.py`:

- **MCPContext**: Shared context (user_query, companies, tickers, extracted_terms)
- **MCPRequest**: Standardized request with context, timestamp, source
- **MCPResponse**: Standardized response with data, context_updates, status

## 📦 Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Reddit API credentials (optional, for sentiment analysis)

### Setup

1. **Navigate to the directory**
   ```bash
   cd langchain_agents
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   REDDIT_CLIENT_ID=your_reddit_client_id_here
   REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
   ```

4. **Prepare document data** (optional)

   Place PDF financial documents in `./raw_data/` directory:
   ```bash
   mkdir -p raw_data
   # Add PDFs with format: company-year.pdf (e.g., apple-2023.pdf)
   ```

## 🚀 Usage

### Starting the Application

**Run FastAPI server + CLI:**
```bash
python src/main.py
```

This starts:
- FastAPI server on `http://localhost:8000`
- Interactive CLI interface

**Using Docker:**
```bash
# Build the image
docker build -t financeagents-backend .

# Run the container
docker run -p 8000:8000 financeagents-backend
```

**Using uvicorn directly:**
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### REST API Usage

**Endpoint:** `POST /query`

**Request:**
```json
{
  "query": "What is Apple's latest financial performance?"
}
```

**Response:**
```json
{
  "response": {
    "FinanceAgent": {
      "summary": "Analysis of Apple's internal documents..."
    },
    "YahooAgent": {
      "summary": "30-day stock performance shows..."
    },
    "SECAgent": {
      "summary": "Latest SEC filings indicate..."
    },
    "RedditAgent": {
      "summary": "Social sentiment analysis reveals..."
    }
  }
}
```

### CLI Interface

When running `python src/main.py`, interact directly in the terminal:
```
Enter your query (or 'exit' to quit): What is the current stock price of Tesla?
```

### Example Queries

**Stock Analysis:**
```
Tell me about Tesla stock performance
```

**Company Comparison:**
```
Compare Microsoft and Google stock performance
```

**Market Sentiment:**
```
What is the sentiment around NVDA on Reddit?
```

**Document Analysis:**
```
What are Amazon's key financial metrics?
```

**General Query:**
```
What is a P/E ratio?
```

## 📊 How It Works

### 1. Semantic Query Classification

The router uses sentence transformers to determine query relevance:

```python
# Calculate similarity between query and finance keywords
similarity_score = semantic_similarity(query, finance_keywords)

if similarity_score >= 0.4:
    # Finance-related query
    route_to_financial_agents()
else:
    # General query
    route_to_general_agent()
```

### 2. Company/Ticker Extraction

- Maintains hardcoded mapping for common companies (Apple → AAPL, etc.)
- Scans `raw_data/` directory for additional company names from PDF filenames
- Case-insensitive matching in query text

### 3. Document Analysis (RAG)

**FinanceAgent:**
- Checks for existing ChromaDB index at `working_dir/vector_db/chroma_index`
- If missing, builds index from PDFs in `raw_data/` directory
- Uses HuggingFace `all-MiniLM-L6-v2` embeddings
- Stores metadata: file_name, year, company
- Queries retrieve relevant passages for GPT synthesis

### 4. Parallel Agent Execution

```python
# RouterAgent uses asyncio.gather() for concurrent execution
results = await asyncio.gather(*[
    agent.run(mcp_request) for agent in selected_agents
])
```

Some agents use `loop.run_in_executor()` to wrap synchronous code.

### 5. Response Processing Pipeline

1. RouterAgent dispatches query to selected agents
2. Each agent returns MCPResponse with data field
3. `src/main.py` post-processes responses using `improve_agent_response()`
4. GPT-3.5-turbo summarizes and cleans agent output
5. Final response maps agent names to {summary: "..."}

## 📁 Project Structure

```
langchain_agents/
├── src/                      # Source code
│   ├── main.py               # FastAPI application entry
│   └── agents/               # Agent implementations
│       └── router.py         # Semantic routing and orchestration
│
├── tests/                    # Test files
│   └── sample_outputs/       # Sample agent response outputs
│
├── working_dir/              # Generated data (gitignored)
│   ├── vector_db/            # ChromaDB persistence
│   │   └── chroma_index/     # Vector embeddings
│   └── logs/                 # Monitor logs
│
├── raw_data/                 # Financial documents (PDFs)
├── requirements.txt          # Python dependencies
├── dockerfile                # Docker configuration
└── README.md                 # This file
```

> **Note:** Shared agent implementations (FinanceAgent, YahooAgent, RedditAgent, SECAgent, GeneralAgent, MonitorAgent) and communication schemas live in the top-level `shared_lib/` directory at the repository root.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Yes |
| `REDDIT_CLIENT_ID` | Reddit API client ID | Optional |
| `REDDIT_CLIENT_SECRET` | Reddit API client secret | Optional |

### Company/Ticker Mapping

Defined in `src/agents/router.py`:
```python
COMPANY_TICKER_MAP = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    # ... add more companies
}
```

### Finance Keywords

The router maintains a list of finance-related keywords for semantic matching:
- stock, investment, portfolio, earnings, P/E ratio, dividend
- revenue, profit margin, market cap, volatility
- And more...

## 📡 API Endpoints

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

**Available Endpoints:**

- `POST /query` - Process financial queries
- `GET /health` - Health check endpoint
- `GET /` - Welcome message

## 🔍 Key Features

### 1. Semantic Similarity Routing

Unlike keyword-based routing, this uses vector embeddings to understand query intent:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
similarity = cosine_similarity(query_embedding, keyword_embeddings)
```

### 2. Dynamic Company Discovery

Automatically discovers companies from PDF filenames in `raw_data/`:
```
raw_data/
├── apple-2023.pdf      # Detected: "apple"
├── microsoft-2024.pdf  # Detected: "microsoft"
└── tesla-2023.pdf      # Detected: "tesla"
```

### 3. Flexible Agent Selection

Agents are selected dynamically based on:
- Query classification (finance vs. general)
- Presence of company names/tickers
- Availability of data sources

### 4. Response Enhancement

Each agent's raw output is processed by GPT-3.5-turbo to:
- Improve formatting and readability
- Summarize key insights
- Remove irrelevant information
- Maintain professional tone

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Adding New Agents

1. Create agent file in `shared_lib/agents/` directory
2. Implement MCP protocol interface:
   ```python
   async def run(self, mcp_request: MCPRequest) -> MCPResponse:
       # Your agent logic
       return MCPResponse(data={...})
   ```
3. Add agent to router logic in `src/agents/router.py`
4. Update agent selection criteria

### Modifying Semantic Threshold

Adjust the similarity threshold in `src/agents/router.py`:
```python
# Default: 0.4
if similarity_score >= 0.4:  # Make stricter: 0.6, more lenient: 0.3
    # Finance query
```

### Vector Database Management

**Rebuild index:**
```bash
# Delete existing index
rm -rf working_dir/vector_db/chroma_index

# Restart application (will rebuild automatically)
python src/main.py
```

## 📊 Monitoring and Logging

- All agent activities logged to `working_dir/logs/monitor_logs.json`
- JSON lines format with timestamps, queries, responses, status
- MonitorAgent tracks system health and performance

## 📚 Technologies Used

- **LangChain**: Agent framework and orchestration
- **FastAPI**: Modern web framework for REST API
- **ChromaDB**: Vector database for embeddings
- **HuggingFace**: Transformers and embedding models
- **Sentence Transformers**: Semantic similarity calculations
- **OpenAI GPT-3.5**: Response improvement and generation
- **yfinance**: Yahoo Finance API wrapper
- **PRAW**: Reddit API wrapper
- **secedgar**: SEC EDGAR API client

## ⚡ Performance

- **Semantic Routing**: < 1 second for query classification
- **Parallel Execution**: 3-5x faster than sequential processing
- **Vector Search**: Sub-second document retrieval
- **Typical Response Times**:
  - General queries: < 5 seconds
  - Single-company analysis: 10-20 seconds
  - Multi-agent comprehensive analysis: 20-40 seconds

## 🐛 Troubleshooting

### Common Issues

**"Vector database not found"**
- Ensure PDFs are in `raw_data/` directory
- Database builds automatically on first run
- Check write permissions for `working_dir/vector_db/` directory

**"OPENAI_API_KEY not found"**
- Verify `.env` file exists
- Check environment variables are loaded correctly
- Ensure API key is valid and has credits

**"Redis connection error"**
- Context store requires Redis but is not currently used in main flow
- You can ignore this warning for basic functionality
- Install Redis if you want to use context persistence

**"Agent timeout"**
- Some queries may take longer for comprehensive analysis
- Network latency affects external API calls (Yahoo, SEC, Reddit)
- Consider caching frequently requested data

**"Low similarity score - routing to GeneralAgent"**
- Query may not contain finance keywords
- Adjust similarity threshold if needed
- Add more finance keywords to the list

**"CORS errors"**
- CORS is enabled for all origins by default
- Adjust settings in `src/main.py` if needed for production

## 🔗 Related Implementations

This is the **LangChain** implementation. See the parent directory for other implementations:

- **[LlamaIndex](../llamaindex_agents/README.md)** - Workflow-based with event-driven architecture
- **[CrewAI](../crewai_agents/README.md)** - Crew-based agent coordination

All implementations share the same agent types and data sources but differ in orchestration approach.

## 📄 License

This implementation demonstrates LangChain framework capabilities for financial analysis. Ensure compliance with API terms of service (OpenAI, Yahoo Finance, Reddit, SEC) when deploying.

---

**Built with LangChain** 🦜🔗
