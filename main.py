import os
import sys
from datetime import datetime
from pathlib import Path
from scripts.generate_script import get_random_quote, generate_title_and_description
from scripts.text_to_speech import text_to_speech
from scripts.create_video import create_video
from scripts.upload_youtube import upload_to_youtube

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
        # Get the absolute path of the project root
        project_root = Path(__file__).parent.absolute()

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

        # Step 3: Create video with audio and background image
        print("Creating video...")
        background_image = str(project_root / "assets" / "background.jpg")
        if not os.path.exists(background_image):
            raise FileNotFoundError(f"Background image not found: {background_image}")

        create_video(background_image, paths['audio'], paths['video'])

        # Step 4: Upload to YouTube (placeholder)
        print("Uploading to YouTube...")
        upload_to_youtube(paths['video'], title, description)

        print("\nProcess completed successfully!")
        print(f"Video saved as: {paths['video']}")
        print(f"Title: {title}")
        print(f"Category: {category}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()