# YouTube Shorts Generator

## Step-by-Step Guide to Run the Project

### 1. Prerequisites
- **Python 3.8+** (recommend using Python 3.10 or newer)
- **pip** (Python package installer)
- **FFmpeg** (will be downloaded automatically if missing)
- **Ollama** (for AI models: https://ollama.com/download)
- **Git** (to clone the repository)

### 2. Clone the Repository
```bash
git clone https://github.com/taha-rafi/yt_automation.git
cd yt_automation
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download the LLaVA Model for Background Images
- Open a new terminal and run:
```bash
ollama pull llava
```
- Wait for the download to complete (size: ~7GB)

### 4b. Download the Mistral Model for Quote Generation
- In your terminal, run:
```bash
ollama pull mistral
```
- This model is used for generating quotes and text responses.

### 5. Configure API Keys and Credentials
- Edit `config.json` and add your OpenRouter API key and (optionally) Telegram bot token.
- For YouTube uploads, set up Google Cloud and download `credentials.json` to the project root (see Setup section above).

### 6. (Optional) Add Background Assets
- Place your own images in `assets/backgrounds/` if you want custom backgrounds.
- If not, the script will use AI-generated or gradient backgrounds.

### 7. Run the Script to Generate a Video
```bash
python main.py
```
- The script will generate a quote, synthesize speech, create a video with an AI-generated background, and (optionally) upload to YouTube.

### 8. Troubleshooting
- **Model not found:** If you see `model 'llava' not found`, make sure you ran `ollama pull llava` and that Ollama is running.
- **set_audio error:** This is fixed in the latest code; update if you see this.
- **Large file errors on GitHub:** ffmpeg and other binaries are now in `.gitignore`.
- **Google API errors:** Make sure `credentials.json` is present and correct.

### 9. Useful Commands
- **Test mode:**
  ```bash
  python main.py --test
  ```
- **Scheduled mode:**
  ```bash
  python auto_scheduler.py
  ```

---

For more customization and advanced usage, see the rest of this README and the code comments.

## Features

- AI-powered quote generation using OpenRouter API
- High-quality text-to-speech conversion
- Dynamic video creation with customizable backgrounds
- Automatic YouTube upload with retry mechanism
- Telegram-based approval system with content moderation
- Progress tracking and colored logging
- Background asset management
- Automated scheduling of video creation and uploads

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys in config.json:
```json
{
    "openrouter_api_key": "your_openrouter_api_key",
    "telegram_token": "your_telegram_bot_token",
    "auto_approve_after": 30,
    "admin_chat_ids": []
}
```

4. Set up YouTube API:
   - Create a project in Google Cloud Console
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download credentials.json and place it in the project root

5. Add background assets (optional):
   - Place background images in `assets/backgrounds/`
   - Supported formats: jpg, jpeg, png
   - Default gradient background will be used if no assets are found

## Usage

### Test Mode
```bash
python main.py --test
```

### Scheduled Mode
```bash
python auto_scheduler.py
```

This will run the system with default scheduling (3 times per day).

## Customization

### Posting Schedule
Edit auto_scheduler.py to modify posting times:
```python
posting_times = ["10:00", "15:00", "20:00"]
```

### Video Settings
- Resolution: 1080x1920 (Shorts format)
- Frame rate: 30fps
- Audio: AAC encoded

## Error Handling

- Automatic retries for API calls
- Exponential backoff for failed attempts
- Comprehensive logging in logs directory
- Automatic cleanup of old files

## Directory Structure

- `approved/`: Successfully uploaded videos
- `rejected/`: Rejected or failed videos
- `assets/`: Background images and videos
- `output/`: Temporary files
- `logs/`: Application logs
- `scripts/`: Core functionality modules

## Requirements

- Python 3.8+
- FFmpeg (automatically downloaded if not present)
- Internet connection for API access
- YouTube account for uploads
- Telegram bot for approval system (optional)