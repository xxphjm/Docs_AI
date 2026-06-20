from langchain_core.embeddings import Embeddings
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from backend.app.util.setting import Settings


settings = Settings()


class EmbeddingFunction(Embeddings):
    def __init__(self):
        self.embedding_function = NVIDIAEmbeddings(
            model="nvidia/nv-embed-v1",
            api_key=settings.NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1",
        )

    def embed_query(self, text: str):
        return self.embedding_function.embed_query(text)

    def embed_documents(self, texts):
        return self.embedding_function.embed_documents(texts)

    def get_embedding(self, text: str):
        return self.embed_query(text)

    def get_embeddings(self, texts):
        return self.embed_documents(texts)
