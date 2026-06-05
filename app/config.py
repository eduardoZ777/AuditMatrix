import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configurações globais carregadas a partir de variáveis de ambiente (.env)."""
    LOG_SOURCE_PATH: str = Field(default="logs/sistema.log")
    AUDIT_TEXT_PATH: str = Field(default="logs/auditoria.txt")
    DATABASE_URL: str = Field(default="sqlite:///logs/auditoria.db")
    AUDIT_STORAGE_MODE: str = Field(default="both")  # Opções: "text", "db", "both"
    LOG_PARSER_REGEX: str = Field(
        default=r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s+\[(?P<level>ERROR|Exception)\]\s+\[(?P<nome_programa>[^\]]+)\]\s+\[(?P<modulo_sistema>[^\]]+)\]\s+-\s+(?P<mensagem_erro>.+)$"
    )
    DEBUG: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instancia a configuração singleton
settings = Settings()
