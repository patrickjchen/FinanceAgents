import warnings
warnings.filterwarnings('ignore')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", ".."))  # project root
sys.path.insert(0, _SCRIPT_DIR)  # src/ for local imports
import asyncio
import time
import uvicorn
from fastapi import FastAPI
from datetime import datetime
from agents.ag2_router import RouterAG2
from shared_lib.monitor import MonitorAgent
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import json

from shared_lib.llm_helpers import improve_agent_response, generate_comprehensive_summary

app = FastAPI(
    title="FinanceAgents API - AG2 Implementation",
    description="AI-powered financial analysis using AG2 (formerly AutoGen) multi-agent framework.",
    version="0.1.0",
    contact={
        "name": "FinanceAgents",
        "url": "https://localhost:8002",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router_agent = RouterAG2()


class MessageRequest(BaseModel):
    query: str


async def get_query_response(query: str) -> dict:
    from shared_lib.schemas import MCPRequest, MCPContext
    try:
        mcp_request = MCPRequest(context=MCPContext(user_query=query))
        mcp_response = await router_agent.route(mcp_request, None)
        if not mcp_response or not mcp_response.data:
            return {}
        improved = {}
        has_general = False
        for agent, result in mcp_response.data.items():
            if not result or (isinstance(result, dict) and result.get("error")):
                continue
            print(f"[main.py] {agent} response BEFORE LLM:\n{result}")
            if agent == "general":
                has_general = True
                if isinstance(result, dict) and "general" in result and len(result) == 1:
                    improved_content = result["general"]
                elif isinstance(result, dict) and "response" in result:
                    improved_content = result["response"]
                else:
                    improved_content = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                improved["GeneralAgent"] = {"summary": improved_content}
            else:
                if isinstance(result, dict):
                    content = json.dumps(result, ensure_ascii=False)
                else:
                    content = str(result)
                improved_content = await improve_agent_response(agent, content)
                print(f"[main.py] {agent} response AFTER LLM:\n{improved_content}")
                agent_key_map = {
                    "reddit": "RedditAgent",
                    "finance": "FinanceAgent",
                    "yahoo": "YahooAgent",
                    "sec": "SecAgent",
                }
                agent_key = agent_key_map.get(agent, agent.capitalize() + "Agent")
                improved[agent_key] = {"summary": improved_content}
        if not improved:
            return {}

        if not has_general:
            print(f"\n{'='*60}")
            print(f"Generating comprehensive summary...")
            print(f"{'='*60}")
            summary = await generate_comprehensive_summary(query, improved)
            improved["FinalSummary"] = {"summary": summary}
            print(f"\n{'='*60}")
            print(f"FINAL SUMMARY")
            print(f"{'='*60}")
            print(summary)
            print(f"{'='*60}\n")

        return improved
    except Exception as e:
        timestamp = datetime.now().isoformat()
        with open("monitor_logs.json", "a") as f:
            f.write(f"[{timestamp}] Exception in get_query_response: {e}\n")
        return {}


async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=8002, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        cli_query_loop(),
    )


async def cli_query_loop():
    from shared_lib.constants import COMPANY_TICKER_MAP
    monitor = MonitorAgent()
    await asyncio.sleep(2)
    tickers = sorted(set(COMPANY_TICKER_MAP.values()))
    companies = ", ".join(tickers)
    sep = "=" * 60
    banner = f"""
{sep}
  FinanceAgents CLI (AG2)
{sep}
Supported tickers for financial queries:
  {companies}

Other queries will be handled by the GeneralAgent.
Type 'exit' or 'quit' to stop.
"""
    try:
        while True:
            print(banner)
            query = await asyncio.to_thread(input, "Enter your question: ")
            if query.strip().lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            timestamp = datetime.now().isoformat()
            print(f"[{timestamp}] Sending query to RouterAG2..." + query)
            await get_query_response(query)
            time.sleep(0.5)
    except Exception as e:
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] Exception occurred: {e}")
        monitor.log_health("Main", "EXCEPTION", f"Timestamp: {timestamp}, Error: {e}")


@app.post("/query")
async def chat_endpoint(request: MessageRequest):
    response_data = await get_query_response(request.query)
    return {"response": response_data}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "implementation": "AG2",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/agents")
async def list_agents():
    return {
        "available_agents": [
            "FinanceAgent - Internal document analysis using RAG",
            "YahooAgent - Real-time stock data",
            "SECAgent - SEC filing analysis",
            "RedditAgent - Async social media sentiment analysis",
            "GeneralAgent - General queries and system information",
        ],
        "framework": "AG2 (formerly AutoGen)",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    asyncio.run(main())
