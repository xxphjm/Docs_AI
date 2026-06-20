from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    NVIDIA_API_KEY: str
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "docs-ai"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    default_collection_name: str = "docs_ai"
    cors_origins: str = "http://localhost:5173"
    upload_dir: Path = ROOT_DIR / "backend" / "storage" / "uploads"
    chroma_dir: Path = ROOT_DIR / "chroma_db"

    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

