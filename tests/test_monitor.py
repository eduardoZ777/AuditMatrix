import time
import threading
import pytest
from typing import List
from app.monitor import LogMonitor
from app.parser import ErrorParser
from app.repository import AuditRepository
from app.models import ParsedErrorLog

class MockRepository(AuditRepository):
    """Simple mock repository to inspect saved entries during test."""
    
    def __init__(self) -> None:
        self.saved_entries: List[ParsedErrorLog] = []

    def save(self, entry: ParsedErrorLog) -> None:
        self.saved_entries.append(entry)

    def get_all(self) -> List[ParsedErrorLog]:
        return self.saved_entries


def test_log_monitor_loop(tmp_path: pytest.TempPathFactory) -> None:
    """Verifies that the log monitor detects appended error lines in real-time using threading."""
    source_log = tmp_path / "sistema.log"
    
    # Create the initial source log file with a non-error line
    with open(source_log, "w", encoding="utf-8") as f:
        f.write("2026-06-04 12:00:00 [INFO] [App] [Main] - Application bootstrapped\n")

    repo = MockRepository()
    parser = ErrorParser()

    # Set read_from_start to True and poll_interval to 0.05 seconds for fast test execution
    monitor = LogMonitor(
        log_source_path=str(source_log),
        repository=repo,
        parser=parser,
        poll_interval=0.05,
        read_from_start=True
    )

    # Launch monitor thread in the background
    monitor_thread = threading.Thread(target=monitor.start)
    monitor_thread.daemon = True
    monitor_thread.start()

    # Allow thread to start and seek positions
    time.sleep(0.1)

    # Append an error line
    with open(source_log, "a", encoding="utf-8") as f:
        f.write("2026-06-04 12:01:00 [ERROR] [ERPMain] [DBConnection] - SQL Server Timeout\n")
        f.flush()

    # Allow the monitor to pick up and process the change
    time.sleep(0.2)

    # Gracefully stop the monitor loop and join the thread
    monitor.stop()
    monitor_thread.join(timeout=1.0)

    # Assertions
    assert len(repo.saved_entries) == 1
    captured = repo.saved_entries[0]
    assert captured.nome_programa == "ERPMain"
    assert captured.modulo_sistema == "DBConnection"
    assert captured.mensagem_erro == "SQL Server Timeout"
    assert captured.level == "ERROR"
