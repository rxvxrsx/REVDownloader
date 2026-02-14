#!/usr/bin/env python3
"""
Create a simple icon for REV Music Downloader
Requires: pip install pillow

Usage: python create_icon.py [style]
  style: 1 = Music note (default), 2 = Letter R, 3 = Download arrow
"""

from PIL import Image, ImageDraw, ImageFont
import sys

def create_music_icon():
    """Create music note icon drawn as shapes"""
    
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        scale = size / 256
        margin = int(10 * scale)
        
        # Background circle
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill='#00d9a5'
        )
        
        # Inner circle
        inner_margin = int(25 * scale)
        draw.ellipse(
            [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
            fill='#1e1e2e'
        )
        
        # Draw music note (beamed eighth notes)
        note_color = '#00d9a5'
        cx = size // 2
        cy = size // 2
        
        # Note heads
        head_size = int(16 * scale)
        head1_x = cx - int(20 * scale)
        head1_y = cy + int(15 * scale)
        head2_x = cx + int(20 * scale)
        head2_y = cy + int(5 * scale)
        
        draw.ellipse([head1_x - head_size//2, head1_y - head_size//2,
                      head1_x + head_size//2, head1_y + head_size//2], fill=note_color)
        draw.ellipse([head2_x - head_size//2, head2_y - head_size//2,
                      head2_x + head_size//2, head2_y + head_size//2], fill=note_color)
        
        # Stems
        stem_width = max(2, int(4 * scale))
        stem_height = int(50 * scale)
        draw.rectangle([head1_x, head1_y - stem_height, head1_x + stem_width, head1_y], fill=note_color)
        draw.rectangle([head2_x, head2_y - stem_height, head2_x + stem_width, head2_y], fill=note_color)
        
        # Beam
        beam_height = int(8 * scale)
        draw.rectangle([head1_x, head1_y - stem_height, head2_x + stem_width, head1_y - stem_height + beam_height], fill=note_color)
        
        images.append(img)
    
    images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
    images[0].save('icon.png', format='PNG')
    print("Music note icon created!")

def create_r_icon():
    """Create letter R icon"""
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        scale = size / 256
        margin = int(10 * scale)
        
        draw.ellipse([margin, margin, size - margin, size - margin], fill='#00d9a5')
        
        # Letter R
        try:
            font = ImageFont.truetype("arialbd.ttf", int(140 * scale))
        except:
            try:
                font = ImageFont.truetype("arial.ttf", int(140 * scale))
            except:
                font = ImageFont.load_default()
        
        text = "R"
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (size - (bbox[2] - bbox[0])) // 2
        y = (size - (bbox[3] - bbox[1])) // 2
        draw.text((x, y), text, fill='#000000', font=font)
        
        images.append(img)
    
    images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
    images[0].save('icon.png', format='PNG')
    print("Letter R icon created!")

def create_arrow_icon():
    """Create download arrow icon"""
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        scale = size / 256
        margin = int(10 * scale)
        
        draw.ellipse([margin, margin, size - margin, size - margin], fill='#00d9a5')
        
        cx = size // 2
        cy = size // 2
        arrow_color = '#000000'
        
        # Arrow shaft
        line_width = max(3, int(12 * scale))
        draw.line([(cx, cy - int(40 * scale)), (cx, cy + int(20 * scale))], fill=arrow_color, width=line_width)
        
        # Arrow head
        head_size = int(25 * scale)
        draw.polygon([
            (cx - head_size, cy + int(10 * scale)),
            (cx + head_size, cy + int(10 * scale)),
            (cx, cy + int(40 * scale))
        ], fill=arrow_color)
        
        images.append(img)
    
    images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
    images[0].save('icon.png', format='PNG')
    print("Download arrow icon created!")

if __name__ == '__main__':
    # Get style from command line argument or default to music note
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = "1"
    
    if choice == "1":
        create_music_icon()
    elif choice == "2":
        create_r_icon()
    elif choice == "3":
        create_arrow_icon()
    else:
        print("Usage: python create_icon.py [1|2|3]")
        print("  1 = Music note (default)")
        print("  2 = Letter R")
        print("  3 = Download arrow")
        print()
        print("Creating music note icon...")
        create_music_icon()
