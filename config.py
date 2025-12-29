"""Configuration management for FinChat Global.

Environment variables override defaults. Use .env for local development.
"""
from dataclasses import dataclass
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Embedding / chunk settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1200"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "250"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))

    # Paths
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    VECTOR_DB_DIR: str = os.getenv("VECTOR_DB_DIR", "./vector_db")

    # LLM settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    # Cache / Redis
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # Rate limiting
    RATE_LIMIT_PER_MIN: int = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))

    # Misc
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1","true","yes")


config = Config()
