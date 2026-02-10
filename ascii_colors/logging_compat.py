import sys
import atexit
from typing import Any, Dict, List, Optional, Union
from ascii_colors.constants import LogLevel, DEBUG, WARNING, INFO
from ascii_colors.core import ASCIIColors
from ascii_colors.handlers import Handler, ConsoleHandler, FileHandler, StreamHandler
from ascii_colors.formatters import Formatter

_logger_cache: Dict[str, '_AsciiLoggerAdapter'] = {}

class _AsciiLoggerAdapter:
    def __init__(self, name: str): self.name = name
    def setLevel(self, level: Union[int, str]): ASCIIColors.set_log_level(_lvl(level))
    def addHandler(self, h: Handler): ASCIIColors.add_handler(h)
    def removeHandler(self, h: Handler): ASCIIColors.remove_handler(h)
    def debug(self, m: str, *a, **k): ASCIIColors._log(LogLevel.DEBUG, m, a, logger_name=self.name, **k)
    def info(self, m: str, *a, **k): ASCIIColors._log(LogLevel.INFO, m, a, logger_name=self.name, **k)
    def warning(self, m: str, *a, **k): ASCIIColors._log(LogLevel.WARNING, m, a, logger_name=self.name, **k)
    def error(self, m: str, *a, **k): ASCIIColors._log(LogLevel.ERROR, m, a, logger_name=self.name, **k)
    def critical(self, m: str, *a, **k): ASCIIColors._log(LogLevel.CRITICAL, m, a, logger_name=self.name, **k)
    def exception(self, m: str, *a, **k): k['exc_info'] = True; self.error(m, *a, **k)

def _lvl(l: Union[int, str]) -> int:
    if isinstance(l, int): return l
    return {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}.get(l.upper(), 30)

def getLogger(name: Optional[str] = None) -> _AsciiLoggerAdapter:
    n = name or "root"
    if n not in _logger_cache: _logger_cache[n] = _AsciiLoggerAdapter(n)
    return _logger_cache[n]

def basicConfig(**kwargs: Any) -> None:
    # Check if we should skip due to already being called or handlers already exist (unless force=True)
    force = kwargs.get('force', False)
    if not force:
        # Skip if basicConfig was already called OR if handlers already exist (via ASCIIColors API)
        if ASCIIColors._basicConfig_called or len(ASCIIColors._handlers) > 0:
            return
    
    ASCIIColors.clear_handlers()
    level = _lvl(kwargs.get('level', WARNING))
    ASCIIColors.set_log_level(level)
    f = Formatter(fmt=kwargs.get('format'), datefmt=kwargs.get('datefmt'), style=kwargs.get('style', '%'))
    
    if 'handlers' in kwargs:
        for h in kwargs['handlers']:
            if not h.formatter: h.setFormatter(f)
            ASCIIColors.add_handler(h)
    elif 'filename' in kwargs:
        h = FileHandler(kwargs['filename'], mode=kwargs.get('filemode', 'a'), formatter=f)
        ASCIIColors.add_handler(h)
    else:
        h = ConsoleHandler(stream=kwargs.get('stream'), level=level, formatter=f)
        ASCIIColors.add_handler(h)
    ASCIIColors._basicConfig_called = True

def shutdown():
    for h in ASCIIColors._handlers:
        try: h.close()
        except Exception: pass

atexit.register(shutdown)
