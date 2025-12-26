"""
Systematic Review Screening Package

A production-grade system for automated screening of articles in systematic reviews
using LLM-powered agents with a two-tier screening process.
"""

__version__ = "1.0.0"
__author__ = "Zanwen Fu"

from .agents.screening_agent import TwoTierScreeningAgent, CitationClassifier, DetailedScreener
from .llms.chatgpt import LLMClient, get_llm_client
from .config.config import get_config, load_config_from_env

__all__ = [
    "TwoTierScreeningAgent",
    "CitationClassifier",
    "DetailedScreener",
    "LLMClient",
    "get_llm_client",
    "get_config",
    "load_config_from_env",
]
