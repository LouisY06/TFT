# TFT Voice Assistant

A voice-activated coach for Teamfight Tactics that provides real-time strategic advice.

## Features
- Real-time game advice
- Gold/economy management
- Level timing recommendations
- Team composition guidance

## Requirements
- Python 3.9+
- PyAudio
- SpeechRecognition
- pyttsx3

## Setup

### Clone and Install
```bash
# Clone repository
git clone https://github.com/louisyu/TFT.git
cd TFT

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Assistant
python ./main.py