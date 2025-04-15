# YouTube Shorts Generator

An automated system for generating and uploading YouTube Shorts using OpenRouter API integration.

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