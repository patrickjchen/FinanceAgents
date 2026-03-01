import warnings
warnings.filterwarnings('ignore')
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from datetime import datetime
import traceback
import json
from fastapi import APIRouter, BackgroundTasks
from mcp.schemas import MCPRequest, MCPResponse, MCPContext
from typing import List, Dict, Any, Optional
import asyncio
import logging

from shared_lib.query_classification import (
    extract_companies as _extract_companies,
    map_to_tickers as _map_to_tickers,
    is_financial_query as _is_financial_query,
    determine_agents as _determine_agents,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class RouterCrew:
    def __init__(self):
        self._raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "raw_data")

    def extract_companies(self, query: str) -> List[str]:
        return _extract_companies(
            query,
            raw_data_dir=self._raw_data_dir,
            on_error=lambda msg: logger.error(msg),
        )

    def map_to_tickers(self, companies: List[str]) -> List[str]:
        return _map_to_tickers(companies)

    def is_financial_query(self, query: str, companies: List[str], tickers: List[str]) -> bool:
        return _is_financial_query(query, companies, tickers)

    def determine_agents(self, user_query: str, companies: List[str], tickers: List[str]) -> List[str]:
        return _determine_agents(
            user_query, companies, tickers,
            agent_order="reddit_first",
            on_error=lambda msg: logger.error(msg),
        )

    async def run_agent(self, agent_name: str, mcp_request: MCPRequest, bg: BackgroundTasks) -> Optional[Any]:
        """Run an agent with comprehensive error handling"""
        try:
            # Dynamically import agent to isolate dependencies
            if agent_name == "FinanceAgent":
                from shared_lib.agents.finance_agent import FinanceAgent
                agent_class = FinanceAgent
            elif agent_name == "YahooAgent":
                from shared_lib.agents.yahoo_agent import YahooAgent
                agent_class = YahooAgent
            elif agent_name == "SECAgent":
                from shared_lib.agents.sec_agent import SECAgent
                agent_class = SECAgent
            elif agent_name == "RedditAgent":
                from shared_lib.agents.reddit_agent import RedditAgent
                agent_class = RedditAgent
            elif agent_name == "GeneralAgent":
                from shared_lib.agents.general_agent import GeneralAgent
                agent_class = GeneralAgent
            else:
                logger.error(f"Agent {agent_name} not supported")
                return None

            agent_instance = agent_class()

            if agent_name == "RedditAgent":
                return await agent_instance.run(mcp_request, bg)
            elif agent_name == "GeneralAgent":
                # GeneralAgent.run takes only mcp_request
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, agent_instance.run, mcp_request)
            else:
                # Run synchronous agents in thread pool
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, agent_instance.run, mcp_request)
        except ImportError as e:
            logger.error(f"Import error for {agent_name}: {e}")
            return {"error": f"Agent dependencies missing: {e}"}
        except Exception as e:
            logger.error(f"Error running agent {agent_name}: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    async def route(self, mcp_request: MCPRequest, bg: BackgroundTasks) -> MCPResponse:
        start_time = datetime.now()
        user_query = mcp_request.context.user_query if mcp_request.context else ""

        # Safely extract companies and tickers
        try:
            companies = self.extract_companies(user_query) or []
            tickers = self.map_to_tickers(companies) or []
        except Exception as e:
            logger.error(f"Error extracting companies/tickers: {e}")
            companies = []
            tickers = []

        # Determine which agents to run using smart classification
        try:
            agent_names = self.determine_agents(user_query, companies, tickers)
        except Exception as e:
            logger.error(f"Error determining agents: {e}")
            agent_names = ["RedditAgent", "FinanceAgent"]

        log_message = {
            "router": "RouterCrew",
            "started_timestamp": start_time.isoformat(),
            "companies": companies,
            "tickers": tickers,
            "sub_agents": agent_names,
            "status": "processing"
        }

        responses = {}
        context_updates = {}
        status = "success"

        try:
            # Create context safely
            context = MCPContext(
                user_query=user_query,
                companies=companies,
                tickers=tickers,
                extracted_terms={},
                version=getattr(mcp_request.context, "version", "1.0")
            )
            updated_request = MCPRequest(
                request_id=mcp_request.request_id,
                context=context
            )

            # Run agents concurrently
            tasks = []
            for agent_name in agent_names:
                tasks.append(self.run_agent(agent_name, updated_request, bg))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results with comprehensive checks
            for agent_name, result in zip(agent_names, results):
                key_name = agent_name.lower().replace("agent", "")

                # Handle exceptions and errors
                if isinstance(result, Exception):
                    responses[key_name] = {"error": str(result)}
                    status = "partial_failure"
                elif result is None:
                    responses[key_name] = {"error": "Agent returned no response"}
                    status = "partial_failure"
                else:
                    # Handle different agent response formats
                    if hasattr(result, 'data'):
                        responses[key_name] = result.data
                        if hasattr(result, 'context_updates'):
                            try:
                                if result.context_updates:
                                    context_updates.update(result.context_updates)
                            except Exception as e:
                                logger.error(f"Error updating context: {e}")
                    elif isinstance(result, dict):
                        responses[key_name] = result
                    else:
                        responses[key_name] = {"response": str(result)}
        except Exception as e:
            status = "failed"
            responses["error"] = str(e)
            logger.error(f"Routing error: {e}")
            logger.error(traceback.format_exc())

        completed_time = datetime.now()
        log_message.update({
            "completed_timestamp": completed_time.isoformat(),
            "status": status
        })

        # Safely log results
        try:
            with open("monitor_logs.json", "a") as f:
                f.write(json.dumps(log_message) + "\n")
        except Exception as e:
            logger.error(f"[RouterCrew] Logging error: {e}")

        logger.info(json.dumps(log_message, indent=2))

        # Return response with fallbacks
        return MCPResponse(
            request_id=mcp_request.request_id or "unknown",
            data=responses or {"error": "No agents responded"},
            context_updates=context_updates or {},
            status=status,
            timestamp=completed_time
        )

@router.post("/query", response_model=MCPResponse)
async def handle_query(request: MCPRequest, bg: BackgroundTasks):
    router_crew = RouterCrew()
    return await router_crew.route(request, bg)
