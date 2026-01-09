"""Experiment model."""
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.database import Base


class Experiment(Base):
    """A/B experiment configuration."""

    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    variants = Column(JSONB, nullable=False)  # {"control": 50, "variant_a": 30, "variant_b": 20}
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Experiment {self.key} active={self.active}>"
