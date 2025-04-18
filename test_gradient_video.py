from moviepy.editor import ImageClip
import os

WIDTH = 1080
HEIGHT = 1920
DURATION = 5  # seconds

background_path = os.path.join('assets', 'backgrounds', 'gradient_debug.png')
output_path = os.path.join('output', 'test_gradient_only.mp4')

if not os.path.exists(background_path):
    raise FileNotFoundError(f"Gradient image not found: {background_path}")

clip = ImageClip(background_path).set_duration(DURATION)
if clip.size != (WIDTH, HEIGHT):
    clip = clip.resize(newsize=(WIDTH, HEIGHT))
clip.write_videofile(output_path, fps=24)
print(f"Test gradient video saved to {output_path}")
