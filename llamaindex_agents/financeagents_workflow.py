"""
FinanceAgents Workflow Implementation using LlamaIndex Workflow

This replaces the router-based system with a more robust workflow architecture
that provides better orchestration, error handling, and parallel execution.
"""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
from llama_index.core.workflow.context import Context

from shared_lib.schemas import MCPRequest, MCPResponse, MCPContext
from shared_lib.monitor import MonitorAgent

from shared_lib.constants import COMPANY_TICKER_MAP, FINANCIAL_KEYWORDS
from shared_lib.query_classification import (
    extract_companies as _extract_companies,
    map_to_tickers as _map_to_tickers,
    is_financial_query as _is_financial_query,
    determine_agents as _determine_agents,
)

# ============================================================================
# Workflow Events
# ============================================================================

class QueryAnalyzedEvent(Event):
    """Event fired after query analysis"""
    user_query: str
    companies: List[str]
    tickers: List[str]
    selected_agents: List[str]

class AgentExecutionCompleteEvent(Event):
    """Event fired when all agents have completed execution"""
    agent_results: Dict[str, Any]
    successful_agents: List[str]
    failed_agents: List[str]
    execution_times: Dict[str, float]

class ResponsesImprovedEvent(Event):
    """Event fired after individual responses are improved"""
    improved_results: Dict[str, Any]
    original_results: Dict[str, Any]

class FinalSummaryEvent(Event):
    """Event fired after comprehensive summary is generated"""
    final_results: Dict[str, Any]
    summary: str

# ============================================================================
# Main FinanceAgents Workflow
# ============================================================================

class FinanceAgentsWorkflow(Workflow):
    """
    FinanceAgents Financial Analysis Workflow

    This workflow orchestrates multiple AI agents to provide comprehensive
    financial analysis. The flow consists of:

    1. Query Analysis - Extract companies, tickers, determine relevant agents
    2. Parallel Agent Execution - Run selected agents concurrently
    3. Response Improvement - Enhance individual agent outputs
    4. Summary Generation - Create comprehensive analysis
    5. Result Finalization - Package and return complete response
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitor = MonitorAgent()
        self.agent_instances = {}
        self._raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data")
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agent instances"""
        self.agent_instances = {}

        # Local LlamaIndex-specific agents (loaded dynamically)
        local_agents = [
            ("FinanceAgent", "finance_agent", "FinanceAgent"),
            ("YahooAgent", "yahoo_agent_enhanced", "YahooAgentEnhanced"),
            ("RedditAgent", "reddit_agent", "RedditAgent"),
        ]

        for agent_key, module_name, class_name in local_agents:
            try:
                module = __import__(module_name)
                agent_class = getattr(module, class_name)
                self.agent_instances[agent_key] = agent_class()
            except Exception as e:
                self.monitor.log_error("FinanceAgentsWorkflow", f"Failed to initialize {agent_key}: {e}")
                continue

        # Shared agents from shared_lib
        try:
            from shared_lib.agents.sec_agent import SECAgent
            self.agent_instances["SECAgent"] = SECAgent()
        except Exception as e:
            self.monitor.log_error("FinanceAgentsWorkflow", f"Failed to initialize SECAgent: {e}")

        try:
            from shared_lib.agents.general_agent import GeneralAgent
            self.agent_instances["GeneralAgent"] = GeneralAgent()
        except Exception as e:
            self.monitor.log_error("FinanceAgentsWorkflow", f"Failed to initialize GeneralAgent: {e}")

        self.monitor.log_health("FinanceAgentsWorkflow", "INITIALIZED", f"Loaded {len(self.agent_instances)} agents")

    # ========================================================================
    # Query Analysis Methods (thin wrappers around lib functions)
    # ========================================================================

    def extract_companies(self, query: str) -> List[str]:
        return _extract_companies(
            query,
            raw_data_dir=self._raw_data_dir,
            on_error=lambda msg: self.monitor.log_error("FinanceAgentsWorkflow", msg),
        )

    def map_to_tickers(self, companies: List[str]) -> List[str]:
        return _map_to_tickers(companies)

    def is_financial_query(self, query: str, companies: List[str], tickers: List[str]) -> bool:
        return _is_financial_query(query, companies, tickers)

    def determine_agents(self, user_query: str, companies: List[str], tickers: List[str]) -> List[str]:
        return _determine_agents(
            user_query, companies, tickers,
            agent_order="finance_first",
            on_error=lambda msg: self.monitor.log_error("FinanceAgentsWorkflow", msg),
        )

    # ========================================================================
    # Workflow Steps
    # ========================================================================

    @step
    async def analyze_query(self, ctx: Context, ev: StartEvent) -> QueryAnalyzedEvent:
        """Step 1: Analyze the incoming query and determine execution plan"""
        start_time = datetime.now()
        user_query = ev.get("user_query", "")

        try:
            # Extract companies and tickers
            companies = self.extract_companies(user_query)
            tickers = self.map_to_tickers(companies)
            selected_agents = self.determine_agents(user_query, companies, tickers)

            # Log analysis results
            analysis_info = {
                "query": user_query,
                "companies": companies,
                "tickers": tickers,
                "selected_agents": selected_agents
            }

            # Store in context using workflow globals
            self.user_query = user_query
            self.companies = companies
            self.tickers = tickers
            self.selected_agents = selected_agents
            self.analysis_time = (datetime.now() - start_time).total_seconds()

            self.monitor.log_health("FinanceAgentsWorkflow", "QUERY_ANALYZED", json.dumps(analysis_info))

            return QueryAnalyzedEvent(
                user_query=user_query,
                companies=companies,
                tickers=tickers,
                selected_agents=selected_agents
            )

        except Exception as e:
            self.monitor.log_error("FinanceAgentsWorkflow", f"Query analysis failed: {e}")
            return QueryAnalyzedEvent(
                user_query=user_query,
                companies=[],
                tickers=[],
                selected_agents=["FinanceAgent", "RedditAgent"]
            )

    @step
    async def execute_agents(self, ctx: Context, ev: QueryAnalyzedEvent) -> AgentExecutionCompleteEvent:
        """Step 2: Execute all selected agents in parallel"""
        start_time = datetime.now()


        # Create MCP request
        mcp_context = MCPContext(
            user_query=ev.user_query,
            companies=ev.companies,
            tickers=ev.tickers
        )
        request = MCPRequest(context=mcp_context)


        async def execute_single_agent(agent_name: str) -> tuple[str, Any, bool, float, Optional[str]]:
            """Execute a single agent and return results"""
            agent_start = datetime.now()

            try:
                agent = self.agent_instances.get(agent_name)
                if not agent:
                    error_msg = f"Agent {agent_name} not found in initialized agents"
                    raise ValueError(error_msg)

                # Execute agent (handle async RedditAgent)
                if agent_name == "RedditAgent":
                    result = await agent.run(request)
                else:
                    result = agent.run(request)

                execution_time = (datetime.now() - agent_start).total_seconds()

                # Extract data from MCP response
                if hasattr(result, 'data'):
                    agent_data = result.data
                elif hasattr(result, '__dict__'):
                    agent_data = result.__dict__
                else:
                    agent_data = result

                return agent_name, agent_data, True, execution_time, None

            except Exception as e:
                execution_time = (datetime.now() - agent_start).total_seconds()
                error_msg = str(e)
                self.monitor.log_error("FinanceAgentsWorkflow", f"{agent_name} execution failed: {error_msg}")
                return agent_name, {}, False, execution_time, error_msg

        # Execute all agents in parallel
        agent_tasks = [execute_single_agent(agent) for agent in ev.selected_agents]
        results = await asyncio.gather(*agent_tasks)

        # Process results
        agent_results = {}
        successful_agents = []
        failed_agents = []
        execution_times = {}

        for agent_name, data, success, exec_time, error in results:
            execution_times[agent_name] = exec_time

            if success:
                agent_results[agent_name.lower()] = data
                successful_agents.append(agent_name)
            else:
                failed_agents.append(agent_name)

        total_time = (datetime.now() - start_time).total_seconds()

        # Store in workflow instance
        self.agent_results = agent_results
        self.execution_times = execution_times

        self.monitor.log_health("FinanceAgentsWorkflow", "AGENTS_EXECUTED",
                              f"Success: {len(successful_agents)}, Failed: {len(failed_agents)}")

        return AgentExecutionCompleteEvent(
            agent_results=agent_results,
            successful_agents=successful_agents,
            failed_agents=failed_agents,
            execution_times=execution_times
        )

    @step
    async def improve_responses(self, ctx: Context, ev: AgentExecutionCompleteEvent) -> ResponsesImprovedEvent:
        """Step 3: Improve individual agent responses using LLM"""
        if not ev.agent_results:
            return ResponsesImprovedEvent(
                improved_results={},
                original_results={}
            )


        # Import the improvement function
        from main import improve_agent_response

        improved_results = {}

        async def improve_single_response(agent_name: str, result: Any) -> tuple[str, str]:
            """Improve a single agent response"""
            try:
                if not result or (isinstance(result, dict) and result.get("error")):
                    return agent_name, str(result)


                # Handle different response formats
                if agent_name == "generalagent":
                    if isinstance(result, dict):
                        if "response" in result:
                            content = result["response"]
                        elif len(result) == 1 and "general" in result:
                            content = result["general"]
                        else:
                            content = json.dumps(result, ensure_ascii=False)
                    else:
                        content = str(result)
                    return agent_name, content
                else:
                    # Convert to string for LLM processing
                    if isinstance(result, dict):
                        content = json.dumps(result, ensure_ascii=False, indent=2)
                    else:
                        content = str(result)

                    improved_content = await improve_agent_response(agent_name, content)
                    return agent_name, improved_content

            except Exception as e:
                return agent_name, str(result)

        # Improve all responses in parallel
        improvement_tasks = [
            improve_single_response(agent_name, result)
            for agent_name, result in ev.agent_results.items()
        ]

        improvements = await asyncio.gather(*improvement_tasks)

        # Process improved results
        for agent_name, improved_content in improvements:
            # Map to consistent output format
            agent_key = self._get_agent_key(agent_name)
            improved_results[agent_key] = {"summary": improved_content}


        return ResponsesImprovedEvent(
            improved_results=improved_results,
            original_results=ev.agent_results
        )

    @step
    async def generate_comprehensive_summary(self, ctx: Context, ev: ResponsesImprovedEvent) -> FinalSummaryEvent:
        """Step 4: Generate comprehensive final summary (skipped for GeneralAgent-only results)"""
        user_query = getattr(self, 'user_query', 'Unknown query')

        # Skip summary generation if only GeneralAgent responded
        has_general_only = (
            len(ev.improved_results) == 1
            and "GeneralAgent" in ev.improved_results
        )

        if has_general_only:
            return FinalSummaryEvent(
                final_results=ev.improved_results,
                summary=""
            )

        try:
            # Import summary generation function
            from main import generate_comprehensive_summary

            summary = await generate_comprehensive_summary(
                user_query,
                ev.original_results,
                ev.improved_results
            )

            # Add summary to final results
            final_results = ev.improved_results.copy()
            final_results["FinalSummary"] = {"summary": summary}


            return FinalSummaryEvent(
                final_results=final_results,
                summary=summary
            )

        except Exception as e:
            self.monitor.log_error("FinanceAgentsWorkflow", f"Summary generation failed: {e}")

            # Return results without summary
            fallback_summary = f"""
{'='*80}
ANALYSIS SUMMARY
{'='*80}

Query: "{user_query}"

Analysis completed using {len(ev.improved_results)} agents.
Please review the detailed responses above for insights.

Note: Advanced summary generation temporarily unavailable.
{'='*80}
"""

            final_results = ev.improved_results.copy()
            final_results["FinalSummary"] = {"summary": fallback_summary}

            return FinalSummaryEvent(
                final_results=final_results,
                summary=fallback_summary
            )

    @step
    async def finalize_results(self, ctx: Context, ev: FinalSummaryEvent) -> StopEvent:
        """Step 5: Finalize and package the complete response"""

        # Get metadata from workflow instance
        analysis_time = getattr(self, 'analysis_time', 0)
        execution_times = getattr(self, 'execution_times', {})

        total_workflow_time = sum(execution_times.values()) + analysis_time


        # Package final response
        response_data = {
            "status": "success",
            "results": ev.final_results,
            "metadata": {
                "workflow_version": "2.0",
                "total_agents": len(execution_times),
                "execution_times": execution_times,
                "analysis_time": analysis_time,
                "total_time": total_workflow_time,
                "completion_time": datetime.now().isoformat(),
                "agent_order": list(execution_times.keys())
            }
        }

        self.monitor.log_health("FinanceAgentsWorkflow", "COMPLETED",
                              f"Total time: {total_workflow_time:.2f}s")

        return StopEvent(result=response_data)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_agent_key(self, agent: str) -> str:
        """Map agent names to consistent output keys"""
        agent_mapping = {
            "reddit": "RedditAgent",
            "redditagent": "RedditAgent",
            "finance": "FinanceAgent",
            "financeagent": "FinanceAgent",
            "yahoo": "YahooAgent",
            "yahooagent": "YahooAgent",
            "yahoo_enhanced": "YahooAgent",
            "sec": "SECAgent",
            "secagent": "SECAgent",
            "general": "GeneralAgent",
            "generalagent": "GeneralAgent",
        }

        return agent_mapping.get(agent.lower(), f"{agent.capitalize()}Agent")

# ============================================================================
# Workflow Execution Function
# ============================================================================

async def run_financeagents_analysis(user_query: str, timeout: int = 300) -> Dict[str, Any]:
    """
    Execute the complete FinanceAgents workflow for financial analysis

    Args:
        user_query: The financial question or query to analyze
        timeout: Maximum execution time in seconds (default: 5 minutes)

    Returns:
        Dict containing the complete analysis results
    """
    try:
        workflow = FinanceAgentsWorkflow(timeout=timeout, verbose=False)
        result = await workflow.run(user_query=user_query)
        return result

    except asyncio.TimeoutError:
        return {
            "status": "timeout",
            "error": f"Workflow exceeded {timeout} seconds timeout",
            "results": {}
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": {}
        }
