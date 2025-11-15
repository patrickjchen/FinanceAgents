import warnings
warnings.filterwarnings('ignore')
from agents.monitor import MonitorAgent
from datetime import datetime
import os
import traceback
import json
from sentence_transformers import SentenceTransformer, util
from fastapi import APIRouter, BackgroundTasks
from mcp.schemas import MCPRequest, MCPResponse, MCPContext
from agents.general_agent import GeneralAgent
from agents.finance_agent import FinanceAgent
from agents.yahoo_agent import YahooAgent
from agents.sec_agent import SECAgent
from agents.reddit_agent import RedditAgent
import asyncio

router = APIRouter()

# Example mapping of company names to tickers (expand as needed)
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
    # Add more as needed
}

class RouterAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.finance_topics = [
            "stock", "loan", "investment", "finance", "bank", "dividend", "equity", "bond", "portfolio", "asset", "liability", "balance sheet", "income statement", "cash flow", "financial report"
        ]
        raw_data_dir = "./backend/raw_data"
        if os.path.exists(raw_data_dir):
            file_topics = [os.path.splitext(f)[0].replace("-", " ").replace("_", " ") for f in os.listdir(raw_data_dir) if f.lower().endswith(".pdf")]
            self.finance_topics += file_topics
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.threshold = 0.4

    def extract_companies(self, query: str):
        companies = set()
        query_lower = query.lower()
        for name in COMPANY_TICKER_MAP.keys():
            if name in query_lower:
                companies.add(name)
        raw_data_dir = "./backend/raw_data"
        if os.path.exists(raw_data_dir):
            for fname in os.listdir(raw_data_dir):
                if fname.lower().endswith(".pdf"):
                    base = os.path.splitext(fname)[0]
                    company = base.split("-")[0] if "-" in base else base
                    if company.lower() in query_lower:
                        companies.add(company.lower())
        return list(companies)

    def map_to_tickers(self, companies):
        tickers = []
        for name in companies:
            ticker = COMPANY_TICKER_MAP.get(name.lower())
            if ticker:
                tickers.append(ticker)
        return list(set(tickers))

    def is_finance_query(self, query: str):
        query_emb = self.embedder.encode(query, convert_to_tensor=True)
        topic_embs = self.embedder.encode(self.finance_topics, convert_to_tensor=True)
        sims = util.pytorch_cos_sim(query_emb, topic_embs)[0]
        max_sim = float(sims.max())
        return max_sim > self.threshold, max_sim

    async def route(self, mcp_request: MCPRequest, bg: BackgroundTasks) -> MCPResponse:
        start_time = datetime.now()
        user_query = mcp_request.context.user_query
        companies = self.extract_companies(user_query)
        tickers = self.map_to_tickers(companies)
        is_finance, sim_score = self.is_finance_query(user_query)
        sub_agents = []
        status = "processing"
        responses = {}
        context_updates = {}
        log_message = {
            "router": "RouterAgent",
            "started_timestamp": start_time.isoformat(),
            "companies": companies,
            "tickers": tickers,
            "sub_agents": [],
            "status": "processing"
        }
        try:
            context = MCPContext(
                user_query=user_query,
                companies=companies,
                tickers=tickers,
                extracted_terms={},
                version=mcp_request.context.version
            )
            loop = asyncio.get_event_loop()
            tasks = []
            agent_names = []
            # Always use the updated context for all agents
            if not is_finance:
                gen_agent = GeneralAgent()
                gen_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, gen_agent.run, gen_req))
                agent_names.append("GeneralAgent")
            elif is_finance and tickers:
                reddit_agent = RedditAgent()
                reddit_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(reddit_agent.run(reddit_req, bg))
                agent_names.append("RedditAgent")
                finance_agent = FinanceAgent()
                finance_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, finance_agent.run, finance_req))
                agent_names.append("FinanceAgent")
                yahoo_agent = YahooAgent()
                yahoo_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, yahoo_agent.run, yahoo_req))
                agent_names.append("YahooAgent")
                sec_agent = SECAgent()
                sec_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, sec_agent.run, sec_req))
                agent_names.append("SECAgent")
                gen_agent = GeneralAgent()
                gen_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, gen_agent.run, gen_req))
                agent_names.append("GeneralAgent")
            elif is_finance and not tickers and companies:
                reddit_agent = RedditAgent()
                reddit_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(reddit_agent.run(reddit_req, bg))
                agent_names.append("RedditAgent")
                finance_agent = FinanceAgent()
                finance_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, finance_agent.run, finance_req))
                agent_names.append("FinanceAgent")
                gen_agent = GeneralAgent()
                gen_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, gen_agent.run, gen_req))
                agent_names.append("GeneralAgent")
            elif is_finance and not companies:
                reddit_agent = RedditAgent()
                reddit_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(reddit_agent.run(reddit_req, bg))
                agent_names.append("RedditAgent")
                gen_agent = GeneralAgent()
                gen_req = MCPRequest(request_id=mcp_request.request_id, context=context)
                tasks.append(loop.run_in_executor(None, gen_agent.run, gen_req))
                agent_names.append("GeneralAgent")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for name, result in zip(agent_names, results):
                if isinstance(result, Exception):
                    responses[name.lower()] = {"error": str(result)}
                    status = "failed"
                elif name == "RedditAgent" and hasattr(result, 'data'):
                    responses["reddit"] = result.data
                    if getattr(result, 'context_updates', None):
                        context_updates.update(result.context_updates)
                elif name == "FinanceAgent":
                    responses["finance"] = result.data if hasattr(result, 'data') else result
                elif name == "YahooAgent":
                    responses["yahoo"] = result.data if hasattr(result, 'data') else result
                elif name == "SECAgent":
                    responses["sec"] = result.data if hasattr(result, 'data') else result
                elif name == "GeneralAgent":
                    responses["general"] = result.data if hasattr(result, 'data') else result
                sub_agents.append(name)
            status = "success" if status != "failed" else status
        except Exception as e:
            status = "failed"
            responses["error"] = str(e)
            traceback.print_exc()
        completed_time = datetime.now()
        log_message.update({
            "completed_timestamp": completed_time.isoformat(),
            "sub_agents": sub_agents,
            "status": status
        })
        try:
            with open("monitor_logs.json", "a") as f:
                f.write(json.dumps(log_message) + "\n")
        except Exception as e:
            print(f"[RouterAgent] Logging error: {e}")
        print(json.dumps(log_message, indent=2))
        return MCPResponse(
            request_id=mcp_request.request_id,
            data=responses,
            context_updates=context_updates,
            status=status,
            timestamp=completed_time
        )

@router.post("/query", response_model=MCPResponse)
async def handle_query(request: MCPRequest, bg: BackgroundTasks):
    router_agent = RouterAgent()
    return await router_agent.route(request, bg)