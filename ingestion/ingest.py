"""
ingest.py — DOSM Household Income ingestion pipeline (Ollama version)
Run: python ingest.py
Requires: ollama pull nomic-embed-text  (run once before ingesting)
"""

import os
import sys
import logging
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import (
    OLLAMA_BASE_URL, EMBEDDING_MODEL, EMBEDDING_DIM,
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    DATASETS_DIR, CHUNK_SIZE, CHUNK_OVERLAP,
)
from converters import FILE_CONVERTERS

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


def load_docs():
    """Read all CSVs → list of LangChain Documents."""
    docs = []
    for filename, converter in FILE_CONVERTERS.items():
        path = os.path.join(DATASETS_DIR, filename)
        if not os.path.exists(path):
            log.warning(f"Missing: {path} — skipping")
            continue
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            try:
                docs.append(converter(row))
            except Exception as e:
                log.warning(f"Skipped row in {filename}: {e}")
        log.info(f"  {filename}: {len(df)} rows loaded")
    log.info(f"Total documents: {len(docs)}")
    return docs


def chunk(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    log.info(f"Chunks after splitting: {len(chunks)}")
    return chunks


def setup_collection(client):
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        log.info(f"Dropping existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )
    log.info(f"Created collection: {COLLECTION_NAME}")
    
    # Add payload indexes for metadata filtering
    from qdrant_client.models import PayloadSchemaType
    client.create_payload_index(COLLECTION_NAME, "metadata.state", PayloadSchemaType.KEYWORD)
    client.create_payload_index(COLLECTION_NAME, "metadata.year",  PayloadSchemaType.KEYWORD)
    client.create_payload_index(COLLECTION_NAME, "metadata.level", PayloadSchemaType.KEYWORD)
    log.info("Payload indexes created for state, year, level.")

def embed_and_store(chunks):
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    setup_collection(client)

    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    log.info(f"Embedding {len(chunks)} chunks with {EMBEDDING_MODEL} → Qdrant ...")
    log.info("This may take a few minutes on first run (fully local, no API calls).")

    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY or None,
        collection_name=COLLECTION_NAME,
    )
    log.info("Upload complete.")
    return vectorstore


def smoke_test(vectorstore):
    log.info("Running smoke test...")
    queries = [
        "Malaysia national median income 2022",
        "highest income state 2022",
        "Johor Bahru district income",
    ]
    for q in queries:
        results = vectorstore.similarity_search(q, k=2)
        log.info(f"  Q: {q}")
        for r in results:
            log.info(f"    → {r.page_content[:100]}")


def main():
    log.info(f"Using Ollama at {OLLAMA_BASE_URL}")
    log.info(f"Embedding model : {EMBEDDING_MODEL}")

    docs   = load_docs()
    if not docs:
        log.error("No documents loaded. Check your datasets/ folder.")
        sys.exit(1)

    chunks = chunk(docs)
    vs     = embed_and_store(chunks)
    smoke_test(vs)
    log.info("Done. Vector store is ready for n8n.")


if __name__ == "__main__":
    main()