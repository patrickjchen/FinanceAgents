"""LlamaIndex-native RAGAgent: retrieval over the internal filings in raw_data/.

Mirrors shared_lib/agents/rag_agent.py but on a persisted VectorStoreIndex
(working_dir/vector_db/llamaindex_storage) instead of Chroma. Owns the
index; FinanceAgent (src/finance_agent.py) builds its analysis on top.

    RAGAgent.retrieve(query, company=None, k=3) -> list[dict]
    RAGAgent.query_engine                       -> retrieval + synthesis
    RAGAgent.run(MCPRequest)                    -> MCPResponse, data under "rag"
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.core.postprocessor import SimilarityPostprocessor

from shared_lib.schemas import MCPRequest, MCPResponse
from shared_lib.monitor import MonitorAgent
from shared_lib.embeddings import get_llamaindex_embedding
from llm_settings import make_llm

PERSIST_DIR = "./working_dir/vector_db/llamaindex_storage"
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "raw_data")
DOC_EXTENSIONS = (".pdf", ".htm", ".html")
DEFAULT_TOP_K = 3

_index: Optional[VectorStoreIndex] = None


def list_raw_files(raw_data_dir: str = RAW_DATA_DIR) -> List[str]:
    return sorted(f for f in os.listdir(raw_data_dir) if f.lower().endswith(DOC_EXTENSIONS))


def file_metadata(fname: str) -> Dict[str, str]:
    base = os.path.splitext(fname)[0]
    year_match = re.search(r"(20\d{2})", base)
    company = base.split("-")[0] if "-" in base else base
    return {
        "file_name": fname,
        "company": company.lower(),
        "year": year_match.group(1) if year_match else "Unknown",
    }


def _configure_settings():
    Settings.embed_model = get_llamaindex_embedding()   # cached per process
    Settings.llm = make_llm(temperature=0.1)


def _load_documents(only_files: Optional[List[str]] = None):
    if not os.path.exists(RAW_DATA_DIR):
        raise ValueError(f"Raw data directory not found: {RAW_DATA_DIR}")
    kwargs = {"required_exts": list(DOC_EXTENSIONS)}
    if only_files is not None:
        if not only_files:
            return []
        kwargs["input_files"] = [os.path.join(RAW_DATA_DIR, f) for f in only_files]
    else:
        kwargs["input_dir"] = RAW_DATA_DIR
    documents = SimpleDirectoryReader(**kwargs).load_data()
    for doc in documents:
        fname = os.path.basename(doc.metadata.get("file_path", ""))
        doc.metadata.update(file_metadata(fname))
    return documents


def _indexed_files(index: VectorStoreIndex) -> set:
    return {
        (n.metadata or {}).get("file_name")
        for n in index.docstore.docs.values()
        if (n.metadata or {}).get("file_name")
    }


def _sync_index(index: VectorStoreIndex, monitor: MonitorAgent) -> None:
    """Insert any raw_data file that is not yet in the index, then persist."""
    missing = [f for f in list_raw_files(RAW_DATA_DIR) if f not in _indexed_files(index)]
    if not missing:
        return
    print(f"[RAGAgent] Indexing {len(missing)} new file(s): {missing}")
    for doc in _load_documents(only_files=missing):
        index.insert(doc)
    os.makedirs(PERSIST_DIR, exist_ok=True)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    monitor.log_health("RAGAgent", "UPDATED", f"Indexed {len(missing)} new file(s)")


def _build_index(monitor: MonitorAgent) -> VectorStoreIndex:
    documents = _load_documents()
    if not documents:
        raise ValueError("No documents found in raw_data for RAG.")
    index = VectorStoreIndex.from_documents(documents)
    os.makedirs(PERSIST_DIR, exist_ok=True)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    monitor.log_health("RAGAgent", "CREATED", f"Vector index created with {len(documents)} documents")
    return index


def _get_index(monitor: MonitorAgent) -> VectorStoreIndex:
    """Load the persisted index, building it from raw_data on first use."""
    global _index
    if _index is not None:
        return _index
    _configure_settings()
    try:
        if os.path.exists(PERSIST_DIR):
            storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
            _index = load_index_from_storage(storage_context)
            monitor.log_health("RAGAgent", "LOADED", "Vector index loaded from storage")
        else:
            _index = _build_index(monitor)
    except Exception as e:
        monitor.log_error("RAGAgent", f"Index initialization failed: {e}")
        _index = _build_index(monitor)
    _sync_index(_index, monitor)   # pick up files added since the index was built
    return _index


class RAGAgent:
    """Retrieve passages from the internal filings for a query."""

    # all-MiniLM-L6-v2 cosine scores for good matches sit around 0.4-0.65, so a
    # 0.7 cutoff (the old FinanceAgent default) filtered every node out.
    def __init__(self, similarity_cutoff: float = 0.3):
        self.monitor = MonitorAgent()
        self.raw_data_dir = RAW_DATA_DIR
        self.index = _get_index(self.monitor)
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=DEFAULT_TOP_K,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)],
        )

    # ---- reusable retrieval -------------------------------------------------

    def company_files(self, company: str) -> List[str]:
        needle = company.lower()
        return [f for f in list_raw_files(self.raw_data_dir) if needle in f.lower()]

    def retrieve(self, query: str, company: Optional[str] = None, k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """Top-k passages for the query, optionally restricted to one company's files.

        Returns dicts with file_name, company, year, content, score
        (higher score = closer match).
        """
        files = None
        if company:
            files = self.company_files(company)
            if not files:
                return []
        # Over-fetch when filtering so k survives the post-filter.
        retriever = self.index.as_retriever(similarity_top_k=k if files is None else k * 4)
        nodes = retriever.retrieve(query)
        passages = []
        for n in nodes:
            meta = n.metadata or {}
            if files is not None and meta.get("file_name") not in files:
                continue
            passages.append({
                "file_name": meta.get("file_name", "Unknown"),
                "company": meta.get("company", (company or "").lower()),
                "year": meta.get("year", "Unknown"),
                "content": n.text,
                "score": float(n.score) if n.score is not None else None,
            })
            if len(passages) >= k:
                break
        return passages

    # ---- agent contract -----------------------------------------------------

    def run(self, request: MCPRequest) -> MCPResponse:
        companies = request.context.companies or []
        user_query = request.context.user_query
        response_data: Any = []
        status = "processing"
        try:
            if companies:
                for company in companies:
                    files = self.company_files(company)
                    if not files:
                        continue
                    passages = self.retrieve(f"{company} {user_query}", company=company)
                    response_data.append({
                        "company": company,
                        "files": files,
                        "passages": [self._preview(p) for p in passages],
                    })
            else:
                response_data.append({
                    "query": user_query,
                    "passages": [self._preview(p) for p in self.retrieve(user_query)],
                })
            status = "success"
            self.monitor.log_health("RAGAgent", "SUCCESS", f"Retrieved for {len(companies)} companies")
        except Exception as e:
            status = "failed"
            response_data = {"error": str(e)}
            self.monitor.log_error("RAGAgent", str(e), {"companies": companies, "query": user_query})

        completed_time = datetime.now()
        return MCPResponse(
            request_id=request.request_id,
            data={"rag": response_data},
            context_updates={"last_rag_query": completed_time.isoformat()},
            status=status,
            timestamp=completed_time,
        )

    @staticmethod
    def _preview(passage: Dict[str, Any], limit: int = 1000) -> Dict[str, Any]:
        text = passage["content"]
        return {**passage, "content": text[:limit] + ("..." if len(text) > limit else "")}
