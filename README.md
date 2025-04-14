# YouTube Shorts Automation System

An AI-powered system for automatically generating and managing YouTube Shorts content with approval workflow.

## Features

- 🤖 AI-powered quote generation
- 🎙️ Text-to-speech conversion
- 🎥 Automatic video creation for YouTube Shorts format (1080x1920)
- ✅ Telegram-based approval system
- 📊 Video organization (approved/rejected)
- 📅 Scheduled posting
- 🔄 Automatic GitHub backup

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Telegram Bot:
   - Message @BotFather on Telegram
   - Create new bot using `/newbot`
   - Copy the token provided

3. Configure the system:
   - Add your Telegram bot token to `config.json`
   - Register as admin using the `/register` command in your bot

4. Run the system:
```bash
python auto_scheduler.py --token YOUR_BOT_TOKEN
```

Or run in test mode:
```bash
python auto_scheduler.py --token YOUR_BOT_TOKEN --test
```

## Project Structure

- `scripts/` - Core functionality modules
- `assets/` - Background images and resources
- `output/` - Temporary files during processing
- `approved/` - Successfully approved videos
- `rejected/` - Rejected videos
- `model_cache/` - AI model cache

## Features

### AI Quote Generation
- Uses distilGPT2 for fast, efficient quote generation
- Fallback to preset quotes if needed
- Multiple categories: motivation, success, mindset, etc.

### Video Creation
- Vertical format optimized for YouTube Shorts (1080x1920)
- Custom background with gradient design
- High-quality text-to-speech using Google TTS
- ffmpeg for professional video encoding

### Approval System
- Telegram bot integration
- Instant notifications for new videos
- Quick approve/reject buttons
- Auto-approval option after timeout
- Video preview capability

### Scheduling
- Multiple daily posting slots
- Configurable posting times
- Automatic video generation and queuing

## Requirements

- Python 3.8+
- ffmpeg (automatically downloaded)
- Internet connection for TTS and AI model
- Telegram account for approvals

## License

Private repository - All rights reserved