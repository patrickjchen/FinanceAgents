import requests
import json
import os
import openai
from datetime import datetime
from typing import List, Dict, Any, Optional
from shared_lib.schemas import MCPRequest, MCPResponse
from shared_lib.monitor import MonitorAgent


class SECAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        self.sec_api_base = "https://data.sec.gov/api/xbrl"
        self.headers = {
            "User-Agent": "FinanceAgents SEC Agent contact@example.com"
        }

        self.company_cik_map = {
            "apple": "0000320193",
            "microsoft": "0000789019",
            "google": "0001652044",
            "alphabet": "0001652044",
            "amazon": "0001018724",
            "meta": "0001326801",
            "facebook": "0001326801",
            "tesla": "0001318605",
            "nvidia": "0001045810",
            "netflix": "0001065280"
        }

    def _get_cik(self, company: str) -> Optional[str]:
        """Get CIK (Central Index Key) for a company"""
        return self.company_cik_map.get(company.lower())

    def _fetch_company_facts(self, cik: str) -> Dict[str, Any]:
        """Fetch company facts from SEC API"""
        try:
            cik_padded = cik.zfill(10)
            url = f"{self.sec_api_base}/companyfacts/CIK{cik_padded}.json"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.monitor.log_error("SECAgent", f"API request failed for CIK {cik}: {e}")
            return {"error": f"Failed to fetch data for CIK {cik}: {str(e)}"}
        except Exception as e:
            self.monitor.log_error("SECAgent", f"Unexpected error for CIK {cik}: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    def _extract_key_metrics(self, company_facts: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key financial metrics from SEC company facts"""
        try:
            if "error" in company_facts:
                return company_facts

            facts = company_facts.get("facts", {})
            metrics = {}

            key_gaap_tags = {
                "Revenues": ["us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"],
                "NetIncomeLoss": ["us-gaap:NetIncomeLoss", "us-gaap:ProfitLoss"],
                "Assets": ["us-gaap:Assets"],
                "Liabilities": ["us-gaap:Liabilities"],
                "StockholdersEquity": ["us-gaap:StockholdersEquity"],
                "EarningsPerShare": ["us-gaap:EarningsPerShareBasic"]
            }

            gaap_facts = facts.get("us-gaap", {})

            for metric_name, possible_tags in key_gaap_tags.items():
                for tag in possible_tags:
                    if tag.split(":")[-1] in gaap_facts:
                        tag_data = gaap_facts[tag.split(":")[-1]]
                        units = tag_data.get("units", {})
                        if "USD" in units:
                            recent_data = sorted(
                                [item for item in units["USD"] if item.get("form") in ["10-K", "10-Q"]],
                                key=lambda x: x.get("end", ""),
                                reverse=True
                            )
                            if recent_data:
                                metrics[metric_name] = {
                                    "value": recent_data[0].get("val"),
                                    "end_date": recent_data[0].get("end"),
                                    "form": recent_data[0].get("form"),
                                    "period": recent_data[0].get("fp")
                                }
                        break

            return metrics

        except Exception as e:
            self.monitor.log_error("SECAgent", f"Error extracting metrics: {e}")
            return {"error": f"Error extracting metrics: {str(e)}"}

    def _analyze_sec_data_with_llm(self, company: str, sec_data: Dict[str, Any], user_query: str) -> str:
        """Use LLM to analyze SEC data and provide insights"""
        try:
            if "error" in sec_data:
                return f"Unable to analyze SEC data: {sec_data['error']}"

            if not self.client:
                return "LLM analysis unavailable (OPENAI_API_KEY not set)"

            company_info = sec_data.get("entityName", company)
            cik = sec_data.get("cik", "Unknown")

            prompt = f"""
            As a financial analyst, analyze the SEC filing data for {company_info} (CIK: {cik}) and respond to: "{user_query}"

            Available Financial Metrics:
            {json.dumps(sec_data, indent=2)}

            Please provide:
            1. Key financial highlights from the most recent filings
            2. Trends in financial performance
            3. Notable metrics relevant to the user's query
            4. Any regulatory or compliance insights
            5. Investment implications based on SEC data

            Focus on factual analysis based on the provided SEC data. Keep the response concise and professional.
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"LLM analysis error: {str(e)}"

    def run(self, request: MCPRequest) -> MCPResponse:
        """Process SEC filing analysis query"""
        start_time = datetime.now()
        companies = request.context.companies
        user_query = request.context.user_query
        response_data = []
        status = "processing"

        try:
            if not companies:
                return MCPResponse(
                    request_id=request.request_id,
                    data={"sec": {"error": "No companies specified for SEC analysis"}},
                    status="failed",
                    timestamp=datetime.now()
                )

            for company in companies:
                cik = self._get_cik(company)

                if not cik:
                    company_result = {
                        "company": company,
                        "error": f"CIK not found for {company}. Company not supported."
                    }
                else:
                    company_facts = self._fetch_company_facts(cik)

                    if "error" in company_facts:
                        company_result = {
                            "company": company,
                            "cik": cik,
                            "error": company_facts["error"]
                        }
                    else:
                        metrics = self._extract_key_metrics(company_facts)
                        entity_name = company_facts.get("entityName", company)
                        trading_symbol = company_facts.get("tradingSymbol", "Unknown")

                        analysis = self._analyze_sec_data_with_llm(
                            company,
                            {
                                "entityName": entity_name,
                                "tradingSymbol": trading_symbol,
                                "cik": cik,
                                "metrics": metrics
                            },
                            user_query
                        )

                        company_result = {
                            "company": company,
                            "entity_name": entity_name,
                            "trading_symbol": trading_symbol,
                            "cik": cik,
                            "key_metrics": metrics,
                            "llm_analysis": analysis,
                            "data_source": "SEC EDGAR API"
                        }

                response_data.append(company_result)

            status = "success"
            self.monitor.log_health("SECAgent", "SUCCESS", f"Processed SEC data for {len(companies)} companies")

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            response_data = {"error": error_msg}
            self.monitor.log_error("SECAgent", error_msg, {"companies": companies, "query": user_query})

        completed_time = datetime.now()

        return MCPResponse(
            request_id=request.request_id,
            data={"sec": response_data},
            context_updates={"last_sec_query": completed_time.isoformat()},
            status=status,
            timestamp=completed_time
        )

    def get_llm_prompt(self, filings_data):
        return (
            "You are a financial document analyst. Given the following SEC filings, summarize the key data, time period, and provide a concise summary for each file. Do not just list file names.\n\n" +
            f"Filings: {json.dumps(filings_data, ensure_ascii=False)}"
        )
