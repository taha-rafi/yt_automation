import os
import json
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from scripts.utils import logger, retry_api_call

@retry_api_call(max_retries=3, delay=2, backoff=2)
def text_to_speech_api_call(client, text):
    """Make the TTS API call with retry support"""
    return client.audio.speech.create(
        model="azure/11labs",
        voice="alloy",
        input=text
    )

def text_to_speech(text, output_file):
    """Convert text to speech using OpenRouter's TTS API with progress tracking"""
    try:
        # Load config
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        logger.info("Initializing text-to-speech conversion...")
        with tqdm(total=100, desc="Converting to Speech", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
            # Initialize OpenRouter client
            pbar.update(10)
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=config['openrouter_api_key']
            )

            # Use OpenRouter's TTS endpoint with retries
            pbar.update(20)
            logger.info("Generating speech...")
            response = text_to_speech_api_call(client, text)

            # Save the audio file with progress tracking
            pbar.update(70)
            logger.info("Saving audio file...")
            response.stream_to_file(output_file)
            
            pbar.update(100 - pbar.n)  # Complete progress bar
            logger.info("Speech generation completed successfully")
            return True

    except Exception as e:
        logger.error(f"Error in text to speech conversion: {e}")
        if os.path.exists(output_file):
            try:
                os.remove(output_file)  # Cleanup failed output
            except:
                pass
        return False

if __name__ == "__main__":
    from scripts.utils import setup_logging
    logger = setup_logging()
    sample_text = "The best way to get started is to quit talking and begin doing."
    text_to_speech(sample_text, "output.mp3")