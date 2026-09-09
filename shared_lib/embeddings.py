"""Process-wide, lazily built embedding models.

Every router constructs a fresh FinanceAgent per query. Building a
HuggingFace embedding model each time reloads the weights and makes
sentence-transformers re-check ~20 model files against huggingface.co,
which is slow and floods the log with httpx INFO lines. Cache the model
here so the download / freshness check happens once per process.
"""

import logging
import os

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# The per-request loggers are only interesting when debugging the Hub itself.
for _name in ("httpx", "httpcore", "huggingface_hub", "huggingface_hub.utils._http",
              "sentence_transformers", "transformers"):
    logging.getLogger(_name).setLevel(logging.WARNING)

_langchain_embeddings = None
_llamaindex_embedding = None


def get_langchain_embeddings():
    """LangChain ``HuggingFaceEmbeddings`` (used by the shared FinanceAgent)."""
    global _langchain_embeddings
    if _langchain_embeddings is None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        _langchain_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _langchain_embeddings


def get_llamaindex_embedding():
    """LlamaIndex ``HuggingFaceEmbedding`` (used by llamaindex_agents' FinanceAgent)."""
    global _llamaindex_embedding
    if _llamaindex_embedding is None:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        _llamaindex_embedding = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_NAME)
    return _llamaindex_embedding
