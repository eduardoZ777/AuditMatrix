import logging
import re
from typing import Optional
from app.config import settings
from app.models import ParsedErrorLog

logger = logging.getLogger(__name__)

class ErrorParser:
    """Uses regular expressions to extract structured details from raw log lines."""
    
    def __init__(self, regex_pattern: Optional[str] = None) -> None:
        pattern_str = regex_pattern or settings.LOG_PARSER_REGEX
        try:
            self.pattern = re.compile(pattern_str)
            logger.info("ErrorParser initialized successfully with pattern.")
        except re.error as e:
            logger.critical(f"Failed to compile regex pattern: {e}. Pattern: {pattern_str}")
            raise ValueError(f"Invalid regex pattern: {e}") from e

    def parse_line(self, line: str) -> Optional[ParsedErrorLog]:
        """Parses a single log line. Returns ParsedErrorLog if matched and validated, else None."""
        stripped = line.strip()
        if not stripped:
            return None

        match = self.pattern.match(stripped)
        if not match:
            # Not an error log or did not match the structure
            return None

        gd = match.groupdict()
        
        # Verify required group keys are present in match
        required_keys = {"timestamp", "nome_programa", "modulo_sistema", "mensagem_erro"}
        missing_keys = required_keys - gd.keys()
        if missing_keys:
            if settings.DEBUG:
                logger.warning(
                    f"Regex match successful but missing required named groups: {missing_keys}"
                )
            return None

        try:
            # level can be defaulted if not present in regex
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
                    f"Failed to validate parsed log data from line: '{stripped}'. Error: {e}"
                )
            return None
