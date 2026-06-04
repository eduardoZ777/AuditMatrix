import logging
import os
import time
from typing import Optional
from app.parser import ErrorParser
from app.repository import AuditRepository

logger = logging.getLogger(__name__)

class LogMonitor:
    """Monitors a log file in real-time, parsing and auditing error logs."""

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
        """Signals the monitor loop to stop running."""
        logger.info("Stopping log monitor...")
        self._running = False

    def start(self) -> None:
        """Starts the real-time polling loop."""
        self._running = True
        logger.info(f"Log monitor service started. Tracking: {self.log_source_path}")

        # Ensure directory for source log exists
        src_dir = os.path.dirname(self.log_source_path)
        if src_dir:
            os.makedirs(src_dir, exist_ok=True)

        # Loop until file is created or stopped
        while self._running and not os.path.exists(self.log_source_path):
            logger.warning(
                f"Source log file not found. Waiting for creation: {self.log_source_path}"
            )
            time.sleep(2.0)

        if not self._running:
            return

        try:
            # Open source log file, ignoring encoding issues
            with open(self.log_source_path, "r", encoding="utf-8", errors="ignore") as f:
                if self.read_from_start:
                    logger.info("Reading source log from the beginning.")
                    f.seek(0)
                    current_position = 0
                else:
                    logger.info("Seeking to the end of the source log.")
                    f.seek(0, 2)
                    current_position = f.tell()

                while self._running:
                    # Check for file status (rotation, truncation, deletion)
                    try:
                        current_size = os.path.getsize(self.log_source_path)
                    except FileNotFoundError:
                        logger.warning("Source log file vanished. Re-initializing wait...")
                        f.close()
                        while self._running and not os.path.exists(self.log_source_path):
                            time.sleep(2.0)
                        if not self._running:
                            break
                        # Re-open the file
                        f = open(self.log_source_path, "r", encoding="utf-8", errors="ignore")
                        f.seek(0)
                        current_position = 0
                        continue

                    # If file shrank, it was truncated or rotated
                    if current_size < current_position:
                        logger.info("Source log file size decreased. Resetting pointer to start.")
                        f.seek(0)
                        current_position = 0

                    line = f.readline()
                    if not line:
                        # End of file reached. Sleep and poll again.
                        time.sleep(self.poll_interval)
                        continue

                    current_position = f.tell()

                    # Process the new log line
                    try:
                        parsed = self.parser.parse_line(line)
                        if parsed:
                            logger.info(
                                f"Captured Error -> Program: {parsed.nome_programa} | "
                                f"Module: {parsed.modulo_sistema}"
                            )
                            self.repository.save(parsed)
                    except Exception as e:
                        logger.error(f"Error processing parsed line: {e}", exc_info=True)

        except Exception as e:
            logger.critical(f"Unhandled exception in log monitor loop: {e}", exc_info=True)
            raise
        finally:
            logger.info("Log monitor loop terminated.")
