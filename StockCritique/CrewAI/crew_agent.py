from crewai import Agent, Task, Crew
from crewai.tools import tool
from mcp.schemas import MCPRequest, MCPResponse
from agents.finance_agent import FinanceAgent
from agents.general_agent import GeneralAgent
from agents.reddit_agent import RedditAgent
from agents.yahoo_agent import YahooAgent
from agents.sec_agent import SECAgent
from datetime import datetime

# Define Tool functions using CrewAI @tool decorator
@tool
def finance_tool(user_query: str) -> str:
    """Run FinanceAgent using a user query"""
    return FinanceAgent().run(MCPRequest(request_id="crew-finance", context={"user_query": user_query}))

@tool
def general_tool(user_query: str) -> str:
    """Run GeneralAgent using a user query"""
    return GeneralAgent().run(MCPRequest(request_id="crew-general", context={"user_query": user_query}))

@tool
def yahoo_tool(user_query: str) -> str:
    """Run YahooAgent using a user query"""
    return YahooAgent().run(MCPRequest(request_id="crew-yahoo", context={"user_query": user_query}))

@tool
def sec_tool(user_query: str) -> str:
    """Run SECAgent using a user query"""
    return SECAgent().run(MCPRequest(request_id="crew-sec", context={"user_query": user_query}))

@tool
def reddit_tool(user_query: str) -> str:
    """Run RedditAgent using a user query"""
    return RedditAgent().run(MCPRequest(request_id="crew-reddit", context={"user_query": user_query}))

# Define CrewAI agents
finance_agent = Agent(
    name="finance",
    role="Financial analyst",
    goal="Extract and summarize internal financial documents",
    backstory="An expert who reads internal PDFs to find key financial data.",
    tools=[finance_tool]
)

general_agent = Agent(
    name="general",
    role="General answerer",
    goal="Respond to general questions",
    backstory="A helpful assistant that provides clear and concise answers.",
    tools=[general_tool]
)

yahoo_agent = Agent(
    name="yahoo",
    role="Market data analyzer",
    goal="Analyze stock trends from Yahoo Finance",
    backstory="An expert in financial statistics from real-time stock data.",
    tools=[yahoo_tool]
)

sec_agent = Agent(
    name="sec",
    role="SEC filing summarizer",
    goal="Analyze and summarize SEC filings",
    backstory="An SEC analyst who reviews and distills key points from filings.",
    tools=[sec_tool]
)

reddit_agent = Agent(
    name="reddit",
    role="Social sentiment analyst",
    goal="Analyze Reddit trends on stock topics",
    backstory="A social media analyst who reads Reddit to detect trends and sentiment.",
    tools=[reddit_tool]
)

# Create task builders
def build_tasks(mcp_request: MCPRequest):
    query = mcp_request.context.user_query
    return [
        Task(description=f"Summarize internal financial PDFs for query: {query}", expected_output="JSON summary", agent=finance_agent, tools=[finance_tool]),
        Task(description=f"Answer general question: {query}", expected_output="General answer", agent=general_agent, tools=[general_tool]),
        Task(description=f"Summarize Reddit sentiment about: {query}", expected_output="Reddit analysis", agent=reddit_agent, tools=[reddit_tool]),
        Task(description=f"Summarize Yahoo stock stats related to: {query}", expected_output="Stock stat summary", agent=yahoo_agent, tools=[yahoo_tool]),
        Task(description=f"Summarize SEC filings for query: {query}", expected_output="SEC summary", agent=sec_agent, tools=[sec_tool]),
    ]

# Main CrewAI runner that returns MCPResponse
def build_crew():
    return Crew(name="BankerAI Crew", agents=[finance_agent, general_agent, yahoo_agent, sec_agent, reddit_agent], tasks=[])

def run_crew(mcp_request: MCPRequest) -> MCPResponse:
    crew = build_crew()
    crew.tasks = build_tasks(mcp_request)
    try:
        result = crew.kickoff(inputs={"user_query": mcp_request.context.user_query})
        response_data = {}

        for task in crew.tasks:
            agent_key = task.agent.name.lower()
            output = result.get(task.description, None)
            print(f"KEY:{agent_key} out:{output}")
            if output:
                response_data[agent_key] = output

        return MCPResponse(
            request_id=mcp_request.request_id,
            data=response_data,
            context_updates=None,
            status="success",
            timestamp=datetime.now()
        )
    except Exception as e:
        return MCPResponse(
            request_id=mcp_request.request_id,
            data={"error": str(e)},
            context_updates=None,
            status="failed",
            timestamp=datetime.now()
        )

