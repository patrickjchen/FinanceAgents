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
from fastapi import FastAPI, Request
from datetime import datetime
#from agents.router import RouterAgent
from agents.crewai_router import RouterCrew
from shared_lib.agents.finance_agent import FinanceAgent
from shared_lib.monitor import MonitorAgent
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import json

from shared_lib.llm_helpers import AGENT_TIPS, improve_agent_response, generate_comprehensive_summary

#from agents.router import router

app = FastAPI(
    title="FinanceAgents API",
    description="The APIs that accept the user's query and respond the answer.",
    version="0.0.1",
    contact={
        "name": "FinanceAgents",
        "url": "https://localhost:8001",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，或指定特定的来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

#router_agent = RouterAgent()
router_agent = RouterCrew()

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
                # GeneralAgent: extract response directly, skip LLM improvement
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

        # Only generate comprehensive summary for financial queries (not GeneralAgent)
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
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)

    # Run both CLI and FastAPI
    await asyncio.gather(
        server.serve(),       # HTTP server
        cli_query_loop()      # CLI loop
    )

async def cli_query_loop():
    from shared_lib.constants import COMPANY_TICKER_MAP
    monitor = MonitorAgent()
    # Wait for uvicorn startup logs to finish before showing the prompt
    await asyncio.sleep(2)
    tickers = sorted(set(COMPANY_TICKER_MAP.values()))
    companies = ", ".join(tickers)
    print("\n" + "=" * 60)
    print("  FinanceAgents CLI (CrewAI)")
    print("=" * 60)
    print("Supported tickers for financial queries:")
    print(f"  {companies}")
    print("\nOther queries will be handled by the GeneralAgent.")
    print("Type 'exit' or 'quit' to stop.\n")
    try:
        while True:
            query = await asyncio.to_thread(input, "Enter your question: ")
            if query.strip().lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            timestamp = datetime.now().isoformat()
            print(f"[{timestamp}] Sending query to RouterAgent..." + query)
            # start querying and await response
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

if __name__ == "__main__":
    asyncio.run(main())
