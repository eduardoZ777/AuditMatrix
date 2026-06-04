import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional
from app.config import settings
from app.database import SessionLocal
from app.models import AuditLogEntry, ParsedErrorLog

logger = logging.getLogger(__name__)

class AuditRepository(ABC):
    """Abstract Repository pattern interface for Audited Logs."""

    @abstractmethod
    def save(self, entry: ParsedErrorLog) -> None:
        """Persist a parsed error log."""
        pass

    @abstractmethod
    def get_all(self) -> List[ParsedErrorLog]:
        """Retrieve all persisted error logs."""
        pass


class TextFileAuditRepository(AuditRepository):
    """Saves and loads audited logs to/from a structured flat text file."""

    def __init__(self, filepath: Optional[str] = None) -> None:
        self.filepath = filepath or settings.AUDIT_TEXT_PATH
        # Ensure directories exist
        dir_name = os.path.dirname(self.filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        # Regex to parse the saved logs back for the dashboard
        self.read_pattern = re.compile(
            r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+\[(?P<nome_programa>[^\]]+)\]\s+\[(?P<modulo_sistema>[^\]]+)\]\s+->\s+(?P<mensagem_erro>.+)$"
        )

    def save(self, entry: ParsedErrorLog) -> None:
        formatted_entry = (
            f"[{entry.timestamp}] [{entry.level}] [{entry.nome_programa}] "
            f"[{entry.modulo_sistema}] -> {entry.mensagem_erro}"
        )
        
        # Safe write with retry mechanism for Windows environment concurrency
        max_retries = 5
        delay = 0.1
        for attempt in range(max_retries):
            try:
                with open(self.filepath, "a", encoding="utf-8") as f:
                    try:
                        import portalocker
                        portalocker.lock(f, portalocker.LOCK_EX)
                    except ImportError:
                        pass
                    f.write(formatted_entry + "\n")
                    return
            except PermissionError as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"PermissionError: Failed to write to {self.filepath} after {max_retries} attempts."
                    )
                    raise e
                time.sleep(delay)

    def get_all(self) -> List[ParsedErrorLog]:
        if not os.path.exists(self.filepath):
            return []

        entries = []
        # Safe read with retry mechanism
        max_retries = 5
        delay = 0.1
        for attempt in range(max_retries):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    try:
                        import portalocker
                        portalocker.lock(f, portalocker.LOCK_SH)
                    except ImportError:
                        pass
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        match = self.read_pattern.match(line)
                        if match:
                            gd = match.groupdict()
                            entries.append(
                                ParsedErrorLog(
                                    timestamp=gd["timestamp"],
                                    level=gd["level"],
                                    nome_programa=gd["nome_programa"],
                                    modulo_sistema=gd["modulo_sistema"],
                                    mensagem_erro=gd["mensagem_erro"],
                                )
                            )
                return entries
            except PermissionError:
                if attempt == max_retries - 1:
                    logger.error(f"PermissionError: Failed to read from {self.filepath}.")
                    return []
                time.sleep(delay)
        return []


class SQLAlchemyAuditRepository(AuditRepository):
    """Saves and loads audited logs to/from a relational database using SQLAlchemy."""

    def __init__(self) -> None:
        # Tables are initialized externally or dynamically
        pass

    def save(self, entry: ParsedErrorLog) -> None:
        db_entry = AuditLogEntry.from_pydantic(entry)
        with SessionLocal() as session:
            try:
                session.add(db_entry)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to commit log entry to database: {e}")
                raise

    def get_all(self) -> List[ParsedErrorLog]:
        with SessionLocal() as session:
            try:
                db_entries = (
                    session.query(AuditLogEntry)
                    .order_by(AuditLogEntry.timestamp.desc())
                    .all()
                )
                return [
                    ParsedErrorLog(
                        timestamp=e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        level=e.level,
                        nome_programa=e.nome_programa,
                        modulo_sistema=e.modulo_sistema,
                        mensagem_erro=e.mensagem_erro,
                    )
                    for e in db_entries
                ]
            except Exception as e:
                logger.error(f"Failed to query log entries from database: {e}")
                return []


class CompositeAuditRepository(AuditRepository):
    """Composite pattern to write to multiple repositories simultaneously."""

    def __init__(self, repositories: List[AuditRepository]) -> None:
        self.repositories = repositories

    def save(self, entry: ParsedErrorLog) -> None:
        for repo in self.repositories:
            try:
                repo.save(entry)
            except Exception as e:
                logger.error(
                    f"Composite repository failed to save via {repo.__class__.__name__}: {e}"
                )

    def get_all(self) -> List[ParsedErrorLog]:
        # Returns from the first available repository
        for repo in self.repositories:
            try:
                return repo.get_all()
            except Exception as e:
                logger.error(
                    f"Composite repository failed to get_all via {repo.__class__.__name__}: {e}"
                )
        return []


def get_repository() -> AuditRepository:
    """Factory function to build the correct repository based on configuration."""
    mode = settings.AUDIT_STORAGE_MODE.lower()
    repos: List[AuditRepository] = []

    if mode in ("text", "both"):
        repos.append(TextFileAuditRepository())
    if mode in ("db", "both"):
        repos.append(SQLAlchemyAuditRepository())

    if not repos:
        # Fallback
        logger.warning(
            f"Invalid storage mode '{settings.AUDIT_STORAGE_MODE}'. Defaulting to 'text'."
        )
        return TextFileAuditRepository()

    if len(repos) == 1:
        return repos[0]

    return CompositeAuditRepository(repos)
