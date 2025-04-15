import os
from gtts import gTTS
from pathlib import Path
from scripts.utils import logger, retry_api_call, load_config
import time

@retry_api_call(max_retries=3, delay=2)
def text_to_speech(text, output_file):
    """Convert text to speech using Google Text-to-Speech"""
    try:
        logger.info("Initializing text-to-speech conversion...")
        
        # Create gTTS instance
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save the audio file
        tts.save(output_file)
        
        logger.info(f"Successfully saved audio to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {str(e)}")
        raise

if __name__ == "__main__":
    from scripts.utils import setup_logging
    logger = setup_logging()
    sample_text = "The best way to get started is to quit talking and begin doing."
    text_to_speech(sample_text, "output.mp3")