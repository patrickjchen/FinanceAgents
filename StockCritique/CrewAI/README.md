# BankerAI Backend

A FastAPI-based financial analysis system that uses specialized AI agents to provide comprehensive insights from multiple data sources including financial documents, SEC filings, real-time stock data, and social media sentiment.

## Features

- **Multi-Agent Architecture**: Intelligent routing to specialized agents based on query content
- **Real-Time Stock Data**: Integration with Yahoo Finance for live market data
- **Document Analysis**: RAG-based analysis of financial documents using ChromaDB and HuggingFace embeddings
- **SEC Filings Processing**: Automated analysis of SEC financial reports
- **Sentiment Analysis**: Reddit sentiment analysis for mentioned companies
- **Concurrent Processing**: Async agent execution for fast response times
- **Dual Interface**: Both REST API and CLI interface
- **MCP Protocol**: Standardized communication protocol across all agents

## Architecture

### Core Components

**Router System** (`agents/crewai_router.py`)
- Analyzes queries to determine relevant agents
- Extracts company names and stock tickers
- Orchestrates concurrent agent execution
- Aggregates responses into comprehensive insights

**Specialized Agents**
- **GeneralAgent**: Handles non-financial queries
- **FinanceAgent**: Analyzes internal documents using RAG
- **YahooAgent**: Fetches real-time stock market data
- **SECAgent**: Processes SEC financial filings
- **RedditAgent**: Performs sentiment analysis on social media
- **MonitorAgent**: Tracks system health and logging

**MCP Protocol** (`mcp/schemas.py`)
- Standardized request/response format
- Context sharing between agents
- Consistent error handling

## Quick Start

### Prerequisites

- Python 3.8+
- pip
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CrewAI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
```

4. (Optional) Add financial documents:
```bash
# Place PDF files in the raw_data/ directory
cp your-financial-documents.pdf raw_data/
```

### Running the Application

**Local Development:**
```bash
python main.py
```

This starts:
- FastAPI server on `http://localhost:8000`
- Interactive CLI interface

**Using Docker:**
```bash
# Build the image
docker build -t bankerai-backend .

# Run the container
docker run -p 8000:8000 bankerai-backend
```

## Usage

### REST API

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
  "response": "Comprehensive financial analysis...",
  "agents_used": ["YahooAgent", "SECAgent", "FinanceAgent"],
  "companies": ["Apple"],
  "tickers": ["AAPL"]
}
```

### CLI Interface

When running `python main.py`, you can interact directly in the terminal:
```
Enter your query (or 'exit' to quit): What is the current stock price of Tesla?
```

### Example Queries

- "What is Apple's revenue trend?"
- "Compare Microsoft and Google stock performance"
- "What is the sentiment around TSLA on Reddit?"
- "Analyze Amazon's latest SEC filing"
- "What are the key financial metrics for NVDA?"

## Project Structure

```
CrewAI/
├── agents/                 # Agent implementations
│   ├── crewai_router.py   # Router and orchestration
│   ├── finance_agent.py   # Document analysis agent
│   ├── yahoo_agent.py     # Stock data agent
│   ├── sec_agent.py       # SEC filings agent
│   ├── reddit_agent.py    # Sentiment analysis agent
│   ├── general_agent.py   # General queries agent
│   └── monitor.py         # System monitoring
├── mcp/                   # MCP protocol schemas
│   ├── schemas.py         # Request/response models
│   └── context_store.py   # Context management
├── raw_data/              # Financial documents (PDFs)
├── vector_db/             # ChromaDB vector database
├── main.py                # FastAPI application entry point
├── dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
└── CLAUDE.md             # Development guidelines

```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for response improvement | Yes |
| `REDDIT_CLIENT_ID` | Reddit API client ID | Yes |
| `REDDIT_CLIENT_SECRET` | Reddit API client secret | Yes |

### Company/Ticker Mapping

The system automatically extracts company names and tickers from:
- Hardcoded mappings in `COMPANY_TICKER_MAP`
- PDF filenames in the `raw_data/` directory
- Natural language processing of the query

## Development

### Running Tests

```bash
pytest
```

### Adding New Agents

1. Create a new agent file in `agents/`
2. Implement the MCP protocol interface
3. Add agent to router logic in `agents/crewai_router.py`
4. Update agent selection criteria

### Document Processing

The FinanceAgent uses:
- **Embeddings**: HuggingFace "all-MiniLM-L6-v2" model
- **Vector DB**: ChromaDB for semantic search
- **Documents**: PDFs from `raw_data/` directory

The vector database is automatically built on first run.

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Monitoring and Logging

- All agent activities are logged to `monitor_logs.json`
- MonitorAgent tracks system health and performance
- Comprehensive error handling with graceful fallbacks

## Technologies Used

- **FastAPI**: Modern web framework for building APIs
- **CrewAI**: Multi-agent orchestration framework
- **LangChain**: LLM application framework
- **ChromaDB**: Vector database for embeddings
- **HuggingFace**: Embedding models and transformers
- **OpenAI GPT**: Response improvement and generation
- **PRAW**: Reddit API wrapper
- **yfinance**: Yahoo Finance API wrapper

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

**Vector database not found:**
- Ensure PDFs are in `raw_data/` directory
- The database will be built automatically on first run

**API key errors:**
- Verify `.env` file exists and contains valid API keys
- Check that environment variables are loaded correctly

**Agent timeout:**
- Some queries may take longer for comprehensive analysis
- Consider increasing timeout values for complex queries

**CORS errors:**
- CORS is enabled by default for all origins
- Adjust CORS settings in `main.py` if needed

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for similar problems
- Review the `CLAUDE.md` file for development guidelines

## Acknowledgments

- OpenAI for GPT models
- CrewAI framework
- LangChain community
- HuggingFace for embeddings
