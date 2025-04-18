# YouTube Shorts Generator

## Full Step-by-Step Guide (with YouTube Upload & Stable Diffusion Backgrounds)

### 1. Prerequisites
- **Python 3.8+** (recommend using Python 3.10 or newer)
- **pip** (Python package installer)
- **FFmpeg** (will be downloaded automatically if missing)
- **Git** (to clone the repository)
- **A GPU (NVIDIA recommended) for local Stable Diffusion**

### 2. Install Stable Diffusion WebUI (AUTOMATIC1111)
- Go to: https://github.com/AUTOMATIC1111/stable-diffusion-webui
- Download as ZIP or clone with:
  ```bash
  git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
  ```
- Extract/open the folder.
- Download the SD v1.5 model (`v1-5-pruned-emaonly.ckpt` from Hugging Face) and place it in `models/Stable-diffusion/` inside the WebUI folder.

### 3. Enable the API
- Edit `webui-user.bat` (Windows) and add this line:
  ```
  set COMMANDLINE_ARGS=--api
  ```
- Save and double-click `webui-user.bat` to launch the WebUI.
- Wait for the server to start (first time takes a while).
- You should see a local URL like: `http://127.0.0.1:7860/`

### 4. Test the API
- Open [http://127.0.0.1:7860/docs](http://127.0.0.1:7860/docs) in your browser. You should see the API documentation.

### 5. Clone This Repository
```bash
git clone https://github.com/taha-rafi/yt_automation.git
cd yt_automation
```

### 6. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 7. Configure API Keys and Credentials
- Edit `config.json` and add your OpenRouter API key and (optionally) Telegram bot token.
- For YouTube uploads, set up Google Cloud and download `credentials.json` to the project root.

### 8. Set Up YouTube API for Uploads
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Go to **APIs & Services > Library**, search for and enable **YouTube Data API v3**
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth client ID**
6. Set application type to **Desktop app**
7. Download the `credentials.json` file and place it in your project root
8. The first time you upload, a browser window will open for Google authentication—sign in and approve access

### 9. Run the Script to Generate and Upload a Video
- Make sure Stable Diffusion WebUI is running (see above).
- Then run:
```bash
python main.py
```
- The script will:
  1. Generate a quote using Mistral
  2. Generate a background image using Stable Diffusion
  3. Convert quote to speech
  4. Create a video with text and background
  5. Upload to YouTube (if credentials are set)

### 10. Test Mode (No Upload)
```bash
python main.py --test
```

### 11. Scheduled Mode (Automatic Posting)
```bash
python auto_scheduler.py
```

### 12. Troubleshooting
- **Stable Diffusion API not working:** Make sure WebUI is running with `--api` and you can access `http://127.0.0.1:7860/docs`.
- **Large file errors on GitHub:** ffmpeg and other binaries are now in `.gitignore` and history is cleaned.
- **Google API errors:** Make sure `credentials.json` is present and correct.
- **YouTube upload fails:** Double-check your Google Cloud setup and that you approved OAuth access.

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

---

## ⚡️ MoviePy v2.x Compatibility Notes (2025)

- This project now uses **MoviePy v2.x**. The old `moviepy.editor` import and `.set_` methods are no longer supported.
- **How to import:**
  ```python
  from moviepy import ImageClip, VideoFileClip, CompositeVideoClip
  # Or import * for all
  from moviepy import *
  ```
- **How to set duration/opacity:**
  ```python
  # OLD (v1.x):
  clip = ImageClip('img.png').set_duration(5).set_opacity(1)
  # NEW (v2.x):
  clip = ImageClip('img.png').with_duration(5).with_opacity(1)
  ```
- All methods like `.set_duration()`, `.set_opacity()`, `.set_position()` etc. are now `.with_duration()`, `.with_opacity()`, `.with_position()`, etc.
- If you see `ModuleNotFoundError: No module named 'moviepy.editor'`, update your imports as shown above.
- See the [official v2 migration guide](https://zulko.github.io/moviepy/getting_started/updating_to_v2.html) for more info.

---

## 🛠️ Local Stable Diffusion (diffusers)
- The project now supports local image generation using the `diffusers` library (Stable Diffusion v1.5) for backgrounds.
- If SD image generation fails, a fallback gradient (or solid color) background will be used.
- Make sure your system has enough RAM/GPU for local SD.

---

## 🧪 Minimal Video Test
If you ever want to test MoviePy and your install, run:
```bash
python scripts/test_red_video.py
```
This should create a 5-second red (or blueish, depending on your ffmpeg) video at `output/test_red_video.mp4`.

---

## 🔥 Troubleshooting
- **MoviePy import errors:**
  - Make sure you use `from moviepy import ...` (not `moviepy.editor`).
  - If pip install fails, try `pip install --user --upgrade --force-reinstall --no-cache-dir moviepy`.
- **Stable Diffusion errors:**
  - Check your GPU/CPU resources and diffusers install.
- **Background not visible/black:**
  - Try saving fallback backgrounds as JPEG for color accuracy.
  - Confirm your output images are not blank and are being loaded by MoviePy.