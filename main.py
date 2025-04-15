import os
import sys
import json
from datetime import datetime
from pathlib import Path
from scripts.generate_script import get_random_quote, generate_title_and_description
from scripts.text_to_speech import text_to_speech
from scripts.online_video_creator import VideoCreator
from scripts.upload_youtube import upload_to_youtube

def load_config():
    """Load configuration from config.json"""
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return json.load(f)
    else:
        config = {
            'bannerbear_api_key': '',  # Add your Bannerbear API key here
            'admin_chat_ids': [],
            'auto_approve_after': 30
        }
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        return config

def ensure_directories():
    """Ensure all required directories exist"""
    os.makedirs('output', exist_ok=True)
    os.makedirs('assets', exist_ok=True)

def generate_output_paths():
    """Generate unique output paths for files based on timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        'audio': f"output/speech_{timestamp}.mp3",
        'video': f"output/video_{timestamp}.mp4"
    }

def main():
    try:
        # Initialize video creator
        video_creator = VideoCreator()

        # Ensure directories exist
        ensure_directories()

        # Generate paths for output files
        paths = generate_output_paths()

        # Step 1: Generate a random motivational quote and metadata
        quote, category = get_random_quote()
        title, description = generate_title_and_description(quote, category)
        print(f"Generated Quote ({category}): {quote}")

        # Step 2: Convert quote to speech
        print("Converting text to speech...")
        text_to_speech(quote, paths['audio'])

        # Step 3: Create video using moviepy
        print("Creating video...")
        if not video_creator.create_video(quote, paths['audio'], paths['video']):
            raise RuntimeError("Failed to create video")

        # Step 4: Upload to YouTube
        print("Uploading to YouTube...")
        upload_to_youtube(paths['video'], title, description)

        print("\nProcess completed successfully!")
        print(f"Video saved as: {paths['video']}")
        print(f"Title: {title}")
        print(f"Category: {category}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()