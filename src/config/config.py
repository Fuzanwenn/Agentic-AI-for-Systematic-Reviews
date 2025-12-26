"""
Configuration Management

This module handles all configuration settings for the systematic review application,
including API keys, model settings, and application parameters.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for Language Model settings."""
    
    # API Configuration
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))
    
    # Model Settings
    gpt_4o_mini_model: str = "gpt-4o-mini"
    o3_mini_model: str = "gpt-4o-mini"  # Currently using gpt-4o-mini as fallback
    
    # Request Settings
    timeout: int = 20
    max_retries: int = 3
    retry_delay: int = 10
    
    # Cost Tracking (USD per 1000 tokens)
    pricing: dict = field(default_factory=lambda: {
        "gpt-4o-mini": {"prompt": 0.0005 / 1000, "completion": 0.0015 / 1000},
        "o3-mini": {"prompt": 0.0005 / 1000, "completion": 0.0015 / 1000},
    })
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            logger.warning(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
            )


@dataclass
class AppConfig:
    """Main application configuration."""
    
    # LLM Configuration
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    src_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    output_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "output")
    
    # Logging Configuration
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Application Settings
    enable_cost_tracking: bool = True
    enable_disagreement_tracking: bool = True
    
    def __post_init__(self):
        """Ensure directories exist and validate configuration."""
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for the application."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format=self.log_format
        )


# Singleton configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the application configuration (singleton pattern).
    
    Returns:
        The application configuration instance
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def load_config_from_env():
    """
    Load configuration from environment variables.
    
    This should be called at application startup to initialize
    configuration from .env file or environment variables.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded configuration from .env file")
    except ImportError:
        logger.warning(
            "python-dotenv not installed. Environment variables will be used directly."
        )
    
    # Reinitialize config to pick up environment variables
    global _config
    _config = AppConfig()
    return _config


def validate_api_key() -> bool:
    """
    Validate that an API key is configured.
    
    Returns:
        True if API key is present, False otherwise
    """
    config = get_config()
    if not config.llm.api_key:
        logger.error(
            "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
        return False
    return True
