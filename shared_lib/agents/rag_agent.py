"""RAGAgent: retrieval over the internal filings in raw_data/.

This is the retrieval half of what FinanceAgent used to do inline. It owns
the vector index (build, persist, load) and exposes:

    RAGAgent.retrieve(query, company=None, k=3) -> list[dict]
        Reusable by any agent that wants grounded passages.

    RAGAgent.run(MCPRequest) -> MCPResponse
        The standard agent contract, so routers / CrewAI / AG2 can dispatch
        it like YahooAgent or SECAgent. Returns raw passages under "rag";
        it makes no LLM call. Summarisation is left to the caller
        (FinanceAgent, or the post-processing pass in main.py).

The index is cached per process (see _get_vector_db) so repeated agent
construction does not re-open or rebuild it.
"""

import json
import os
import re
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from langchain_community.document_loaders import PyPDFLoader, BSHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared_lib.embeddings import get_langchain_embeddings
from shared_lib.monitor import MonitorAgent
from shared_lib.schemas import MCPRequest, MCPResponse

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "raw_data")
VECTOR_DB_PATH = "working_dir/vector_db/chroma_index"   # CWD-relative, like monitor.py
DOC_EXTENSIONS = (".pdf", ".htm", ".html")
DEFAULT_TOP_K = 3
CHUNK_SIZE = 1000          # chars; HTML filings load as one huge document otherwise
CHUNK_OVERLAP = 100

_vector_db = None


def list_raw_files(raw_data_dir: str = RAW_DATA_DIR) -> List[str]:
    return sorted(
        f for f in os.listdir(raw_data_dir) if f.lower().endswith(DOC_EXTENSIONS)
    )


def file_metadata(fname: str) -> Dict[str, str]:
    """Derive {file_name, company, year} from a raw_data file name."""
    base = os.path.splitext(fname)[0]
    year_match = re.search(r"(20\d{2})", base)
    company = base.split("-")[0] if "-" in base else base
    return {
        "file_name": fname,
        "company": company.lower(),
        "year": year_match.group(1) if year_match else "Unknown",
    }


def _load_documents(raw_data_dir: str, only_files: Optional[List[str]] = None):
    """Load (and chunk) raw_data files. ``only_files`` restricts to those names."""
    docs = []
    for fname in list_raw_files(raw_data_dir):
        if only_files is not None and fname not in only_files:
            continue
        path = os.path.join(raw_data_dir, fname)
        loader = PyPDFLoader(path) if fname.lower().endswith(".pdf") else BSHTMLLoader(path)
        meta = file_metadata(fname)
        for d in loader.load():
            d.metadata = {**(d.metadata or {}), **meta}
            docs.append(d)
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_documents(docs)


def _indexed_files(db) -> set:
    """File names already present in the Chroma collection."""
    try:
        metas = db.get(include=["metadatas"]).get("metadatas") or []
    except Exception:
        return set()
    return {m.get("file_name") for m in metas if m and m.get("file_name")}


def _sync_index(db, raw_data_dir: str, monitor: Optional[MonitorAgent] = None):
    """Add any raw_data file that is not yet in the index (incremental refresh)."""
    missing = [f for f in list_raw_files(raw_data_dir) if f not in _indexed_files(db)]
    if not missing:
        return
    print(f"[RAGAgent] Indexing {len(missing)} new file(s): {missing}")
    docs = _load_documents(raw_data_dir, only_files=missing)
    if docs:
        db.add_documents(docs)
    if monitor:
        monitor.log_health("RAGAgent", f"Indexed {len(docs)} chunks from {len(missing)} new file(s)")


def _get_vector_db(monitor: Optional[MonitorAgent] = None):
    """Load the persisted Chroma index, building it from raw_data on first use."""
    global _vector_db
    if _vector_db is not None:
        return _vector_db

    embeddings = get_langchain_embeddings()
    if os.path.exists(VECTOR_DB_PATH) and os.listdir(VECTOR_DB_PATH):
        status = "ChromaDB index loaded successfully"
        db = Chroma(persist_directory=VECTOR_DB_PATH, embedding_function=embeddings)
    else:
        status = "ChromaDB index built from scratch"
        print(f"[RAGAgent] {status} at {datetime.now()}. Building from raw_data...")
        docs = _load_documents(RAW_DATA_DIR)
        if not docs:
            raise ValueError("No documents found in raw_data for RAG.")
        print(f"[RAGAgent] Loaded {len(docs)} documents. Creating ChromaDB index...")
        db = Chroma.from_documents(docs, embeddings, persist_directory=VECTOR_DB_PATH)
    if monitor:
        monitor.log_health("RAGAgent", status)
    _sync_index(db, RAW_DATA_DIR, monitor)   # pick up files added since the index was built
    _vector_db = db
    return db


class RAGAgent:
    """Retrieve passages from the internal filings for a query."""

    def __init__(self):
        self.monitor = MonitorAgent()
        self.raw_data_dir = RAW_DATA_DIR
        try:
            self.db = _get_vector_db(self.monitor)
        except Exception as e:
            self.monitor.log_health("RAGAgent", "FAILED", str(e))
            print(f"[RAGAgent] Error during index setup: {e}")
            print(traceback.format_exc())
            raise

    # ---- reusable retrieval -------------------------------------------------

    def company_files(self, company: str) -> List[str]:
        """Raw files whose name mentions the company (case-insensitive)."""
        needle = company.lower()
        return [f for f in list_raw_files(self.raw_data_dir) if needle in f.lower()]

    def retrieve(self, query: str, company: Optional[str] = None, k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """Top-k passages for the query, optionally restricted to one company's files.

        Returns dicts with file_name, company, year, page, content, distance
        (lower distance = closer match).
        """
        search_filter = None
        if company:
            files = self.company_files(company)
            if not files:
                return []
            search_filter = {"file_name": {"$in": files}} if len(files) > 1 else {"file_name": files[0]}

        results = self.db.similarity_search_with_score(query, k=k, filter=search_filter)
        passages = []
        for doc, distance in results:
            meta = doc.metadata or {}
            passages.append({
                "file_name": meta.get("file_name", "Unknown"),
                "company": meta.get("company", (company or "").lower()),
                "year": meta.get("year", "Unknown"),
                "page": meta.get("page"),
                "content": doc.page_content,
                "distance": float(distance),
            })
        return passages

    # ---- agent contract -----------------------------------------------------

    def run(self, request: MCPRequest) -> MCPResponse:
        start_time = datetime.now()
        companies = request.context.companies or []
        user_query = request.context.user_query
        response_data: Any = []
        status = "processing"
        print(f"[RAGAgent] Companies: {companies}, Query: {user_query}")
        try:
            if companies:
                for company in companies:
                    files = self.company_files(company)
                    if not files:
                        print(f"[RAGAgent] No internal files about {company}.")
                        continue
                    passages = self.retrieve(f"{company} {user_query}", company=company)
                    response_data.append({
                        "company": company,
                        "files": files,
                        "passages": [self._preview(p) for p in passages],
                    })
            else:
                passages = self.retrieve(user_query)
                response_data.append({
                    "query": user_query,
                    "passages": [self._preview(p) for p in passages],
                })
            status = "success"
        except Exception as e:
            print(f"[RAGAgent] Exception: {e}")
            status = "failed"
            response_data = {"error": str(e)}

        completed_time = datetime.now()
        log_message = {
            "agent": "RAGAgent",
            "started_timestamp": start_time.isoformat(),
            "companies": companies,
            "response": response_data,
            "completed_timestamp": completed_time.isoformat(),
            "status": status,
        }
        try:
            with open("monitor_logs.json", "a") as f:
                f.write(json.dumps(log_message) + "\n")
        except Exception as e:
            print(f"[RAGAgent] Logging error: {e}")

        return MCPResponse(
            request_id=request.request_id,
            data={"rag": response_data},
            context_updates=None,
            status=status,
        )

    @staticmethod
    def _preview(passage: Dict[str, Any], limit: int = 1000) -> Dict[str, Any]:
        text = passage["content"]
        return {**passage, "content": text[:limit] + ("..." if len(text) > limit else "")}
