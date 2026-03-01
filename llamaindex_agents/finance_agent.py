import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from shared_lib.schemas import MCPRequest, MCPResponse
from shared_lib.monitor import MonitorAgent

class FinanceAgent:
    def __init__(self):
        self.monitor = MonitorAgent()

        # Configure LlamaIndex settings
        Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
        Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

        self.persist_dir = "./vector_db/llamaindex_storage"
        self.raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data")

        # Initialize or load the vector index
        self.index = self._get_or_create_index()

        # Create query engine
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=3,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)]
        )

    def _get_or_create_index(self) -> VectorStoreIndex:
        """Get existing index or create new one from documents"""
        try:
            if os.path.exists(self.persist_dir):
                # Load existing index
                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                index = load_index_from_storage(storage_context)
                self.monitor.log_health("FinanceAgent", "LOADED", "Vector index loaded from storage")
                return index
            else:
                # Create new index
                return self._create_new_index()
        except Exception as e:
            self.monitor.log_error("FinanceAgent", f"Index initialization failed: {e}")
            return self._create_new_index()

    def _create_new_index(self) -> VectorStoreIndex:
        """Create a new vector index from PDF and HTML documents"""
        try:
            if not os.path.exists(self.raw_data_dir):
                raise ValueError(f"Raw data directory not found: {self.raw_data_dir}")

            # Load documents (supports PDF and HTML SEC filings)
            reader = SimpleDirectoryReader(
                input_dir=self.raw_data_dir,
                required_exts=[".pdf", ".htm", ".html"],
            )
            documents = reader.load_data()

            if not documents:
                raise ValueError("No PDF documents found")

            # Add metadata to documents
            for doc in documents:
                file_path = doc.metadata.get('file_path', '')
                file_name = os.path.basename(file_path)

                # Extract company and year from filename
                base_name = os.path.splitext(file_name)[0]
                year_match = re.search(r"(20\d{2})", base_name)
                year = year_match.group(1) if year_match else "Unknown"
                company = base_name.split("-")[0] if "-" in base_name else base_name

                doc.metadata.update({
                    "file_name": file_name,
                    "company": company.lower(),
                    "year": year
                })

            # Create index
            index = VectorStoreIndex.from_documents(documents)

            # Persist index
            os.makedirs(self.persist_dir, exist_ok=True)
            index.storage_context.persist(persist_dir=self.persist_dir)

            self.monitor.log_health("FinanceAgent", "CREATED", f"Vector index created with {len(documents)} documents")
            return index

        except Exception as e:
            self.monitor.log_error("FinanceAgent", f"Index creation failed: {e}")
            raise

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

                    # Query the index
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
            # This would require custom filtering in a real implementation
            # For now, return a basic response
            query = f"documents related to {company}"
            response = self.query_engine.query(query)

            return [
                {
                    "file_name": node.metadata.get('file_name', 'Unknown'),
                    "company": node.metadata.get('company', company),
                    "year": node.metadata.get('year', 'Unknown'),
                    "relevance_score": node.score if hasattr(node, 'score') else None
                }
                for node in response.source_nodes
            ]
        except Exception as e:
            self.monitor.log_error("FinanceAgent", f"Error getting company documents: {e}")
            return []