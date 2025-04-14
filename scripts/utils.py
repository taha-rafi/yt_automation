import os
import sys
import requests
import zipfile
import shutil
from pathlib import Path

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
    
    print("Downloading portable ffmpeg...")
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
        print(f"Error downloading ffmpeg: {e}")
        return False

if __name__ == "__main__":
    ensure_ffmpeg()