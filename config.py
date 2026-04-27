"""Configuration management for the Resume Screening Agent."""

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class ScoringWeights:
    """Configurable weights for the multi-factor scoring system."""
    embeddings: float = 0.40
    required_skills: float = 0.35
    preferred_skills: float = 0.15
    experience: float = 0.10

    def validate(self):
        total = self.embeddings + self.required_skills + self.preferred_skills + self.experience
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total:.2f}")

    def as_dict(self):
        return {
            "Embeddings (semantic)": self.embeddings,
            "Required Skills": self.required_skills,
            "Preferred Skills": self.preferred_skills,
            "Experience": self.experience,
        }


@dataclass
class Config:
    """Application configuration."""

    # Embedding model
    embedding_model: str = "paraphrase-multilingual-mpnet-base-v2"

    # LLM settings
    llm_provider: str = "gemini"   # "gemini", "anthropic", "none"
    gemini_model: str = "gemini-2.0-flash"
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # API keys (read from environment)
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Processing limits
    max_pages: int = 5
    max_batch_size: int = 50

    # Scoring weights
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)

    @classmethod
    def from_env(cls) -> "Config":
        cfg = cls()
        cfg.google_api_key = os.getenv("GOOGLE_API_KEY")
        cfg.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if os.getenv("EMBEDDING_MODEL"):
            cfg.embedding_model = os.getenv("EMBEDDING_MODEL")
        return cfg
