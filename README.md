# TFT Voice Assistant 🎮🔊

A powerful voice-activated assistant for Teamfight Tactics (TFT) that combines computer vision, natural language processing, and AI strategy analysis to provide real-time gameplay advice.

## ✨ Features

### 🎙️ Voice Commands
- **Voice Recognition**: Ask questions about your current game state
- **Text-to-Speech**: Get spoken strategic advice
- **Hotkey Support**: Ctrl+Shift+S to activate, Ctrl+Shift+A for game analysis

### 👁️ Computer Vision
- **Screen Analysis**: Automatically detect gold, level, health, and round
- **Shop Monitoring**: Real-time champion detection in shop
- **Board Analysis**: Champion positioning and synergy detection

### 🧠 Manual Input + AI Analysis
- **Natural Language Parsing**: "I have 50 gold level 7 with jinx and vi on board"
- **Champion Recognition**: Fuzzy matching and aliases (e.g., "mf" → "Miss Fortune")
- **Hybrid Approach**: Combines manual input with vision for maximum accuracy

### 🚀 Strategic Advice
- **AI-Powered**: Uses Google Gemini for strategic analysis
- **Context-Aware**: Considers your exact game state for personalized advice
- **Economy Management**: Gold spending vs saving recommendations
- **Positioning**: Board setup and champion placement advice

## 🔧 One-Click Installation

### Prerequisites
- **Python 3.8+** installed
- **macOS** (recommended - TTS optimized)
- **Internet connection** for dependency download
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))

### Installation Steps

1. **Download** the project files
2. **Run** the installer:
   ```bash
   python install.py
   ```
3. **Add your API key** to `.env` file:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```
4. **Launch** the application:
   - **macOS**: Double-click "TFT Voice Assistant.command" on Desktop
   - **Command line**: `./launch.sh` or `python launch.py`

That's it! The installer automatically:
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Sets up configuration files
- ✅ Creates sample game data
- ✅ Creates launcher scripts
- ✅ Sets up desktop shortcut

## 🎮 How to Use

### Quick Start
1. **Start TFT** and open the game
2. **Launch** the assistant
3. **Use hotkeys**:
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

### Manual + Vision Hybrid
The assistant combines the best of both approaches:
- **Voice input** for complex champion information
- **Vision detection** for numerical stats (gold, level, health, round)
- **Fallback support** - works even if vision fails

## ⚙️ Configuration

### Screen Calibration (Optional)
Run the calibration tool to optimize vision detection:
```bash
python tools/calibration_tool.py
```

### Settings (.env file)
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
LOG_LEVEL=INFO
TTS_ENABLED=true
TTS_TIMEOUT=30
VISION_ENABLED=true
MANUAL_INPUT_ENABLED=true
```

## 🗂️ Project Structure
```
TFT/
├── install.py              # One-click installer
├── launch.py              # Application launcher
├── launch.sh              # Shell launcher (macOS/Linux)
├── main.py                # Main application
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (create from template)
│
├── assistant/             # Voice recognition & AI
│   ├── rules_engine.py    # Main AI processing
│   ├── manual_input_handler.py  # Natural language parsing
│   ├── gemini_service.py  # AI service integration
│   └── tts_utils.py       # Text-to-speech
│
├── vision/                # Computer vision
│   ├── game_state_analyzer.py  # Screen analysis
│   └── champion_detector.py    # Champion recognition
│
├── config/                # Configuration files
├── data/                  # Game data (champions, comps)
├── logs/                  # Application logs
└── tools/                 # Utility tools
    └── calibration_tool.py # Screen calibration GUI
```

## 🐛 Troubleshooting

### Common Issues

**"No module named ..."**
- Run: `python install.py` to reinstall dependencies

**Voice recognition not working**
- Check microphone permissions
- Ensure internet connection (Google Speech API)

**Vision detection inaccurate**
- Run calibration tool: `python tools/calibration_tool.py`
- Adjust screen regions in `config/screen_calibration.json`

**TTS not working on macOS**
- macOS `say` command should work by default
- Check system voice settings

**API errors**
- Verify your Gemini API key in `.env` file
- Check API quota and billing

### Logs
Check `logs/` directory for detailed error information:
- `logs/tft_assistant.log` - Main application log
- `logs/performance.log` - Performance metrics

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional champion/item detection
- Support for other TTS engines
- Windows/Linux optimization
- UI improvements

## 📄 License

MIT License - See LICENSE file for details.

## 🔗 Links

- [TFT Official Site](https://teamfighttactics.leagueoflegends.com/)
- [Google Gemini API](https://makersuite.google.com/)
- [Report Issues](https://github.com/your-repo/issues)

---

**Enjoy climbing the TFT ladder with your AI assistant! 🚀**