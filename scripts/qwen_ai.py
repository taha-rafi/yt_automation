import os
import sys
import requests
import json
from ollama import Client
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import ffmpeg
import subprocess
from pathlib import Path
from scripts.utils import logger, retry_api_call, get_random_background_asset

class QwenAI:
    def __init__(self, api_key=None):  # api_key is kept for backward compatibility
        self.client = Client(host='http://localhost:11434')
        self.model = "mistral"  # Using Mistral as the default model
        self.width = 1080
        self.height = 1920
        self.project_root = Path(__file__).parent.parent
        self.ffmpeg_path = str(self.project_root / 'bin' / 'ffmpeg' / 'ffmpeg.exe')
        self.temp_dir = self.project_root / 'output'
        self.logger = logger

    def _create_gradient_background(self):
        """Create a gradient background image"""
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        for y in range(self.height):
            # Create a smooth gradient from dark to light blue
            r = int(20 + (y / self.height) * 40)
            g = int(40 + (y / self.height) * 60)
            b = int(80 + (y / self.height) * 100)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        return image

    def _add_text_to_image(self, image, text):
        """Add text overlay to the image"""
        draw = ImageDraw.Draw(image)

        # Split text into lines
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            if len(current_line) >= 4:
                lines.append(' '.join(current_line))
                current_line = []
        if current_line:
            lines.append(' '.join(current_line))

        formatted_text = '\n'.join(lines)

        # Try to use Arial font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            except:
                font = ImageFont.load_default()

        # Calculate text position
        text_bbox = draw.multiline_textbbox((0, 0), formatted_text, font=font, align='center')
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2

        # Draw text outline
        outline_color = "black"
        outline_width = 3
        for adj in range(-outline_width, outline_width+1):
            for adj2 in range(-outline_width, outline_width+1):
                draw.multiline_text(
                    (x+adj, y+adj2),
                    formatted_text,
                    font=font,
                    fill=outline_color,
                    align='center'
                )

        # Draw main text
        draw.multiline_text(
            (x, y),
            formatted_text,
            font=font,
            fill="white",
            align='center'
        )

        return image

    def generate_video(self, text, audio_path, output_path, progress_callback=None):
        """Generate a video with text overlay and audio."""
        try:
            print("Creating video from image...")
            self.logger.info("Creating video with text overlay...")

            # Use a temp file in the same directory as the output
            output_dir = os.path.dirname(output_path)
            temp_video = os.path.join(output_dir, "temp_video.mp4")

            # Create the video from the image
            image = self._create_gradient_background()
            image = self._add_text_to_image(image, text)
            image.save(temp_video)

            print("Adding audio to video...")
            # Get audio duration
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['format']['duration'])

            # Create video stream
            try:
                stream = ffmpeg.input(temp_video).video
                audio = ffmpeg.input(audio_path).audio

                # Combine video and audio
                ffmpeg.output(
                    stream,
                    audio,
                    output_path,
                    vcodec='libx264',
                    acodec='aac'
                ).overwrite_output().run()

                # Clean up temp file
                if os.path.exists(temp_video):
                    os.remove(temp_video)

                return True
            except Exception as e:
                print(f"Error in video generation: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"Error generating video: {str(e)}")
            return False

    def generate_text(self, prompt, max_tokens=500):
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                max_tokens=max_tokens
            )
            return response['response']
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return None

    def generate_script(self, topic, style="informative and engaging", length="short"):
        prompt = f"Write a {length} script about {topic}. The style should be {style}. "
        prompt += "The script should be suitable for a vertical video format (YouTube Shorts/TikTok)."
        
        response = self.generate_text(prompt)
        if response:
            return response.strip()
        return None

    def continue_iteration(self, previous_response):
        try:
            response = self.client.generate(
                model=self.model,
                prompt=previous_response,
                system="Continue from where you left off.",
                stream=False
            )
            return response['response']
        except Exception as e:
            self.logger.error(f"Error continuing iteration: {str(e)}")
            return None