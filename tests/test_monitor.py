import time
import threading
import pytest
from typing import List
from app.monitor import LogMonitor
from app.parser import ErrorParser
from app.repository import AuditRepository
from app.models import ParsedErrorLog

class MockRepository(AuditRepository):
    """Mecanismo mock simples para inspecionar os logs gravados durante os testes."""
    
    def __init__(self) -> None:
        self.saved_entries: List[ParsedErrorLog] = []

    def save(self, entry: ParsedErrorLog) -> None:
        self.saved_entries.append(entry)

    def get_all(self) -> List[ParsedErrorLog]:
        return self.saved_entries


def test_log_monitor_loop(tmp_path: pytest.TempPathFactory) -> None:
    """Valida se o monitor captura e processa logs adicionados dinamicamente ao arquivo em tempo real."""
    source_log = tmp_path / "sistema.log"
    
    # Cria o arquivo de log original com uma linha de informação inicial
    with open(source_log, "w", encoding="utf-8") as f:
        f.write("2026-06-04 12:00:00 [INFO] [App] [Main] - Application bootstrapped\n")

    repo = MockRepository()
    parser = ErrorParser()

    # Define o monitor com intervalo rápido de polling (0.05s) para acelerar a execução do teste
    monitor = LogMonitor(
        log_source_path=str(source_log),
        repository=repo,
        parser=parser,
        poll_interval=0.05,
        read_from_start=True
    )

    # Inicia a thread em background para rodar o monitor
    monitor_thread = threading.Thread(target=monitor.start)
    monitor_thread.daemon = True
    monitor_thread.start()

    # Aguarda a inicialização da thread do monitor
    time.sleep(0.1)

    # Simula a inserção de um erro gerado pelo ERP original
    with open(source_log, "a", encoding="utf-8") as f:
        f.write("2026-06-04 12:01:00 [ERROR] [ERPMain] [DBConnection] - SQL Server Timeout\n")
        f.flush()

    # Aguarda o polling capturar a alteração
    time.sleep(0.2)

    # Encerra o monitor graciosamente
    monitor.stop()
    monitor_thread.join(timeout=1.0)

    # Asserções finais
    assert len(repo.saved_entries) == 1
    captured = repo.saved_entries[0]
    assert captured.nome_programa == "ERPMain"
    assert captured.modulo_sistema == "DBConnection"
    assert captured.mensagem_erro == "SQL Server Timeout"
    assert captured.level == "ERROR"
