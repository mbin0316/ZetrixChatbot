from config import *
from langchain_ollama import OllamaEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedder = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

vector = embedder.embed_query('mean median household income 2022')
results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=vector,
    limit=5,
    with_payload=True,
    query_filter=Filter(
        must=[
            FieldCondition(key="metadata.state", match=MatchValue(value="Johor")),
            FieldCondition(key="metadata.year", match=MatchValue(value="2022")),
            FieldCondition(key="metadata.level", match=MatchValue(value="state")),
        ]
    )
)
for r in results.points:
    print(r.payload.get('page_content', ''))
    print()