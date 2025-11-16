# FinanceAgents

An AI-powered financial analysis system that provides comprehensive investment insights by combining data from multiple sources. This project demonstrates the same financial analysis system implemented using three different agent frameworks: **LlamaIndex**, **CrewAI**, and **LangChain**.

## 🎯 What Does FinanceAgents Do?

FinanceAgents is a multi-agent system that answers financial queries by orchestrating specialized AI agents. When you ask a financial question, the system automatically:

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

## 📦 Project Structure

This repository contains three separate implementations of the same financial analysis system:

```
FinanceAgents/
├── llamaindex_agents/     # LlamaIndex Workflow implementation
├── crewai_agenets/        # CrewAI implementation
├── langchain_agents/      # LangChain implementation
└── README.md              # This file
```

### Implementation Comparison

| Framework | Architecture | Orchestration | Key Features |
|-----------|--------------|---------------|--------------|
| **LlamaIndex** | Event-driven workflow | Declarative workflow steps | Robust parallel execution, built-in timeout handling |
| **CrewAI** | Router-based | Concurrent async execution | Agent crew coordination, MCP protocol |
| **LangChain** | Router-based | Semantic similarity routing | Query classification via sentence transformers |

All three implementations share:
- **Specialized Agents**: Finance, Yahoo, SEC, Reddit, General agents
- **RAG Capabilities**: Vector database with HuggingFace embeddings
- **Dual Interface**: REST API + Interactive CLI
- **MCP Protocol**: Standardized agent communication
- **Parallel Processing**: Fast concurrent agent execution

## 🚀 Getting Started

### Choose Your Implementation

Each implementation is self-contained in its own directory. Navigate to the implementation you want to use:

- **[llamaindex_agents/](./llamaindex_agents/README.md)** - Recommended for production use (most robust)
- **[crewai_agenets/](./crewai_agenets/README.md)** - Great for crew-based agent coordination
- **[langchain_agents/](./langchain_agents/)** - Best for semantic query routing

Each directory contains its own README with detailed setup instructions.

### Prerequisites

All implementations require:
- Python 3.8+
- OpenAI API key
- Reddit API credentials (optional, for sentiment analysis)

### Quick Start (LlamaIndex Example)

```bash
# Navigate to implementation directory
cd llamaindex_agents

# Install dependencies
pip install -r requirements.txt

# Create .env file with API keys
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
EOF

# Run the application
python main.py
```

See each implementation's README for specific setup instructions.

## 🏗️ Common Architecture

### Specialized Agents

All implementations use these specialized agents:

| Agent | Purpose | Data Source |
|-------|---------|-------------|
| **FinanceAgent** | Analyze internal financial documents | PDF documents via RAG/Vector DB |
| **YahooAgent** | Real-time stock data and metrics | Yahoo Finance API |
| **SECAgent** | Regulatory filings and compliance | SEC EDGAR API |
| **RedditAgent** | Market sentiment analysis | Reddit API (r/stocks, r/investing) |
| **GeneralAgent** | General context and information | GPT-powered responses |

### Data Flow

```
User Query
    ↓
Query Analysis (Extract companies/tickers)
    ↓
Agent Selection (Determine relevant agents)
    ↓
Parallel Agent Execution (Finance, Yahoo, SEC, Reddit, General)
    ↓
Response Enhancement (LLM improves each output)
    ↓
Summary Generation (Synthesize comprehensive report)
    ↓
Final Response
```

## 💡 Example Queries

Try these queries with any implementation:

**Stock Analysis:**
```
Tell me about Tesla stock
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
What are the key metrics in Apple's financial reports?
```

**Multi-company Analysis:**
```
Analyze the tech sector: Apple, Microsoft, Google, and Amazon
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the implementation directory you're using:

```env
OPENAI_API_KEY=your_openai_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
```

### Adding Financial Documents

To enable document analysis:

1. Create a `raw_data/` directory in your chosen implementation folder
2. Add PDF financial documents with format: `company-year.pdf` (e.g., `apple-2023.pdf`)
3. The system will automatically build a vector index on first run

### Supported Companies

Built-in mappings for major companies:
- Apple (AAPL), Microsoft (MSFT), Google/Alphabet (GOOGL)
- Amazon (AMZN), Meta/Facebook (META), Tesla (TSLA)
- NVIDIA (NVDA), Netflix (NFLX), Intel (INTC), IBM (IBM)

Add new companies by:
1. Adding PDF documents to `raw_data/`
2. Updating the company-ticker mapping in the router/workflow file

## 📚 Technologies Used

### Common Technologies
- **OpenAI GPT-3.5/4**: Language models for analysis and synthesis
- **HuggingFace**: Embedding models for semantic search
- **ChromaDB**: Vector database for document storage
- **FastAPI**: REST API framework
- **yfinance**: Yahoo Finance data access
- **PRAW**: Reddit API client

### Framework-Specific
- **LlamaIndex**: Workflow orchestration and RAG
- **CrewAI**: Multi-agent crew coordination
- **LangChain**: Agent chaining and semantic routing

## 🎓 Learning Resources

This project is ideal for:
- Learning different agent frameworks and their trade-offs
- Understanding RAG (Retrieval-Augmented Generation) systems
- Building multi-agent financial analysis systems
- Comparing workflow vs router architectures
- Exploring parallel agent execution patterns

## 📖 Documentation

- [LlamaIndex Implementation](./llamaindex_agents/README.md) - Event-driven workflow architecture
- [CrewAI Implementation](./crewai_agenets/README.md) - Crew-based agent coordination
- LangChain Implementation - Semantic routing (see `langchain_agents/CLAUDE.md`)

## 🤝 Contributing

Each implementation is independently maintained. To contribute:

1. Choose the implementation you want to enhance
2. Follow that implementation's development guidelines
3. Test your changes thoroughly
4. Submit a pull request with clear description

## 📄 License

This project demonstrates AI agent frameworks for educational purposes. Ensure compliance with API terms of service (OpenAI, Yahoo Finance, Reddit, SEC) when deploying.

## ⚠️ Disclaimer

This system is for educational and research purposes only. It is not financial advice. Always consult with qualified financial professionals before making investment decisions.

---

**Choose your framework and start analyzing!** 🚀
