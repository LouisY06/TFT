import pyautogui
import time
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def wait_for_shop(
    path: str = "photo/reroll_text.png", 
    confidence: float = 0.8,
    timeout: Optional[float] = None
) -> bool:
    """Wait for the TFT shop to appear on screen.
    
    Args:
        path: Path to the shop indicator image
        confidence: Image matching confidence threshold (0.0-1.0)
        timeout: Maximum time to wait in seconds (None for infinite)
        
    Returns:
        True when shop is detected
        
    Raises:
        FileNotFoundError: If the reference image doesn't exist
        ValueError: If confidence is not in valid range
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
    
    full_path = Path(path).resolve()
    if not full_path.exists():
        raise FileNotFoundError(f"Shop reference image not found: {full_path}")
    
    logger.info(f"Looking for shop using image: {full_path}")
    logger.info(f"Confidence threshold: {confidence}")
    
    start_time = time.time()
    
    while True:
        try:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                logger.warning(f"Shop detection timeout after {timeout} seconds")
                return False
            
            location = pyautogui.locateOnScreen(str(full_path), confidence=confidence)
            if location:
                logger.info(f"Shop detected at {location}")
                time.sleep(2)  # Brief pause for stability
                return True
                
        except pyautogui.ImageNotFoundException:
            # This is expected when image is not found
            pass
        except Exception as e:
            logger.error(f"Error during shop detection: {e}")
            # Continue trying despite errors
        
        time.sleep(1)

def shop_still_visible(
    path: str = "photo/reroll_text.png", 
    confidence: float = 0.8
) -> bool:
    """Check if the TFT shop is still visible on screen.
    
    Args:
        path: Path to the shop indicator image
        confidence: Image matching confidence threshold (0.0-1.0)
        
    Returns:
        True if shop is visible, False otherwise
    """
    if not 0.0 <= confidence <= 1.0:
        logger.warning(f"Invalid confidence value: {confidence}, using 0.8")
        confidence = 0.8
    
    full_path = Path(path).resolve()
    if not full_path.exists():
        logger.error(f"Shop reference image not found: {full_path}")
        return False
    
    try:
        location = pyautogui.locateOnScreen(str(full_path), confidence=confidence)
        is_visible = location is not None
        if is_visible:
            logger.debug(f"Shop still visible at {location}")
        return is_visible
        
    except pyautogui.ImageNotFoundException:
        return False
    except Exception as e:
        logger.error(f"Error checking shop visibility: {e}")
        return False

def get_shop_region() -> Optional[Tuple[int, int, int, int]]:
    """Get the detected shop region coordinates.
    
    Returns:
        Tuple of (left, top, width, height) if shop found, None otherwise
    """
    try:
        location = pyautogui.locateOnScreen("photo/reroll_text.png", confidence=0.8)
        if location:
            return (location.left, location.top, location.width, location.height)
        return None
    except Exception as e:
        logger.error(f"Error getting shop region: {e}")
        return None

