# TFT Voice Assistant

A voice-activated assistant for Teamfight Tactics (TFT) that combines computer vision, natural language processing, and AI strategy analysis to provide real-time gameplay advice.

## Features

### Voice Commands
- Voice Recognition: Ask questions about your current game state
- Text-to-Speech: Get spoken strategic advice
- Hotkey Support: Ctrl+Shift+S to activate, Ctrl+Shift+A for game analysis

### Computer Vision
- Screen Analysis: Automatically detect gold, level, health, and round
- Shop Monitoring: Real-time champion detection in shop
- Board Analysis: Champion positioning and synergy detection

### Manual Input + AI Analysis
- Natural Language Parsing: "I have 50 gold level 7 with jinx and vi on board"
- Champion Recognition: Fuzzy matching and aliases (e.g., "mf" for "Miss Fortune")
- Hybrid Approach: Combines manual input with vision for maximum accuracy

### Strategic Advice
- AI-Powered: Uses Google Gemini for strategic analysis
- Context-Aware: Considers your exact game state for personalized advice
- Economy Management: Gold spending vs saving recommendations
- Positioning: Board setup and champion placement advice

## Installation

### Prerequisites
- Python 3.8+ installed
- macOS (recommended - TTS optimized)
- Internet connection for dependency download
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation Steps

1. Download the project files
2. Run the installer:
   ```bash
   python install.py
   ```
3. Add your API key to `.env` file:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```
4. Launch the application:
   - macOS: Double-click "TFT Voice Assistant.command" on Desktop
   - Command line: `./launch.sh` or `python launch.py`

## How to Use

### Quick Start
1. Start TFT and open the game
2. Launch the assistant
3. Use hotkeys:
   - `Ctrl+Shift+S`: Ask a question
   - `Ctrl+Shift+A`: Analyze current game state
   - `Esc`: Exit

### Voice Commands Examples
```
"I have 50 gold level 7 with jinx and vi on my board, caitlyn on bench, shop has jayce. What should I do?"

"My board has jinx and vi, bench has caitlyn, trying to play enforcers"

"Level 6 with 30 health, should I reroll or save?"

"What comp should I play with these champions?"
```

