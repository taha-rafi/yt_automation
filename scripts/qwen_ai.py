import os
import sys
import requests
import json
import numpy as np
import io
import subprocess
import shutil
from pathlib import Path
from scripts.utils import logger, retry_api_call, get_random_background_asset
from ollama import Client
from PIL import Image, ImageDraw, ImageFont
from moviepy.video.VideoClip import VideoClip, ColorClip, ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.AudioClip import AudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

class QwenAI:
    def __init__(self, api_key=None):  # api_key is kept for backward compatibility
        self.logger = logger
        self.client = Client(host='http://localhost:11434')
        self.model = "mistral"  # Using Mistral as the default model
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

    def generate_video(self, text, audio_path, output_path, progress_callback=None):
        """Generate a video with text overlay and animations using MoviePy."""
        try:
            print("Creating video with MoviePy...")
            self.logger.info("Creating animated video...")

            # Get audio duration first
            audio = AudioFileClip(audio_path)
            audio_duration = audio.duration

            # Create a gradient background with dynamic color shift and particles
            def make_frame(t):
                # Create multiple frames for motion blur
                frames = []
                blur_samples = 3
                
                # Define color themes with higher contrast
                themes = [
                    [(20, 30, 50), (40, 60, 100)],  # Darker blue theme
                    [(40, 20, 40), (80, 40, 80)],   # Darker purple theme
                    [(20, 40, 30), (40, 80, 60)]    # Darker teal theme
                ]
                
                # Smoothly transition between themes
                theme_duration = audio_duration / len(themes)  # Complete cycle matches audio duration
                theme_index = int(t / theme_duration)
                theme_progress = (t % theme_duration) / theme_duration
                
                current_theme = themes[theme_index % len(themes)]
                next_theme = themes[(theme_index + 1) % len(themes)]
                
                for i in range(blur_samples):
                    sub_t = t + (i / blur_samples) * 0.04  # 0.04s blur window
                    scale = 1 + 0.02 * sub_t  # Reduced zoom to 2%
                    scaled_h = int(self.height * scale)
                    scaled_w = int(self.width * scale)
                    
                    # Create scaled gradient with dynamic color
                    scaled = np.zeros((scaled_h, scaled_w, 3), dtype=np.uint8)
                    
                    # Generate fewer particles for better visibility
                    num_particles = 30
                    particle_positions = []
                    for p in range(num_particles):
                        # Calculate particle position based on time
                        angle = (p / num_particles) * 2 * np.pi + t * 0.3  # Slower rotation
                        radius = (self.width / 5) * (1 + np.sin(t * 1.5 + p * 0.3) * 0.15)  # Smaller radius
                        x = int(self.width/2 + np.cos(angle) * radius)
                        y = int(self.height/2 + np.sin(angle) * radius)
                        particle_positions.append((x, y))
                    
                    for y in range(scaled_h):
                        progress = y / scaled_h
                        
                        # Interpolate between current and next theme
                        start_color = [
                            int(current_theme[0][c] * (1 - theme_progress) + next_theme[0][c] * theme_progress)
                            for c in range(3)
                        ]
                        end_color = [
                            int(current_theme[1][c] * (1 - theme_progress) + next_theme[1][c] * theme_progress)
                            for c in range(3)
                        ]
                        
                        color = [
                            int(start_color[c] + (end_color[c] - start_color[c]) * progress)
                            for c in range(3)
                        ]
                        
                        # Reduce wave effect
                        wave = np.sin(y / 40 + t * 1.5) * 5  # Smaller amplitude, slower wave
                        color = [min(255, max(0, c + int(wave))) for c in color]
                        scaled[y, :] = color
                    
                    # Add particles with reduced glow
                    for x, y in particle_positions:
                        if 0 <= y < scaled_h and 0 <= x < scaled_w:
                            # Create glowing particle effect
                            glow_radius = 15  # Smaller glow radius
                            for dy in range(-glow_radius, glow_radius + 1):
                                for dx in range(-glow_radius, glow_radius + 1):
                                    py, px = y + dy, x + dx
                                    if 0 <= py < scaled_h and 0 <= px < scaled_w:
                                        distance = np.sqrt(dx*dx + dy*dy)
                                        if distance <= glow_radius:
                                            intensity = (1 - distance/glow_radius) * 0.2  # Reduced intensity
                                            scaled[py, px] = np.minimum(255, scaled[py, px] + np.array([255, 255, 255]) * intensity)
                    
                    # Crop to original size from center
                    start_y = (scaled_h - self.height) // 2
                    start_x = (scaled_w - self.width) // 2
                    frames.append(scaled[start_y:start_y + self.height, start_x:start_x + self.width])
                
                # Average the frames for motion blur
                return np.mean(frames, axis=0).astype(np.uint8)
            
            background = VideoClip(make_frame, duration=audio_duration)
            
            # Create PIL image for text with dynamic effects
            def make_text_frame(t):
                # Create a new image for each frame
                img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 80)
                except:
                    font = ImageFont.load_default()
                
                # Split text into lines
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
                
                # Calculate text position with reduced animation
                line_spacing = 1.2
                font_height = font.size
                total_height = len(lines) * (font_height * line_spacing)
                base_y = (self.height - total_height) // 2
                
                # Add subtle bounce effect synchronized with audio
                bounce_amount = 3  # Reduced bounce
                bounce_freq = 1.0  # Slower bounce
                bounce_offset = bounce_amount * np.sin(t * 2 * np.pi * bounce_freq)
                
                # Add gentle rotation synchronized with audio
                rotation_amount = 1  # Reduced rotation
                rotation = rotation_amount * np.sin(t * 2 * np.pi * 0.5)  # 0.5 Hz
                
                # Calculate opacity for fade effect
                opacity = 1.0
                fade_duration = audio_duration * 0.15  # 15% of audio duration for fade
                if t < fade_duration:
                    opacity = (t / fade_duration) ** 0.5
                elif t > audio_duration - fade_duration:
                    opacity = ((audio_duration - t) / fade_duration) ** 0.5
                
                y = base_y + bounce_offset
                
                # Create rotated image for text
                text_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                
                # Draw each line with glow effect
                for line in lines:
                    bbox = text_draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (self.width - text_width) // 2
                    
                    # Draw glow effect
                    glow_color = (255, 255, 255, int(30 * opacity))  # Reduced glow
                    glow_radius = 2  # Smaller glow radius
                    for offset_x in range(-glow_radius, glow_radius + 1):
                        for offset_y in range(-glow_radius, glow_radius + 1):
                            if offset_x*offset_x + offset_y*offset_y <= glow_radius*glow_radius:
                                text_draw.text(
                                    (x + offset_x, y + offset_y),
                                    line,
                                    font=font,
                                    fill=glow_color
                                )
                    
                    # Draw shadow layers
                    shadow_dist = 2  # Reduced shadow distance
                    shadow_alpha = int(80 * opacity)  # Reduced shadow opacity
                    for i in range(2):  # Fewer shadow layers
                        offset = shadow_dist * (i + 1) / 2
                        shadow_color = (0, 0, 0, shadow_alpha // (i + 1))
                        text_draw.text((x + offset, y + offset), line, font=font, fill=shadow_color)
                    
                    # Draw main text with slight pulse synchronized with audio
                    pulse = int(10 * np.sin(t * 2 * np.pi))  # Reduced pulse
                    text_color = (255, min(255, 255 + pulse), min(255, 255 + pulse), int(255 * opacity))
                    text_draw.text((x, y), line, font=font, fill=text_color)
                    
                    y += font_height * line_spacing
                
                # Rotate the text image
                rotated = text_img.rotate(rotation, expand=False, resample=Image.BICUBIC)
                
                # Composite the rotated text onto the main image
                img.paste(rotated, (0, 0), rotated)
                
                # Convert to numpy array with alpha handling
                frame = np.array(img)
                if frame.shape[2] == 4:
                    rgb = frame[..., :3]
                    alpha = frame[..., 3:4] / 255.0
                    return rgb * alpha + (1 - alpha) * 0
                
                return frame
            
            txt_clip = VideoClip(make_text_frame, duration=audio_duration)
            
            # Combine clips
            video = CompositeVideoClip([background, txt_clip])
            
            # Add audio and match duration
            video = video.set_duration(audio_duration)
            video = video.set_audio(audio)
            
            # Write the result
            video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',  
                bitrate='4000k',  
                threads=4,  
                ffmpeg_params=[
                    '-profile:v', 'high',  
                    '-level', '4.0',  
                    '-pix_fmt', 'yuv420p',  
                    '-movflags', '+faststart'  
                ]
            )

            # Clean up
            video.close()
            audio.close()

            return True

        except Exception as e:
            self.logger.error(f"Error generating video: {str(e)}")
            return False

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
        prompt = f"""Generate a short, inspiring quote about {topic}. 
        The quote should be original, meaningful, and no longer than 15 words.
        Return only the quote, without quotation marks or attribution."""
        
        try:
            response = self.generate_text(prompt)
            return response.strip() if response else None
        except Exception as e:
            self.logger.error(f"Error generating quote: {str(e)}")
            return None