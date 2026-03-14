"""
OpenRouter API client with usage tracking and global rate limiting.
"""
import requests
import os
import threading
import time
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Known OpenRouter API parameters for validation
_KNOWN_OPENROUTER_PARAMS = {
    'model', 'messages', 'temperature', 'max_tokens',
    'max_reasoning_tokens', 'reasoning', 'tools', 'top_p',
    'top_k', 'presence_penalty', 'frequency_penalty',
    'seed', 'stop', 'stream', 'response_format', 'user'
}


class RateLimiter:
    """Thread-safe rate limiter for API calls.
    
    Ensures that requests across all workers respect a minimum interval
    between API calls to stay within rate limits.
    
    Args:
        min_interval: Minimum seconds between API calls (default: 1.0 = 60 req/min)
    """
    
    def __init__(self, min_interval=1.0):
        self.min_interval = min_interval
        self.lock = threading.Lock()
        self.last_call_time = None
    
    def acquire(self):
        """Acquire permission to make an API call, blocking if necessary."""
        with self.lock:
            now = time.time()
            if self.last_call_time:
                elapsed = now - self.last_call_time
                if elapsed < self.min_interval:
                    sleep_time = self.min_interval - elapsed
                    logger.debug(f"Rate limit: waiting {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
            self.last_call_time = time.time()


class GlobalRateLimiter:
    """
    Thread-safe singleton rate limiter shared across all OpenRouterClient instances.
    
    Ensures global rate limiting across all API calls regardless of which
    model or client makes the request. This prevents hitting API rate limits
    when running multiple models in parallel.
    
    The rate limit interval can be configured via:
    - Environment variable: OPENROUTER_RATE_LIMIT_SECONDS (default: 1.0)
    - Programmatic: GlobalRateLimiter.get_instance(min_interval=2.0)
    
    Example:
        >>> # Get the global singleton (creates if needed)
        >>> limiter = GlobalRateLimiter.get_instance()
        >>> limiter.acquire()  # Blocks until safe to proceed
        
        >>> # Reset the singleton (useful for testing)
        >>> GlobalRateLimiter.reset()
    """
    
    _instance = None
    _lock = threading.Lock()
    _min_interval = 1.0
    
    @classmethod
    def get_instance(cls, min_interval=None):
        """
        Get or create the global rate limiter singleton.
        
        Thread-safe singleton pattern with double-checked locking.
        
        Args:
            min_interval: Minimum seconds between API calls.
                         If None, uses environment variable OPENROUTER_RATE_LIMIT_SECONDS
                         or defaults to 1.0. Only applies on first creation.
        
        Returns:
            GlobalRateLimiter: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    # Determine interval: param > env var > default
                    if min_interval is None:
                        min_interval = float(os.getenv('OPENROUTER_RATE_LIMIT_SECONDS', '1.0'))
                    
                    cls._min_interval = min_interval
                    cls._instance = cls(min_interval)
                    logger.info(f"Global rate limiter initialized: {min_interval} seconds between requests")
        return cls._instance
    
    @classmethod
    def reset(cls):
        """
        Reset the global rate limiter singleton.
        
        This method is primarily intended for testing purposes. After calling reset(),
        the next call to get_instance() will create a new GlobalRateLimiter instance.
        
        Example:
            >>> GlobalRateLimiter.reset()  # Clear existing singleton
            >>> limiter = GlobalRateLimiter.get_instance(min_interval=5.0)  # New instance
        """
        with cls._lock:
            cls._instance = None
            logger.debug("Global rate limiter reset")
    
    def __init__(self, min_interval=1.0):
        """Initialize rate limiter (private - use get_instance())."""
        self.rate_limiter = RateLimiter(min_interval=min_interval)
    
    def acquire(self):
        """Acquire permission to make an API call, blocking if necessary."""
        self.rate_limiter.acquire()
    
    @property
    def min_interval(self):
        """Get the current minimum interval between requests."""
        return GlobalRateLimiter._min_interval


class OpenRouterClient:
    """OpenRouter API client with cumulative usage tracking and global rate limiting."""

    def __init__(self, api_key=None, timeout=300, use_global_rate_limit=True, custom_rate_limiter=None):
        """
        Initialize OpenRouter API client.
        
        Args:
            api_key: OpenRouter API key (default: from OPENROUTER_API_KEY env var)
            timeout: Request timeout in seconds (default: 300)
            use_global_rate_limit: If True, use global rate limiter singleton (default: True)
            custom_rate_limiter: Optional custom rate limiter (overrides global if provided)
        
        The client automatically uses a global rate limiter to prevent hitting API limits
        when running multiple models in parallel. To disable rate limiting, set
        use_global_rate_limit=False.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        self.timeout = timeout
        
        # Configure rate limiting
        if custom_rate_limiter is not None:
            # Use custom rate limiter (for flexibility/testing)
            self.rate_limiter = custom_rate_limiter
            logger.debug("Using custom rate limiter")
        elif use_global_rate_limit:
            # Use global singleton (default, recommended)
            self.rate_limiter = GlobalRateLimiter.get_instance()
            logger.debug("Using global rate limiter")
        else:
            # No rate limiting (backward compatibility/explicit disable)
            self.rate_limiter = None
            logger.debug("Rate limiting disabled")
        
        self.cumulative_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.total_reasoning_tokens = 0
        self.total_cached_tokens = 0
        self.request_count = 0
        self.api_calls = []

    def chat_completion(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        max_reasoning_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        tools: Optional[List] = None,
        **kwargs
    ) -> Dict:
        """
        Send chat completion request to OpenRouter API.

        Args:
            model: Model identifier
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum completion tokens
            max_reasoning_tokens: Maximum reasoning tokens
            timeout: Request timeout (overrides instance default)
            tools: Function calling tools
            **kwargs: Additional OpenRouter API parameters (forwarded directly)

        Returns:
            API response dictionary

        Raises:
            Exception: If API request fails
        """
        # Validate kwargs against known parameters
        unknown_params = set(kwargs.keys()) - _KNOWN_OPENROUTER_PARAMS
        if unknown_params:
            print(f"Warning: Unknown OpenRouter parameters: {unknown_params}. "
                  f"These will be ignored. Valid parameters: {_KNOWN_OPENROUTER_PARAMS}")

        effective_timeout = timeout if timeout is not None else self.timeout
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build base payload with explicit parameters
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        # Add optional explicit parameters
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        # Only send reasoning params for models that explicitly opt in.
        # Sending reasoning={effort:"low"} to non-reasoning models (e.g. GPT-4.1-mini,
        # Gemini Flash) causes OpenRouter to return empty content with reasoning in a
        # separate field, producing silent empty answers.
        if max_reasoning_tokens is not None:
            payload["max_reasoning_tokens"] = max_reasoning_tokens
            if max_reasoning_tokens == 0:
                payload["reasoning"] = {"effort": "none"}
            else:
                payload["reasoning"] = {"effort": "low"}

        if tools is not None:
            payload["tools"] = tools

        # Merge known kwargs (unknown ones already warned and filtered)
        valid_kwargs = {k: v for k, v in kwargs.items() if k in _KNOWN_OPENROUTER_PARAMS}
        payload.update(valid_kwargs)

        max_retries = 3
        retryable_statuses = {429, 500, 502, 503, 504}
        retry_delay = 1.5

        for attempt in range(max_retries):
            try:
                # Acquire rate limit before each API attempt.
                if self.rate_limiter:
                    self.rate_limiter.acquire()

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=effective_timeout
                )

                if response.status_code == 200:
                    response_data = response.json()
                    usage = response_data.get('usage', {})

                    cost = usage.get('cost', 0.0)
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                    total_tokens = usage.get('total_tokens', 0)
                    reasoning_tokens = usage.get('completion_tokens_details', {}).get('reasoning_tokens', 0)
                    cached_tokens = usage.get('prompt_tokens_details', {}).get('cached_tokens', 0)

                    self.cumulative_cost += cost
                    self.total_prompt_tokens += prompt_tokens
                    self.total_completion_tokens += completion_tokens
                    self.total_tokens += total_tokens
                    self.total_reasoning_tokens += reasoning_tokens
                    self.total_cached_tokens += cached_tokens
                    self.request_count += 1

                    call_info = {
                        "request_id": response_data.get('id'),
                        "model": model,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "reasoning_tokens": reasoning_tokens,
                        "cached_tokens": cached_tokens,
                        "cost": cost,
                        "cost_details": usage.get('cost_details', {}),
                        "response": response_data['choices'][0]['message']['content'],
                        "error_type": None
                    }
                    self.api_calls.append(call_info)

                    return response_data

                # Retry transient server/rate-limit failures
                if response.status_code in retryable_statuses and attempt < max_retries - 1:
                    logger.warning(
                        "Transient OpenRouter error %s on attempt %s/%s. Retrying in %.1fs.",
                        response.status_code,
                        attempt + 1,
                        max_retries,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
                    continue
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(
                        "OpenRouter timeout on attempt %s/%s. Retrying in %.1fs.",
                        attempt + 1,
                        max_retries,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
                    continue
                break

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "OpenRouter request exception %s on attempt %s/%s. Retrying in %.1fs.",
                        type(e).__name__,
                        attempt + 1,
                        max_retries,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
                    continue
                break

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "OpenRouter API error on attempt %s/%s: %s. Retrying in %.1fs.",
                        attempt + 1,
                        max_retries,
                        str(e)[:200],
                        retry_delay,
                    )
                    time.sleep(retry_delay)
                    continue
                break

        # Final fallback: never raise here, return empty content so the benchmark can continue.
        self.request_count += 1
        call_info = {
            "request_id": None,
            "model": model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "reasoning_tokens": 0,
            "cached_tokens": 0,
            "cost": 0.0,
            "cost_details": {},
            "response": "",
            "error_type": "api_failed_after_retries"
        }
        self.api_calls.append(call_info)

        return {
            "choices": [{"message": {"content": ""}}],
            "id": None,
            "usage": None
        }

    def get_usage_summary(self) -> Dict:
        """Get summary of API usage."""
        return {
            "request_count": self.request_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_reasoning_tokens": self.total_reasoning_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "cumulative_cost": self.cumulative_cost,
            "average_cost_per_request": self.cumulative_cost / self.request_count if self.request_count > 0 else 0
        }

    def reset_usage(self):
        """Reset usage tracking."""
        self.cumulative_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.total_reasoning_tokens = 0
        self.total_cached_tokens = 0
        self.request_count = 0
        self.api_calls = []

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        Get vector embedding for text.
        
        Args:
            text: Input text
            model: Embedding model name (default: text-embedding-3-small)
            
        Returns:
            List of floats representing the embedding vector
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": text
        }
        
        # Simple retry logic matching original client
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Calculate cost for embeddings roughly if needed, 
                    # but usually negligible or not returned in same format
                    # For now just return the vector
                    return data["data"][0]["embedding"]
                
                logger.warning(f"Embedding API Error {response.status_code}: {response.text}")
                
            except Exception as e:
                logger.error(f"Embedding request failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                
        # Return zero vector as fallback (1536 dim for text-embedding-ada-002)
        return [0.0] * 1536

