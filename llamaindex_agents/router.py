import os
import re
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from schemas import MCPRequest, MCPResponse, MCPContext
from monitor import MonitorAgent

FINANCIAL_KEYWORDS = [
    "stock", "stocks", "share", "shares", "price", "prices",
    "earnings", "revenue", "profit", "loss", "income",
    "invest", "investment", "investor", "investing",
    "dividend", "dividends", "yield",
    "market", "markets", "trading", "trade", "trader",
    "buy", "sell", "hold", "bullish", "bearish", "bull", "bear",
    "portfolio", "asset", "assets", "liability", "liabilities",
    "sec", "filing", "filings", "10-k", "10-q", "10k", "10q",
    "quarterly", "annual", "fiscal", "financial", "finance",
    "balance sheet", "income statement", "cash flow",
    "p/e", "ratio", "eps", "ebitda", "roi", "roe",
    "analyst", "forecast", "valuation", "capitalization",
    "ipo", "merger", "acquisition", "bond", "bonds",
    "equity", "debt", "loan", "bank", "banking",
    "nasdaq", "nyse", "s&p", "dow", "etf", "fund",
    "hedge", "mutual", "index",
    "volatility", "volume", "momentum",
    "ticker", "symbol", "chart",
    "report", "quarter", "guidance", "outlook",
    "sentiment", "wall street",
]

class LlamaIndexRouter:
    def __init__(self):
        self.monitor = MonitorAgent()

        # Company to ticker mapping
        self.company_ticker_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "netflix": "NFLX",
            "intel": "INTC",
            "ibm": "IBM",
        }

    def extract_companies(self, query: str) -> List[str]:
        """Extract company names from query"""
        companies = set()
        if not query:
            return []

        query_lower = query.lower()

        # Check against known companies
        for company_name in self.company_ticker_map.keys():
            try:
                if re.search(rf'\b{re.escape(company_name)}\b', query_lower):
                    companies.add(company_name)
            except re.error:
                if company_name in query_lower:
                    companies.add(company_name)

        # Also check for ticker symbols directly (e.g. "MSFT", "AAPL")
        ticker_to_company = {}
        for comp, tick in self.company_ticker_map.items():
            ticker_to_company.setdefault(tick.lower(), comp)
        for ticker_lower, comp in ticker_to_company.items():
            try:
                if re.search(rf'\b{re.escape(ticker_lower)}\b', query_lower):
                    companies.add(comp)
            except re.error:
                if ticker_lower in query_lower:
                    companies.add(comp)

        # Check against raw data directory files
        raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data")
        if os.path.exists(raw_data_dir):
            try:
                for fname in os.listdir(raw_data_dir):
                    if fname.lower().endswith((".pdf", ".htm", ".html")):
                        base = os.path.splitext(fname)[0]
                        company = base.split("-")[0] if "-" in base else base
                        company_lower = company.lower()
                        try:
                            if re.search(rf'\b{re.escape(company_lower)}\b', query_lower):
                                companies.add(company_lower)
                        except re.error:
                            if company_lower in query_lower:
                                companies.add(company_lower)
            except Exception as e:
                self.monitor.log_error("LlamaIndexRouter", f"Error extracting companies: {e}")

        return list(companies)

    def map_to_tickers(self, companies: List[str]) -> List[str]:
        """Map company names to stock tickers"""
        if not companies:
            return []

        tickers = []
        for company in companies:
            ticker = self.company_ticker_map.get(company.lower())
            if ticker:
                tickers.append(ticker)

        return list(set(tickers))

    def is_financial_query(self, query: str, companies: List[str], tickers: List[str]) -> bool:
        """Smart two-step check to determine if query is financial."""
        query_lower = query.lower().strip()

        if companies or tickers:
            remaining = query_lower
            for company in companies:
                remaining = re.sub(rf'\b{re.escape(company)}\b', '', remaining).strip()
            for ticker in tickers:
                remaining = re.sub(rf'\b{re.escape(ticker.lower())}\b', '', remaining).strip()

            if not remaining or len(remaining.strip()) <= 2:
                return True

            for keyword in FINANCIAL_KEYWORDS:
                if keyword in remaining:
                    return True

            return False

        for keyword in FINANCIAL_KEYWORDS:
            if keyword in query_lower:
                return True

        return False

    def determine_agents(self, user_query: str, companies: List[str], tickers: List[str]) -> List[str]:
        """Determine which agents to run based on smart query classification."""
        try:
            is_finance = self.is_financial_query(user_query, companies, tickers)
            if is_finance:
                if tickers:
                    return ["FinanceAgent", "YahooAgent", "SECAgent", "RedditAgent"]
                else:
                    return ["FinanceAgent", "RedditAgent"]
            else:
                return ["GeneralAgent"]
        except Exception as e:
            self.monitor.log_error("LlamaIndexRouter", f"Error determining agents: {e}")
            return ["FinanceAgent", "RedditAgent"]

    async def run_agent(self, agent_name: str, mcp_request: MCPRequest) -> Optional[Any]:
        """Run a specific agent with error handling"""
        try:
            # Dynamic import to avoid circular dependencies
            if agent_name == "FinanceAgent":
                from finance_agent import FinanceAgent
                agent = FinanceAgent()
                return agent.run(mcp_request)

            elif agent_name == "YahooAgent":
                from yahoo_agent import YahooAgent
                agent = YahooAgent()
                return agent.run(mcp_request)

            elif agent_name == "SECAgent":
                from sec_agent import SECAgent
                agent = SECAgent()
                return agent.run(mcp_request)

            elif agent_name == "RedditAgent":
                from reddit_agent import RedditAgent
                agent = RedditAgent()
                return agent.run(mcp_request)

            elif agent_name == "GeneralAgent":
                from general_agent import GeneralAgent
                agent = GeneralAgent()
                return agent.run(mcp_request)

            else:
                self.monitor.log_error("LlamaIndexRouter", f"Unknown agent: {agent_name}")
                return {"error": f"Agent {agent_name} not found"}

        except ImportError as e:
            error_msg = f"Import error for {agent_name}: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)
            return {"error": error_msg}

        except Exception as e:
            error_msg = f"Error running {agent_name}: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)
            return {"error": error_msg}

    async def route(self, mcp_request: MCPRequest) -> MCPResponse:
        """Main routing logic for processing requests"""
        start_time = datetime.now()
        user_query = mcp_request.context.user_query if mcp_request.context else ""

        try:
            # Extract companies and tickers
            companies = self.extract_companies(user_query)
            tickers = self.map_to_tickers(companies)

            # Determine which agents to run
            agent_names = self.determine_agents(user_query, companies, tickers)

            # Update context
            updated_context = MCPContext(
                user_query=user_query,
                companies=companies,
                tickers=tickers,
                extracted_terms={"agent_names": agent_names},
                version=getattr(mcp_request.context, "version", "1.0")
            )

            updated_request = MCPRequest(
                request_id=mcp_request.request_id,
                context=updated_context
            )

            # Log routing decision
            routing_log = {
                "router": "LlamaIndexRouter",
                "timestamp": start_time.isoformat(),
                "query": user_query,
                "companies": companies,
                "tickers": tickers,
                "agents": agent_names,
                "status": "routing"
            }

            # Run agents concurrently
            tasks = []
            for agent_name in agent_names:
                task = self.run_agent(agent_name, updated_request)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            responses = {}
            context_updates = {}
            overall_status = "success"

            for agent_name, result in zip(agent_names, results):
                agent_key = agent_name.lower().replace("agent", "")

                if isinstance(result, Exception):
                    responses[agent_key] = {"error": str(result)}
                    overall_status = "partial_failure"
                elif result is None:
                    responses[agent_key] = {"error": "Agent returned no response"}
                    overall_status = "partial_failure"
                else:
                    # Handle MCPResponse objects
                    if hasattr(result, 'data'):
                        responses.update(result.data)
                        if hasattr(result, 'context_updates') and result.context_updates:
                            context_updates.update(result.context_updates)
                    elif isinstance(result, dict):
                        responses[agent_key] = result
                    else:
                        responses[agent_key] = {"response": str(result)}

            completed_time = datetime.now()

            # Update routing log
            routing_log.update({
                "completed_timestamp": completed_time.isoformat(),
                "status": overall_status,
                "agents_completed": len(responses)
            })

            # Log results
            try:
                with open("monitor_logs.json", "a") as f:
                    f.write(json.dumps(routing_log) + "\n")
            except Exception as e:
                self.monitor.log_error("LlamaIndexRouter", f"Logging error: {e}")

            return MCPResponse(
                request_id=mcp_request.request_id,
                data=responses,
                context_updates=context_updates,
                status=overall_status,
                timestamp=completed_time
            )

        except Exception as e:
            error_msg = f"Routing failed: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)

            return MCPResponse(
                request_id=mcp_request.request_id,
                data={"error": error_msg},
                context_updates={},
                status="failed",
                timestamp=datetime.now()
            )