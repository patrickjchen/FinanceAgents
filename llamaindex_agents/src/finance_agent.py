import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from shared_lib.schemas import MCPRequest, MCPResponse
from shared_lib.monitor import MonitorAgent
from rag_agent import RAGAgent

class FinanceAgent:
    """Financial analysis over the internal filings (LlamaIndex).

    Retrieval and the vector index belong to RAGAgent; this agent runs the
    query engine (retrieval + LLM synthesis) and extracts financial metrics
    from the source passages.
    """

    def __init__(self):
        self.monitor = MonitorAgent()
        self.rag = RAGAgent()
        self.query_engine = self.rag.query_engine

    def _extract_financial_metrics(self, text: str) -> Dict[str, str]:
        """Extract financial metrics from text using regex patterns"""
        metrics = {}
        patterns = {
            "Revenue": r"Revenue[s]?:?\s*\$?([\d,\.]+)",
            "Operating Income": r"Operating Income[s]?:?\s*\$?([\d,\.]+)",
            "Net Income": r"Net Income[s]?:?\s*\$?([\d,\.]+)",
            "Earnings Per Share": r"Earnings Per Share[s]?:?\s*\$?([\d,\.]+)",
            "Total Assets": r"Total Assets[s]?:?\s*\$?([\d,\.]+)",
            "Total Liabilities": r"Total Liabilities[s]?:?\s*\$?([\d,\.]+)"
        }

        for metric, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics[metric] = match.group(1)

        return metrics

    def run(self, request: MCPRequest) -> MCPResponse:
        """Process finance query using LlamaIndex"""
        start_time = datetime.now()
        companies = request.context.companies
        user_query = request.context.user_query
        response_data = []
        status = "processing"

        try:
            if not companies:
                # General financial query
                response = self.query_engine.query(user_query)
                response_data = {
                    "general_query": user_query,
                    "response": str(response),
                    "source_nodes": [
                        {
                            "text": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                            "metadata": node.metadata,
                            "score": node.score if hasattr(node, 'score') else None
                        }
                        for node in response.source_nodes[:3]
                    ]
                }
            else:
                # Company-specific queries
                for company in companies:
                    # Create company-specific query
                    company_query = f"Information about {company}: {user_query}"

                    # Query the index (retrieval + synthesis)
                    response = self.query_engine.query(company_query)

                    # Extract metrics from source nodes
                    all_metrics = {}
                    source_summaries = []

                    for node in response.source_nodes[:3]:
                        metrics = self._extract_financial_metrics(node.text)
                        all_metrics.update(metrics)

                        source_summaries.append({
                            "file_name": node.metadata.get('file_name', 'Unknown'),
                            "company": node.metadata.get('company', company),
                            "year": node.metadata.get('year', 'Unknown'),
                            "text_snippet": node.text[:300] + "..." if len(node.text) > 300 else node.text,
                            "metrics": metrics,
                            "relevance_score": node.score if hasattr(node, 'score') else None
                        })

                    company_data = {
                        "company": company,
                        "query_response": str(response),
                        "extracted_metrics": all_metrics,
                        "source_documents": source_summaries,
                        "total_sources": len(response.source_nodes)
                    }

                    response_data.append(company_data)

            status = "success"
            self.monitor.log_health("FinanceAgent", "SUCCESS", f"Processed query for {len(companies)} companies")

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            response_data = {"error": error_msg}
            self.monitor.log_error("FinanceAgent", error_msg, {"companies": companies, "query": user_query})

        completed_time = datetime.now()

        return MCPResponse(
            request_id=request.request_id,
            data={"finance": response_data},
            context_updates={"last_finance_query": completed_time.isoformat()},
            status=status,
            timestamp=completed_time
        )

    def get_company_documents(self, company: str) -> List[Dict[str, Any]]:
        """Get all documents related to a specific company"""
        try:
            return [
                {
                    "file_name": p["file_name"],
                    "company": p["company"],
                    "year": p["year"],
                    "relevance_score": p["score"],
                }
                for p in self.rag.retrieve(f"documents related to {company}", company=company)
            ]
        except Exception as e:
            self.monitor.log_error("FinanceAgent", f"Error getting company documents: {e}")
            return []
