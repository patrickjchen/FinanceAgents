from datetime import datetime
from shared_lib.monitor import MonitorAgent
import os
import traceback
import json
import random
import re
from shared_lib.schemas import MCPRequest, MCPResponse
from shared_lib.agents.rag_agent import RAGAgent

class FinanceAgent:
    """Financial analysis over the internal filings.

    Retrieval is delegated to RAGAgent; this agent adds metric extraction and
    the analyst-style LLM summary on top of the retrieved passages.
    """

    def __init__(self):
        self.monitor = MonitorAgent()
        try:
            self.rag = RAGAgent()
        except Exception as e:
            self.monitor.log_health("FinanceAgent", "FAILED", str(e))
            print(f"[FinanceAgent] Error during RAG setup: {e}")
            print(traceback.format_exc())
            raise
        self.prompts = [
            "As a professional investment banker, answer the following question with expertise and clarity:",
            "As a senior financial analyst, provide a detailed and insightful answer to the following question:",
            "Imagine you are advising a client at a top investment bank. Please answer the following question with authority and precision:",
            "As a finance expert, respond to the following question with a focus on actionable insights:",
            "As an investment banking professional, answer this question referencing relevant financial documents and topics:",
            # Few-shot style prompts:
            "Client: What are the key risks in this investment?\nBanker: As your investment banker, here are the main risks to consider... Now, answer the following question:",
            "Client: Can you summarize the financial performance?\nBanker: Certainly, here is a professional summary... Now, answer the following question:",
            "Client: What is the outlook for this sector?\nBanker: Based on the latest reports and my expertise, here is the outlook... Now, answer the following question:",
            "Client: Should we proceed with this acquisition?\nBanker: Here is my professional advice based on the data... Now, answer the following question:"
        ]

    def extract_metrics(self, text):
        metrics = {}
        patterns = {
            "Revenue": r"Revenue[s]?:?\s*\$?([\d,\.]+)",
            "Operating Income": r"Operating Income[s]?:?\s*\$?([\d,\.]+)",
            "Net Income": r"Net Income[s]?:?\s*\$?([\d,\.]+)",
            "Earnings Per Share": r"Earnings Per Share[s]?:?\s*\$?([\d,\.]+)",
            "Total Assets": r"Total Assets[s]?:?\s*\$?([\d,\.]+)",
            "Total Liabilities": r"Total Liabilities[s]?:?\s*\$?([\d,\.]+)"
        }
        for key, pat in patterns.items():
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                metrics[key] = match.group(1)
        return metrics

    def get_llm_prompt(self, companies_data):
        return (
            "You are a financial analyst. Given the following company data extracted from internal financial documents, "
            "summarize the key financial data and provide a concise summary for each company. Only include companies present in the data.\n\n" +
            f"Data: {json.dumps(companies_data, ensure_ascii=False)}"
        )

    def run(self, request: MCPRequest) -> MCPResponse:
        start_time = datetime.now()
        companies = request.context.companies
        user_query = request.context.user_query
        response_data = []
        status = "processing"
        print(f"[FinanceAgent] Companies: {companies}")
        try:
            for company in companies:
                print(f"[FinanceAgent] Processing company: {company}")
                # 1. Retrieve relevant passages for the query from the company's files (via RAGAgent)
                if not self.rag.company_files(company):
                    print(f"There is no internal files about the {company}.")
                    continue
                passages = self.rag.retrieve(f"{company} {user_query}", company=company, k=3)
                if not passages:
                    print(f"No relevant content found for {company}.")
                    continue
                # 2. Summarize relevant content with key data and descriptions via LLM
                summaries = []
                for p in passages:
                    snippet = p["content"][:1000]
                    key_data = self.extract_metrics(snippet)
                    prompt = (
                        f"You are a financial analyst. Here is some internal document content for {company} relevant to the query: '{user_query}'.\n"
                        f"Content: {snippet}\n"
                        f"Key Data: {json.dumps(key_data, ensure_ascii=False)}\n"
                        f"Please summarize the key financial data and provide a concise, professional summary for the user."
                    )
                    try:
                        summary = self._call_llm(prompt)
                    except Exception as e:
                        summary = f"LLM error: {e}"
                    summaries.append({
                        "file_name": p.get("file_name", "Unknown"),
                        "summary": summary,
                        "key_data": key_data
                    })
                response_data.append({
                    "company": company,
                    "summaries": summaries
                })
            print(f"[FinanceAgent] Final response_data: {response_data}")
            status = "success"
        except Exception as e:
            print(f"[FinanceAgent] Exception: {e}")
            status = "failed"
            response_data = {"error": str(e)}
        completed_time = datetime.now()
        log_message = {
            "agent": "FinanceAgent",
            "started_timestamp": start_time.isoformat(),
            "companies": companies,
            "response": response_data,
            "completed_timestamp": completed_time.isoformat(),
            "status": status
        }
        try:
            with open('monitor_logs.json', 'a') as f:
                f.write(json.dumps(log_message) + '\n')
        except Exception as e:
            print(f"[FinanceAgent] Logging error: {e}")
        return MCPResponse(
            request_id=request.request_id,
            data={"finance": response_data},
            context_updates=None,
            status=status
        )

    def _call_llm(self, prompt: str) -> str:
        from shared_lib.llm_config import require_llm_client, get_llm_model
        client = require_llm_client()
        response = client.chat.completions.create(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def _summarize_relevant(self, text: str) -> str:
        if not text:
            return "No relevant content found."
        return text[:150] + ("..." if len(text) > 150 else "")

    def summarize_as_banker(self, snippet, metrics):
        summary = "Based on the provided financial data, "
        if metrics:
            summary += ", ".join([f"the {k.lower()} was ${v}" for k, v in metrics.items()]) + ". "
        summary += "The above figures are extracted from the most relevant section of the document."
        summary += " If you would like to know more related information, please let me know."
        return summary
