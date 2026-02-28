import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from schemas import MCPRequest, MCPResponse, MCPContext
from monitor import MonitorAgent

from shared_lib.constants import COMPANY_TICKER_MAP, FINANCIAL_KEYWORDS
from shared_lib.query_classification import (
    extract_companies as _extract_companies,
    map_to_tickers as _map_to_tickers,
    is_financial_query as _is_financial_query,
    determine_agents as _determine_agents,
)


class LlamaIndexRouter:
    def __init__(self):
        self.monitor = MonitorAgent()
        self._raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data")

    def extract_companies(self, query: str) -> List[str]:
        return _extract_companies(
            query,
            raw_data_dir=self._raw_data_dir,
            on_error=lambda msg: self.monitor.log_error("LlamaIndexRouter", msg),
        )

    def map_to_tickers(self, companies: List[str]) -> List[str]:
        return _map_to_tickers(companies)

    def is_financial_query(self, query: str, companies: List[str], tickers: List[str]) -> bool:
        return _is_financial_query(query, companies, tickers)

    def determine_agents(self, user_query: str, companies: List[str], tickers: List[str]) -> List[str]:
        return _determine_agents(
            user_query, companies, tickers,
            agent_order="finance_first",
            on_error=lambda msg: self.monitor.log_error("LlamaIndexRouter", msg),
        )

    async def run_agent(self, agent_name: str, mcp_request: MCPRequest) -> Optional[Any]:
        """Run a specific agent with error handling"""
        try:
            # Dynamic import to avoid circular dependencies
            if agent_name == "FinanceAgent":
                from finance_agent import FinanceAgent
                agent = FinanceAgent()
                return agent.run(mcp_request)

            elif agent_name == "YahooAgent":
                from yahoo_agent import YahooAgent
                agent = YahooAgent()
                return agent.run(mcp_request)

            elif agent_name == "SECAgent":
                from sec_agent import SECAgent
                agent = SECAgent()
                return agent.run(mcp_request)

            elif agent_name == "RedditAgent":
                from reddit_agent import RedditAgent
                agent = RedditAgent()
                return agent.run(mcp_request)

            elif agent_name == "GeneralAgent":
                from general_agent import GeneralAgent
                agent = GeneralAgent()
                return agent.run(mcp_request)

            else:
                self.monitor.log_error("LlamaIndexRouter", f"Unknown agent: {agent_name}")
                return {"error": f"Agent {agent_name} not found"}

        except ImportError as e:
            error_msg = f"Import error for {agent_name}: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)
            return {"error": error_msg}

        except Exception as e:
            error_msg = f"Error running {agent_name}: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)
            return {"error": error_msg}

    async def route(self, mcp_request: MCPRequest) -> MCPResponse:
        """Main routing logic for processing requests"""
        start_time = datetime.now()
        user_query = mcp_request.context.user_query if mcp_request.context else ""

        try:
            # Extract companies and tickers
            companies = self.extract_companies(user_query)
            tickers = self.map_to_tickers(companies)

            # Determine which agents to run
            agent_names = self.determine_agents(user_query, companies, tickers)

            # Update context
            updated_context = MCPContext(
                user_query=user_query,
                companies=companies,
                tickers=tickers,
                extracted_terms={"agent_names": agent_names},
                version=getattr(mcp_request.context, "version", "1.0")
            )

            updated_request = MCPRequest(
                request_id=mcp_request.request_id,
                context=updated_context
            )

            # Log routing decision
            routing_log = {
                "router": "LlamaIndexRouter",
                "timestamp": start_time.isoformat(),
                "query": user_query,
                "companies": companies,
                "tickers": tickers,
                "agents": agent_names,
                "status": "routing"
            }

            # Run agents concurrently
            tasks = []
            for agent_name in agent_names:
                task = self.run_agent(agent_name, updated_request)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            responses = {}
            context_updates = {}
            overall_status = "success"

            for agent_name, result in zip(agent_names, results):
                agent_key = agent_name.lower().replace("agent", "")

                if isinstance(result, Exception):
                    responses[agent_key] = {"error": str(result)}
                    overall_status = "partial_failure"
                elif result is None:
                    responses[agent_key] = {"error": "Agent returned no response"}
                    overall_status = "partial_failure"
                else:
                    # Handle MCPResponse objects
                    if hasattr(result, 'data'):
                        responses.update(result.data)
                        if hasattr(result, 'context_updates') and result.context_updates:
                            context_updates.update(result.context_updates)
                    elif isinstance(result, dict):
                        responses[agent_key] = result
                    else:
                        responses[agent_key] = {"response": str(result)}

            completed_time = datetime.now()

            # Update routing log
            routing_log.update({
                "completed_timestamp": completed_time.isoformat(),
                "status": overall_status,
                "agents_completed": len(responses)
            })

            # Log results
            try:
                with open("monitor_logs.json", "a") as f:
                    f.write(json.dumps(routing_log) + "\n")
            except Exception as e:
                self.monitor.log_error("LlamaIndexRouter", f"Logging error: {e}")

            return MCPResponse(
                request_id=mcp_request.request_id,
                data=responses,
                context_updates=context_updates,
                status=overall_status,
                timestamp=completed_time
            )

        except Exception as e:
            error_msg = f"Routing failed: {e}"
            self.monitor.log_error("LlamaIndexRouter", error_msg)

            return MCPResponse(
                request_id=mcp_request.request_id,
                data={"error": error_msg},
                context_updates={},
                status="failed",
                timestamp=datetime.now()
            )
