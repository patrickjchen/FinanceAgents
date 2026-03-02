"""
FinanceAgents Workflow Design using LlamaIndex Workflow (AgentWorkFlow)

This demonstrates how to restructure the current router-based system
into a more robust workflow-based architecture.
"""

from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
from llama_index.core.workflow.context import Context
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

# Define Events for the workflow
class QueryAnalyzedEvent(Event):
    """Event fired after query analysis"""
    user_query: str
    companies: List[str]
    tickers: List[str]
    is_finance_query: bool
    selected_agents: List[str]

class AgentCompletedEvent(Event):
    """Event fired when an agent completes"""
    agent_name: str
    result: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class AllAgentsCompletedEvent(Event):
    """Event fired when all agents have completed"""
    results: Dict[str, Any]
    successful_agents: List[str]
    failed_agents: List[str]

class SummaryGeneratedEvent(Event):
    """Event fired after final summary is generated"""
    summary: str
    complete_results: Dict[str, Any]

class FinanceAgentsWorkflow(Workflow):
    """
    FinanceAgents Financial Analysis Workflow

    Flow:
    1. Analyze query (extract companies, determine agents)
    2. Run agents in parallel
    3. Collect and improve results
    4. Generate comprehensive summary
    5. Return final response
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_instances = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agent instances"""
        try:
            from finance_agent import FinanceAgent
            from yahoo_agent_enhanced import YahooAgentEnhanced
            from reddit_agent import RedditAgent
            from shared_lib.agents.sec_agent import SECAgent
            from shared_lib.agents.general_agent import GeneralAgent

            self.agent_instances = {
                "FinanceAgent": FinanceAgent(),
                "YahooAgent": YahooAgentEnhanced(),
                "RedditAgent": RedditAgent(),
                "SECAgent": SECAgent(),
                "GeneralAgent": GeneralAgent()
            }
        except Exception as e:
            print(f"Error initializing agents: {e}")

    @step
    async def analyze_query(self, ctx: Context, ev: StartEvent) -> QueryAnalyzedEvent:
        """Step 1: Analyze the incoming query"""
        user_query = ev.get("user_query", "")

        # Import router logic for query analysis
        from shared_lib.query_classification import extract_companies, map_to_tickers, is_financial_query, determine_agents
        router = LlamaIndexRouter()

        # Extract companies and tickers
        companies = router.extract_companies(user_query)
        tickers = router.map_to_tickers(companies)
        is_finance = router.is_finance_query(user_query)
        selected_agents = router.determine_agents(user_query, tickers)

        print(f"🔍 Query Analysis:")
        print(f"  Companies: {companies}")
        print(f"  Tickers: {tickers}")
        print(f"  Finance Query: {is_finance}")
        print(f"  Selected Agents: {selected_agents}")

        # Store in context for later steps
        await ctx.set("user_query", user_query)
        await ctx.set("companies", companies)
        await ctx.set("tickers", tickers)
        await ctx.set("selected_agents", selected_agents)
        await ctx.set("agent_results", {})
        await ctx.set("successful_agents", [])
        await ctx.set("failed_agents", [])

        return QueryAnalyzedEvent(
            user_query=user_query,
            companies=companies,
            tickers=tickers,
            is_finance_query=is_finance,
            selected_agents=selected_agents
        )

    @step
    async def run_agents_parallel(self, ctx: Context, ev: QueryAnalyzedEvent) -> AllAgentsCompletedEvent:
        """Step 2: Run all selected agents in parallel"""
        from shared_lib.schemas import MCPRequest, MCPContext

        # Create MCP request
        mcp_context = MCPContext(
            user_query=ev.user_query,
            companies=ev.companies,
            tickers=ev.tickers
        )
        request = MCPRequest(context=mcp_context)

        # Run agents in parallel
        async def run_single_agent(agent_name: str) -> AgentCompletedEvent:
            try:
                print(f"🚀 Starting {agent_name}...")
                agent = self.agent_instances.get(agent_name)
                if not agent:
                    return AgentCompletedEvent(
                        agent_name=agent_name,
                        result={},
                        success=False,
                        error=f"Agent {agent_name} not found"
                    )

                # Run the agent
                if agent_name == "RedditAgent":
                    result = agent.run(request)  # Sync call
                else:
                    result = agent.run(request)  # All are sync now

                print(f"✅ {agent_name} completed successfully")
                return AgentCompletedEvent(
                    agent_name=agent_name,
                    result=result.data if hasattr(result, 'data') else result,
                    success=True
                )

            except Exception as e:
                print(f"❌ {agent_name} failed: {e}")
                return AgentCompletedEvent(
                    agent_name=agent_name,
                    result={},
                    success=False,
                    error=str(e)
                )

        # Run all agents in parallel
        agent_tasks = [run_single_agent(agent) for agent in ev.selected_agents]
        agent_events = await asyncio.gather(*agent_tasks)

        # Collect results
        results = {}
        successful_agents = []
        failed_agents = []

        for event in agent_events:
            if event.success:
                results[event.agent_name.lower()] = event.result
                successful_agents.append(event.agent_name)
            else:
                failed_agents.append(event.agent_name)
                print(f"⚠️ {event.agent_name} failed: {event.error}")

        # Store in context
        await ctx.set("agent_results", results)
        await ctx.set("successful_agents", successful_agents)
        await ctx.set("failed_agents", failed_agents)

        return AllAgentsCompletedEvent(
            results=results,
            successful_agents=successful_agents,
            failed_agents=failed_agents
        )

    @step
    async def improve_responses(self, ctx: Context, ev: AllAgentsCompletedEvent) -> AllAgentsCompletedEvent:
        """Step 3: Improve individual agent responses"""
        improved_results = {}

        # Import improvement function
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from main import improve_agent_response

        for agent_name, result in ev.results.items():
            try:
                if not result or (isinstance(result, dict) and result.get("error")):
                    continue

                print(f"🔧 Improving {agent_name} response...")

                # Convert to string for LLM processing
                if isinstance(result, dict):
                    content = json.dumps(result, ensure_ascii=False, indent=2)
                else:
                    content = str(result)

                improved_content = await improve_agent_response(agent_name, content)
                improved_results[agent_name] = {"summary": improved_content}

            except Exception as e:
                print(f"⚠️ Failed to improve {agent_name} response: {e}")
                # Keep original response
                improved_results[agent_name] = {"summary": str(result)}

        # Update context
        await ctx.set("improved_results", improved_results)

        return AllAgentsCompletedEvent(
            results=improved_results,
            successful_agents=ev.successful_agents,
            failed_agents=ev.failed_agents
        )

    @step
    async def generate_final_summary(self, ctx: Context, ev: AllAgentsCompletedEvent) -> SummaryGeneratedEvent:
        """Step 4: Generate comprehensive final summary"""
        user_query = await ctx.get("user_query")
        original_results = await ctx.get("agent_results")
        improved_results = ev.results

        # Import summary generation function
        from main import generate_comprehensive_summary

        try:
            print("📋 Generating comprehensive summary...")
            summary = await generate_comprehensive_summary(
                user_query,
                original_results,
                improved_results
            )

            # Add summary to results
            final_results = improved_results.copy()
            final_results["FinalSummary"] = {"summary": summary}

            return SummaryGeneratedEvent(
                summary=summary,
                complete_results=final_results
            )

        except Exception as e:
            print(f"⚠️ Failed to generate summary: {e}")
            # Return without summary
            return SummaryGeneratedEvent(
                summary="Summary generation failed",
                complete_results=improved_results
            )

    @step
    async def finalize_response(self, ctx: Context, ev: SummaryGeneratedEvent) -> StopEvent:
        """Step 5: Finalize and return the complete response"""
        successful_agents = await ctx.get("successful_agents", [])
        failed_agents = await ctx.get("failed_agents", [])

        print(f"🎉 Workflow completed!")
        print(f"  ✅ Successful agents: {len(successful_agents)}")
        print(f"  ❌ Failed agents: {len(failed_agents)}")

        return StopEvent(result={
            "status": "success" if successful_agents else "failed",
            "results": ev.complete_results,
            "metadata": {
                "successful_agents": successful_agents,
                "failed_agents": failed_agents,
                "total_agents": len(successful_agents) + len(failed_agents),
                "completion_time": datetime.now().isoformat()
            }
        })

# Example usage function
async def run_financeagents_workflow(user_query: str) -> Dict[str, Any]:
    """
    Run the FinanceAgents workflow for a given query
    """
    workflow = FinanceAgentsWorkflow(timeout=300)  # 5 minute timeout

    result = await workflow.run(user_query=user_query)
    return result