import chromadb
from config import CHROMA_HOST, CHROMA_PORT

def get_client():
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

def get_or_create_collection(name: str = "customer_context"):
    client = get_client()
    return client.get_or_create_collection(name=name)

def add_documents(documents: list[str], ids: list[str], metadatas: list[dict] = None):
    collection = get_or_create_collection()
    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas or [{} for _ in documents]
    )

def query_context(account_id: str, n_results: int = 3) -> list[str]:
    collection = get_or_create_collection()
    results = collection.query(
        query_texts=[account_id],
        n_results=n_results
    )
    if results and results["documents"]:
        return results["documents"][0]
    return []