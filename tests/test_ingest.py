"""
test_ingest.py
==============
Ingest 類別的單元測試。

測試策略：使用 unittest.mock 模擬所有外部依賴
（PyPDFLoader、RecursiveCharacterTextSplitter、ChromaDB），
讓測試完全離線、不需要真實 PDF 檔案或資料庫。
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from backend.app.ingest import Ingest


class TestIngestInit(unittest.TestCase):
    """測試 Ingest.__init__ 初始化行為"""

    @patch("backend.app.ingest.ChromaDB")
    def test_init_stores_pdf_path(self, mock_chroma):
        """__init__ 應正確儲存 pdf_path"""
        ingest = Ingest(pdf_path="/fake/path.pdf", collection_name="test_col")
        self.assertEqual(ingest.pdf_path, "/fake/path.pdf")

    @patch("backend.app.ingest.ChromaDB")
    def test_init_stores_collection_name(self, mock_chroma):
        """__init__ 應正確儲存 collection_name"""
        ingest = Ingest(pdf_path="/fake/path.pdf", collection_name="my_collection")
        self.assertEqual(ingest.collection_name, "my_collection")

    @patch("backend.app.ingest.ChromaDB")
    def test_init_creates_chromadb_with_collection_name(self, mock_chroma):
        """__init__ 應以正確的 collection_name 初始化 ChromaDB"""
        Ingest(pdf_path="/fake/path.pdf", collection_name="my_collection")
        mock_chroma.assert_called_once_with(collection_name="my_collection")


class TestAddVectorDB(unittest.TestCase):
    """測試 Ingest.add_vector_db 核心流程"""

    def _make_fake_docs(self, n=3):
        """產生 n 個假 Document 物件"""
        docs = []
        for i in range(n):
            docs.append(
                Document(
                    page_content=f"這是第 {i} 頁的內容",
                    metadata={"source": "sample.pdf", "page": i},
                )
            )
        return docs

    @patch("backend.app.ingest.ChromaDB")
    @patch("backend.app.ingest.RecursiveCharacterTextSplitter")
    @patch("backend.app.ingest.PyPDFLoader")
    def test_loader_called_with_pdf_path(self, mock_loader_cls, mock_splitter_cls, mock_chroma):
        """add_vector_db 應以正確路徑呼叫 PyPDFLoader"""
        fake_docs = self._make_fake_docs(2)
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = fake_docs
        mock_loader_cls.return_value = mock_loader_instance

        mock_splitter_instance = MagicMock()
        mock_splitter_instance.split_documents.return_value = fake_docs
        mock_splitter_cls.return_value = mock_splitter_instance

        ingest = Ingest(pdf_path="/fake/doc.pdf", collection_name="col")
        ingest.add_vector_db()

        mock_loader_cls.assert_called_once_with("/fake/doc.pdf")

    @patch("backend.app.ingest.ChromaDB")
    @patch("backend.app.ingest.RecursiveCharacterTextSplitter")
    @patch("backend.app.ingest.PyPDFLoader")
    def test_splitter_called_with_correct_params(self, mock_loader_cls, mock_splitter_cls, mock_chroma):
        """add_vector_db 應使用正確的 chunk_size 和 chunk_overlap 建立 splitter"""
        fake_docs = self._make_fake_docs(1)
        mock_loader_cls.return_value.load.return_value = fake_docs
        mock_splitter_cls.return_value.split_documents.return_value = fake_docs

        ingest = Ingest(pdf_path="/fake/doc.pdf", collection_name="col")
        ingest.add_vector_db()

        mock_splitter_cls.assert_called_once_with(chunk_size=1000, chunk_overlap=200)

    @patch("backend.app.ingest.ChromaDB")
    @patch("backend.app.ingest.RecursiveCharacterTextSplitter")
    @patch("backend.app.ingest.PyPDFLoader")
    def test_add_documents_called_with_correct_ids_and_documents(
        self, mock_loader_cls, mock_splitter_cls, mock_chroma_cls
    ):
        """add_vector_db 應將正確的 ids 與 Document 物件傳入 db.add_documents"""
        fake_chunks = self._make_fake_docs(3)
        mock_loader_cls.return_value.load.return_value = fake_chunks
        mock_splitter_cls.return_value.split_documents.return_value = fake_chunks

        mock_db = MagicMock()
        mock_chroma_cls.return_value = mock_db

        ingest = Ingest(pdf_path="/fake/doc.pdf", collection_name="col")
        ingest.add_vector_db()

        expected_ids = ["doc-0", "doc-1", "doc-2"]
        expected_documents = fake_chunks
        mock_db.add_documents.assert_called_once_with(ids=expected_ids, documents=expected_documents)

    @patch("backend.app.ingest.ChromaDB")
    @patch("backend.app.ingest.RecursiveCharacterTextSplitter")
    @patch("backend.app.ingest.PyPDFLoader")
    def test_ids_are_sequential_strings(self, mock_loader_cls, mock_splitter_cls, mock_chroma):
        """ids 應為從 '0' 開始的連續字串"""
        n = 5
        fake_chunks = self._make_fake_docs(n)
        mock_loader_cls.return_value.load.return_value = fake_chunks
        mock_splitter_cls.return_value.split_documents.return_value = fake_chunks

        mock_db = MagicMock()
        mock_chroma.return_value = mock_db

        ingest = Ingest(pdf_path="/fake/doc.pdf", collection_name="col")
        ingest.add_vector_db()

        actual_ids = mock_db.add_documents.call_args.kwargs["ids"]
        self.assertEqual(actual_ids, [f"doc-{i}" for i in range(n)])

    @patch("backend.app.ingest.ChromaDB")
    @patch("backend.app.ingest.RecursiveCharacterTextSplitter")
    @patch("backend.app.ingest.PyPDFLoader")
    def test_single_chunk_still_works(self, mock_loader_cls, mock_splitter_cls, mock_chroma):
        """只有一個 chunk 時，流程仍應正常執行"""
        fake_chunks = self._make_fake_docs(1)
        mock_loader_cls.return_value.load.return_value = fake_chunks
        mock_splitter_cls.return_value.split_documents.return_value = fake_chunks

        mock_db = MagicMock()
        mock_chroma.return_value = mock_db

        ingest = Ingest(pdf_path="/fake/doc.pdf", collection_name="col")
        ingest.add_vector_db()

        mock_db.add_documents.assert_called_once()

    @patch("backend.app.ingest.ChromaDB")
    @patch("backend.app.ingest.RecursiveCharacterTextSplitter")
    @patch("backend.app.ingest.PyPDFLoader")
    def test_page_content_extracted_from_chunks(self, mock_loader_cls, mock_splitter_cls, mock_chroma):
        """documents 清單應保留 LangChain Document 物件"""
        fake_chunks = self._make_fake_docs(2)
        mock_loader_cls.return_value.load.return_value = fake_chunks
        mock_splitter_cls.return_value.split_documents.return_value = fake_chunks

        mock_db = MagicMock()
        mock_chroma.return_value = mock_db

        ingest = Ingest(pdf_path="/fake/doc.pdf", collection_name="col")
        ingest.add_vector_db()

        actual_documents = mock_db.add_documents.call_args.kwargs["documents"]
        for doc in actual_documents:
            self.assertIsInstance(doc, Document)


if __name__ == "__main__":
    unittest.main(verbosity=2)
