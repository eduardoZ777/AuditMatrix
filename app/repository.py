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
    """Interface abstrata do padrão Repository para logs de auditoria."""

    @abstractmethod
    def save(self, entry: ParsedErrorLog) -> None:
        """Salva/Persiste um log de erro validado."""
        pass

    @abstractmethod
    def get_all(self) -> List[ParsedErrorLog]:
        """Recupera todos os logs de erro gravados."""
        pass


class TextFileAuditRepository(AuditRepository):
    """Implementação física que salva logs em arquivos de texto locais com rotação diária."""

    def __init__(self, filepath: Optional[str] = None) -> None:
        # Resolve o diretório de destino a partir do arquivo configurado
        path = filepath or settings.AUDIT_TEXT_PATH
        self.log_dir = os.path.dirname(path) or "logs"
        os.makedirs(self.log_dir, exist_ok=True)

        # Permite uso de arquivos estáticos apenas em testes automatizados
        self.is_static = False
        if filepath and (
            "test" in os.path.basename(filepath) or filepath.endswith("_test.txt")
        ):
            self.is_static = True
            self.static_path = filepath

        # Regex para ler de volta e analisar os logs salvos
        self.read_pattern = re.compile(
            r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+\[(?P<nome_programa>[^\]]+)\]\s+\[(?P<modulo_sistema>[^\]]+)\]\s+->\s+(?P<mensagem_erro>.+)$"
        )

    def _get_filepath(self) -> str:
        """Gera o nome do arquivo dinamicamente com base na data local atual."""
        if self.is_static:
            return self.static_path
        
        # Constrói o nome do arquivo, ex: logs/auditoria_2026-06-04.txt
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"auditoria_{date_str}.txt")

    def save(self, entry: ParsedErrorLog) -> None:
        formatted_entry = (
            f"[{entry.timestamp}] [{entry.level}] [{entry.nome_programa}] "
            f"[{entry.modulo_sistema}] -> {entry.mensagem_erro}"
        )
        
        target_path = self._get_filepath()

        # Segurança de concorrência: mecanismos de locking e retentativa para Windows
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
                        f"PermissionError: Falha ao gravar em {target_path} após {max_retries} tentativas."
                    )
                    raise e
                time.sleep(delay)

    def get_all(self) -> List[ParsedErrorLog]:
        """Lê todos os logs de erro de todos os arquivos auditoria_*.txt na pasta."""
        if self.is_static:
            files_to_read = [self.static_path] if os.path.exists(self.static_path) else []
        else:
            if not os.path.exists(self.log_dir):
                return []
            # Lista arquivos correspondentes no diretório de logs
            files_to_read = [
                os.path.join(self.log_dir, f)
                for f in os.listdir(self.log_dir)
                if f.startswith("auditoria_") and f.endswith(".txt")
            ]
            files_to_read.sort()  # Ordena cronologicamente

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
                    break  # Leitura realizada com sucesso, quebra o loop de retentativas
                except PermissionError:
                    if attempt == max_retries - 1:
                        logger.error(f"PermissionError: Falha ao ler de {filepath}.")
                    time.sleep(delay)

        return entries


def get_repository() -> AuditRepository:
    """Função factory para instanciar o repositório de logs rotacionados."""
    return TextFileAuditRepository()
