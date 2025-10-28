"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Configuration
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    app_host: str = Field(default="0.0.0.0", description="Application host")
    app_port: int = Field(default=8000, description="Application port")

    # Confluence Configuration
    confluence_url: str = Field(..., description="Confluence base URL")
    confluence_username: str = Field(..., description="Confluence username")
    confluence_api_token: str = Field(..., description="Confluence API token")
    confluence_space_keys: str = Field(
        default="", description="Comma-separated Confluence space keys"
    )
    confluence_labels: str = Field(
        default="", description="Comma-separated Confluence labels to filter"
    )

    # SMTP Configuration
    smtp_host: str = Field(default="0.0.0.0", description="SMTP server host")
    smtp_port: int = Field(default=1025, description="SMTP server port")
    smtp_allowed_senders: str = Field(
        ..., description="Comma-separated list of allowed email senders"
    )

    # ServiceNow Configuration
    servicenow_url: str = Field(..., description="ServiceNow instance URL")
    servicenow_username: str = Field(..., description="ServiceNow username")
    servicenow_password: str = Field(..., description="ServiceNow password")
    servicenow_api_version: str = Field(default="v1", description="ServiceNow API version")
    servicenow_assignment_group: str = Field(
        default="IT Support", description="Default assignment group"
    )
    servicenow_category: str = Field(default="Incident", description="Incident category")
    servicenow_urgency: int = Field(default=3, ge=1, le=5, description="Incident urgency (1-5)")
    servicenow_impact: int = Field(default=3, ge=1, le=5, description="Incident impact (1-5)")

    # LLM Configuration
    llm_provider: str = Field(default="ollama", description="LLM provider (ollama)")
    llm_model: str = Field(default="mistral:7b-instruct", description="LLM model name")
    llm_base_url: str = Field(default="http://ollama:11434", description="LLM base URL")
    llm_temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="LLM temperature"
    )
    llm_max_tokens: int = Field(default=512, ge=1, description="Maximum tokens for LLM response")
    llm_top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="LLM top-p sampling")
    llm_timeout: int = Field(default=120, ge=1, description="LLM request timeout in seconds")

    # Vector Database Configuration
    vectordb_type: str = Field(default="chromadb", description="Vector database type")
    vectordb_path: str = Field(default="/data/chromadb", description="Vector database path")
    vectordb_collection_name: str = Field(
        default="confluence_docs", description="Collection name"
    )
    vectordb_persist: bool = Field(default=True, description="Enable persistence")

    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model name"
    )
    embedding_device: str = Field(default="cpu", description="Device for embedding (cpu/cuda)")
    embedding_batch_size: int = Field(
        default=32, ge=1, description="Batch size for embedding generation"
    )

    # RAG Configuration
    rag_chunk_size: int = Field(default=800, ge=100, description="Text chunk size")
    rag_chunk_overlap: int = Field(default=200, ge=0, description="Chunk overlap size")
    rag_top_k_results: int = Field(default=5, ge=1, description="Number of top results to retrieve")
    rag_similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Similarity threshold"
    )
    rag_max_context_length: int = Field(
        default=2000, ge=100, description="Maximum context length for LLM"
    )

    # Retry Configuration
    retry_max_attempts: int = Field(default=3, ge=1, description="Maximum retry attempts")
    retry_wait_exponential_multiplier: int = Field(
        default=1, ge=1, description="Exponential backoff multiplier"
    )
    retry_wait_exponential_max: int = Field(
        default=10, ge=1, description="Maximum wait time for exponential backoff"
    )

    # Microsoft Teams Configuration
    teams_webhook_url: str = Field(
        default="", description="Microsoft Teams webhook URL for notifications"
    )
    teams_enabled: bool = Field(
        default=False, description="Enable Microsoft Teams notifications"
    )

    # Mock Services Configuration
    use_mock_services: bool = Field(default=True, description="Use mock services for testing")
    mock_confluence_port: int = Field(default=8001, description="Mock Confluence API port")
    mock_servicenow_port: int = Field(default=8002, description="Mock ServiceNow API port")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v_upper

    @field_validator("embedding_device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate device."""
        allowed_devices = {"cpu", "cuda", "mps"}
        v_lower = v.lower()
        if v_lower not in allowed_devices:
            raise ValueError(f"embedding_device must be one of {allowed_devices}")
        return v_lower

    @property
    def confluence_spaces_list(self) -> List[str]:
        """Get Confluence space keys as a list."""
        if not self.confluence_space_keys:
            return []
        return [s.strip() for s in self.confluence_space_keys.split(",") if s.strip()]

    @property
    def confluence_labels_list(self) -> List[str]:
        """Get Confluence labels as a list."""
        if not self.confluence_labels:
            return []
        return [label.strip() for label in self.confluence_labels.split(",") if label.strip()]

    @property
    def smtp_allowed_senders_list(self) -> List[str]:
        """Get allowed email senders as a list."""
        return [sender.strip().lower() for sender in self.smtp_allowed_senders.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
