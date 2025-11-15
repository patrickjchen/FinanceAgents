from datetime import datetime
from agents.monitor import MonitorAgent
import os
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
import traceback
import json
import random
import re
from mcp.schemas import MCPRequest, MCPResponse

class FinanceAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db_path = "vector_db/chroma_index"
        self.retriever = self._get_retriever()
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

    def _get_retriever(self):
        try:
            start_time = datetime.now()
            if os.path.exists(self.vector_db_path) and os.listdir(self.vector_db_path):
                status = "ChromaDB index loaded successfully"
                db = Chroma(persist_directory=self.vector_db_path, embedding_function=self.embeddings)
                retriever = db.as_retriever()
            else:
                status = "ChromaDB index built from scratch"
                print(f"[FinanceAgent] {status} at {start_time}. Building from raw_data...")
                docs = []
                raw_data_dir = "./backend/raw_data"
                for fname in os.listdir(raw_data_dir):
                    if fname.lower().endswith(".pdf"):
                        pdf_path = os.path.join(raw_data_dir, fname)
                        base = os.path.splitext(fname)[0]
                        year_match = re.search(r"(20\d{2})", base)
                        year = year_match.group(1) if year_match else "Unknown"
                        company = base.split("-")[0] if "-" in base else base
                        loader = PyPDFLoader(pdf_path)
                        loaded_docs = loader.load()
                        for d in loaded_docs:
                            d.metadata = d.metadata or {}
                            d.metadata["file_name"] = fname
                            d.metadata["year"] = year
                            d.metadata["company"] = company.lower()
                        docs.extend(loaded_docs)
                if not docs:
                    raise ValueError("No PDF documents found in raw_data for RAG.")
                print(f"[FinanceAgent] Loaded {len(docs)} documents. Creating ChromaDB index...")
                db = Chroma.from_documents(docs, self.embeddings, persist_directory=self.vector_db_path)
                db.persist()
                retriever = db.as_retriever()
            self.monitor.log_health("FinanceAgent", status)
            return retriever
        except Exception as e:
            self.monitor.log_health("FinanceAgent", "FAILED", str(e))
            print(f"[FinanceAgent] Error during RAG setup: {e}")
            print(traceback.format_exc())
            raise

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
        raw_data_dir = "./backend/raw_data"
        try:
            for company in companies:
                print(f"[FinanceAgent] Processing company: {company}")
                # 1. Check for files about the company
                company_files = [fname for fname in os.listdir(raw_data_dir) if company.lower() in fname.lower() and fname.lower().endswith('.pdf')]
                if not company_files:
                    print(f"There is no internal files about the {company}.")
                    continue
                # 2. Retrieve relevant content for the query from those files
                docs = []
                for fname in company_files:
                    pdf_path = os.path.join(raw_data_dir, fname)
                    loader = PyPDFLoader(pdf_path)
                    loaded_docs = loader.load()
                    docs.extend(loaded_docs)
                # Use retriever to get relevant docs for the query
                if not docs:
                    print(f"No content loaded from files for {company}.")
                    continue
                db = Chroma.from_documents(docs, self.embeddings)
                relevant_docs = db.similarity_search(f"{company} {user_query}", k=3)
                # 3. Summarize relevant content with key data and descriptions via LLM
                summaries = []
                for d in relevant_docs:
                    snippet = d.page_content[:1000]
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
                        "file_name": d.metadata.get('file_name', 'Unknown'),
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
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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
