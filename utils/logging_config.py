import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10_000_000,  # 10MB
    backup_count: int = 5,
    format_str: Optional[str] = None
) -> None:
    """Setup application logging with both console and file handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for no file logging)
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        format_str: Custom log format string
    """
    if format_str is None:
        format_str = (
            "%(asctime)s | %(name)s | %(levelname)s | "
            "%(filename)s:%(lineno)d | %(message)s"
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log initial message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {level}")
    if log_file:
        logger.info(f"Log file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)

# Performance logger for OCR and API timing
def log_performance(operation: str, duration: float, **kwargs) -> None:
    """Log performance metrics for operations."""
    perf_logger = logging.getLogger("performance")
    extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    perf_logger.info(f"PERF | {operation} | {duration:.3f}s | {extra_info}")

# Error logger for detailed error reporting
def log_error_with_context(error: Exception, context: dict) -> None:
    """Log an error with additional context information."""
    error_logger = logging.getLogger("errors")
    context_str = " | ".join(f"{k}={v}" for k, v in context.items())
    error_logger.error(f"ERROR | {type(error).__name__}: {error} | {context_str}")