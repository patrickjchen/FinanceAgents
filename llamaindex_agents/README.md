# FinanceAgents - LlamaIndex Implementation

FinanceAgents is an AI-powered financial analysis system that provides comprehensive investment insights by combining data from multiple sources. Built with the LlamaIndex framework, it orchestrates specialized AI agents to deliver in-depth stock analysis, regulatory insights, and market sentiment—all in one query.

## 🎯 What Does FinanceAgents Do?

When you ask a financial question, FinanceAgents automatically:

1. **Analyzes your query** to extract company names and stock tickers
2. **Selects relevant agents** based on your question type
3. **Runs agents in parallel** for fast, comprehensive analysis
4. **Synthesizes results** into a cohesive investment report

All in seconds, giving you:
- 📊 **Real-time stock data** from Yahoo Finance
- 📄 **SEC filing analysis** from regulatory documents
- 💬 **Social sentiment** from Reddit discussions
- 📚 **Internal document analysis** using RAG (Retrieval-Augmented Generation)
- 🎯 **Comprehensive summary** synthesizing all insights

## 🏗️ Architecture

### Workflow-Based Design

FinanceAgents uses a **LlamaIndex Workflow** architecture for robust, parallel execution:

```
User Query
    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 1: Query Analysis                                 │
│  • Extract companies & tickers                          │
│  • Determine relevant agents                            │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: Parallel Agent Execution                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │FinanceAgent  │ │ YahooAgent   │ │ SECAgent     │   │
│  │(RAG Docs)    │ │(Market Data) │ │(Filings)     │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
│  ┌──────────────┐ ┌──────────────┐                     │
│  │RedditAgent   │ │GeneralAgent  │                     │
│  │(Sentiment)   │ │(Context)     │                     │
│  └──────────────┘ └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: Response Improvement                           │
│  • LLM enhances each agent's output                     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  Step 4: Comprehensive Summary                          │
│  • Synthesize all data into executive report            │
└─────────────────────────────────────────────────────────┘
    ↓
Complete Investment Analysis
```

### Specialized Agents

Each agent focuses on a specific data source:

| Agent | Purpose | Data Source |
|-------|---------|-------------|
| **FinanceAgent** | Analyze internal financial documents | PDF documents via RAG/Vector DB |
| **YahooAgent** | Real-time stock data and metrics | Yahoo Finance API |
| **SECAgent** | Regulatory filings and compliance | SEC EDGAR API |
| **RedditAgent** | Market sentiment analysis | Reddit API (r/stocks, r/investing) |
| **GeneralAgent** | General context and information | GPT-powered responses |

## 📦 Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Reddit API credentials (optional, for sentiment analysis)

### Setup

1. **Clone the repository**
   ```bash
   cd llamaindex_agents
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root:
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

### Starting FinanceAgents

Run the system with environment variables:

```bash
env $(cat ./.env) python src/main.py
```

You'll see:

```
Starting FinanceAgents - LlamaIndex Implementation...
INFO:     Started server process [15258]
INFO:     Waiting for application startup.

============================================================
FinanceAgents - Workflow Implementation
Interactive CLI Started - Powered by LlamaIndex Workflow
============================================================

Enter your financial question (or 'quit' to exit):
```

The system starts:
- **FastAPI server** on `http://0.0.0.0:8001` (for API access)
- **Interactive CLI** for direct queries

### Example Queries

**Stock Analysis:**
```
Enter your financial question (or 'quit' to exit): tell me about Tesla stock
```

**Output:**
```
============================================================
🚀 Starting FinanceAgents Workflow Analysis
📝 Query: tell me about Tesla stock
🕐 Start Time: 11:39:33
============================================================
[YahooAgentEnhanced] Fetching data for TSLA
[YahooAgentEnhanced] Analyzing query: tell me about Tesla stock

============================================================
🎯 FinanceAgents Workflow Results
⏱️ Total Execution Time: 24.03 seconds
📊 Status: success
============================================================

✅ Response received from agents:

📊 YahooAgent:
- Market Cap: $1.34 trillion
- Current Price: $404.35
- Price Range: $320.11 - $468.37
- Total Return: 22.32%
- Average Daily Return: 0.36%
- Volatility: 3.18% daily standard deviation
...

📊 SECAgent:
Key Financial Highlights (Q3 2025):
- Revenues: $69.92 billion
- Net Income: $2.95 billion
- Total Assets: $133.73 billion
- Stockholders' Equity: $79.97 billion
...

📊 FinalSummary:
================================================================================
🎯 COMPREHENSIVE INVESTMENT ANALYSIS
================================================================================

**Key Findings:**
- Tesla has shown strong financial performance in Q3 2025
- Stock experienced volatility with 22.32% total return over 3 months
- SEC filings indicate compliance and transparency

**Investment Perspective:**
- Strong growth trends suggest positive outlook
- Innovative EV approach attracts long-term investors

**Risk Assessment:**
- Stock price volatility poses short-term risks
- Long-term growth potential with sustainable energy focus

**Actionable Recommendations:**
- Consider as long-term investment opportunity
- Monitor stock performance and diversify portfolio
- Conduct further market trend analysis
================================================================================
```

**Company Comparison:**
```
Compare Apple and Microsoft stocks
```

**Market Sentiment:**
```
What is the sentiment around NVIDIA on social media?
```

**Document Analysis:**
```
What are the key metrics in Tesla's financial reports?
```

### Exiting

Type `quit`, `exit`, or `q` to stop the CLI.

## 🌐 API Access

FinanceAgents also runs as a REST API server on port 8001.

### Endpoints

**POST `/query`** - Process financial queries
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Apple stock performance?"}'
```

Response:
```json
{
  "response": {
    "YahooAgent": {
      "summary": "Apple (AAPL) analysis..."
    },
    "SECAgent": {
      "summary": "SEC filing insights..."
    },
    "FinalSummary": {
      "summary": "🎯 COMPREHENSIVE INVESTMENT ANALYSIS..."
    }
  }
}
```

**GET `/health`** - Health check
```bash
curl http://localhost:8001/health
```

**GET `/agents`** - List available agents
```bash
curl http://localhost:8001/agents
```

## 🔧 Configuration

### Supported Companies

FinanceAgents includes built-in mappings for major companies:
- Apple (AAPL), Microsoft (MSFT), Google/Alphabet (GOOG)
- Amazon (AMZN), Meta/Facebook (META), Tesla (TSLA)
- NVIDIA (NVDA), Netflix (NFLX), Intel (INTC), IBM (IBM)

**Add new companies:**
1. Add PDF documents to `./raw_data/` (format: `company-year.pdf`)
2. Update `config/companies.json` at the project root with the company name and ticker

### Agent Selection

FinanceAgents automatically selects agents based on query type:

| Query Type | Agents Activated |
|------------|------------------|
| Non-finance query | GeneralAgent only |
| Finance query with ticker | All agents (Finance, Yahoo, SEC, Reddit, General) |
| Finance query without ticker | FinanceAgent + RedditAgent + GeneralAgent |

Finance keywords: stock, investment, portfolio, earnings, P/E ratio, dividend, etc.

### Data Storage

- **Vector Database**: `./working_dir/vector_db/llamaindex_storage/` (FinanceAgent RAG index)
- **Yahoo Index**: `./working_dir/financial_data/yahoo_index/` (cached market data)
- **CSV Exports**: `./working_dir/financial_data/csv/` (stock data exports)
- **Logs**: `working_dir/logs/monitor_logs.json` (agent performance and errors)

## 🧪 Testing

Run tests to verify system functionality:

```bash
# Test workflow system
python tests/test_workflow.py

# Test basic agent functionality
python tests/test_implementation.py

# Test Yahoo agent with CSV capabilities
python tests/test_yahoo_enhanced.py
```

## 📊 Performance

- **Parallel Execution**: 30-50% faster than sequential processing
- **Timeout**: Default 300 seconds (5 minutes) for complex queries
- **Typical Response Times**:
  - Simple queries: < 15 seconds
  - Multi-agent analysis: 20-30 seconds
  - Comprehensive reports: 30-60 seconds

## 🛠️ Troubleshooting

### Common Issues

**"OPENAI_API_KEY not found"**
- Ensure `.env` file exists with valid API key
- Run with: `env $(cat ./.env) python src/main.py`

**"No PDF documents found"**
- Create `./raw_data/` directory
- Add PDF files with format: `company-year.pdf`
- Or continue without PDFs (FinanceAgent will be skipped)

**"Reddit agent failed"**
- Reddit credentials are optional
- System continues with other agents if Reddit fails
- Add credentials to `.env` for sentiment analysis

**"Workflow timeout"**
- Increase timeout in workflow call
- Check internet connectivity
- Verify API keys are valid

**Agent-specific errors**
- Check `working_dir/logs/monitor_logs.json` for detailed error logs
- Verify all dependencies installed: `pip install -r requirements.txt`

## 📁 Project Structure

```
llamaindex_agents/
├── src/
│   ├── main.py                    # FastAPI server & CLI entry point
│   ├── finance_agent.py           # RAG-based document analysis
│   ├── yahoo_agent_enhanced.py    # Stock market data
│   ├── reddit_agent.py            # Social sentiment analysis
│   └── agents/
│       ├── __init__.py
│       └── router.py              # Main workflow orchestration
│
├── tests/
│   ├── test_workflow.py           # Workflow system tests
│   ├── test_implementation.py     # Basic agent tests
│   ├── test_yahoo_enhanced.py     # Yahoo agent tests
│   ├── simple_test.py             # Simple tests
│   ├── workflow_design.py         # Workflow design tests
│   ├── debug_agents.py            # Agent debugging
│   └── debug_router.py            # Router debugging
│
├── working_dir/
│   ├── vector_db/                 # Vector database storage
│   ├── financial_data/            # Market data cache & exports
│   └── logs/
│       └── monitor_logs.json      # System logs
│
├── raw_data/                      # PDF documents (create this)
├── requirements.txt               # Python dependencies
└── .env                           # Environment variables (create this)
```

## 🔍 How It Works

### Document Analysis (RAG)

1. PDF documents in `./raw_data/` are processed by FinanceAgent
2. Text is embedded using HuggingFace "all-MiniLM-L6-v2" model
3. Vectors stored in ChromaDB at `./working_dir/vector_db/` for semantic search
4. Queries retrieve relevant document passages
5. GPT-3.5-turbo synthesizes answers from retrieved context

### Market Data

1. YahooAgent fetches real-time data via `yfinance` library
2. Calculates metrics: returns, volatility, ranges, volumes
3. Can export data to CSV for further analysis
4. Creates vector index for historical query caching

### SEC Filings

1. SECAgent queries SEC EDGAR API for company filings
2. Extracts key financial metrics and regulatory insights
3. Provides compliance and transparency assessment

### Sentiment Analysis

1. RedditAgent searches stock-related subreddits
2. Analyzes discussion sentiment and trends
3. Provides social media perspective on stocks

### Synthesis

All agent outputs are:
1. Enhanced by GPT-3.5-turbo for clarity
2. Synthesized into comprehensive executive summary
3. Returned with metadata (execution times, status)

## 🌟 Key Features

- **Multi-Source Intelligence**: Combines internal docs, market data, regulatory filings, and social sentiment
- **Parallel Processing**: Agents run concurrently for maximum speed
- **Smart Routing**: Automatically selects relevant agents based on query
- **LLM Enhancement**: Improves readability and generates executive summaries
- **Robust Error Handling**: Individual agent failures don't break the system
- **Dual Interface**: Both CLI and REST API access
- **Comprehensive Logging**: Track performance and debug issues
- **Extensible**: Easy to add new agents and data sources

## 📚 Technologies

- **LlamaIndex**: Workflow orchestration and RAG framework
- **OpenAI GPT-3.5**: Language model for analysis and synthesis
- **HuggingFace**: Embedding model for semantic search
- **ChromaDB**: Vector database for document storage
- **FastAPI**: REST API framework
- **yfinance**: Yahoo Finance data access
- **PRAW**: Reddit API client
- **SEC EDGAR**: Regulatory filing access

## 📝 Version History

- **v3.0.0** - Workflow implementation (current)
  - Event-driven architecture
  - Parallel agent execution
  - Enhanced error handling

- **v2.0.0** - Router-based implementation (legacy)
  - Sequential agent processing
  - Basic orchestration

## 🤝 Contributing

To extend FinanceAgents:

1. **Add a new agent**: Implement `run(mcp_request)` method returning `MCPResponse`
2. **Add new data sources**: Integrate APIs in respective agent files
3. **Enhance workflow**: Add new workflow steps with event definitions
4. **Update documentation**: Keep CLAUDE.md and README.md in sync

## 📄 License

This implementation demonstrates LlamaIndex capabilities for financial analysis. Ensure compliance with API terms of service (OpenAI, Yahoo Finance, Reddit, SEC) when deploying.

## 🔗 Resources

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Yahoo Finance API](https://github.com/ranaroussi/yfinance)
- [SEC EDGAR](https://www.sec.gov/edgar)
- [PRAW Documentation](https://praw.readthedocs.io/)

---

**Built with ❤️ using LlamaIndex**
