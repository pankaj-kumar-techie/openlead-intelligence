# OpenLead Intelligence - Logging Module

"""
Structured logging with file and console handlers.
Supports colored console output and rotating file logs.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import colorlog


class Logger:
    """Custom logger with file and console handlers."""
    
    _instances = {}
    
    def __new__(cls, name: str = "openlead", log_dir: Optional[Path] = None, 
                log_level: str = "INFO", log_to_file: bool = True, 
                log_to_console: bool = True):
        """Singleton pattern to avoid duplicate loggers."""
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str = "openlead", log_dir: Optional[Path] = None,
                 log_level: str = "INFO", log_to_file: bool = True,
                 log_to_console: bool = True):
        """
        Initialize logger with file and console handlers.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Enable file logging
            log_to_console: Enable console logging
        """
        # Avoid re-initialization
        if hasattr(self, '_initialized'):
            return
        
        self.name = name
        self.log_dir = log_dir or Path("logs")
        self.log_level = getattr(logging, log_level.upper())
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Add handlers
        if self.log_to_console:
            self._add_console_handler()
        
        if self.log_to_file:
            self._add_file_handler()
        
        self._initialized = True
    
    def _add_console_handler(self):
        """Add colored console handler."""
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        # Colored formatter
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """Add rotating file handler."""
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler (10MB per file, keep 5 backups)
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        
        # File formatter (more detailed)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)


def get_logger(name: str = "openlead", **kwargs) -> Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        **kwargs: Additional arguments for Logger initialization
    
    Returns:
        Logger instance
    """
    return Logger(name, **kwargs)


# Create default logger
default_logger = get_logger()


if __name__ == "__main__":
    # Test logging
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    try:
        1 / 0
    except Exception:
        logger.exception("An exception occurred")
