# YouTube Shorts Automation

## Overview
This project automates the creation and uploading of motivational YouTube Shorts. It uses AI to generate quotes, converts them to speech, creates a video with dynamic backgrounds, and uploads directly to YouTube.

---

## Features
- **AI-powered quote generation** (Mistral/Ollama)
- **Text-to-speech** audio creation
- **Dynamic video backgrounds** (Stable Diffusion or gradient)
- **Automated YouTube upload**
- **Error handling & logging**
- **Configurable via `config.json`**

---

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- pip
- FFmpeg (auto-downloaded if missing)
- (Optional) NVIDIA GPU for Stable Diffusion

### 2. Clone the Repository
```bash
git clone https://github.com/taha-rafi/yt_automation.git
cd yt_automation
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
- Open `config.json` and set your OpenRouter API key and (optionally) Telegram bot token.

### 5. YouTube API Setup
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a project, enable **YouTube Data API v3**
- Go to **APIs & Services > Credentials**
- Create OAuth client ID (Desktop app)
- Download `credentials.json` and place it in your project root

### 6. (Optional) Stable Diffusion WebUI
- Install [AUTOMATIC1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- Download SD v1.5 model and place in `models/Stable-diffusion/`
- Edit `webui-user.bat` and add `set COMMANDLINE_ARGS=--api`
- Run the WebUI and ensure the API is accessible at `http://127.0.0.1:7860/docs`

### 7. Run the Script
```bash
python main.py
```

---

## Usage
- The script will:
  1. Generate an AI quote and category
  2. Convert quote to speech
  3. Create a video with animated text and background
  4. Upload to YouTube (if credentials are set)

### Test Mode
Run without uploading:
```bash
python main.py --test
```

### Scheduled Posting
Automate posting at set times:
```bash
python auto_scheduler.py
```

---

## Directory Structure
```
yt_automation/
├── main.py
├── config.json
├── credentials.json   # (do not share)
├── requirements.txt
├── README.md
├── scripts/
│   ├── ai_generator.py
│   ├── qwen_ai.py
│   ├── online_video_creator.py
│   ├── utils.py
│   └── ...
├── output/
│   └── *.mp3, *.mp4
└── ...
```

---

## Troubleshooting
- **Missing credentials.json:** Download from Google Cloud and place in root.
- **Stable Diffusion errors:** Ensure WebUI is running with `--api` and model is present.
- **MoviePy errors:** Use correct imports: `from moviepy import ...`
- **YouTube upload fails:** Double-check Google Cloud setup and OAuth approval.

---

## Notes
- Never commit `credentials.json` or `token.json` to version control.
- For background customization, add images to `assets/backgrounds/`.
- Logging and error details are saved in the `logs/` directory.

---

For further customization or issues, see code comments or contact the maintainer.