import os
import json
from pathlib import Path
from tqdm import tqdm
from scripts.qwen_ai import QwenAI
from scripts.utils import logger

class VideoCreator:
    def __init__(self):
        # Load config
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.qwen = QwenAI(config['openrouter_api_key'])

    def create_video(self, quote_text, audio_file, output_file):
        """Create a video using OpenRouter API with progress tracking"""
        try:
            logger.info("Starting video creation process...")

            # Create progress bar
            with tqdm(total=100, desc="Creating Video", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
                pbar.update(10)
                logger.info("Initializing video generation...")

                # Start video generation
                success = self.qwen.generate_video(quote_text, audio_file, output_file,
                                                progress_callback=lambda p: pbar.update(int(p * 80)))

                if success:
                    pbar.update(100 - pbar.n)  # Ensure we reach 100%
                    logger.info("Video created successfully!")
                    return True
                else:
                    logger.error("Failed to create video")
                    return False

        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return False

if __name__ == "__main__":
    creator = VideoCreator()
    creator.create_video(
        "Test quote text for video creation",
        "test_audio.mp3",
        "test_output.mp4"
    )