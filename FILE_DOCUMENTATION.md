# TFT Assistant - File Documentation

## Core Application Files

### `main.py`
**Purpose**: Entry point for the TFT (Teamfight Tactics) assistant application
- Sets up logging and configuration
- Initializes voice recognition and microphone
- Contains the main game loop that waits for shop detection
- Handles voice commands and processes them through the rules engine
- Manages cleanup of temporary files on exit
- Registers exit handlers and keyboard shortcuts

### `requirements.txt`
**Purpose**: Python package dependencies
- Lists all required Python packages and their versions
- Used for setting up the virtual environment with `pip install -r requirements.txt`

### `scraper.py`
**Purpose**: Web scraping functionality
- Scrapes TFT composition data from external sources
- Converts scraped data into JSON format for the assistant to use

## Assistant Module (`assistant/`)

### `voice_assistant.py`
**Purpose**: Main voice assistant class with AI integration
- Integrates with Google Gemini AI for advanced query processing
- Handles complex voice queries beyond simple pattern matching
- Provides context-aware responses about TFT strategy
- Manages data loading (champions, compositions)
- Built with error handling and logging

### `rules_engine.py`
**Purpose**: Simple pattern-based query processing
- Processes voice queries using regular expressions
- Handles basic inventory management queries ("I have X, what should I sell?")
- Provides fallback responses for unsupported queries
- Works with composition data to suggest optimal champions

### `gemini_service.py`
**Purpose**: Google Gemini AI API integration
- Handles authentication and API calls to Google Gemini
- Provides AI-powered responses for complex TFT strategy questions
- Manages API errors and rate limiting

### `tts_utils.py`
**Purpose**: Text-to-speech functionality
- Converts text responses to spoken audio
- Handles voice output for the assistant's responses

### `ocr_utils.py`
**Purpose**: Optical Character Recognition utilities
- Provides OCR functionality for reading game text
- Extracts information from game screenshots

### `manual_input_handler.py`
**Purpose**: Manual input processing
- Handles user input when voice recognition isn't available
- Provides alternative input methods for the assistant

## Configuration (`config/`)

### `settings.py`
**Purpose**: Application configuration management
- Defines settings for paths, voice recognition, and game detection
- Centralizes configuration values used throughout the application

### `__init__.py`
**Purpose**: Python package initialization
- Makes the config directory a Python package

## OCR Module (`ocr/`)

### `detect_shop.py`
**Purpose**: Game shop detection
- Monitors the game screen for shop interface appearance
- Triggers assistant activation when shop is detected

### `shop_monitor.py`
**Purpose**: Continuous shop monitoring
- Provides ongoing monitoring of the shop interface
- Handles shop state changes and updates

### `capture.py`
**Purpose**: Screen capture functionality
- Takes screenshots of the game for analysis
- Provides image data for OCR and computer vision

### `matching.py`
**Purpose**: Champion matching and recognition
- Matches champions in screenshots to known champion data
- Loads and compares champion templates

### `scraper_runner.py`
**Purpose**: OCR scraping coordination
- Coordinates various OCR tasks
- Manages the flow of screen capture and analysis

## Engine Module (`engine/`)

### `comp_scraper.py`
**Purpose**: Composition data scraping
- Scrapes team compositions from websites like Mobafire
- Extracts meta information about optimal team builds

### `decision_engine.py`
**Purpose**: Game decision logic
- Implements decision-making algorithms for TFT strategy
- Analyzes game state and provides strategic recommendations

## Vision Module (`vision/`)

### `champion_detector.py`
**Purpose**: Computer vision for champion detection
- Uses image processing to identify champions in game screenshots
- Provides visual recognition capabilities

### `game_state_analyzer.py`
**Purpose**: Game state analysis
- Analyzes the current game state from visual information
- Provides context for decision making

## Utilities (`utils/`)

### `logging_config.py`
**Purpose**: Logging configuration
- Sets up application-wide logging
- Defines log levels, formats, and output destinations

### `__init__.py`
**Purpose**: Python package initialization
- Makes the utils directory a Python package

## Files Excluded from Repository (in .gitignore)

- `.env` - Environment variables (contains API keys - NEVER commit!)
- `logs/` - Log files
- `assets/`, `screenshots/`, `photo/` - Images and screenshots
- `comps_html/` - Scraped HTML files
- `tools/` - Calibration tools (not needed in main repo)
- `venv/`, `__pycache__/` - Python virtual environment and cache files
- Installation files (`install.py`, `setup.py`, `INSTALL.txt`)

## Key Features

This TFT Assistant provides:
1. **Voice Recognition**: Listens for voice commands about game strategy
2. **AI Integration**: Uses Google Gemini for intelligent responses
3. **Screen Monitoring**: Detects when the game shop is open
4. **Champion Recognition**: Identifies champions through computer vision
5. **Strategic Advice**: Provides recommendations based on current game state
6. **Team Composition Analysis**: Suggests optimal team builds and champion sales

## Security Notes

- API keys are stored in `.env` file (excluded from git)
- Sensitive files have been removed from git history
- All cache files and logs are excluded from version control