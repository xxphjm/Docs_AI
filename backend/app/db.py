from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.app.util.embedding import EmbeddingFunction


_DB_DIR = Path(__file__).resolve().parents[2] / "chroma_db"


class ChromaDB:
    def __init__(self, collection_name: str = "docs_ai"):
        self.embeddings = EmbeddingFunction()
        self.collection = Chroma(
            collection_name=collection_name,
            persist_directory=str(_DB_DIR),
            embedding_function=self.embeddings,
        )

    def add_documents(self, ids: list[str], documents: list[Document]):
        self.collection.add_documents(documents=documents, ids=ids)

    def as_retriever(self, n_results: int = 5):
        return self.collection.as_retriever(search_kwargs={"k": n_results})

    def query(self, query: str, n_results: int = 5):
        return self.collection.similarity_search(query, k=n_results)

