import warnings
warnings.filterwarnings('ignore')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys
import asyncio
import time
import uvicorn
from fastapi import FastAPI, Request
from datetime import datetime
#from agents.router import RouterAgent
from agents.crewai_router import RouterCrew
from agents.finance_agent import FinanceAgent
from agents.general_agent import GeneralAgent
from agents.monitor import MonitorAgent
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import openai
import json

#from agents.router import router

app = FastAPI(
    title="BankerAI API",
    description="The APIs that accept the user's query and respond the answer.",
    version="0.0.1",
    contact={
        "name": "BankerAI",
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

# LLM tips for sub agents
AGENT_TIPS = {
    "reddit": "Reddit agent response is related to stock market topics on social media with sentiment analysis.",
    "finance": "Finance agent response is about company's info from internal financial docs.",
    "yahoo": "Yahoo agent response is about statistic data and summary based on real time stock price per company in last 30 days.",
    "sec": "SEC agent response is about public company's financial info from SEC files."
}

async def improve_agent_response(agent: str, content: str) -> str:
    """Use LLM to improve, summarize, and clean up agent output."""
    if not content:
        return ""
    tip = AGENT_TIPS.get(agent, "")
    prompt = (
        f"You are an expert assistant. Here is a response from the {agent} agent. "
        f"{tip}\n"
        f"Please improve the output format, summarize the response, and remove unrelated content. "
        f"Your summary must include key data and important content from the agent's response (not just file names), so the user gets all relevant information. "
        f"Make the summary informative and retain important details, not just a list of file names. "
        f"Include the agent name in the summary.\n\nResponse:\n{content}"
    )
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return content  # fallback
        client = openai.OpenAI(api_key=api_key)
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        # Log error but do not show to frontend
        with open("monitor_logs.json", "a") as f:
            f.write(f"LLM error for {agent}: {e}\n")
        return content

async def get_query_response(query: str) -> dict:
    from mcp.schemas import MCPRequest, MCPContext
    try:
        mcp_request = MCPRequest(context=MCPContext(user_query=query))
        mcp_response = await router_agent.route(mcp_request, None)
        #mcp_response = await run_crew(mcp_request)
        if not mcp_response or not mcp_response.data:
            return {}
        improved = {}
        for agent, result in mcp_response.data.items():
            if not result or (isinstance(result, dict) and result.get("error")):
                continue
            # Print before LLM
            print(f"[main.py] {agent} response BEFORE LLM:\n{result}")
            if agent == "general":
                # If result is a dict with a 'general' key, extract the value
                if isinstance(result, dict) and "general" in result and len(result) == 1:
                    improved_content = result["general"]
                else:
                    improved_content = result
            else:
                if isinstance(result, dict):
                    content = json.dumps(result, ensure_ascii=False)
                else:
                    content = str(result)
                improved_content = await improve_agent_response(agent, content)
            # Print after LLM
            print(f"[main.py] {agent} response AFTER LLM:\n{improved_content}")
            # Map agent key to output name
            agent_key = agent.capitalize() + "Agent" if agent != "sec" else "SecAgent"
            if agent == "reddit":
                agent_key = "RedditAgent"
            elif agent == "finance":
                agent_key = "FinanceAgent"
            elif agent == "yahoo":
                agent_key = "YahooAgent"
            elif agent == "general":
                agent_key = "GeneralAgent"
            improved[agent_key] = {"summary": improved_content}
        if not improved:
            return {}
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
    monitor = MonitorAgent()
    try:
        while True:
            query = await asyncio.to_thread(input, "Enter your question: ")
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
