import pytest
from app.parser import ErrorParser
from app.models import ParsedErrorLog

def test_parser_valid_line() -> None:
    """Verifies that a valid log line matching the default regex is parsed correctly."""
    line = "2026-06-04 12:00:00 [ERROR] [ERPMain] [LoginView] - User authentication failed."
    parser = ErrorParser()
    parsed = parser.parse_line(line)

    assert parsed is not None
    assert parsed.timestamp == "2026-06-04 12:00:00"
    assert parsed.level == "ERROR"
    assert parsed.nome_programa == "ERPMain"
    assert parsed.modulo_sistema == "LoginView"
    assert parsed.mensagem_erro == "User authentication failed."

def test_parser_valid_exception_level() -> None:
    """Verifies that 'Exception' log level works in parser."""
    line = "2026-06-04 12:05:00 [Exception] [BillingService] [InvoiceGen] - Connection timeout."
    parser = ErrorParser()
    parsed = parser.parse_line(line)

    assert parsed is not None
    assert parsed.level == "Exception"
    assert parsed.nome_programa == "BillingService"
    assert parsed.modulo_sistema == "InvoiceGen"
    assert parsed.mensagem_erro == "Connection timeout."

def test_parser_non_matching_line() -> None:
    """Verifies that non-error levels (e.g. INFO) are filtered out and return None."""
    line = "2026-06-04 12:00:00 [INFO] [ERPMain] [LoginView] - User admin logged in."
    parser = ErrorParser()
    parsed = parser.parse_line(line)

    assert parsed is None

def test_parser_empty_line() -> None:
    """Verifies empty or spacing lines return None."""
    parser = ErrorParser()
    assert parser.parse_line("") is None
    assert parser.parse_line("   \n") is None

def test_parser_invalid_regex_compilation() -> None:
    """Verifies compiling an invalid regex pattern raises ValueError."""
    with pytest.raises(ValueError):
        ErrorParser(regex_pattern="[unclosed brackets")
