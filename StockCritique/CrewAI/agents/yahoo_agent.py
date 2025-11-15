import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
from agents.monitor import MonitorAgent
import time
import warnings
from mcp.schemas import MCPRequest, MCPResponse
import os
import openai
warnings.filterwarnings('ignore')


class YahooAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.client = openai.OpenAI(api_key=self.api_key)

    def run(self, request: MCPRequest) -> MCPResponse:
        start_time = datetime.now()
        tickers = request.context.tickers
        end_date = datetime.now().date()
        response_data = []
        status = "processing"
        try:
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                data = stock.history(period="1mo")
                if data.empty:
                    stats = {"error": f"No data found for {ticker} in the last 30 days."}
                    summary = "No data available."
                else:
                    close_prices = data['Close']
                    min_price = float(close_prices.min())
                    max_price = float(close_prices.max())
                    mean_price = float(close_prices.mean())
                    last_close = float(close_prices.iloc[-1])
                    std_dev = float(close_prices.std())
                    pct_change = float(((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100) if close_prices.iloc[0] != 0 else 0
                    volatility = float(close_prices.pct_change().std() * (252 ** 0.5) * 100)
                    stats = {
                        "min_close": min_price,
                        "max_close": max_price,
                        "mean_close": mean_price,
                        "std_dev_30d": std_dev,
                        "percent_change_30d": pct_change,
                        "volatility_annualized": volatility,
                        "last_close": last_close
                    }
                    # Data analysis summary via OpenAI
                    try:
                        prompt = (
                            f"Analyze the following 30-day stock price statistics for {ticker}:\n"
                            f"Min Close: ${min_price:.2f}\n"
                            f"Max Close: ${max_price:.2f}\n"
                            f"Mean Close: ${mean_price:.2f}\n"
                            f"Std Dev (30d): ${std_dev:.2f}\n"
                            f"Percent Change (30d): {pct_change:.2f}%\n"
                            f"Volatility (annualized): {volatility:.2f}%\n"
                            f"Last Close: ${last_close:.2f}\n"
                            f"Provide a brief professional summary and any notable trends."
                        )
                        response = self.client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        summary = response.choices[0].message.content
                    except Exception as e:
                        summary = f"OpenAI summary error: {e}"
                response_data.append({
                    "ticker": ticker,
                    "statistics": stats,
                    "analysis_summary": summary
                })
            status = "success"
        except Exception as e:
            status = "failed"
            response_data = {"error": str(e)}
        completed_time = datetime.now()
        log_message = {
            "agent": "YahooAgent",
            "started_timestamp": start_time.isoformat(),
            "response": response_data,
            "completed_timestamp": completed_time.isoformat(),
            "status": status
        }
        try:
            with open("monitor_logs.json", "a") as f:
                f.write(json.dumps(log_message) + "\n")
        except Exception as e:
            print(f"[YahooAgent] Logging error: {e}")
        return MCPResponse(
            request_id=request.request_id,
            data={"yahoo": response_data},
            context_updates=None,
            status=status
        )

    def get_llm_prompt(self, tickers_data):
        return (
            "You are a stock market analyst. Given the following 30-day stock statistics for each ticker, summarize the key statistics, highlight notable trends, and provide a user-friendly summary for each ticker.\n\n" +
            f"Data: {json.dumps(tickers_data, ensure_ascii=False)}"
        )

