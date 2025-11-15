import json
from datetime import datetime
from typing import List  # Remove Dict, use dict instead
import requests  # SEC API
from mcp.schemas import MCPRequest, MCPResponse

class SECAgent:
    def __init__(self):
        self.sec_endpoint = "https://data.sec.gov/api/xbrl/companyfacts/"
    
    def get_llm_prompt(self, filings_data):
        return (
            "You are a financial document analyst. Given the following SEC filings, summarize the key data, time period, and provide a concise summary for each file. Do not just list file names.\n\n" +
            f"Filings: {json.dumps(filings_data, ensure_ascii=False)}"
        )

    def _extract_key_data(self, content: str) -> dict:
        # Placeholder: extract key data (e.g., revenue, net income) from content
        # In real use, use regex or NLP to extract financial metrics
        key_data = {}
        if "revenue" in content.lower():
            key_data["revenue"] = "Found in content"
        if "net income" in content.lower():
            key_data["net_income"] = "Found in content"
        return key_data

    def _extract_time_period(self, file_name: str) -> str:
        # Extract time period from file name if possible
        import re
        match = re.search(r'(\d{4}(?:Q\d)?)', file_name)
        return match.group(1) if match else "Unknown"

    def run(self, request: MCPRequest) -> MCPResponse:
        start_time = datetime.now()
        companies = request.context.companies
        user_query = request.context.user_query
        response_data = []
        status = "processing"
        try:
            for company in companies:
                cik = self._get_cik(company)
                filings = self._get_filings(cik)
                company_files = []
                for filing in filings:
                    relevant_text = self._extract_relevant(filing, user_query)
                    summary = self._summarize_relevant(relevant_text)
                    key_data = self._extract_key_data(filing.get("content", ""))
                    time_period = self._extract_time_period(filing.get("file_name", ""))
                    company_files.append({
                        "company": company,
                        "file_name": filing.get("file_name", "Unknown"),
                        "key_data": key_data,
                        "time_period": time_period,
                        "summary": summary
                    })
                response_data.append({
                    "company": company,
                    "files": company_files
                })
            status = "success"
        except Exception as e:
            status = "failed"
            response_data = {"error": str(e)}
        completed_time = datetime.now()
        log_message = {
            "agent": "SECAgent",
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
            print(f"[SECAgent] Logging error: {e}")
        return MCPResponse(
            request_id=request.request_id,
            data={"sec": response_data},
            context_updates=None,
            status=status
        )
    
    def _get_cik(self, company: str) -> str:
        # Placeholder: return a mock CIK or implement lookup
        # In real use, map company name to CIK using a lookup table or API
        return "0000320193"  # Example: Apple Inc.

    def _get_filings(self, cik: str) -> List[dict]:
        # Placeholder: fetch filings from SEC EDGAR (mocked for now)
        # In real use, fetch and parse filings from SEC API
        # Return a list of dicts with at least 'file_name' and 'content'
        return [
            {"file_name": "10-K_2023.txt", "content": "This is a mock 10-K annual report for 2023. Revenue grew..."},
            {"file_name": "10-Q_2024Q1.txt", "content": "This is a mock 10-Q quarterly report for Q1 2024. Net income..."}
        ]

    def _extract_relevant(self, filing: dict, query: str) -> str:
        # Placeholder: extract relevant text from filing based on query (mocked)
        content = filing.get("content", "")
        # In real use, use NLP or keyword search to extract relevant sections
        if query.lower() in content.lower():
            return content
        return content[:200]  # Return first 200 chars as fallback

    def _summarize_relevant(self, text: str) -> str:
        # Placeholder: summarize relevant text (mocked)
        if not text:
            return "No relevant content found."
        return text[:150] + ("..." if len(text) > 150 else "")

    def _log(self, message: dict):
        with open('monitor_logs.json', 'a') as f:
            f.write(json.dumps(message) + '\n')
        print(json.dumps(message, indent=2))