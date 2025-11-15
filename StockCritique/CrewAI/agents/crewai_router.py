import warnings
warnings.filterwarnings('ignore')
from datetime import datetime
import os
import traceback
import json
from fastapi import APIRouter, BackgroundTasks
from mcp.schemas import MCPRequest, MCPResponse, MCPContext
from typing import List, Dict, Any, Optional
import asyncio
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Example mapping of company names to tickers
COMPANY_TICKER_MAP = {
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

class RouterCrew:
    def __init__(self):
        self.finance_keywords = [
            "stock", "stocks", "loan", "loans", "invest", "investment", "finance", 
            "bank", "banks", "banking", "dividend", "equity", "bond", "bonds",
            "portfolio", "asset", "assets", "liability", "liabilities", 
            "balance sheet", "income statement", "cash flow", "financial report",
            "earnings", "revenue", "profit", "loss", "market cap", "valuation",
            "merger", "acquisition", "IPO", "interest rate", "inflation",
            "recession", "bull market", "bear market", "trading", "exchange",
            "securities", "broker", "dividend yield", "P/E ratio", "EPS"
        ]
        raw_data_dir = "./backend/raw_data"
        if os.path.exists(raw_data_dir):
            try:
                file_topics = [os.path.splitext(f)[0].replace("-", " ").replace("_", " ") 
                              for f in os.listdir(raw_data_dir) if f.lower().endswith(".pdf")]
                self.finance_keywords.extend(file_topics)
            except Exception as e:
                logger.error(f"Error loading finance keywords: {e}")

    def extract_companies(self, query: str) -> List[str]:
        companies = set()
        if not query:
            return []
            
        query_lower = query.lower()
        
        # Check against known companies
        for name in list(COMPANY_TICKER_MAP.keys()):
            try:
                if re.search(rf'\b{re.escape(name)}\b', query_lower):
                    companies.add(name)
            except re.error:
                if name in query_lower:
                    companies.add(name)
        
        # Check raw data directory
        raw_data_dir = "./backend/raw_data"
        if os.path.exists(raw_data_dir):
            try:
                for fname in os.listdir(raw_data_dir):
                    if fname.lower().endswith(".pdf"):
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
                logger.error(f"Error extracting companies from files: {e}")
        return list(companies)

    def map_to_tickers(self, companies: List[str]) -> List[str]:
        if not companies:
            return []
            
        tickers = []
        for name in companies:
            try:
                ticker = COMPANY_TICKER_MAP.get(name.lower())
                if ticker:
                    tickers.append(ticker)
            except Exception:
                continue
        return list(set(tickers))

    def is_finance_query(self, query: str) -> bool:
        if not query or not isinstance(query, str):
            return False
            
        query_lower = query.lower()
        # Check for finance keywords
        for keyword in self.finance_keywords:
            try:
                if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                    return True
            except re.error:
                if keyword in query_lower:
                    return True
        
        # Check for ticker patterns (e.g., AAPL, MSFT)
        try:
            if re.search(r'\b[A-Z]{2,5}\b', query):
                return True
        except re.error:
            pass
            
        return False

    def determine_agents(self, user_query: str, tickers: List[str]) -> List[str]:
        """Safely determine which agents to run"""
        try:
            is_finance = self.is_finance_query(user_query)
            
            if not is_finance:
                return ["GeneralAgent"]
            elif is_finance and tickers:
                return ["RedditAgent", "FinanceAgent", "YahooAgent", "SECAgent", "GeneralAgent"]
            else:  # is_finance and not tickers
                return ["RedditAgent", "FinanceAgent", "GeneralAgent"]
        except Exception as e:
            logger.error(f"Error determining agents: {e}")
            return ["GeneralAgent"]  # Fallback to general agent

    async def run_agent(self, agent_name: str, mcp_request: MCPRequest, bg: BackgroundTasks) -> Optional[Any]:
        """Run an agent with comprehensive error handling"""
        try:
            # Dynamically import agent to isolate dependencies
            if agent_name == "GeneralAgent":
                from agents.general_agent import GeneralAgent
                agent_class = GeneralAgent
            elif agent_name == "FinanceAgent":
                from agents.finance_agent import FinanceAgent
                agent_class = FinanceAgent
            elif agent_name == "YahooAgent":
                from agents.yahoo_agent import YahooAgent
                agent_class = YahooAgent
            elif agent_name == "SECAgent":
                from agents.sec_agent import SECAgent
                agent_class = SECAgent
            elif agent_name == "RedditAgent":
                from agents.reddit_agent import RedditAgent
                agent_class = RedditAgent
            else:
                logger.error(f"Agent {agent_name} not supported")
                return None
                
            agent_instance = agent_class()
            
            if agent_name == "RedditAgent":
                return await agent_instance.run(mcp_request, bg)
            else:
                # Run synchronous agents in thread pool
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, agent_instance.run, mcp_request)
        except ImportError as e:
            logger.error(f"Import error for {agent_name}: {e}")
            return {"error": f"Agent dependencies missing: {e}"}
        except Exception as e:
            logger.error(f"Error running agent {agent_name}: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    async def route(self, mcp_request: MCPRequest, bg: BackgroundTasks) -> MCPResponse:
        start_time = datetime.now()
        user_query = mcp_request.context.user_query if mcp_request.context else ""
        
        # Safely extract companies and tickers
        try:
            companies = self.extract_companies(user_query) or []
            tickers = self.map_to_tickers(companies) or []
        except Exception as e:
            logger.error(f"Error extracting companies/tickers: {e}")
            companies = []
            tickers = []
        
        # Safely determine agents
        try:
            agent_names = self.determine_agents(user_query, tickers) or ["GeneralAgent"]
        except Exception as e:
            logger.error(f"Error determining agents: {e}")
            agent_names = ["GeneralAgent"]
        
        log_message = {
            "router": "RouterCrew",
            "started_timestamp": start_time.isoformat(),
            "companies": companies,
            "tickers": tickers,
            "sub_agents": agent_names,
            "status": "processing"
        }
        
        responses = {}
        context_updates = {}
        status = "success"
        
        try:
            # Create context safely
            context = MCPContext(
                user_query=user_query,
                companies=companies,
                tickers=tickers,
                extracted_terms={},
                version=getattr(mcp_request.context, "version", "1.0")
            )
            updated_request = MCPRequest(
                request_id=mcp_request.request_id,
                context=context
            )
            
            # Run agents concurrently
            tasks = []
            for agent_name in agent_names:
                tasks.append(self.run_agent(agent_name, updated_request, bg))
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results with comprehensive checks
            for agent_name, result in zip(agent_names, results):
                key_name = agent_name.lower().replace("agent", "")
                
                # Handle exceptions and errors
                if isinstance(result, Exception):
                    responses[key_name] = {"error": str(result)}
                    status = "partial_failure"
                elif result is None:
                    responses[key_name] = {"error": "Agent returned no response"}
                    status = "partial_failure"
                else:
                    # Handle different agent response formats
                    if hasattr(result, 'data'):
                        responses[key_name] = result.data
                        if hasattr(result, 'context_updates'):
                            try:
                                if result.context_updates:
                                    context_updates.update(result.context_updates)
                            except Exception as e:
                                logger.error(f"Error updating context: {e}")
                    elif isinstance(result, dict):
                        responses[key_name] = result
                    else:
                        responses[key_name] = {"response": str(result)}
        except Exception as e:
            status = "failed"
            responses["error"] = str(e)
            logger.error(f"Routing error: {e}")
            logger.error(traceback.format_exc())
            
        completed_time = datetime.now()
        log_message.update({
            "completed_timestamp": completed_time.isoformat(),
            "status": status
        })
        
        # Safely log results
        try:
            with open("monitor_logs.json", "a") as f:
                f.write(json.dumps(log_message) + "\n")
        except Exception as e:
            logger.error(f"[RouterCrew] Logging error: {e}")
            
        logger.info(json.dumps(log_message, indent=2))
        
        # Return response with fallbacks
        return MCPResponse(
            request_id=mcp_request.request_id or "unknown",
            data=responses or {"error": "No agents responded"},
            context_updates=context_updates or {},
            status=status,
            timestamp=completed_time
        )

@router.post("/query", response_model=MCPResponse)
async def handle_query(request: MCPRequest, bg: BackgroundTasks):
    router_crew = RouterCrew()
    return await router_crew.route(request, bg)
