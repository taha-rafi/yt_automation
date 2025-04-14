import cv2
import ffmpeg
import numpy as np
import os
import subprocess
import sys
from .utils import ensure_ffmpeg

def check_ffmpeg():
    """Check if ffmpeg is installed and accessible"""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        print("Error: ffmpeg is not installed or not in system PATH")
        print("\nPlease install ffmpeg:")
        if sys.platform.startswith('win'):
            print("1. Download from: https://github.com/BtbN/FFmpeg-Builds/releases")
            print("2. Extract the zip file")
            print("3. Add the bin folder to your system PATH")
        elif sys.platform.startswith('linux'):
            print("Run: sudo apt-get install ffmpeg")
        elif sys.platform.startswith('darwin'):
            print("Run: brew install ffmpeg")
        return False

def create_default_background(width=1080, height=1920):
    """Create a default gradient background for shorts"""
    # Create gradient background
    background = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        color = int(255 * (1 - y/height))  # Gradient from white to black
        background[y, :] = [color, color, color]

    # Add some style - simple rectangle in the middle
    margin = 100
    cv2.rectangle(background,
                 (margin, height//2 - 200),
                 (width - margin, height//2 + 200),
                 (0, 0, 0), 2)

    return background

def create_video(background_image, audio_file, output_file):
    # Ensure ffmpeg is available
    if not ensure_ffmpeg():
        raise RuntimeError("Failed to setup ffmpeg")

    try:
        # Try to load the background image
        img = cv2.imread(background_image)
        if img is None:
            print("Warning: Could not load background image, using default background")
            img = create_default_background()
    except Exception as e:
        print(f"Error loading background image: {e}")
        img = create_default_background()

    target_width = 1080
    target_height = 1920

    # Resize image maintaining aspect ratio and add black padding
    img_aspect = img.shape[1] / img.shape[0]
    target_aspect = target_width / target_height

    if img_aspect > target_aspect:
        # Image is wider than target
        new_width = target_width
        new_height = int(new_width / img_aspect)
        padding_top = (target_height - new_height) // 2
        padding_bottom = target_height - new_height - padding_top
        padding_left = 0
        padding_right = 0
    else:
        # Image is taller than target
        new_height = target_height
        new_width = int(new_height * img_aspect)
        padding_left = (target_width - new_width) // 2
        padding_right = target_width - new_width - padding_left
        padding_top = 0
        padding_bottom = 0

    # Resize image
    img = cv2.resize(img, (new_width, new_height))

    # Add padding
    img = cv2.copyMakeBorder(
        img,
        padding_top,
        padding_bottom,
        padding_left,
        padding_right,
        cv2.BORDER_CONSTANT,
        value=[0, 0, 0]
    )

    # Get audio duration using ffmpeg
    probe = ffmpeg.probe(audio_file)
    audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
    duration = float(probe['format']['duration'])

    # Create temporary video without audio
    temp_video = 'temp_output.mp4'
    height, width = img.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, 30, (width, height))  # 30fps for smoother playback

    # Write the same image for each frame
    n_frames = int(duration * 30)  # 30 fps
    for _ in range(n_frames):
        out.write(img)

    out.release()

    # Combine video with audio using ffmpeg
    input_video = ffmpeg.input(temp_video)
    input_audio = ffmpeg.input(audio_file)

    # Set appropriate encoding parameters for YouTube Shorts
    ffmpeg.output(
        input_video,
        input_audio,
        output_file,
        vcodec='libx264',
        acodec='aac',
        video_bitrate='2500k',
        audio_bitrate='128k',
        r=30,  # 30fps
        pix_fmt='yuv420p',  # Required for compatibility
        **{'loglevel': 'quiet'}
    ).overwrite_output().run()

    # Clean up temporary file
    if os.path.exists(temp_video):
        os.remove(temp_video)

if __name__ == "__main__":
    create_video("../assets/background.jpg", "output.mp3", "output.mp4")