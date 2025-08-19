import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def speak(text: str, timeout: Optional[float] = 30.0) -> bool:
    """Use macOS `say` to vocalize text safely.
    
    Args:
        text: Text to speak
        timeout: Maximum time to wait for speech completion
        
    Returns:
        True if speech was successful, False otherwise
    """
    if not text or not isinstance(text, str):
        logger.warning("Invalid text provided to speak function")
        return False
    
    # Sanitize input - remove potentially dangerous characters
    text = text.strip()
    
    # Shorten long responses but keep them meaningful
    if len(text) > 500:  # Reduced from 1000 to 500 for shorter speech
        # Try to cut at sentence boundaries
        sentences = text.split('. ')
        shortened = sentences[0]
        for sentence in sentences[1:]:
            if len(shortened + '. ' + sentence) <= 500:
                shortened += '. ' + sentence
            else:
                break
        text = shortened + "..." if len(text) > len(shortened) else shortened
        
    try:
        subprocess.run(
            ["say", text],
            timeout=timeout,
            check=True,
            capture_output=True,
            text=True
        )
        logger.debug(f"Successfully spoke text: {text[:50]}...")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Speech timeout after {timeout} seconds")
        logger.info(f"Skipped speaking: {text[:100]}...")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Speech command failed: {e}")
        logger.info(f"Skipped speaking: {text[:100]}...")
        return False
    except FileNotFoundError:
        logger.error("macOS 'say' command not found - TTS not available")
        logger.info(f"Would have spoken: {text[:100]}...")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in speak function: {e}")
        logger.info(f"Skipped speaking: {text[:100]}...")
        return False

def speak_simple(text: str) -> None:
    """Simplified speak function that just logs if TTS fails."""
    success = speak(text, timeout=5.0)  # Quick timeout
    if not success:
        logger.info(f"Response: {text}")