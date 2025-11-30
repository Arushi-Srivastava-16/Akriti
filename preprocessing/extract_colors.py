"""
Extract colors from floor plan images and update room_colors_config.py

This script analyzes images in the dataset to find the exact colors used
for each room type and updates the configuration file.
"""

import numpy as np
from PIL import Image
from pathlib import Path
from collections import Counter
import json

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "data" / "raw" / "images"
MAPPING_FILE = BASE_DIR / "data" / "image_annotation_mapping.json"


def rgb_to_hex(r, g, b):
    """Convert RGB to hex."""
    return f"#{r:02x}{g:02x}{b:02x}"


def analyze_image_colors(image_path: Path):
    """Extract unique colors from an image."""
    img = Image.open(image_path)
    img_array = np.array(img)
    
    # Convert RGBA to RGB if needed
    if img_array.shape[-1] == 4:
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3:] / 255.0
        white_bg = np.ones_like(rgb) * 255
        img_array = (rgb * alpha + white_bg * (1 - alpha)).astype(np.uint8)
    
    # Get unique colors
    pixels = img_array.reshape(-1, 3)
    unique_colors = np.unique(pixels, axis=0)
    
    return unique_colors


def categorize_color(color):
    """Categorize a color based on RGB values."""
    r, g, b = int(color[0]), int(color[1]), int(color[2])
    
    # Skip background colors
    if r > 240 and g > 240 and b > 240:  # White
        return "background"
    if r < 15 and g < 15 and b < 15:  # Black
        return "black"
    if r > 200 and g < 50 and b < 50:  # Bright red (doors)
        return "red_door"
    
    # Room colors based on user's description
    # Dark green = balcony
    if r < 120 and g > 100 and b < 100:
        return "balcony"
    
    # Orange = master bedroom
    if r > 200 and 100 < g < 200 and b < 100:
        return "master_bedroom"
    
    # Light blue = bathroom
    if b > 150 and b > r and b > g and r < 180 and g < 180:
        return "bathroom"
    
    # Yellow = common room
    if r > 200 and g > 200 and b < 100:
        return "common_room"
    
    # Light green/cream = living room
    if 150 < r < 250 and 150 < g < 250 and 100 < b < 200:
        if abs(g - r) < 60:
            return "living_room"
    
    # Red/pink = kitchen (but not bright red which is doors)
    if r > 180 and g < 150 and b < 150 and not (r > 200 and g < 50 and b < 50):
        return "kitchen"
    
    return "unknown"


def extract_colors_from_dataset(num_samples=10):
    """Extract colors from multiple images in the dataset."""
    
    # Load mapping
    if not MAPPING_FILE.exists():
        print("❌ Mapping file not found. Run create_mapping.py first!")
        return
    
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    
    print(f"📊 Analyzing {num_samples} images from dataset...")
    
    # Collect colors by category
    color_categories = {
        "balcony": [],
        "master_bedroom": [],
        "bathroom": [],
        "common_room": [],
        "living_room": [],
        "kitchen": [],
    }
    
    # Sample images
    sample_pairs = mapping["pairs"][:num_samples]
    
    for pair in sample_pairs:
        image_path = BASE_DIR / pair["image_path"]
        if not image_path.exists():
            continue
        
        try:
            colors = analyze_image_colors(image_path)
            
            for color in colors:
                category = categorize_color(color)
                if category in color_categories:
                    r, g, b = int(color[0]), int(color[1]), int(color[2])
                    hex_color = rgb_to_hex(r, g, b)
                    color_categories[category].append({
                        "rgb": (r, g, b),
                        "hex": hex_color
                    })
        except Exception as e:
            print(f"⚠️  Error processing {image_path.name}: {e}")
    
    # Get most common colors for each category
    room_colors = {}
    
    for category, colors in color_categories.items():
        if not colors:
            continue
        
        # Count occurrences
        color_counts = Counter([c["hex"] for c in colors])
        
        # Get top 3 most common colors
        most_common = color_counts.most_common(3)
        
        # Convert to room name
        room_name_map = {
            "balcony": "balcony",
            "master_bedroom": "master bedroom",
            "bathroom": "bathroom",
            "common_room": "common room",
            "living_room": "living room",
            "kitchen": "kitchen",
        }
        
        room_name = room_name_map[category]
        room_colors[room_name] = []
        
        for hex_color, count in most_common:
            # Find RGB for this hex
            rgb = next((c["rgb"] for c in colors if c["hex"] == hex_color), None)
            if rgb:
                room_colors[room_name].append({
                    "hex": hex_color,
                    "rgb": rgb,
                    "count": count
                })
    
    return room_colors


def update_config_file(room_colors):
    """Update the room_colors_config.py file with extracted colors."""
    
    config_file = BASE_DIR / "preprocessing" / "room_colors_config.py"
    
    # Read current config
    with open(config_file) as f:
        content = f.read()
    
    # Generate new config content
    config_lines = [
        '"""',
        "Color Configuration File for Room Identification",
        "",
        "This file was auto-generated by extract_colors.py",
        "You can manually edit it to add/remove colors.",
        '"""',
        "",
        "# Room color mappings",
        "ROOM_COLORS = {",
    ]
    
    for room_name in ["balcony", "master bedroom", "bathroom", "common room", "living room", "kitchen"]:
        config_lines.append(f'    "{room_name}": [')
        
        if room_name in room_colors:
            for color_info in room_colors[room_name]:
                hex_color = color_info["hex"]
                rgb = color_info["rgb"]
                count = color_info.get("count", 0)
                config_lines.append(f'        "{hex_color}",  # RGB: {rgb} (found {count} times)')
                # Also add RGB tuple
                config_lines.append(f'        {rgb},  # Same as {hex_color}')
        else:
            config_lines.append('        # No colors found - add manually')
        
        config_lines.append('    ],')
        config_lines.append('')
    
    config_lines.append('}')
    
    # Write new config
    with open(config_file, 'w') as f:
        f.write('\n'.join(config_lines))
    
    print(f"✅ Updated {config_file}")


def main():
    """Main function."""
    print("🎨 Extracting colors from dataset images...\n")
    
    # Extract colors from multiple images
    room_colors = extract_colors_from_dataset(num_samples=20)
    
    # Print results
    print("\n" + "="*60)
    print("📊 EXTRACTED COLORS")
    print("="*60)
    
    for room_name, colors in room_colors.items():
        print(f"\n{room_name.upper()}:")
        if colors:
            for color_info in colors[:3]:  # Show top 3
                print(f"  {color_info['hex']} (RGB: {color_info['rgb']}) - found {color_info.get('count', 0)} times")
        else:
            print("  No colors found")
    
    print("\n" + "="*60)
    
    # Update config file
    print("\n💾 Updating configuration file...")
    update_config_file(room_colors)
    
    print("\n✅ Done! Colors have been added to room_colors_config.py")
    print("   You can now run: python preprocessing/image_to_svg.py")


if __name__ == "__main__":
    main()

