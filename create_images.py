from PIL import Image, ImageDraw, ImageFont
import os

def create_logo():
    # Create a new image with a white background
    img = Image.new('RGB', (200, 50), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw text
    draw.text((10, 10), "EcoFarm Connect", fill='darkgreen')
    
    # Save the image
    img.save('connect/static/connect/images/logo.png')

def create_favicon():
    # Create a new image with a transparent background
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple icon
    draw.ellipse([0, 0, 31, 31], fill='darkgreen')
    draw.text((8, 8), "EC", fill='white')
    
    # Save the image
    img.save('connect/static/connect/images/favicon.png')

# Create directories if they don't exist
os.makedirs('connect/static/connect/images', exist_ok=True)

# Create images
create_logo()
create_favicon() 