import os
import sys
import requests
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import ffmpeg
import subprocess
from pathlib import Path

class QwenAI:
    def __init__(self, api_key):
        self.client = None
        self.api_key = api_key
        self.width = 1080
        self.height = 1920
        self.project_root = Path(__file__).parent.parent
        self.ffmpeg_path = str(self.project_root / 'bin' / 'ffmpeg' / 'ffmpeg.exe')
        self.temp_dir = self.project_root / 'output'

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

    def generate_video(self, text, audio_path, output_path):
        """Generate a video with text overlay and background"""
        try:
            print("Creating base image...")
            # Create base image with gradient
            base_image = self._create_gradient_background()

            print("Adding text overlay...")
            # Add text overlay
            final_image = self._add_text_to_image(base_image, text)

            # Save temporary image
            temp_image_path = "temp_frame.jpg"
            temp_video_path = "temp_video.mp4"
            final_image.save(temp_image_path)

            print("Creating video from image...")
            # Get audio duration using ffprobe
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['format']['duration'])

            # Create video from image using ffmpeg
            (
                ffmpeg
                .input(temp_image_path, loop=1, t=duration)
                .output(temp_video_path, vcodec='libx264', pix_fmt='yuv420p', r=30)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            print("Adding audio to video...")
            # Add audio to video
            video = ffmpeg.input(temp_video_path)
            audio = ffmpeg.input(audio_path)

            # Combine video with audio
            (
                ffmpeg
                .output(video, audio, output_path,
                       vcodec='copy',
                       acodec='aac',
                       strict='experimental')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            # Cleanup temporary files
            os.remove(temp_image_path)
            os.remove(temp_video_path)

            return True

        except Exception as e:
            print(f"Error in video generation: {e}")
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            return False

    def generate_creative_quote(self, topic):
        """Generate a creative quote using Qwen AI"""
        try:
            from openai import OpenAI
            if self.client is None:
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key
                )

            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://youtube-shorts-generator.com",
                    "X-Title": "YouTube Shorts Generator"
                },
                model="qwen/qwen2.5-72b-instruct:free",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative writer specializing in motivational and inspirational quotes."
                    },
                    {
                        "role": "user",
                        "content": f"Create a unique and inspiring quote about {topic}. Make it concise and impactful."
                    }
                ]
            )

            quote = completion.choices[0].message.content
            if not quote:
                raise Exception("No quote generated")

            # Clean up the quote
            quote = quote.strip().strip('"').strip()
            return quote

        except Exception as e:
            print(f"Error in Qwen AI quote generation: {e}")
            return None