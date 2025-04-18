import sys
sys.path.append(r'C:\Users\NBC\AppData\Roaming\Python\Python310\site-packages')
from moviepy import ImageClip

# Use the existing red background image
clip = ImageClip("output/background_sd.png").with_duration(5)
clip.write_videofile("output/test_red_video.mp4", fps=24)
print("[TEST] test_red_video.mp4 created!")
