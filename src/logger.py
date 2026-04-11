"""
Logging Setup for the TTC System

This module configures logging to show messages both on screen and in a log file.
All system events are recorded here for debugging and analysis.
"""

import logging
import logging.handlers
from pathlib import Path
from config import LOGGING_CONFIG



def setup_logging(name: str, level: str = None) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    level = level or LOGGING_CONFIG["log_level"]
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if needed
    log_file = Path(LOGGING_CONFIG["log_file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Format
    formatter = logging.Formatter(LOGGING_CONFIG["log_format"])
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_file),
            maxBytes=LOGGING_CONFIG["max_log_size_mb"] * 1024 * 1024,
            backupCount=LOGGING_CONFIG["backup_count"]
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Module-level convenience function
def get_logger(name: str) -> logging.Logger:
    """Get or create a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging(name)
    return logger
