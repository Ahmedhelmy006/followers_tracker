"""
Environment variables handler.

This module provides utility functions for managing environment variables,
validating their presence, and providing fallbacks.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

def load_env_file(env_path: Union[str, Path]) -> bool:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Path to the .env file.
        
    Returns:
        True if the file was loaded successfully, False otherwise.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Using default environment variables.")
        return False
    
    try:
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load .env file: {str(e)}")
        return False

def get_required_env_var(var_name: str) -> str:
    """
    Get a required environment variable.
    
    Args:
        var_name: The name of the environment variable.
        
    Returns:
        The value of the environment variable.
        
    Raises:
        ValueError: If the environment variable is not set.
    """
    value = os.getenv(var_name)
    if value is None:
        logger.error(f"Required environment variable {var_name} is not set")
        raise ValueError(f"Required environment variable {var_name} is not set")
    return value

def get_env_var(var_name: str, default: Any = None) -> Any:
    """
    Get an environment variable with a default fallback.
    
    Args:
        var_name: The name of the environment variable.
        default: The default value to use if the environment variable is not set.
        
    Returns:
        The value of the environment variable or the default value.
    """
    return os.getenv(var_name, default)

def validate_env_vars(required_vars: List[str]) -> bool:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names.
        
    Returns:
        True if all required variables are set, False otherwise.
    """
    missing_vars = []
    
    for var_name in required_vars:
        if os.getenv(var_name) is None:
            missing_vars.append(var_name)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def create_env_file_from_template(template_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    Create a new .env file from a template if it doesn't exist.
    
    Args:
        template_path: Path to the template file.
        output_path: Path where the new .env file should be created.
        
    Returns:
        True if the file was created successfully, False otherwise.
    """
    template_path = Path(template_path)
    output_path = Path(output_path)
    
    if output_path.exists():
        logger.info(f".env file already exists at {output_path}")
        return True
    
    if not template_path.exists():
        logger.error(f"Template file not found at {template_path}")
        return False
    
    try:
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the template content to the new file
        with template_path.open('r') as template_file:
            template_content = template_file.read()
        
        with output_path.open('w') as output_file:
            output_file.write(template_content)
        
        logger.info(f"Created .env file at {output_path} from template")
        return True
    except Exception as e:
        logger.error(f"Failed to create .env file: {str(e)}")
        return False