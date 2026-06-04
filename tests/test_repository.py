import os
from datetime import datetime
import pytest
from app.models import ParsedErrorLog
from app.repository import TextFileAuditRepository

def test_text_file_repository_static(tmp_path: pytest.TempPathFactory) -> None:
    """Verifies that TextFileAuditRepository works correctly with a static test filepath."""
    temp_file = tmp_path / "auditoria_test.txt"
    repo = TextFileAuditRepository(filepath=str(temp_file))

    log = ParsedErrorLog(
        timestamp="2026-06-04 12:00:00",
        level="ERROR",
        nome_programa="TestApp",
        modulo_sistema="TestMod",
        mensagem_erro="Static file write error",
    )

    repo.save(log)

    assert os.path.exists(temp_file)
    with open(temp_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert (
        "[2026-06-04 12:00:00] [ERROR] [TestApp] [TestMod] -> Static file write error"
        in content
    )

    loaded = repo.get_all()
    assert len(loaded) == 1
    assert loaded[0].nome_programa == "TestApp"
    assert loaded[0].mensagem_erro == "Static file write error"


def test_text_file_repository_rotation(tmp_path: pytest.TempPathFactory) -> None:
    """Verifies that TextFileAuditRepository dynamically creates daily-rotating log files."""
    # Point the repository to a temporary directory instead of a file
    repo = TextFileAuditRepository(filepath=os.path.join(str(tmp_path), "fake_auditoria.txt"))

    log = ParsedErrorLog(
        timestamp="2026-06-04 12:30:00",
        level="ERROR",
        nome_programa="RotatingApp",
        modulo_sistema="RotationMod",
        mensagem_erro="Rotated file write test",
    )

    repo.save(log)

    # Determine dynamic path: logs/auditoria_YYYY-MM-DD.txt
    date_str = datetime.now().strftime("%Y-%m-%d")
    expected_file = tmp_path / f"auditoria_{date_str}.txt"

    assert os.path.exists(expected_file)
    with open(expected_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert (
        "[2026-06-04 12:30:00] [ERROR] [RotatingApp] [RotationMod] -> Rotated file write test"
        in content
    )

    loaded = repo.get_all()
    assert len(loaded) == 1
    assert loaded[0].nome_programa == "RotatingApp"
    assert loaded[0].mensagem_erro == "Rotated file write test"
