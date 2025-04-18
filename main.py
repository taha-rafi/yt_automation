import os
from datetime import datetime
from scripts.ai_generator import AIScriptGenerator
from scripts.online_video_creator import VideoCreator
from scripts.text_to_speech import text_to_speech
from scripts.upload_youtube import upload_to_youtube
from scripts.utils import logger
from pathlib import Path

def main():
    """Main workflow for generating, voicing, creating, and uploading a YouTube Shorts video."""
    logger.info("Starting YouTube Shorts Generator")
    generator = AIScriptGenerator()
    video_creator = VideoCreator()
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    uploads_dir = Path("uploads")
    run_dir = uploads_dir / now
    (run_dir / "background").mkdir(parents=True, exist_ok=True)
    (run_dir / "audio").mkdir(parents=True, exist_ok=True)
    (run_dir / "video").mkdir(parents=True, exist_ok=True)
    (run_dir / "text").mkdir(parents=True, exist_ok=True)
    paths = {
        'audio': str(run_dir / "audio" / f"speech_{now}.mp3"),
        'video': str(run_dir / "video" / f"video_{now}.mp4")
    }

    # Step 1: Generate quote
    quote, category = generator.generate_quote()
    title = quote if len(quote) < 100 else quote[:97] + '...'
    description = quote + "\n\n" if quote else ""
    description += " ".join([f"#{tag}" for tag in ["motivation", "inspiration", "quotes", "shorts", category]])
    logger.info(f"Using quote ({category}): {quote}")

    # Save quote and metadata
    with open(run_dir / "text" / "quote.txt", "w", encoding="utf-8") as f:
        f.write(quote)
    with open(run_dir / "text" / "meta.txt", "w", encoding="utf-8") as f:
        f.write(f"category: {category}\ntitle: {title}\ndescription: {description}")

    # Step 2: Convert quote to speech
    logger.info("Converting text to speech...")
    if not text_to_speech(quote, paths['audio']):
        raise RuntimeError("Failed to convert text to speech")

    # Step 3: Create video
    logger.info("Creating video...")
    if not video_creator.create_video(quote, paths['audio'], paths['video']):
        raise RuntimeError("Failed to create video")

    # Move background image if generated
    background_img = Path("output/background_sd.png")
    if background_img.exists():
        dest_bg = run_dir / "background" / background_img.name
        background_img.replace(dest_bg)

    # Step 4: Upload to YouTube
    logger.info("Uploading to YouTube...")
    # Prepare hashtags for tags (remove # and split)
    tags = [tag.replace("#", "") for tag in ["motivation", "inspiration", "quotes", "shorts", category] if tag]

    # Use background image as thumbnail if it exists
    thumbnail_path = str((run_dir / "background" / "background_sd.png"))
    if not Path(thumbnail_path).exists():
        thumbnail_path = None

    if upload_to_youtube(paths['video'], title, description, thumbnail_path=thumbnail_path, tags=tags):
        logger.info("Upload successful!")
        logger.info(f"Title: {title}")
        logger.info(f"Category: {category}")
    else:
        raise RuntimeError("Failed to upload video")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")