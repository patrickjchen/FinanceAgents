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
from agents.router import RouterAgent
from agents.finance_agent import FinanceAgent
from agents.monitor import MonitorAgent
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
import json

from agents.router import router

app = FastAPI(
    title="FinanceAgents API",
    description="The APIs that accept the user's query and respond the answer.",
    version="0.0.1",
    contact={
        "name": "FinanceAgents",
        "url": "https://localhost:8000",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，或指定特定的来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

router_agent = RouterAgent()

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

async def generate_comprehensive_summary(user_query: str, agent_results: dict) -> str:
    """Generate a comprehensive summary combining all agent outputs."""
    if not agent_results:
        return ""
    combined = "\n\n".join(
        f"--- {name} ---\n{data.get('summary', str(data))}"
        for name, data in agent_results.items()
    )
    prompt = (
        f"You are a senior financial analyst. The user asked: \"{user_query}\"\n\n"
        f"Below are the analysis results from multiple specialized agents:\n\n"
        f"{combined}\n\n"
        f"Please provide a comprehensive summary that:\n"
        f"1. Synthesizes key findings from all agents\n"
        f"2. Highlights important financial metrics, stock data, and sentiment\n"
        f"3. Provides an overall assessment of the company/stock\n"
        f"4. Notes any risks or concerns\n"
        f"Keep the summary concise but informative."
    )
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Summary unavailable (no API key)."
        client = openai.OpenAI(api_key=api_key)
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        with open("monitor_logs.json", "a") as f:
            f.write(f"LLM error for summary: {e}\n")
        return "Summary generation failed."

async def get_query_response(query: str) -> dict:
    from mcp.schemas import MCPRequest, MCPContext
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
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
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
