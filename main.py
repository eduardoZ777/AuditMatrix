import argparse
import logging
import os
import sys
from app.config import settings
from app.monitor import LogMonitor
from app.parser import ErrorParser
from app.repository import get_repository

def setup_logging(debug: bool) -> None:
    """Configures system-wide logging to output to console and file."""
    level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    # Ensure logs folder exists
    os.makedirs("logs", exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Stream Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(stream_handler)

    # File Handler for the auditor's internal logs
    file_handler = logging.FileHandler("logs/monitor_service.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

def main() -> None:
    """Main execution orchestrator."""
    parser = argparse.ArgumentParser(
        description="AuditMatrix: Enterprise Real-Time Error Auditor"
    )
    parser.add_argument(
        "--read-from-start",
        action="store_true",
        help="Audit the source log from the beginning instead of tailing from the end",
    )
    args = parser.parse_args()

    setup_logging(settings.DEBUG)
    logger = logging.getLogger("AuditMatrix.Main")

    logger.info("=========================================")
    logger.info("AuditMatrix Error Monitor Starting (Daemon)...")
    logger.info(f"Source Log File: {os.path.abspath(settings.LOG_SOURCE_PATH)}")
    logger.info(f"Storage Dir:     {os.path.dirname(settings.AUDIT_TEXT_PATH) or 'logs/'}")
    logger.info("=========================================")

    # Instantiate Core Layers
    try:
        error_parser = ErrorParser()
        repository = get_repository()
    except Exception as e:
        logger.critical(f"Failed to bootstrap application components: {e}", exc_info=True)
        sys.exit(1)

    # Bootstrap the Monitor
    monitor = LogMonitor(
        log_source_path=settings.LOG_SOURCE_PATH,
        repository=repository,
        parser=error_parser,
        read_from_start=args.read_from_start,
    )

    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("AuditMatrix Monitor shutdown initiated by user.")
    except Exception as e:
        logger.critical(f"AuditMatrix crashed due to an unhandled exception: {e}")
        sys.exit(1)
    finally:
        monitor.stop()
        logger.info("AuditMatrix Monitor stopped cleanly. System offline.")

if __name__ == "__main__":
    main()
