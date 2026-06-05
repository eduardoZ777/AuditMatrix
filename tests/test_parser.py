import pytest
from app.parser import ErrorParser
from app.models import ParsedErrorLog

def test_parser_valid_line() -> None:
    """Valida se uma linha de log correta correspondente ao formato regex é extraída com sucesso."""
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
    """Valida se o nível de erro do tipo 'Exception' é interpretado corretamente pelo parser."""
    line = "2026-06-04 12:05:00 [Exception] [BillingService] [InvoiceGen] - Connection timeout."
    parser = ErrorParser()
    parsed = parser.parse_line(line)

    assert parsed is not None
    assert parsed.level == "Exception"
    assert parsed.nome_programa == "BillingService"
    assert parsed.modulo_sistema == "InvoiceGen"
    assert parsed.mensagem_erro == "Connection timeout."

def test_parser_non_matching_line() -> None:
    """Valida se níveis que não sejam de erro (ex: INFO) são ignorados e retornam None."""
    line = "2026-06-04 12:00:00 [INFO] [ERPMain] [LoginView] - User admin logged in."
    parser = ErrorParser()
    parsed = parser.parse_line(line)

    assert parsed is None

def test_parser_empty_line() -> None:
    """Valida se linhas vazias ou com espaços retornam None."""
    parser = ErrorParser()
    assert parser.parse_line("") is None
    assert parser.parse_line("   \n") is None

def test_parser_invalid_regex_compilation() -> None:
    """Valida se a compilação de uma expressão regular malformada lança ValueError."""
    with pytest.raises(ValueError):
        ErrorParser(regex_pattern="[brackets sem fechamento")
