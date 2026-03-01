import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex, Document, StorageContext, load_index_from_storage
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from shared_lib.schemas import MCPRequest, MCPResponse
from shared_lib.monitor import MonitorAgent

class YahooAgentEnhanced:
    def __init__(self):
        self.monitor = MonitorAgent()

        # Configure LlamaIndex settings
        Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

        # Set up directories
        self.data_dir = "./financial_data"
        self.csv_dir = os.path.join(self.data_dir, "csv")
        self.index_dir = os.path.join(self.data_dir, "yahoo_index")

        # Create directories if they don't exist
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)

        # Initialize or load vector index
        self.index = self._get_or_create_index()

    def _get_or_create_index(self) -> VectorStoreIndex:
        """Get existing index or create new one from CSV files"""
        try:
            if os.path.exists(self.index_dir) and os.listdir(self.index_dir):
                # Load existing index
                storage_context = StorageContext.from_defaults(persist_dir=self.index_dir)
                index = load_index_from_storage(storage_context)
                self.monitor.log_health("YahooAgentEnhanced", "LOADED", "Vector index loaded from storage")
                return index
            else:
                # Create empty index - will be populated as data is added
                index = VectorStoreIndex([])
                self.monitor.log_health("YahooAgentEnhanced", "CREATED", "Empty vector index created")
                return index
        except Exception as e:
            self.monitor.log_error("YahooAgentEnhanced", f"Index initialization failed: {e}")
            # Return empty index as fallback
            return VectorStoreIndex([])

    def _fetch_and_save_stock_data(self, ticker: str, period: str = "1mo") -> Dict[str, Any]:
        """Fetch stock data and save to CSV"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)

            if data.empty:
                return {"error": f"No data found for {ticker}"}

            # Get additional company info
            info = stock.info
            company_name = info.get('longName', ticker)
            sector = info.get('sector', 'Unknown')
            market_cap = info.get('marketCap', 'Unknown')

            # Prepare enhanced DataFrame with metadata
            enhanced_data = data.copy()
            enhanced_data['Ticker'] = ticker
            enhanced_data['Company_Name'] = company_name
            enhanced_data['Sector'] = sector
            enhanced_data['Market_Cap'] = market_cap
            enhanced_data['Date'] = enhanced_data.index

            # Calculate additional metrics
            enhanced_data['Daily_Return'] = enhanced_data['Close'].pct_change()
            enhanced_data['Cumulative_Return'] = (enhanced_data['Close'] / enhanced_data['Close'].iloc[0] - 1) * 100
            enhanced_data['Price_Range'] = enhanced_data['High'] - enhanced_data['Low']
            enhanced_data['Price_Change'] = enhanced_data['Close'].diff()

            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{ticker}_{period}_{timestamp}.csv"
            csv_path = os.path.join(self.csv_dir, csv_filename)
            enhanced_data.to_csv(csv_path, index=False)

            # Create document for vector index
            summary_stats = self._calculate_summary_stats(enhanced_data, ticker, company_name, period)

            # Create rich document with all the data context
            doc_content = f"""
Stock Analysis for {company_name} ({ticker})
Period: {period}
Sector: {sector}
Market Cap: {market_cap}

Summary Statistics:
{json.dumps(summary_stats, indent=2)}

Data File: {csv_filename}
Records: {len(enhanced_data)} trading days
Date Range: {enhanced_data['Date'].min()} to {enhanced_data['Date'].max()}

Key Metrics:
- Current Price: ${enhanced_data['Close'].iloc[-1]:.2f}
- Period High: ${enhanced_data['High'].max():.2f}
- Period Low: ${enhanced_data['Low'].min():.2f}
- Total Return: {((enhanced_data['Close'].iloc[-1] / enhanced_data['Close'].iloc[0]) - 1) * 100:.2f}%
- Average Daily Volume: {enhanced_data['Volume'].mean():.0f}
- Price Volatility (std): {enhanced_data['Close'].std():.2f}
"""

            # Add document to index
            document = Document(
                text=doc_content,
                metadata={
                    "ticker": ticker,
                    "company_name": company_name,
                    "sector": sector,
                    "period": period,
                    "csv_file": csv_filename,
                    "date_created": timestamp,
                    "data_type": "stock_data"
                }
            )

            # Update index with new document
            self.index.insert(document)
            self._persist_index()

            return {
                "ticker": ticker,
                "company_name": company_name,
                "sector": sector,
                "market_cap": market_cap,
                "period": period,
                "csv_file": csv_filename,
                "summary_stats": summary_stats,
                "records_count": len(enhanced_data),
                "status": "success"
            }

        except Exception as e:
            self.monitor.log_error("YahooAgentEnhanced", f"Error fetching data for {ticker}: {e}")
            return {"error": str(e)}

    def _calculate_summary_stats(self, data: pd.DataFrame, ticker: str, company_name: str, period: str) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics"""
        close_prices = data['Close']

        return {
            "ticker": ticker,
            "company_name": company_name,
            "period": period,
            "price_stats": {
                "current_price": float(close_prices.iloc[-1]),
                "min_price": float(close_prices.min()),
                "max_price": float(close_prices.max()),
                "mean_price": float(close_prices.mean()),
                "median_price": float(close_prices.median()),
                "std_dev": float(close_prices.std())
            },
            "returns": {
                "total_return_pct": float(((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100),
                "daily_return_mean": float(data['Daily_Return'].mean() * 100),
                "daily_return_std": float(data['Daily_Return'].std() * 100),
                "best_day": float(data['Daily_Return'].max() * 100),
                "worst_day": float(data['Daily_Return'].min() * 100)
            },
            "volume_stats": {
                "avg_volume": float(data['Volume'].mean()),
                "max_volume": float(data['Volume'].max()),
                "min_volume": float(data['Volume'].min())
            },
            "trading_stats": {
                "trading_days": len(data),
                "avg_daily_range": float(data['Price_Range'].mean()),
                "max_daily_range": float(data['Price_Range'].max())
            }
        }

    def _persist_index(self):
        """Save the index to disk"""
        try:
            self.index.storage_context.persist(persist_dir=self.index_dir)
        except Exception as e:
            self.monitor.log_error("YahooAgentEnhanced", f"Error persisting index: {e}")

    def _query_financial_data(self, query: str, ticker_filter: str = None) -> str:
        """Query the financial data using natural language"""
        try:
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize"
            )

            # Enhance query with context
            enhanced_query = f"""
            Based on the available financial data, please answer the following question:
            {query}

            Please provide specific numbers, trends, and insights where possible.
            If comparing multiple stocks, highlight key differences.
            Focus on actionable investment insights.
            """

            if ticker_filter:
                enhanced_query += f"\nFocus specifically on data for {ticker_filter}."

            response = query_engine.query(enhanced_query)
            return str(response)

        except Exception as e:
            self.monitor.log_error("YahooAgentEnhanced", f"Error querying data: {e}")
            return f"Error analyzing data: {e}"

    def run(self, request: MCPRequest) -> MCPResponse:
        """Process financial data request with enhanced capabilities"""
        start_time = datetime.now()
        companies = request.context.companies or []
        tickers = request.context.tickers or []
        user_query = request.context.user_query
        response_data = []
        status = "processing"

        try:
            # If we have tickers, fetch fresh data
            if tickers:
                for ticker in tickers:
                    print(f"[YahooAgentEnhanced] Fetching data for {ticker}")
                    stock_data = self._fetch_and_save_stock_data(ticker, period="3mo")  # Get 3 months of data
                    response_data.append(stock_data)

            # Perform natural language analysis on the query
            if user_query:
                print(f"[YahooAgentEnhanced] Analyzing query: {user_query}")

                # Determine the focus ticker if any
                focus_ticker = tickers[0] if tickers else None

                # Query the indexed financial data
                analysis_response = self._query_financial_data(user_query, focus_ticker)

                analysis_data = {
                    "query": user_query,
                    "focus_ticker": focus_ticker,
                    "analysis": analysis_response,
                    "data_sources": [item.get("csv_file", "unknown") for item in response_data if "csv_file" in item]
                }

                if tickers:
                    response_data.append(analysis_data)
                else:
                    response_data = [analysis_data]

            status = "success"
            self.monitor.log_health("YahooAgentEnhanced", "SUCCESS", f"Processed data for {len(tickers)} tickers")

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            response_data = {"error": error_msg}
            self.monitor.log_error("YahooAgentEnhanced", error_msg, {"tickers": tickers, "query": user_query})

        completed_time = datetime.now()

        return MCPResponse(
            request_id=request.request_id,
            data={"yahoo_enhanced": response_data},
            context_updates={"last_yahoo_analysis": completed_time.isoformat()},
            status=status,
            timestamp=completed_time
        )

    def get_available_data(self) -> List[Dict[str, Any]]:
        """Get information about available CSV data files"""
        try:
            files_info = []
            for filename in os.listdir(self.csv_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.csv_dir, filename)
                    stat = os.stat(filepath)
                    files_info.append({
                        "filename": filename,
                        "size_bytes": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            return files_info
        except Exception as e:
            self.monitor.log_error("YahooAgentEnhanced", f"Error listing data files: {e}")
            return []

    def query_historical_data(self, query: str) -> str:
        """Public method to query historical data"""
        return self._query_financial_data(query)