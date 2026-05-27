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

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)

    # CORS — comma-separated origins read from env, default to local dev
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
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
    GOOGLE_MODEL: str = Field(default="gemini-1.5-flash")


settings = Settings()
