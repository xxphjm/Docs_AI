from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.db import ChromaDB


class Ingest:
    def __init__(self, pdf_path: str, collection_name: str):
        self.pdf_path = pdf_path
        self.collection_name = collection_name
        self.db = ChromaDB(collection_name=self.collection_name)

    def add_vector_db(self):
        loader = PyPDFLoader(self.pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = splitter.split_documents(docs)

        source_stem = Path(self.pdf_path).stem
        ids = [f"{source_stem}-{i}" for i in range(len(chunks))]
        documents = [Document(page_content=chunk.page_content, metadata=chunk.metadata) for chunk in chunks]
        self.db.add_documents(ids=ids, documents=documents)

        return


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[2] / "data"
    ingest = Ingest(pdf_path=str(data_dir / "sample.pdf"), collection_name="docs_ai")
    ingest.add_vector_db()
