import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, ParsedErrorLog
from app.repository import TextFileAuditRepository, SQLAlchemyAuditRepository
import app.repository

def test_text_file_repository(tmp_path: pytest.TempPathFactory) -> None:
    """Verifies that TextFileAuditRepository correctly writes logs to a text file and reads them back."""
    temp_file = tmp_path / "auditoria_test.txt"
    repo = TextFileAuditRepository(filepath=str(temp_file))

    log = ParsedErrorLog(
        timestamp="2026-06-04 12:00:00",
        level="ERROR",
        nome_programa="TestApp",
        modulo_sistema="TestMod",
        mensagem_erro="Something went wrong",
    )

    repo.save(log)

    # Check physical file contents
    assert os.path.exists(temp_file)
    with open(temp_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert (
        "[2026-06-04 12:00:00] [ERROR] [TestApp] [TestMod] -> Something went wrong"
        in content
    )

    # Test reading back
    loaded = repo.get_all()
    assert len(loaded) == 1
    assert loaded[0].nome_programa == "TestApp"
    assert loaded[0].modulo_sistema == "TestMod"
    assert loaded[0].mensagem_erro == "Something went wrong"

def test_sqlalchemy_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies SQLAlchemyAuditRepository using an in-memory SQLite engine to keep tests fast and isolated."""
    # Setup in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocalTest = sessionmaker(bind=engine)

    # Patch the global SessionLocal inside app.repository to use our test session factory
    monkeypatch.setattr(app.repository, "SessionLocal", SessionLocalTest)

    repo = SQLAlchemyAuditRepository()
    log = ParsedErrorLog(
        timestamp="2026-06-04 12:00:00",
        level="ERROR",
        nome_programa="DBTestApp",
        modulo_sistema="QueryMod",
        mensagem_erro="SQL execution error",
    )

    repo.save(log)

    loaded = repo.get_all()
    assert len(loaded) == 1
    assert loaded[0].nome_programa == "DBTestApp"
    assert loaded[0].modulo_sistema == "QueryMod"
    assert loaded[0].mensagem_erro == "SQL execution error"
