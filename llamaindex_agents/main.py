import warnings
warnings.filterwarnings('ignore')

import os
import sys
import asyncio
import time
import uvicorn
from fastapi import FastAPI, Request
from datetime import datetime
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
import json

# Import FinanceAgents Workflow and schemas
from financeagents_workflow import run_financeagents_analysis
from schemas import MCPRequest, MCPContext
from monitor import MonitorAgent

app = FastAPI(
    title="FinanceAgents API - Workflow Implementation",
    description="AI-powered financial analysis using LlamaIndex Workflow framework",
    version="3.0.0",
    contact={
        "name": "FinanceAgents",
        "url": "https://localhost:8001",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize monitor
monitor = MonitorAgent()

class MessageRequest(BaseModel):
    query: str

# LLM tips for response improvement
AGENT_TIPS = {
    "reddit": "Reddit agent provides social media sentiment analysis from stock-related discussions.",
    "finance": "Finance agent analyzes internal financial documents using RAG technology.",
    "yahoo": "Yahoo agent provides real-time stock data analysis and market statistics.",
    "sec": "SEC agent analyzes public company financial filings and regulatory data.",
    "general": "General agent handles non-financial queries and general information requests.",
}

async def generate_comprehensive_summary(query: str, all_agent_data: dict, improved_responses: dict) -> str:
    """Generate a comprehensive summary after all agents have run"""
    try:
        # Count successful agents
        agent_count = len([a for a in all_agent_data.keys() if a not in ['error']])

        # Create summary of what each agent contributed
        agent_contributions = []
        for agent, data in all_agent_data.items():
            if agent == "finance":
                if isinstance(data, dict) and "finance" in data:
                    finance_data = data["finance"]
                    if isinstance(finance_data, list) and finance_data:
                        companies = [item.get("company", "Unknown") for item in finance_data if isinstance(item, dict)]
                        agent_contributions.append(f"Finance Agent analyzed internal documents for: {', '.join(companies)}")
                    else:
                        agent_contributions.append("Finance Agent provided financial document analysis")

            elif agent == "yahoo" or agent == "yahoo_enhanced":
                if isinstance(data, dict):
                    if "yahoo" in data:
                        yahoo_data = data["yahoo"]
                        if isinstance(yahoo_data, list):
                            tickers = [item.get("ticker", "Unknown") for item in yahoo_data if isinstance(item, dict) and "ticker" in item]
                            agent_contributions.append(f"Yahoo Agent provided real-time market data for: {', '.join(tickers)}")
                    elif "yahoo_enhanced" in data:
                        enhanced_data = data["yahoo_enhanced"]
                        if isinstance(enhanced_data, list):
                            tickers = [item.get("ticker", "Unknown") for item in enhanced_data if isinstance(item, dict) and "ticker" in item]
                            agent_contributions.append(f"Enhanced Yahoo Agent provided comprehensive market analysis for: {', '.join(tickers)}")

            elif agent == "reddit":
                if isinstance(data, dict) and "reddit" in data:
                    reddit_data = data["reddit"]
                    if isinstance(reddit_data, list):
                        companies = [item.get("company", "General market") for item in reddit_data if isinstance(item, dict)]
                        agent_contributions.append(f"Reddit Agent analyzed sentiment for: {', '.join(set(companies))}")

            elif agent == "sec":
                if isinstance(data, dict) and "sec" in data:
                    agent_contributions.append("SEC Agent provided regulatory filing analysis")

        # Create comprehensive prompt
        contributions_text = "\n".join([f"- {contrib}" for contrib in agent_contributions])

        prompt = f"""
You are a senior financial analyst preparing a comprehensive investment report.

QUERY: "{query}"

ANALYSIS SOURCES:
{contributions_text}

DETAILED AGENT RESPONSES:
{json.dumps(all_agent_data, ensure_ascii=False, indent=2)}

Please provide a comprehensive executive summary that:

1. **Key Findings**: Synthesize the most important insights from all {agent_count} agents
2. **Investment Perspective**: What do these findings mean for potential investors?
3. **Market Context**: How do the different data sources (internal docs, market data, sentiment, regulatory) align or conflict?
4. **Risk Assessment**: What risks and opportunities are highlighted across all sources?
5. **Actionable Recommendations**: Based on the complete analysis, what should investors consider?

Format your response as a professional financial summary, highlighting the most critical insights while maintaining objectivity. Focus on actionable intelligence that synthesizes all available data sources.
"""

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Final Summary: Unable to generate comprehensive summary (API key not available). Please review individual agent responses above."

        client = openai.OpenAI(api_key=api_key)
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )
        )

        summary = response.choices[0].message.content
        return f"\n{'='*80}\n🎯 COMPREHENSIVE INVESTMENT ANALYSIS\n{'='*80}\n\n{summary}\n\n{'='*80}"

    except Exception as e:
        # Log error but return a basic summary
        with open("monitor_logs.json", "a") as f:
            f.write(f"Comprehensive summary generation error: {e}\n")

        return f"""
{'='*80}
🎯 ANALYSIS SUMMARY
{'='*80}

Query: "{query}"

This analysis incorporated data from {len(all_agent_data)} specialized agents:
{', '.join(all_agent_data.keys())}

Please review the detailed responses above for complete insights.
Note: Advanced summary generation temporarily unavailable.
{'='*80}
"""

async def improve_agent_response(agent: str, content: str) -> str:
    """Use LLM to improve and summarize agent output"""
    if not content:
        return ""

    tip = AGENT_TIPS.get(agent, "")
    prompt = (
        f"You are an expert financial analyst. Here is a response from the {agent} agent. "
        f"{tip}\n"
        f"Please improve the formatting, provide a clear summary, and ensure all important "
        f"financial data and insights are preserved. Make it user-friendly while maintaining "
        f"professional accuracy. Include the agent name in your response.\n\n"
        f"Response to improve:\n{content}"
    )

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return content  # fallback to original

        client = openai.OpenAI(api_key=api_key)
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
        )
        return response.choices[0].message.content

    except Exception as e:
        # Log error but return original content
        with open("monitor_logs.json", "a") as f:
            f.write(f"LLM improvement error for {agent}: {e}\n")
        return content

async def get_query_response(query: str) -> dict:
    """Process query through FinanceAgents Workflow"""
    try:
        start_time = datetime.now()

        print(f"\n{'='*60}")
        print(f"🚀 Starting FinanceAgents Workflow Analysis")
        print(f"📝 Query: {query}")
        print(f"🕐 Start Time: {start_time.strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        # Execute the workflow
        workflow_result = await run_financeagents_analysis(query, timeout=300)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        print(f"\n{'='*60}")
        print(f"🎯 FinanceAgents Workflow Results")
        print(f"⏱️ Total Execution Time: {total_time:.2f} seconds")
        print(f"📊 Status: {workflow_result.get('status', 'unknown')}")
        print(f"{'='*60}\n")

        # Handle different result types
        if workflow_result.get("status") == "success":
            results = workflow_result.get("results", {})

            # Log successful completion
            monitor.log_health("FinanceAgentsWorkflow", "SUCCESS",
                             f"Query processed in {total_time:.2f}s with {len(results)} results")

            return results if results else {"error": "No valid responses processed"}

        elif workflow_result.get("status") == "timeout":
            error_msg = workflow_result.get("error", "Workflow timeout")
            monitor.log_error("FinanceAgentsWorkflow", f"Timeout: {error_msg}")
            return {"error": error_msg}

        else:
            error_msg = workflow_result.get("error", "Unknown workflow error")
            monitor.log_error("FinanceAgentsWorkflow", f"Workflow failed: {error_msg}")
            return {"error": error_msg}

    except Exception as e:
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] Exception in workflow execution: {e}"

        with open("monitor_logs.json", "a") as f:
            f.write(error_msg + "\n")

        print(f"❌ {error_msg}")
        monitor.log_error("FinanceAgentsWorkflow", f"Execution exception: {e}")

        return {"error": str(e)}

def _get_agent_key(agent: str) -> str:
    """Map agent names to consistent output keys"""
    agent_mapping = {
        "reddit": "RedditAgent",
        "finance": "FinanceAgent",
        "yahoo": "YahooAgent",
        "sec": "SecAgent",
        "general": "GeneralAgent",
    }

    return agent_mapping.get(agent, f"{agent.capitalize()}Agent")

async def main():
    """Main entry point - runs both FastAPI server and CLI"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)

    # Run both HTTP server and CLI loop
    await asyncio.gather(
        server.serve(),
        cli_query_loop()
    )

async def cli_query_loop():
    """Interactive CLI loop for testing"""

    print("\n" + "="*60)
    print("FinanceAgents - Workflow Implementation")
    print("Interactive CLI Started - Powered by LlamaIndex Workflow")
    print("="*60 + "\n")

    try:
        while True:
            query = await asyncio.to_thread(input, "Enter your financial question (or 'quit' to exit): ")

            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not query.strip():
                continue

            timestamp = datetime.now().isoformat()
            print(f"\n[{timestamp}] Processing query: {query}")
            print("-" * 50)

            # Process query
            response = await get_query_response(query)

            # Display results
            if "error" in response:
                print(f"❌ Error: {response['error']}")
            else:
                print("✅ Response received from agents:")
                for agent, data in response.items():
                    print(f"\n📊 {agent}:")
                    if isinstance(data, dict) and "summary" in data:
                        print(data["summary"])
                    else:
                        print(json.dumps(data, indent=2, ensure_ascii=False))

            print("\n" + "-" * 50)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal. Shutting down...")
    except Exception as e:
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] CLI Exception: {e}"
        print(error_msg)
        monitor.log_error("CLI", error_msg)

@app.post("/query")
async def chat_endpoint(request: MessageRequest):
    """FastAPI endpoint for processing queries"""
    try:
        response_data = await get_query_response(request.query)
        return {"response": response_data}
    except Exception as e:
        return {"error": f"API error: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "implementation": "LlamaIndex",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/agents")
async def list_agents():
    """List available agents"""
    return {
        "available_agents": [
            "FinanceAgent - Internal document analysis using RAG",
            "YahooAgent - Real-time stock data and analysis",
            "SECAgent - SEC filing analysis",
            "RedditAgent - Social media sentiment analysis",
            "GeneralAgent - General queries and system information",
        ],
        "framework": "LlamaIndex",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    # Set environment variables for TensorFlow to reduce warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    print("Starting FinanceAgents - LlamaIndex Implementation...")
    asyncio.run(main())