import logging
import os
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from app.config import settings
from app.models import ParsedErrorLog

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
    """Saves audited logs to daily rotating flat text files."""

    def __init__(self, filepath: Optional[str] = None) -> None:
        # Resolve target logs directory from filepath configuration
        path = filepath or settings.AUDIT_TEXT_PATH
        self.log_dir = os.path.dirname(path) or "logs"
        os.makedirs(self.log_dir, exist_ok=True)

        # Allow static file writing only for isolated unit testing
        self.is_static = False
        if filepath and (
            "test" in os.path.basename(filepath) or filepath.endswith("_test.txt")
        ):
            self.is_static = True
            self.static_path = filepath

        # Regex to parse the saved logs back if requested
        self.read_pattern = re.compile(
            r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+\[(?P<nome_programa>[^\]]+)\]\s+\[(?P<modulo_sistema>[^\]]+)\]\s+->\s+(?P<mensagem_erro>.+)$"
        )

    def _get_filepath(self) -> str:
        """Dynamically generates the file path using the current local date."""
        if self.is_static:
            return self.static_path
        
        # Build daily audit filename dynamically, e.g. auditoria_2026-06-04.txt
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"auditoria_{date_str}.txt")

    def save(self, entry: ParsedErrorLog) -> None:
        formatted_entry = (
            f"[{entry.timestamp}] [{entry.level}] [{entry.nome_programa}] "
            f"[{entry.modulo_sistema}] -> {entry.mensagem_erro}"
        )
        
        target_path = self._get_filepath()

        # Concurrency safety: locking and retry mechanism for Windows environments
        max_retries = 5
        delay = 0.1
        for attempt in range(max_retries):
            try:
                with open(target_path, "a", encoding="utf-8") as f:
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
                        f"PermissionError: Failed to write to {target_path} after {max_retries} attempts."
                    )
                    raise e
                time.sleep(delay)

    def get_all(self) -> List[ParsedErrorLog]:
        """Retrieves all parsed error logs from all auditoria_*.txt files in the log directory."""
        if self.is_static:
            files_to_read = [self.static_path] if os.path.exists(self.static_path) else []
        else:
            if not os.path.exists(self.log_dir):
                return []
            # Find all matching files in the logs directory
            files_to_read = [
                os.path.join(self.log_dir, f)
                for f in os.listdir(self.log_dir)
                if f.startswith("auditoria_") and f.endswith(".txt")
            ]
            files_to_read.sort()  # Sort chronologically

        entries = []
        max_retries = 5
        delay = 0.1

        for filepath in files_to_read:
            for attempt in range(max_retries):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
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
                    break  # File read successfully, break retry loop and go to next file
                except PermissionError:
                    if attempt == max_retries - 1:
                        logger.error(f"PermissionError: Failed to read from {filepath}.")
                    time.sleep(delay)

        return entries


def get_repository() -> AuditRepository:
    """Factory function to build the rotating file repository."""
    # Since the project is purely a background daemon, we return the daily rotating repository
    return TextFileAuditRepository()
