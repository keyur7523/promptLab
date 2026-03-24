"""Prompt version model for versioned system prompts."""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.database import Base


class PromptVersion(Base):
    """Versioned system prompt tied to an experiment variant."""

    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("variant", "version", name="uq_variant_version"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variant = Column(String(50), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<PromptVersion {self.variant} v{self.version} active={self.is_active}>"
