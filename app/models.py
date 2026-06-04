from datetime import datetime
from typing import Self
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# --- Pydantic Data Models (Validation & Serialization) ---

class ParsedErrorLog(BaseModel):
    """Pydantic model representing a structured and validated log error."""
    timestamp: str = Field(..., description="Date and time of the log event")
    level: str = Field(..., description="Log level (e.g. ERROR, Exception)")
    nome_programa: str = Field(..., description="Program/executable name")
    modulo_sistema: str = Field(..., description="Module or view name")
    mensagem_erro: str = Field(..., description="Exact error message details")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp can be parsed to ensure data consistency."""
        try:
            # We check if it can be parsed using one of the common formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    datetime.strptime(v, fmt)
                    return v
                except ValueError:
                    continue
            raise ValueError("Timestamp format not recognized")
        except Exception as e:
            raise ValueError(f"Invalid timestamp format: {e}")


# --- SQLAlchemy Database Models ---

class Base(DeclarativeBase):
    """SQLAlchemy base class."""
    pass


class AuditLogEntry(Base):
    """SQLAlchemy model mapping database schema for audited error entries."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    nome_programa: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    modulo_sistema: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    mensagem_erro: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )

    @classmethod
    def from_pydantic(cls, schema: ParsedErrorLog) -> Self:
        """Create a SQLAlchemy DB entry from a parsed Pydantic schema."""
        parsed_dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed_dt = datetime.strptime(schema.timestamp, fmt)
                break
            except ValueError:
                continue

        if not parsed_dt:
            # Fallback to current time if parsing fails unexpectedly
            parsed_dt = datetime.utcnow()

        return cls(
            timestamp=parsed_dt,
            level=schema.level,
            nome_programa=schema.nome_programa,
            modulo_sistema=schema.modulo_sistema,
            mensagem_erro=schema.mensagem_erro
        )
