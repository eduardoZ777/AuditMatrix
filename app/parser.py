import logging
import re
from typing import Optional
from app.config import settings
from app.models import ParsedErrorLog

logger = logging.getLogger(__name__)

class ErrorParser:
    """Classe responsável por utilizar expressões regulares para extrair detalhes de linhas de log."""
    
    def __init__(self, regex_pattern: Optional[str] = None) -> None:
        pattern_str = regex_pattern or settings.LOG_PARSER_REGEX
        try:
            self.pattern = re.compile(pattern_str)
            logger.info("ErrorParser inicializado com sucesso com o padrão regex.")
        except re.error as e:
            logger.critical(f"Falha ao compilar o padrão regex: {e}. Padrão: {pattern_str}")
            raise ValueError(f"Padrão regex inválido: {e}") from e

    def parse_line(self, line: str) -> Optional[ParsedErrorLog]:
        """Processa uma única linha de log. Retorna ParsedErrorLog se corresponder e for válida, senão None."""
        stripped = line.strip()
        if not stripped:
            return None

        match = self.pattern.match(stripped)
        if not match:
            # Não é um log de erro ou não coincide com a estrutura esperada
            return None

        gd = match.groupdict()
        
        # Garante que os grupos de captura obrigatórios estão presentes no match da regex
        required_keys = {"timestamp", "nome_programa", "modulo_sistema", "mensagem_erro"}
        missing_keys = required_keys - gd.keys()
        if missing_keys:
            if settings.DEBUG:
                logger.warning(
                    f"Match da regex bem-sucedido, mas faltam grupos nomeados obrigatórios: {missing_keys}"
                )
            return None

        try:
            # nível de log pode assumir padrão se não estiver presente no regex
            level = gd.get("level", "ERROR")
            
            return ParsedErrorLog(
                timestamp=gd["timestamp"],
                level=level,
                nome_programa=gd["nome_programa"],
                modulo_sistema=gd["modulo_sistema"],
                mensagem_erro=gd["mensagem_erro"]
            )
        except Exception as e:
            if settings.DEBUG:
                logger.debug(
                    f"Falha ao validar os dados de log extraídos na linha: '{stripped}'. Erro: {e}"
                )
            return None
