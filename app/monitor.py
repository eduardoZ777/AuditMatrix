import logging
import os
import time
from typing import Optional
from app.parser import ErrorParser
from app.repository import AuditRepository

logger = logging.getLogger(__name__)

class LogMonitor:
    """Monitora um arquivo de log bruto em tempo real, realizando a filtragem e auditoria de falhas."""

    def __init__(
        self,
        log_source_path: str,
        repository: AuditRepository,
        parser: ErrorParser,
        poll_interval: float = 0.5,
        read_from_start: bool = False,
    ) -> None:
        self.log_source_path = os.path.abspath(log_source_path)
        self.repository = repository
        self.parser = parser
        self.poll_interval = poll_interval
        self.read_from_start = read_from_start
        self._running = False

    def stop(self) -> None:
        """Sinaliza para o loop de monitoramento encerrar."""
        logger.info("Encerrando monitor de log...")
        self._running = False

    def start(self) -> None:
        """Inicia o loop ativo de monitoramento do arquivo (polling)."""
        self._running = True
        logger.info(f"Serviço de monitoramento ativo. Escutando: {self.log_source_path}")

        # Certifica-se de que a pasta pai do log existe
        src_dir = os.path.dirname(self.log_source_path)
        if src_dir:
            os.makedirs(src_dir, exist_ok=True)

        # Aguarda a criação do arquivo de log caso ele não exista no boot
        while self._running and not os.path.exists(self.log_source_path):
            logger.warning(
                f"Arquivo de log original não encontrado. Aguardando criação: {self.log_source_path}"
            )
            time.sleep(2.0)

        if not self._running:
            return

        try:
            # Abre o arquivo original ignorando falhas de encoding unicode
            with open(self.log_source_path, "r", encoding="utf-8", errors="ignore") as f:
                if self.read_from_start:
                    logger.info("Lendo log original a partir do início (importação histórica).")
                    f.seek(0)
                    current_position = 0
                else:
                    logger.info("Movendo ponteiro para o final do log original (escuta ativa).")
                    f.seek(0, 2)
                    current_position = f.tell()

                while self._running:
                    # Verifica o status físico do arquivo (deletado, rotacionado, etc.)
                    try:
                        current_size = os.path.getsize(self.log_source_path)
                    except FileNotFoundError:
                        logger.warning("Log de origem desapareceu do disco. Entrando em modo de espera...")
                        f.close()
                        while self._running and not os.path.exists(self.log_source_path):
                            time.sleep(2.0)
                        if not self._running:
                            break
                        # Reabre o arquivo recém-criado
                        f = open(self.log_source_path, "r", encoding="utf-8", errors="ignore")
                        f.seek(0)
                        current_position = 0
                        continue

                    # Se o arquivo reduziu de tamanho, houve truncamento ou rotação (logrotate)
                    if current_size < current_position:
                        logger.info("O tamanho do log original diminuiu. Reiniciando ponteiro para o início.")
                        f.seek(0)
                        current_position = 0

                    line = f.readline()
                    if not line:
                        # Fim do arquivo alcançado. Aguarda novas linhas.
                        time.sleep(self.poll_interval)
                        continue

                    current_position = f.tell()

                    # Processa a nova linha detectada
                    try:
                        parsed = self.parser.parse_line(line)
                        if parsed:
                            logger.info(
                                f"Erro Capturado -> Programa: {parsed.nome_programa} | "
                                f"Módulo: {parsed.modulo_sistema}"
                            )
                            self.repository.save(parsed)
                    except Exception as e:
                        logger.error(f"Erro ao processar linha analisada: {e}", exc_info=True)

        except Exception as e:
            logger.critical(f"Falha fatal no monitoramento de logs: {e}", exc_info=True)
            raise
        finally:
            logger.info("Serviço de monitoramento de logs encerrado.")
