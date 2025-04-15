import os
import sys
import requests
import zipfile
import shutil
import json
from pathlib import Path
from datetime import datetime
import logging
import colorlog
import time
from functools import wraps
import random

def setup_logging():
    """Setup logging configuration with colored output"""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Create color formatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    # Create handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(formatter)

    # Setup root logger
    logger = colorlog.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Initialize logger
logger = setup_logging()

def retry_api_call(max_retries=3, delay=1, backoff=2):
    """
    Decorator for retrying API calls with exponential backoff
    
    Args:
        max_retries (int): Maximum number of retries
        delay (int): Initial delay in seconds
        backoff (int): Multiply delay by this factor after each failure
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        logger.error(f"Final retry failed: {e}")
                        raise  # Re-raise the last exception
                    
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    logger.info(f"Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                    current_delay *= backoff  # Exponential backoff
            return None  # Should never reach here due to raise above
        return wrapper
    return decorator

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def ensure_ffmpeg():
    """Download and setup portable ffmpeg if not already installed"""
    ffmpeg_dir = Path(__file__).parent.parent / 'bin' / 'ffmpeg'
    ffmpeg_exe = ffmpeg_dir / 'ffmpeg.exe'

    # Check if ffmpeg is already in system PATH
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        pass

    # Check if we already have portable ffmpeg
    if ffmpeg_exe.exists():
        # Add to PATH
        os.environ['PATH'] = str(ffmpeg_dir) + os.pathsep + os.environ['PATH']
        return True

    logger.info("Downloading portable ffmpeg...")
    try:
        # Create directories
        ffmpeg_dir.mkdir(parents=True, exist_ok=True)

        # Download portable ffmpeg
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        response = requests.get(url, stream=True)
        zip_path = ffmpeg_dir / "ffmpeg.zip"

        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Extract ffmpeg
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)

        # Move files from nested directory to bin/ffmpeg
        nested_dir = next(ffmpeg_dir.glob('ffmpeg-*'))
        bin_dir = nested_dir / 'bin'
        for file in bin_dir.glob('*'):
            shutil.move(str(file), str(ffmpeg_dir))

        # Cleanup
        shutil.rmtree(str(nested_dir))
        os.remove(str(zip_path))

        # Add to PATH
        os.environ['PATH'] = str(ffmpeg_dir) + os.pathsep + os.environ['PATH']
        return True

    except Exception as e:
        logger.error(f"Error downloading ffmpeg: {e}")
        return False

def clean_old_files(max_age_days=7):
    """Clean up old files from output and logs directories"""
    try:
        project_root = Path(__file__).parent.parent
        current_time = datetime.now()
        
        # Directories to clean
        dirs_to_clean = [
            project_root / 'output',
            project_root / 'logs'
        ]
        
        for directory in dirs_to_clean:
            if not directory.exists():
                continue
                
            for file_path in directory.glob('*'):
                if not file_path.is_file():
                    continue
                    
                file_age = (current_time - datetime.fromtimestamp(file_path.stat().st_mtime)).days
                if file_age > max_age_days:
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {e}")
                        
    except Exception as e:
        logger.error(f"Error in clean_old_files: {e}")

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent

def ensure_directories():
    """Ensure all required directories exist"""
    project_root = get_project_root()
    directories = ['output', 'assets', 'approved', 'rejected', 'logs']
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            logger.info(f"Created directory: {dir_path}")

def get_random_background_asset():
    """Get a random background video or image from assets directory"""
    project_root = get_project_root()
    backgrounds_dir = project_root / 'assets' / 'backgrounds'
    
    # List all background assets
    video_files = list(backgrounds_dir.glob('*.mp4'))
    image_files = list(backgrounds_dir.glob('*.{jpg,jpeg,png}'))
    
    if not video_files and not image_files:
        # Return default background image path if exists
        default_bg = project_root / 'assets' / 'background.jpg'
        if default_bg.exists():
            return str(default_bg)
        return None
        
    # Prefer videos over images if available
    if video_files:
        return str(random.choice(video_files))
    return str(random.choice(image_files))

def ensure_background_assets():
    """Ensure background assets directory exists and has default background"""
    try:
        project_root = get_project_root()
        backgrounds_dir = project_root / 'assets' / 'backgrounds'
        backgrounds_dir.mkdir(exist_ok=True)
        
        default_bg = project_root / 'assets' / 'background.jpg'
        if not default_bg.exists():
            # Create a simple gradient background as default
            from PIL import Image, ImageDraw
            
            width = 1080
            height = 1920
            image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(image)
            
            for y in range(height):
                r = int(20 + (y / height) * 40)
                g = int(40 + (y / height) * 60)
                b = int(80 + (y / height) * 100)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
                
            image.save(default_bg)
            logger.info("Created default background image")
            
    except Exception as e:
        logger.error(f"Error ensuring background assets: {e}")

if __name__ == "__main__":
    logger = setup_logging()
    ensure_ffmpeg()
    ensure_directories()
    clean_old_files()