import os
import sys
import requests
import json
import numpy as np
import io
import subprocess
import shutil
import base64
from pathlib import Path
from scripts.utils import logger, retry_api_call, get_random_background_asset
from ollama import Client
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, ColorClip, ImageClip, CompositeVideoClip
from moviepy.audio.AudioClip import AudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import torch
from diffusers import StableDiffusionPipeline

class QwenAI:
    def __init__(self, api_key=None):  # api_key is kept for backward compatibility
        self.logger = logger
        self.client = Client(host='http://localhost:11434')
        self.model = "mistral:latest"  # Use explicit model tag
        self.width = 1080  # Width for portrait mode (9:16)
        self.height = 1920  # Height for portrait mode (9:16)
        self.project_root = Path(__file__).parent.parent
        self.temp_dir = self.project_root / 'output'
        self.ffmpeg_path = str(self.project_root / 'tools' / 'ffmpeg' / 'ffmpeg-master-latest-win64-gpl' / 'bin' / 'ffmpeg.exe')
        self._ensure_ffmpeg()

    def _ensure_ffmpeg(self):
        """Ensure ffmpeg is available in the system."""
        try:
            if not os.path.exists(self.ffmpeg_path):
                raise RuntimeError(f"ffmpeg not found at {self.ffmpeg_path}")
            subprocess.run([self.ffmpeg_path, "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, RuntimeError) as e:
            self.logger.error(f"Error checking ffmpeg: {str(e)}")
            raise RuntimeError("ffmpeg is required but not available")

    def _create_gradient_background(self):
        """Create a vertical random gradient background image for testing."""
        print("[DEBUG] Creating random gradient background...")
        from random import randint
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        # Random start/end colors
        r1, g1, b1 = randint(0,255), randint(0,255), randint(0,255)
        r2, g2, b2 = randint(0,255), randint(0,255), randint(0,255)
        for y in range(self.height):
            r = int(r1 + (r2 - r1) * y / self.height)
            g = int(g1 + (g2 - g1) * y / self.height)
            b = int(b1 + (b2 - b1) * y / self.height)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        return img

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
            # Try multiple common font paths
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",  # Windows
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "/System/Library/Fonts/Arial.ttf"  # macOS
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 80)
                    break
            if font is None:
                font = ImageFont.load_default()
        except Exception as e:
            self.logger.warning(f"Error loading font: {e}, using default")
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

    def generate_sd_image(self, prompt, out_path):
        """Generate an image using local Stable Diffusion, asset image, or random gradient based on config."""
        import json
        config_path = self.project_root / 'config.json'
        use_bg = 'sd'  # default
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                use_bg = config.get('background_mode', 'sd')
        print(f"[DEBUG] Background mode: {use_bg}")
        if use_bg == 'gradient':
            image = self._create_gradient_background()
            image.save(out_path)
            print(f"[DEBUG] Random gradient background saved to {out_path}")
            return out_path
        elif use_bg == 'asset':
            from scripts.utils import get_random_background_asset
            asset_path = get_random_background_asset()
            if asset_path:
                img = Image.open(asset_path).resize((self.width, self.height))
                img.save(out_path)
                print(f"[DEBUG] Asset background {asset_path} saved to {out_path}")
                return out_path
            else:
                print("[WARN] No asset found, using gradient fallback.")
                image = self._create_gradient_background()
                image.save(out_path)
                return out_path
        # default: SD
        print(f"[DEBUG] Generating SD image with prompt: {prompt}")
        model_id = "runwayml/stable-diffusion-v1-5"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[DEBUG] Using device: {device}")
        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if device=="cuda" else torch.float32
            )
            pipe = pipe.to(device)
            generator = torch.Generator(device=device).manual_seed(42)
            print("[DEBUG] Pipeline loaded. Generating image...")
            result = pipe(
                prompt,
                negative_prompt="text, watermark, logo, signature, people, face, hands, nsfw, blurry, low quality, artifacts",
                height=self.height,
                width=self.width,
                num_inference_steps=10,
                guidance_scale=8.0,
                generator=generator
            )
            image = result.images[0]
            image.save(out_path)
            try:
                from PIL import Image as PILImage
                img = PILImage.open(out_path).convert("RGB")
                img.save(out_path)
                print(f"[DEBUG] Image at {out_path} converted to RGB and saved again.")
            except Exception as e:
                print(f"[WARN] Could not convert image to RGB: {e}")
            print(f"[DEBUG] SD image saved to {out_path}")
            return out_path
        except Exception as e:
            print(f"[ERROR] Stable Diffusion image generation failed: {e}")
            self.logger.error(f"Stable Diffusion image generation failed: {e}")
            image = self._create_gradient_background()
            image.save(out_path)
            try:
                from PIL import Image as PILImage
                img = PILImage.open(out_path).convert("RGB")
                img.save(out_path)
                print(f"[DEBUG] Image at {out_path} converted to RGB and saved again.")
            except Exception as e:
                print(f"[WARN] Could not convert image to RGB: {e}")
            print(f"[DEBUG] Fallback gradient image saved to {out_path}")
            return out_path

    def generate_video(self, text, audio_path, output_path, progress_callback=None):
        """Generate a video with text overlay and animations using MoviePy and a Stable Diffusion generated background or a vertical blue gradient."""
        try:
            print(f"[DEBUG] Creating video with text: {text}")
            print(f"[DEBUG] Audio path: {audio_path}")
            print(f"[DEBUG] Output video path: {output_path}")
            self.logger.info("Creating animated video...")

            # Get audio duration first
            audio = AudioFileClip(audio_path)
            audio_duration = audio.duration

            # Generate background image using Stable Diffusion
            prompt = f"A beautiful abstract vertical background, no text, 9:16 aspect ratio, vibrant colors, soft lighting"
            background_img_path = os.path.join(os.path.dirname(output_path), 'background_sd.png')
            print(f"[DEBUG] Generating background image at: {background_img_path}")
            self.generate_sd_image(prompt, background_img_path)
            print(f"[DEBUG] Background image generated.")

            # Resize background using PIL (works with any MoviePy version)
            img = Image.open(background_img_path)
            img = img.resize((self.width, self.height))
            img.save(background_img_path)
            background_clip = ImageClip(background_img_path).with_duration(audio_duration).with_opacity(1)

            def make_text_frame(t):
                img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 80)
                except:
                    font = ImageFont.load_default()
                words = text.split()
                lines = []
                current_line = []
                max_width = self.width - 100
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    if bbox[2] <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                line_spacing = 1.2
                font_height = font.size
                total_height = len(lines) * (font_height * line_spacing)
                base_y = (self.height - total_height) // 2
                bounce_amount = 3
                bounce_freq = 1.0
                bounce_offset = bounce_amount * np.sin(t * 2 * np.pi * bounce_freq)
                opacity = 1.0
                fade_duration = audio_duration * 0.15
                if t < fade_duration:
                    opacity = (t / fade_duration) ** 0.5
                elif t > audio_duration - fade_duration:
                    opacity = ((audio_duration - t) / fade_duration) ** 0.5
                y = base_y + bounce_offset
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (self.width - text_width) // 2
                    shadow_dist = 3
                    shadow_alpha = int(100 * opacity)
                    shadow_color = (0, 0, 0, shadow_alpha)
                    for i in range(2):
                        draw.text((x + shadow_dist + i, y + shadow_dist + i), line, font=font, fill=shadow_color)
                    text_color = (255, 255, 255, int(255 * opacity))
                    draw.text((x, y), line, font=font, fill=text_color)
                    y += font_height * line_spacing
                frame = np.array(img)
                return frame  # Preserve alpha channel for transparency
            txt_clip = VideoClip(make_text_frame, duration=audio_duration)
            # Removed set_position and set_opacity, as they are not available for VideoClip in v2.x

            # Combine clips
            video = CompositeVideoClip([background_clip, txt_clip])
            # Set audio and write video
            video.audio = audio
            video.write_videofile(output_path, fps=24, audio_codec='aac')
            audio.close()
            print(f"Video successfully saved to {output_path}")
            if progress_callback:
                progress_callback(100)
            return True
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            print(f"Error generating video: {e}")
            raise

    def generate_text(self, prompt, max_tokens=500):
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt
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

    def generate_creative_quote(self, topic):
        """Generate a creative quote using the Mistral model"""
        import random
        randomizer = random.randint(0, 99999)
        prompt = f"""Generate a short, inspiring quote about {topic}.\nThe quote should be original, meaningful, and no longer than 15 words.\nReturn only the quote, without quotation marks or attribution.\nRandomizer: {randomizer}"""
        print(f"[DEBUG] Quote prompt: {prompt}")
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt
            )
            return response['response'].strip() if response else None
        except Exception as e:
            self.logger.error(f"Error generating quote: {str(e)}")
            return None