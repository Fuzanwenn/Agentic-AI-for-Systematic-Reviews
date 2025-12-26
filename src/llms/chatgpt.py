"""
LLM Interface Module

This module provides a clean interface to interact with OpenAI's language models
for systematic review screening tasks.
"""

import time
import logging
from typing import Tuple, Union, List, Dict, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletion

from config.config import get_config, validate_api_key

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with OpenAI's language models.
    
    Handles API calls, retries, error handling, and cost tracking.
    """
    
    def __init__(self):
        """Initialize the LLM client with configuration."""
        self.config = get_config()
        if not validate_api_key():
            raise ValueError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=self.config.llm.api_key)
        logger.info("LLM client initialized successfully")
    
    def _calculate_cost(self, response: ChatCompletion, model_name: str) -> float:
        """
        Calculate the cost of an API call based on token usage.
        
        Args:
            response: The API response object
            model_name: Name of the model used
            
        Returns:
            Cost in USD
        """
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        
        pricing = self.config.llm.pricing.get(model_name, {})
        if not pricing:
            logger.warning(f"No pricing information for model: {model_name}")
            return 0.0
        
        cost = (
            prompt_tokens * pricing.get("prompt", 0)
            + completion_tokens * pricing.get("completion", 0)
        )
        
        if self.config.enable_cost_tracking:
            logger.info(
                f"API call cost: ${cost:.6f} USD "
                f"(prompt: {prompt_tokens} tokens, completion: {completion_tokens} tokens)"
            )
        
        return cost
    
    def _make_api_call(
        self, 
        model: str,
        messages: Union[str, List[Dict[str, str]]],
        system_message: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, float]:
        """
        Make an API call with retry logic.
        
        Args:
            model: Model name to use
            messages: Either a string or list of message dicts
            system_message: Optional system message
            **kwargs: Additional arguments for the API call
            
        Returns:
            Tuple of (response_content, cost)
            
        Raises:
            Exception: If all retries fail
        """
        # Format messages
        if isinstance(messages, str):
            formatted_messages = []
            if system_message:
                formatted_messages.append({"role": "system", "content": system_message})
            formatted_messages.append({"role": "user", "content": messages})
        else:
            formatted_messages = messages
        
        # Retry loop
        for attempt in range(self.config.llm.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    response_format={"type": "text"},
                    messages=formatted_messages,
                    timeout=self.config.llm.timeout,
                    **kwargs
                )
                
                content = response.choices[0].message.content
                cost = self._calculate_cost(response, model)
                
                logger.debug(f"API call successful on attempt {attempt + 1}")
                return content, cost
                
            except Exception as e:
                logger.warning(
                    f"API call failed (attempt {attempt + 1}/{self.config.llm.max_retries}): {e}"
                )
                if attempt < self.config.llm.max_retries - 1:
                    time.sleep(self.config.llm.retry_delay)
                else:
                    logger.error(f"All API call attempts failed: {e}")
                    raise
    
    def call_gpt_4o_mini(
        self, 
        message: Union[str, List[Dict[str, str]]],
        system_message: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Call GPT-4o-mini model.
        
        Args:
            message: The message(s) to send
            system_message: Optional system message
            
        Returns:
            Tuple of (response_content, cost)
        """
        logger.debug("Calling GPT-4o-mini")
        return self._make_api_call(
            model=self.config.llm.gpt_4o_mini_model,
            messages=message,
            system_message=system_message
        )
    
    def call_o3_mini(
        self, 
        message: Union[str, List[Dict[str, str]]],
        system_message: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Call O3-mini model (currently using GPT-4o-mini as fallback).
        
        Args:
            message: The message(s) to send
            system_message: Optional system message
            
        Returns:
            Tuple of (response_content, cost)
        """
        logger.debug("Calling O3-mini")
        return self._make_api_call(
            model=self.config.llm.o3_mini_model,
            messages=message,
            system_message=system_message
        )


# Singleton instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get the LLM client instance (singleton pattern).
    
    Returns:
        The LLM client instance
    """
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


# Backward compatibility functions
def gpt_4o_mini(
    message: Union[str, List[Dict[str, str]]], 
    tier: str = ""
) -> Tuple[str, float]:
    """
    Legacy function for GPT-4o-mini calls.
    
    Args:
        message: The message(s) to send
        tier: The tier/role (for backward compatibility, not used)
        
    Returns:
        Tuple of (response_content, cost)
    """
    client = get_llm_client()
    return client.call_gpt_4o_mini(message)


def gpt_o3_mini(
    message: Union[str, List[Dict[str, str]]], 
    tier: str = ""
) -> Tuple[str, float]:
    """
    Legacy function for O3-mini calls.
    
    Args:
        message: The message(s) to send
        tier: The tier/role (for backward compatibility, not used)
        
    Returns:
        Tuple of (response_content, cost)
    """
    client = get_llm_client()
    return client.call_o3_mini(message)
