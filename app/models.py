from datetime import datetime
from typing import Self
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# --- Modelos Pydantic (Validação e Serialização) ---

class ParsedErrorLog(BaseModel):
    """Modelo Pydantic que representa um log de erro estruturado e validado."""
    timestamp: str = Field(..., description="Data e hora do evento de log")
    level: str = Field(..., description="Nível do log (ex: ERROR, Exception)")
    nome_programa: str = Field(..., description="Nome do programa ou executável")
    modulo_sistema: str = Field(..., description="Nome do módulo, tela ou classe")
    mensagem_erro: str = Field(..., description="Mensagem exata e detalhes do erro")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Valida se o formato do timestamp é reconhecido para manter a consistência."""
        try:
            # Tenta converter usando formatos comuns de data e hora
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    datetime.strptime(v, fmt)
                    return v
                except ValueError:
                    continue
            raise ValueError("Formato de data e hora não reconhecido")
        except Exception as e:
            raise ValueError(f"Formato de timestamp inválido: {e}")


# --- Modelos de Banco de Dados SQLAlchemy ---

class Base(DeclarativeBase):
    """Classe base declarativa do SQLAlchemy."""
    pass


class AuditLogEntry(Base):
    """Modelo mapeado do SQLAlchemy para persistência no banco de dados de auditoria."""
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
        """Converte um schema Pydantic em uma entidade de banco do SQLAlchemy."""
        parsed_dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed_dt = datetime.strptime(schema.timestamp, fmt)
                break
            except ValueError:
                continue

        if not parsed_dt:
            # Fallback para o horário atual se a conversão falhar inesperadamente
            parsed_dt = datetime.utcnow()

        return cls(
            timestamp=parsed_dt,
            level=schema.level,
            nome_programa=schema.nome_programa,
            modulo_sistema=schema.modulo_sistema,
            mensagem_erro=schema.mensagem_erro
        )
