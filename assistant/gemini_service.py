import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class GeminiConfig:
    """Configuration for Gemini API client."""
    api_key: str
    model: str = "gemini-2.0-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors."""
    pass

class GeminiClient:
    """Centralized Gemini API client with proper error handling and retry logic."""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        if config is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise GeminiAPIError("GEMINI_API_KEY environment variable is required")
            config = GeminiConfig(api_key=api_key)
        
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        
    def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make a request to Gemini API with retry logic."""
        url = f"{self.config.base_url}/models/{self.config.model}:generateContent"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.post(
                    f"{url}?key={self.config.api_key}",
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Gemini API timeout on attempt {attempt + 1}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise GeminiAPIError("API request timed out after all retries")
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limited on attempt {attempt + 1}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay * (attempt + 1) * 2)
                        continue
                raise GeminiAPIError(f"HTTP error: {e}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise GeminiAPIError(f"Request failed: {e}")
        
        raise GeminiAPIError("Failed after all retry attempts")
    
    def _extract_content(self, response_data: Dict[str, Any]) -> str:
        """Extract text content from Gemini response."""
        try:
            content = response_data["candidates"][0]["content"]
            
            if isinstance(content, dict):
                if "text" in content:
                    return content["text"].strip()
                elif "parts" in content:
                    return "".join(
                        part.get("text", "") for part in content["parts"]
                    ).strip()
                else:
                    return json.dumps(content)
            else:
                return str(content).strip()
                
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            raise GeminiAPIError(f"Invalid response format: {response_data}")
    
    def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini API.
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Generated text content
            
        Raises:
            GeminiAPIError: If the API call fails
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
        
        if len(prompt) > 30000:  # Reasonable limit
            logger.warning("Prompt is very long, truncating")
            prompt = prompt[:30000] + "..."
        
        logger.debug(f"Sending prompt to Gemini (length: {len(prompt)})")
        
        try:
            response_data = self._make_request(prompt)
            content = self._extract_content(response_data)
            
            logger.debug(f"Received response from Gemini (length: {len(content)})")
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            raise
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Global client instance for convenience
_global_client: Optional[GeminiClient] = None

def get_global_client() -> GeminiClient:
    """Get or create the global Gemini client instance."""
    global _global_client
    if _global_client is None:
        _global_client = GeminiClient()
    return _global_client

def ask_gemini(prompt: str) -> str:
    """Convenience function for simple Gemini queries using global client."""
    client = get_global_client()
    return client.generate_content(prompt)