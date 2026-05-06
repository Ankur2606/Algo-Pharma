import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_global_logging():
    """Sets up a robust logger with both console and rotating file handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if called multiple times
    if root_logger.handlers:
        return

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    # Console handler — MUST use stderr; stdout is reserved for MCP JSONRPC
    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)
    
    # File handler (Rotating to prevent giant log files, max 10MB per file, keeps last 5)
    fh = RotatingFileHandler("algopharma.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)
