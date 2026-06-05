import argparse
import logging
import os
import sys
from app.config import settings
from app.monitor import LogMonitor
from app.parser import ErrorParser
from app.repository import get_repository

def setup_logging(debug: bool) -> None:
    """Configura o sistema de logs internos do auditor (console e arquivo)."""
    level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    # Garante que a pasta de logs existe
    os.makedirs("logs", exist_ok=True)

    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Limpa handlers existentes
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Stream Handler (saída padrão do terminal)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(stream_handler)

    # File Handler para armazenar logs internos do monitor
    file_handler = logging.FileHandler("logs/monitor_service.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

def main() -> None:
    """Orquestrador principal da execução do daemon."""
    parser = argparse.ArgumentParser(
        description="AuditMatrix: Auditor de Erros em Tempo Real para Produção"
    )
    parser.add_argument(
        "--read-from-start",
        action="store_true",
        help="Audita o arquivo de log original a partir do início (importação de histórico)",
    )
    args = parser.parse_args()

    setup_logging(settings.DEBUG)
    logger = logging.getLogger("AuditMatrix.Main")

    logger.info("=========================================")
    logger.info("Monitor de Erros AuditMatrix Iniciando (Daemon)...")
    logger.info(f"Log Original Monitorado: {os.path.abspath(settings.LOG_SOURCE_PATH)}")
    logger.info(f"Pasta de Auditorias:     {os.path.dirname(settings.AUDIT_TEXT_PATH) or 'logs/'}")
    logger.info("=========================================")

    # Instancia as camadas principais
    try:
        error_parser = ErrorParser()
        repository = get_repository()
    except Exception as e:
        logger.critical(f"Falha ao carregar os componentes principais da aplicação: {e}", exc_info=True)
        sys.exit(1)

    # Inicializa o monitoramento
    monitor = LogMonitor(
        log_source_path=settings.LOG_SOURCE_PATH,
        repository=repository,
        parser=error_parser,
        read_from_start=args.read_from_start,
    )

    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("Encerramento do monitor solicitado pelo usuário (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"AuditMatrix interrompido devido a um erro inesperado: {e}")
        sys.exit(1)
    finally:
        monitor.stop()
        logger.info("Monitor AuditMatrix finalizado de forma limpa. Sistema offline.")

if __name__ == "__main__":
    main()
