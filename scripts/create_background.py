import cv2
import numpy as np
import os
from pathlib import Path

def create_motivational_background(width=1080, height=1920):
    """Create a gradient background with a motivational design"""
    # Create gradient background
    background = np.zeros((height, width, 3), dtype=np.uint8)

    # Create a blue-purple gradient
    for y in range(height):
        # Mix blue and purple based on y position
        blue = int(255 * (1 - y/height))  # Blue decreases from top to bottom
        red = int(128 * (y/height))       # Red increases from top to bottom
        background[y, :] = [blue, 0, red]  # BGR format

    # Add a centered rectangle for text
    margin_x = int(width * 0.1)
    margin_y = int(height * 0.4)
    cv2.rectangle(
        background,
        (margin_x, margin_y),
        (width - margin_x, height - margin_y),
        (255, 255, 255),
        2
    )

    # Add some decorative elements
    # Top corners
    corner_size = 50
    cv2.line(background, (margin_x, margin_y), (margin_x + corner_size, margin_y), (255, 255, 255), 2)
    cv2.line(background, (margin_x, margin_y), (margin_x, margin_y + corner_size), (255, 255, 255), 2)

    cv2.line(background, (width - margin_x, margin_y), (width - margin_x - corner_size, margin_y), (255, 255, 255), 2)
    cv2.line(background, (width - margin_x, margin_y), (width - margin_x, margin_y + corner_size), (255, 255, 255), 2)

    # Bottom corners
    cv2.line(background, (margin_x, height - margin_y), (margin_x + corner_size, height - margin_y), (255, 255, 255), 2)
    cv2.line(background, (margin_x, height - margin_y), (margin_x, height - margin_y - corner_size), (255, 255, 255), 2)

    cv2.line(background, (width - margin_x, height - margin_y), (width - margin_x - corner_size, height - margin_y), (255, 255, 255), 2)
    cv2.line(background, (width - margin_x, height - margin_y), (width - margin_x, height - margin_y - corner_size), (255, 255, 255), 2)

    return background

if __name__ == "__main__":
    # Create the background
    bg = create_motivational_background()

    # Save to assets folder
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets"
    assets_dir.mkdir(exist_ok=True)

    cv2.imwrite(str(assets_dir / "background.jpg"), bg)
    print(f"Background image created at: {assets_dir / 'background.jpg'}")