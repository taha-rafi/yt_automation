import os
import json
from pathlib import Path
from .qwen_ai import QwenAI

class VideoCreator:
    def __init__(self):
        # Load config
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        self.qwen = QwenAI(config['openrouter_api_key'])

    def create_video(self, quote_text, audio_file, output_file):
        """Create a video using OpenRouter API"""
        try:
            print("Generating video with OpenRouter API...")
            success = self.qwen.generate_video(quote_text, audio_file, output_file)
            return success

        except Exception as e:
            print(f"Error creating video: {e}")
            return False

if __name__ == "__main__":
    creator = VideoCreator()
    creator.create_video(
        "Test quote text for video creation",
        "test_audio.mp3",
        "test_output.mp4"
    )