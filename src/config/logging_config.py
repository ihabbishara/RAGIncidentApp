"""Logging configuration using loguru."""

import sys
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from .settings import Settings


def setup_logging(settings: Settings) -> None:
    """
    Configure loguru logger with appropriate settings.

    Args:
        settings: Application settings
    """
    # Remove default handler
    logger.remove()

    # Console handler with formatting
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler with rotation
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger.add(
        logs_dir / "rag_incident_{time:YYYY-MM-DD}.log",
        format=log_format,
        level=settings.log_level,
        rotation="00:00",  # Rotate at midnight
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress rotated logs
        backtrace=True,
        diagnose=True,
    )

    # Error-specific log file
    logger.add(
        logs_dir / "errors_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",  # Keep error logs longer
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logging configured with level: {settings.log_level}")
    logger.info(f"Environment: {settings.environment}")


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Log function call with parameters.

    Args:
        func_name: Name of the function
        **kwargs: Function parameters to log
    """
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


def log_api_request(method: str, url: str, **kwargs: Any) -> None:
    """
    Log API request details.

    Args:
        method: HTTP method
        url: Request URL
        **kwargs: Additional request parameters
    """
    logger.info(f"API Request: {method} {url}")
    if kwargs:
        logger.debug(f"Request params: {kwargs}")


def log_api_response(status_code: int, url: str, response_time: float) -> None:
    """
    Log API response details.

    Args:
        status_code: HTTP status code
        url: Request URL
        response_time: Response time in seconds
    """
    level = "INFO" if 200 <= status_code < 300 else "WARNING"
    logger.log(level, f"API Response: {status_code} {url} ({response_time:.2f}s)")


def log_error(error: Exception, context: Dict[str, Any] | None = None) -> None:
    """
    Log error with context.

    Args:
        error: Exception to log
        context: Additional context information
    """
    logger.error(f"Error occurred: {error}")
    if context:
        logger.error(f"Context: {context}")
    logger.exception(error)


def get_logger(name: str) -> Any:
    """
    Get a logger instance with a specific name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)
