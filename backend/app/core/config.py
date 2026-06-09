from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Sarthi API"

    # Auth Security
    JWT_SECRET: str = Field(default="sarthi-jwt-super-secret-key-2026")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)  # 24 hours

    # MongoDB Configuration
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = Field(default="sarthi")
    PARTNER_TRACK: str = Field(default="MongoDB")
    PARTNER_MCP_SERVER: str = Field(default="mongodb-mcp-server@latest")
    MONGODB_MCP_ENABLED: bool = Field(default=True)
    MONGODB_MCP_READ_ONLY: bool = Field(default=True)
    MONGODB_MCP_STARTUP_TIMEOUT_SECONDS: int = Field(default=15)

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)

    # CORS — allow all origins for development to prevent fetch failures
    CORS_ORIGINS: List[str] = Field(
        default=["*"]
    )

    # Frontend URL (used to build absolute links in notifications etc.)
    FRONTEND_URL: str = Field(default="http://localhost:3000")

    # GitHub — optional, required for Push-to-GitHub feature
    GITHUB_TOKEN: str = Field(default="")
    GITHUB_DEFAULT_ORG: str = Field(default="")

    # Nvidia NIM LLM Configurations
    NVIDIA_API_KEY: str = Field(default="")
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL: str = Field(default="meta/llama-3.3-70b-instruct")

    # OpenRouter LLM Configurations
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = Field(default="openai/gpt-oss-120b:free")

    # Groq LLM Configurations
    GROQ_API_KEY: str = Field(default="")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com/openai/v1")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")

    # Google LLM Configurations
    GOOGLE_API_KEY: str = Field(default="")
    GOOGLE_MODEL: str = Field(default="gemini-3-pro-preview")
    GOOGLE_FAST_MODEL: str = Field(default="gemini-3-flash-preview")
    GOOGLE_REASONING_MODEL: str = Field(default="gemini-3-pro-preview")

    # Google Cloud Vertex AI
    GCP_PROJECT_ID: str = Field(default="")
    GCP_LOCATION: str = Field(default="us-central1")


settings = Settings()

# Ensure the underlying google-genai SDK discovers the API key
import os
if settings.GCP_PROJECT_ID:
    os.environ["GEMINI_VERTEX_PROJECT"] = settings.GCP_PROJECT_ID
    os.environ["GEMINI_VERTEX_LOCATION"] = settings.GCP_LOCATION
elif settings.GOOGLE_API_KEY:
    os.environ["GEMINI_API_KEY"] = settings.GOOGLE_API_KEY
    os.environ["GOOGLE_GENAI_API_KEY"] = settings.GOOGLE_API_KEY
