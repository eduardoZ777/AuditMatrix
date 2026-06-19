import argparse
import logging
import os
import sys
from app.config import settings
from app.monitor import LogMonitor
from app.parser import ErrorParser
from app.repository import get_repository

def setup_logging(debug: bool, log_file_path: str = "logs/monitor_service.log") -> None:
    """Configura o sistema de logs para saída no console e em arquivo."""
    level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    # Garante que a pasta de logs exista com base no caminho fornecido
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Limpa os manipuladores existentes
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Manipulador de Fluxo (Console)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(stream_handler)

    # Manipulador de Arquivo para os logs internos do auditor
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

def main() -> None:
    """Orquestrador principal de execução."""
    parser = argparse.ArgumentParser(
        description="AuditMatrix: Auditor de Erros em Tempo Real"
    )
    parser.add_argument(
        "--read-from-start",
        action="store_true",
        help="Audita o log de origem desde o início em vez de acompanhar a partir do final",
    )
    args = parser.parse_args()

    # Busca o caminho do log nas configurações, usando um padrão caso não exista
    internal_log_path = getattr(settings, 'INTERNAL_LOG_PATH', 'logs/monitor_service.log')
    setup_logging(settings.DEBUG, internal_log_path)
    
    logger = logging.getLogger("AuditMatrix.Main")

    logger.info("=========================================")
    logger.info("Monitor de Erros AuditMatrix Iniciando (Daemon)...")
    logger.info(f"Arquivo de Log de Origem: {os.path.abspath(settings.LOG_SOURCE_PATH)}")
    
    # Define o diretório de armazenamento de forma mais segura
    storage_dir = os.path.dirname(settings.AUDIT_TEXT_PATH) or os.path.dirname(internal_log_path) or 'logs/'
    logger.info(f"Diretório de Armazenamento: {storage_dir}")
    logger.info("=========================================")

    # Instancia as Camadas Principais
    try:
        error_parser = ErrorParser()
        repository = get_repository()
    except Exception as e:
        logger.critical(f"Falha ao inicializar os componentes da aplicação: {e}", exc_info=True)
        sys.exit(1)

    # Inicializa o Monitor
    monitor = LogMonitor(
        log_source_path=settings.LOG_SOURCE_PATH,
        repository=repository,
        parser=error_parser,
        read_from_start=args.read_from_start,
    )

    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("Encerramento do Monitor AuditMatrix iniciado pelo usuário.")
    except Exception as e:
        logger.critical(f"O AuditMatrix falhou devido a uma exceção não tratada: {e}")
        sys.exit(1)
    finally:
        monitor.stop()
        logger.info("Monitor AuditMatrix parado corretamente. Sistema offline.")

if __name__ == "__main__":
    main()