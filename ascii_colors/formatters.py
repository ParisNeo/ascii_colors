import os
import json
import inspect
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Type, List, cast
from ascii_colors.constants import LogLevel
from ascii_colors.utils import get_trace_exception, strip_ansi

class Formatter:
    """Base class for formatting log records into textual representations."""
    _style_mapping: Dict[str, Dict[str, Callable[[Dict[str, Any]], Any]]] = {
        '%': {
            'asctime': lambda r: r['timestamp'].strftime(r.get('datefmt', "%Y-%m-%d %H:%M:%S,%f")[:-3] if r.get('datefmt', '').endswith(',%f') else r.get('datefmt', "%Y-%m-%d %H:%M:%S")),
            'created': lambda r: r['timestamp'].timestamp(),
            'filename': lambda r: r['filename'],
            'funcName': lambda r: r['funcName'],
            'levelname': lambda r: r['levelname'],
            'levelno': lambda r: r['levelno'],
            'lineno': lambda r: r['lineno'],
            'message': lambda r: r['message'],
            'module': lambda r: Path(r['pathname']).stem if r['pathname'] != 'N/A' else 'N/A',
            'msecs': lambda r: int(r['timestamp'].microsecond / 1000),
            'name': lambda r: r.get('name', 'root'),
            'pathname': lambda r: r['pathname'],
            'process': lambda r: os.getpid(),
            'processName': lambda r: threading.current_thread().name,
            'relativeCreated': lambda r: (r['timestamp'] - r.get('_initial_timestamp', r['timestamp'])).total_seconds() * 1000,
            'thread': lambda r: threading.get_ident(),
            'threadName': lambda r: threading.current_thread().name,
        },
        '{': {
            'asctime': lambda r: r['timestamp'].strftime(r.get('datefmt', "%Y-%m-%d %H:%M:%S,%f")[:-3] if r.get('datefmt', '').endswith(',%f') else r.get('datefmt', "%Y-%m-%d %H:%M:%S")),
        }
    }
    _initial_timestamp: datetime = datetime.now()

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style: str = '%', include_source: bool = False, **kwargs: Any):
        if style not in ('%', '{'): raise ValueError(f"Style must be '%' or '{{}}', not '{style}'")
        self.style, self.fmt, self.datefmt, self.include_source = style, fmt, datefmt or "%Y-%m-%d %H:%M:%S,%f", include_source
        self._kwargs = kwargs

    def _is_internal_frame(self, fname: str, func: str, pkg_dir: str) -> bool:
        """Determine if a frame is internal and should be skipped."""
        fname_lower = fname.lower()
        fname_norm = os.path.normcase(os.path.abspath(fname))
        
        # Check if it's from ascii_colors itself
        if fname_norm.startswith(os.path.dirname(pkg_dir)):
            return True
            
        # Check for common internal/logging function names
        if func in ('_log', 'format', 'handle', 'emit', 'debug', 'info', 'warning', 'error', 'critical', 'exception', 'log'):
            return True
            
        # Check for pytest/unittest internal patterns - these are specific to test frameworks
        if func.startswith('_call'):  # _callTestMethod, _callSetUp, etc.
            return True
            
        # Only skip underscore-prefixed functions if they're from test frameworks
        if func.startswith('_') and ('unittest' in fname_lower or 'pytest' in fname_lower or '_pytest' in fname_lower):
            return True
            
        # Skip __call__ only if from test framework files
        if func == '__call__' and ('unittest' in fname_lower or 'pytest' in fname_lower or '_pytest' in fname_lower):
            return True
            
        # Skip run/runTest only if from test frameworks
        if func in ('run', 'runTest') and ('unittest' in fname_lower or 'pytest' in fname_lower or '_pytest' in fname_lower):
            return True
            
        # Skip site-packages files (likely library code, not user code)
        if 'site-packages' in fname_lower:
            return True
            
        return False

    def _find_source_frame(self, start_frame) -> Tuple[str, int, str]:
        """Find the best source frame by walking up the stack.
        
        Returns (filename, lineno, funcName)
        """
        pkg_dir = os.path.dirname(os.path.normcase(os.path.abspath(__file__)))
        
        # First pass: look for test_ functions in test files - these are our best candidates
        frame = start_frame
        depth = 0
        while frame and depth < 50:
            fname = frame.f_code.co_filename
            func = frame.f_code.co_name
            
            # If this is a test function in a test file, use it immediately
            if func.startswith('test_') and 'test' in fname.lower():
                return (str(Path(fname).resolve()), frame.f_lineno, func)
                
            frame = frame.f_back
            depth += 1
        
        # Second pass: look for any non-internal frame
        frame = start_frame
        depth = 0
        while frame and depth < 50:
            fname = frame.f_code.co_filename
            func = frame.f_code.co_name
            
            if not self._is_internal_frame(fname, func, pkg_dir):
                return (str(Path(fname).resolve()), frame.f_lineno, func)
                
            frame = frame.f_back
            depth += 1
        
        # Fallback: use the original frame
        if start_frame:
            return (start_frame.f_code.co_filename, start_frame.f_lineno, start_frame.f_code.co_name)
        return ("N/A", 0, "N/A")

    def format(self, level: LogLevel, message: str, timestamp: datetime, exc_info: Optional[Tuple], logger_name: str = 'root', **kwargs: Any) -> str:
        level_name, level_no = level.name, level.value
        filename, lineno, funcName, pathname = "N/A", 0, "N/A", "N/A"
        
        if self.include_source:
            try:
                frame = inspect.currentframe()
                pathname, lineno, funcName = self._find_source_frame(frame)
                filename = Path(pathname).name if pathname != "N/A" else "N/A"
            except Exception:
                pass

        from ascii_colors.core import ASCIIColors
        log_record: Dict[str, Any] = {
            **ASCIIColors.get_thread_context(), **kwargs,
            "levelno": level_no, "levelname": level_name, "pathname": pathname, "filename": filename,
            "module": Path(pathname).stem if pathname != 'N/A' else 'N/A', "lineno": lineno, "funcName": funcName,
            "created": timestamp.timestamp(), "msecs": int(timestamp.microsecond / 1000),
            "relativeCreated": (timestamp - self._initial_timestamp).total_seconds() * 1000,
            "thread": threading.get_ident(), "threadName": threading.current_thread().name,
            "process": os.getpid(), "processName": threading.current_thread().name, "message": message, "name": logger_name,
            "timestamp": timestamp, "datefmt": self.datefmt, "_initial_timestamp": self._initial_timestamp,
            "asctime": timestamp.strftime(self.datefmt[:-3] if self.datefmt.endswith(',%f') else self.datefmt),
            "level_name": level_name, "level": level_no, "file_name": filename, "line_no": lineno, "func_name": funcName,
        }

        current_fmt = self.fmt or ("%(levelname)s:%(name)s:%(message)s" if self.style == '%' else "{levelname}:{name}:{message}")
        try:
            if self.style == '%':
                class RecordAccessor:
                    def __init__(self, rec): self._rec = rec
                    def __getitem__(self, key):
                        if key in Formatter._style_mapping['%']: return Formatter._style_mapping['%'][key](self._rec)
                        return self._rec[key]
                formatted_message = current_fmt % RecordAccessor(log_record)
            else: formatted_message = current_fmt.format(**log_record)
        except Exception as e: formatted_message = f"[FORMAT_ERROR: {e}]"

        if exc_info: formatted_message += "\n" + self.format_exception(exc_info)
        return formatted_message

    def format_exception(self, exc_info: Tuple) -> str:
        return get_trace_exception(exc_info[1]) if exc_info and exc_info[1] else ""

class JSONFormatter(Formatter):
    """Formats log records into JSON strings."""
    def __init__(self, fmt: Optional[Dict[str, str]] = None, datefmt: Optional[str] = None, style: str = '%', 
                 json_ensure_ascii: bool = False, json_indent: Optional[int] = None, json_separators: Optional[Tuple] = None, 
                 json_sort_keys: bool = False, include_fields: Optional[List[str]] = None, include_source: bool = False, **kwargs: Any):
        super().__init__(style=style, include_source=include_source)
        self.fmt_dict, self.include_fields, self.datefmt_str = fmt, include_fields, datefmt
        self._format_date = (lambda dt: dt.isoformat()) if datefmt is None or datefmt.lower() == "iso" else (lambda dt: dt.strftime(datefmt))
        self.json_ensure_ascii, self.json_indent, self.json_separators, self.json_sort_keys = json_ensure_ascii, json_indent, json_separators, json_sort_keys

    def format(self, level: LogLevel, message: str, timestamp: datetime, exc_info: Optional[Tuple], logger_name: str = 'root', **kwargs: Any) -> str:
        from ascii_colors.core import ASCIIColors
        filename, lineno, funcName, pathname = "N/A", 0, "N/A", "N/A"
        if self.include_source:
            try:
                frame = inspect.currentframe()
                pathname, lineno, funcName = self._find_source_frame(frame)
                filename = Path(pathname).name if pathname != "N/A" else "N/A"
            except Exception:
                pass

        log_record = {
            "levelno": level.value, "levelname": level.name, "asctime": self._format_date(timestamp), "timestamp": timestamp.timestamp(),
            "message": message, "name": logger_name, "pathname": pathname, "filename": filename, "lineno": lineno, "funcName": funcName,
            "module": Path(pathname).stem if pathname != 'N/A' else 'N/A', "process": os.getpid(), 
            "processName": threading.current_thread().name, "thread": threading.get_ident(), "threadName": threading.current_thread().name,
            **ASCIIColors.get_thread_context(), **kwargs
        }

        if exc_info:
            log_record["exc_info"] = self.format_exception(exc_info)
            log_record["exc_type"] = exc_info[0].__name__ if exc_info[0] else None
            log_record["exc_value"] = str(exc_info[1]) if exc_info[1] else None

        final_obj = {}
        if self.include_fields: final_obj = {k: v for k, v in log_record.items() if k in self.include_fields}
        elif self.fmt_dict:
            temp = Formatter(style=self.style, datefmt=self.datefmt_str)
            for key, f in self.fmt_dict.items():
                temp.fmt = f
                final_obj[key] = temp.format(level, "", timestamp, None, logger_name=logger_name, **log_record).split('\n')[0]
        else:
            final_obj = {k: log_record[k] for k in ["timestamp", "levelname", "name", "message", "filename", "lineno", "funcName"] if k in log_record}
            final_obj.update(ASCIIColors.get_thread_context()); final_obj.update(kwargs)
            if "exc_info" in log_record: final_obj["exc_info"] = log_record["exc_info"]

        return json.dumps(final_obj, default=str, ensure_ascii=self.json_ensure_ascii, indent=self.json_indent, separators=self.json_separators, sort_keys=self.json_sort_keys)
