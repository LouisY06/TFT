import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

@dataclass
class OCRSettings:
    """OCR-related configuration settings."""
    confidence_threshold: float = 0.8
    shop_detection_timeout: Optional[float] = None
    bench_region: tuple = (330, 850, 1250, 190)
    template_dir: str = "champ_templates"
    screenshot_dir: str = "assets/screenshots"
    slot_dir: str = "assets/slots"

@dataclass 
class GeminiSettings:
    """Gemini API configuration settings."""
    api_key: Optional[str] = None
    model: str = "gemini-2.0-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class VoiceSettings:
    """Voice recognition and TTS settings."""
    recognition_timeout: float = 5.0
    phrase_time_limit: float = 5.0
    tts_timeout: float = 30.0  # Increased from 10 to 30 seconds
    ambient_noise_adjustment: bool = True

@dataclass
class ScrapingSettings:
    """Web scraping configuration."""
    mobafire_url: str = "https://www.mobafire.com/teamfight-tactics/champions"
    timeout: float = 30.0
    max_retries: int = 3
    user_agent: str = "TFT-Assistant/1.0"
    rate_limit_delay: float = 1.0

@dataclass
class LoggingSettings:
    """Logging configuration."""
    level: str = "INFO"
    log_file: Optional[str] = "logs/tft_assistant.log"
    max_file_size: int = 10_000_000  # 10MB
    backup_count: int = 5
    format_str: str = "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"

@dataclass
class PathSettings:
    """File and directory path settings."""
    data_dir: str = "data"
    comps_html_dir: str = "comps_html"
    champions_file: str = "champions.json"
    traits_file: str = "traits.json"
    comps_file: str = "comps_output.json"

@dataclass
class AppSettings:
    """Main application settings container."""
    ocr: OCRSettings
    gemini: GeminiSettings
    voice: VoiceSettings
    scraping: ScrapingSettings
    logging: LoggingSettings
    paths: PathSettings
    
    @classmethod
    def default(cls) -> 'AppSettings':
        """Create default settings."""
        return cls(
            ocr=OCRSettings(),
            gemini=GeminiSettings(),
            voice=VoiceSettings(),
            scraping=ScrapingSettings(),
            logging=LoggingSettings(),
            paths=PathSettings()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create settings from dictionary."""
        return cls(
            ocr=OCRSettings(**data.get('ocr', {})),
            gemini=GeminiSettings(**data.get('gemini', {})),
            voice=VoiceSettings(**data.get('voice', {})),
            scraping=ScrapingSettings(**data.get('scraping', {})),
            logging=LoggingSettings(**data.get('logging', {})),
            paths=PathSettings(**data.get('paths', {}))
        )

class ConfigManager:
    """Configuration manager for loading and saving settings."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self._settings: Optional[AppSettings] = None
        load_dotenv()  # Load environment variables
    
    def load(self) -> AppSettings:
        """Load settings from file and environment variables."""
        if self._settings is not None:
            return self._settings
        
        # Start with defaults
        settings = AppSettings.default()
        
        # Load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                settings = AppSettings.from_dict(config_data)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
                logger.info("Using default settings")
        else:
            logger.info("No config file found, using defaults")
        
        # Override with environment variables
        self._apply_env_overrides(settings)
        
        self._settings = settings
        return settings
    
    def _apply_env_overrides(self, settings: AppSettings) -> None:
        """Apply environment variable overrides to settings."""
        # Gemini API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            settings.gemini.api_key = api_key
        
        # Logging level
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            settings.logging.level = log_level.upper()
        
        # Data directory
        data_dir = os.getenv("DATA_DIR")
        if data_dir:
            settings.paths.data_dir = data_dir
        
        # OCR confidence threshold
        ocr_confidence = os.getenv("OCR_CONFIDENCE")
        if ocr_confidence:
            try:
                settings.ocr.confidence_threshold = float(ocr_confidence)
            except ValueError:
                logger.warning(f"Invalid OCR_CONFIDENCE value: {ocr_confidence}")
        
        # Gemini timeout
        gemini_timeout = os.getenv("GEMINI_TIMEOUT")
        if gemini_timeout:
            try:
                settings.gemini.timeout = float(gemini_timeout)
            except ValueError:
                logger.warning(f"Invalid GEMINI_TIMEOUT value: {gemini_timeout}")
    
    def save(self, settings: AppSettings) -> None:
        """Save settings to config file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Don't save sensitive data like API keys
            save_data = settings.to_dict()
            if 'gemini' in save_data and 'api_key' in save_data['gemini']:
                save_data['gemini']['api_key'] = None
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=4)
            
            logger.info(f"Settings saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_file}: {e}")
    
    def get_settings(self) -> AppSettings:
        """Get current settings (loads if not already loaded)."""
        if self._settings is None:
            return self.load()
        return self._settings
    
    def update_settings(self, **kwargs) -> None:
        """Update specific settings and save to file."""
        settings = self.get_settings()
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
            else:
                logger.warning(f"Unknown setting: {key}")
        
        self.save(settings)
        self._settings = settings

# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_settings() -> AppSettings:
    """Get current application settings."""
    return get_config().get_settings()

# Convenience functions for accessing specific settings
def get_gemini_settings() -> GeminiSettings:
    """Get Gemini API settings."""
    return get_settings().gemini

def get_ocr_settings() -> OCRSettings:
    """Get OCR settings."""
    return get_settings().ocr

def get_voice_settings() -> VoiceSettings:
    """Get voice settings."""
    return get_settings().voice

def get_scraping_settings() -> ScrapingSettings:
    """Get scraping settings."""
    return get_settings().scraping

def get_logging_settings() -> LoggingSettings:
    """Get logging settings."""
    return get_settings().logging

def get_path_settings() -> PathSettings:
    """Get path settings."""
    return get_settings().paths