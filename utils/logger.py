import logging
import os
from datetime import datetime
from typing import Optional

def setup_logger(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    module_name: str = "followers_tracker"
) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        log_file: Path to the log file. If None, logs will only be printed to console.
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        module_name: Name to use for the logger.
        
    Returns:
        A configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Define formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Add timestamp to log filename if not already present
        if not any(c.isdigit() for c in os.path.basename(log_file)):
            filename, ext = os.path.splitext(log_file)
            log_file = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger