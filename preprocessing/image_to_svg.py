"""
Image to SVG Converter: Convert floor plan images to SVG format.

Approach:
1. Load the PNG floor plan image
2. Detect room boundaries using color segmentation
3. Extract room polygons/rectangles
4. Convert to SVG paths
5. Add labels and dimensions

Usage:
    python preprocessing/image_to_svg.py
"""

import json
import re
import numpy as np
from pathlib import Path
from PIL import Image
import svgwrite
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional
import cv2

# Try to import color configuration, fallback to empty if not found
try:
    from .room_colors_config import ROOM_COLORS
except ImportError:
    try:
        from room_colors_config import ROOM_COLORS
    except ImportError:
        # Default empty configuration
        ROOM_COLORS = {
            "balcony": [],
            "master bedroom": [],
            "bathroom": [],
            "common room": [],
            "living room": [],
            "kitchen": [],
        }


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def normalize_color(color) -> Tuple[int, int, int]:
    """Normalize color input (hex or RGB) to RGB tuple."""
    if isinstance(color, str):
        # Hex code
        return hex_to_rgb(color)
    elif isinstance(color, (list, tuple)) and len(color) == 3:
        # RGB tuple
        return tuple(int(c) for c in color)
    return color


class FloorPlanToSVG:
    """Convert floor plan images to SVG format."""
    
    def __init__(self, image_path: Path, json_data: Dict):
        """Initialize converter with image and parsed JSON data."""
        self.image_path = image_path
        self.json_data = json_data
        self.image = None
        self.image_array = None
        self.rooms = []
        
    def load_image(self):
        """Load and preprocess the floor plan image."""
        self.image = Image.open(self.image_path)
        self.image_array = np.array(self.image)
        
        # Convert RGBA to RGB if needed
        if self.image_array.shape[-1] == 4:
            # Composite on white background
            rgb = self.image_array[:, :, :3]
            alpha = self.image_array[:, :, 3:] / 255.0
            white_bg = np.ones_like(rgb) * 255
            self.image_array = (rgb * alpha + white_bg * (1 - alpha)).astype(np.uint8)
    
    def detect_floor_plan_boundary(self) -> List:
        """
        Detect the outer boundary of the floor plan (black outline).
        Returns the actual shape contour, not a rectangle.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)
        
        # Create binary mask: black (walls) = 1, everything else = 0
        _, binary = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
        
        # Find outer contour
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get the largest contour (should be the outer boundary)
            outer_contour = max(contours, key=cv2.contourArea)
            
            # Simplify the contour to reduce points but keep the shape
            # Use a small epsilon to keep the actual shape
            epsilon = 0.002 * cv2.arcLength(outer_contour, True)
            simplified = cv2.approxPolyDP(outer_contour, epsilon, True)
            
            # Return the actual shape points
            return simplified.squeeze().tolist() if len(simplified) > 2 else []
        
        return []
    
    def detect_doors_gates(self) -> List[Dict]:
        """
        Detect doors/gates:
        - Small red regions on black boundary = main door
        - Other small red regions = interior doors
        """
        doors = []
        
        # First, detect the black boundary to check if red is on it
        gray = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)
        _, black_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
        
        # Detect red regions
        red_mask = (self.image_array[:, :, 0] > 200) & \
                   (self.image_array[:, :, 1] < 50) & \
                   (self.image_array[:, :, 2] < 50)
        
        if np.any(red_mask):
            red_mask_uint8 = (red_mask * 255).astype(np.uint8)
            contours, _ = cv2.findContours(
                red_mask_uint8,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Doors/gates are typically small rectangular regions
                # Main door is usually on the boundary (smaller)
                # Interior doors might be slightly larger
                if 20 < area < 3000:  # Adjusted range for doors
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Check if this red region is on the black boundary
                    # Sample points around the contour to see if they're on black
                    center_x, center_y = x + w//2, y + h//2
                    is_on_boundary = False
                    
                    # Check if center or edges are near black pixels
                    for check_x, check_y in [
                        (center_x, center_y),
                        (x, center_y),
                        (x + w, center_y),
                        (center_x, y),
                        (center_x, y + h)
                    ]:
                        if 0 <= check_y < black_mask.shape[0] and 0 <= check_x < black_mask.shape[1]:
                            if black_mask[check_y, check_x] > 0:  # On black boundary
                                is_on_boundary = True
                                break
                    
                    door_type = "main_door" if is_on_boundary else "door"
                    
                    doors.append({
                        "type": door_type,
                        "bounding_box": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                        "contour": contour.squeeze().tolist()
                    })
        
        return doors
    
    def detect_rooms(self) -> List[Dict]:
        """
        Detect individual rooms using color segmentation.
        Uses actual polygon contours to prevent overlapping.
        """
        
        # Get unique colors (rooms are color-coded)
        pixels = self.image_array.reshape(-1, 3)
        unique_colors = np.unique(pixels, axis=0)
        
        rooms = []
        
        for color in unique_colors:
            # Skip background colors
            if np.all(color > 240):  # White background
                continue
            if np.all(color < 15):   # Black walls
                continue
            
            # Skip small red regions (doors/gates - handled separately)
            # But keep large red/pink regions (kitchen)
            # Check if this color is bright red (door) vs red/pink (kitchen)
            r, g, b = color[0], color[1], color[2]
            is_bright_red = (r > 200 and g < 50 and b < 50)
            
            if is_bright_red:
                # Check the area of this red color
                red_mask = np.all(self.image_array == color, axis=-1)
                red_area = np.sum(red_mask)
                # If it's a small red region, it's likely a door, skip it
                if red_area < 3000:  # Small red = door, large red = kitchen
                    continue
            
            # Create mask for this color
            mask = np.all(self.image_array == color, axis=-1)
            
            # Skip if too small (noise)
            if np.sum(mask) < 200:  # Increased threshold
                continue
            
            # Find contours
            mask_uint8 = (mask * 255).astype(np.uint8)
            contours, _ = cv2.findContours(
                mask_uint8, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if contours:
                # Process ALL contours for this color (not just the largest)
                # This handles multiple rooms of the same type
                for contour in contours:
                    contour_area = cv2.contourArea(contour)
                    
                    # Skip very small contours (noise)
                    if contour_area < 200:
                        continue
                    
                    # Get bounding box for reference
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Simplify contour to polygon (use actual shape, not just bounding box)
                    epsilon = 0.01 * cv2.arcLength(contour, True)
                    approx_polygon = cv2.approxPolyDP(contour, epsilon, True)
                    
                    # Convert to list of points
                    polygon_points = approx_polygon.squeeze().tolist()
                    if len(polygon_points) < 3:
                        # Fallback to bounding box if polygon is invalid
                        polygon_points = [
                            [x, y], [x + w, y], [x + w, y + h], [x, y + h]
                        ]
                    
                    room_data = {
                        "color": color.tolist(),
                        "bounding_box": {
                            "x": int(x),
                            "y": int(y),
                            "width": int(w),
                            "height": int(h)
                        },
                        "area": int(contour_area),
                        "contour": contour.squeeze().tolist(),
                        "polygon": polygon_points
                    }
                    
                    rooms.append(room_data)
        
        self.rooms = rooms
        return rooms
    
    def identify_room_by_color(self, color):
        """
        Identify room type based on exact color matching.
        Uses ROOM_COLORS configuration for precise matching.
        """
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        color_tuple = (r, g, b)
        
        # Check against configured colors with tolerance
        tolerance = 5  # Allow small variations in color
        
        for room_type, configured_colors in ROOM_COLORS.items():
            if not configured_colors:
                continue
            
            for configured_color in configured_colors:
                # Normalize configured color
                cfg_rgb = normalize_color(configured_color)
                cfg_r, cfg_g, cfg_b = cfg_rgb
                
                # Check if color matches within tolerance
                if (abs(r - cfg_r) <= tolerance and 
                    abs(g - cfg_g) <= tolerance and 
                    abs(b - cfg_b) <= tolerance):
                    return room_type
        
        # Fallback: if no exact match, return None
        return None
    
    def match_rooms_to_json(self):
        """
        Match detected visual rooms using color-based identification.
        Handles multiple rooms of the same type.
        """
        
        json_rooms = self.json_data.get("rooms", [])
        
        # Group JSON rooms by type (to handle multiple of same type)
        json_rooms_by_type = {}
        for json_room in json_rooms:
            room_type = json_room["room"].lower()
            if room_type not in json_rooms_by_type:
                json_rooms_by_type[room_type] = []
            json_rooms_by_type[room_type].append(json_room)
        
        # Also create lookup with variations
        variations = {
            "master bedroom": ["master room", "master"],
            "common room": ["common"],
            "living room": ["living"],
            "bathroom": ["bath"],
            "kitchen": ["kitchen"],
            "balcony": ["balcony"]
        }
        
        # Identify rooms by color and match to JSON
        rooms_by_type = {}  # Track how many of each type we've matched
        
        for room in self.rooms:
            color = room["color"]
            room_type = self.identify_room_by_color(color)
            
            if room_type:
                # Initialize counter for this room type
                if room_type not in rooms_by_type:
                    rooms_by_type[room_type] = 0
                
                rooms_by_type[room_type] += 1
                room_index = rooms_by_type[room_type] - 1  # 0-indexed
                
                # Set room name (add number if multiple of same type)
                if rooms_by_type[room_type] > 1:
                    room["name"] = f"{room_type} {rooms_by_type[room_type]}"
                else:
                    room["name"] = room_type
                
                # Try to get dimensions from JSON
                # First try exact match
                if room_type in json_rooms_by_type:
                    json_rooms_list = json_rooms_by_type[room_type]
                    if room_index < len(json_rooms_list):
                        json_room = json_rooms_list[room_index]
                        room["dimensions"] = json_room.get("dimensions", {})
                        room["position"] = json_room.get("position", "")
                    elif len(json_rooms_list) > 0:
                        # Use first one if we have more rooms than JSON entries
                        json_room = json_rooms_list[0]
                        room["dimensions"] = json_room.get("dimensions", {})
                        room["position"] = json_room.get("position", "")
                else:
                    # Try variations
                    matched = False
                    for variant_list in variations.values():
                        for variant in variant_list:
                            if variant in json_rooms_by_type:
                                json_rooms_list = json_rooms_by_type[variant]
                                if room_index < len(json_rooms_list):
                                    json_room = json_rooms_list[room_index]
                                    room["dimensions"] = json_room.get("dimensions", {})
                                    room["position"] = json_room.get("position", "")
                                    matched = True
                                    break
                        if matched:
                            break
            else:
                # Fallback: unknown room
                room["name"] = f"room_{len(self.rooms)}"
    
    def create_svg(self, output_path: Path, width: int = 800, height: int = 600):
        """
        Generate SVG from detected rooms with boundaries and doors.
        
        Args:
            output_path: Where to save the SVG file
            width: SVG canvas width
            height: SVG canvas height
        """
        
        # Create SVG drawing
        dwg = svgwrite.Drawing(
            str(output_path),
            size=(f"{width}px", f"{height}px"),
            viewBox=f"0 0 {width} {height}"
        )
        
        # Add background
        dwg.add(dwg.rect(
            insert=(0, 0),
            size=(width, height),
            fill='white'
        ))
        
        # Calculate scale factor
        img_height, img_width = self.image_array.shape[:2]
        scale_x = width / img_width
        scale_y = height / img_height
        scale = min(scale_x, scale_y) * 0.9  # 90% to leave margin
        
        # Center offset
        offset_x = (width - img_width * scale) / 2
        offset_y = (height - img_height * scale) / 2
        
        def scale_point(point):
            """Scale a point from image coordinates to SVG coordinates."""
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                # Handle both [x, y] and [[x, y]] formats
                if isinstance(point[0], (list, tuple)):
                    point = point[0]
                return (float(point[0]) * scale + offset_x, float(point[1]) * scale + offset_y)
            return (0, 0)
        
        # 1. Draw outer boundary first (so it's behind everything) - actual shape with even width
        boundary = self.detect_floor_plan_boundary()
        if boundary:
            boundary_points = [scale_point(p) for p in boundary]
            if len(boundary_points) >= 3:
                # Use consistent stroke width (even all around)
                boundary_width = 4
                dwg.add(dwg.polygon(
                    points=boundary_points,
                    fill='none',
                    stroke='black',
                    stroke_width=boundary_width,
                    stroke_linejoin='miter',
                    stroke_linecap='butt',
                    id='floor_plan_boundary'
                ))
        
        # 1.5. Draw inner walls (white dividers) - actual shape with even width
        # Detect white regions that are not the background
        gray = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)
        white_mask = (self.image_array[:, :, 0] > 240) & \
                    (self.image_array[:, :, 1] > 240) & \
                    (self.image_array[:, :, 2] > 240)
        
        # Find white contours that are likely walls (thin lines)
        white_mask_uint8 = (white_mask * 255).astype(np.uint8)
        white_contours, _ = cv2.findContours(
            white_mask_uint8,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        wall_width = 3  # Consistent wall width
        
        for contour in white_contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            # Inner walls are typically thin (either width or height is small)
            if area > 50 and (w < 15 or h < 15):  # Thin white lines = inner walls
                # Simplify contour to get cleaner lines
                epsilon = 0.01 * cv2.arcLength(contour, True)
                simplified = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(simplified) >= 2:
                    # Draw as a polyline (follows actual shape)
                    points = [scale_point(p) for p in simplified.squeeze().tolist()]
                    if len(points) >= 2:
                        dwg.add(dwg.polyline(
                            points=points,
                            fill='none',
                            stroke='white',
                            stroke_width=wall_width,
                            stroke_linecap='round',
                            stroke_linejoin='miter',
                            id='inner_wall'
                        ))
        
        # 2. Draw rooms using actual polygon shapes (prevents overlapping)
        # Sort by area (largest first) so smaller rooms draw on top
        sorted_rooms = sorted(self.rooms, key=lambda r: r["area"], reverse=True)
        
        for room in sorted_rooms:
            # Room color (slightly transparent)
            color = room["color"]
            fill_color = f"rgb({color[0]},{color[1]},{color[2]})"
            
            # Sanitize room name for SVG ID
            room_name = room.get('name', 'unknown')
            room_id = f"room_{room_name.replace(' ', '_').replace('-', '_').lower()}"
            room_id = re.sub(r'[^a-zA-Z0-9_-]', '_', room_id)
            
            # Use actual polygon if available, otherwise use bounding box
            if "polygon" in room and room["polygon"] and len(room["polygon"]) >= 3:
                # Scale polygon points
                polygon_points = [scale_point(p) for p in room["polygon"]]
                
                room_group = dwg.g(id=room_id)
                room_group.add(dwg.polygon(
                    points=polygon_points,
                    fill=fill_color,
                    fill_opacity=0.7,
                    stroke='black',
                    stroke_width=1.5
                ))
            else:
                # Fallback to rectangle if polygon not available
                bbox = room["bounding_box"]
                x = bbox["x"] * scale + offset_x
                y = bbox["y"] * scale + offset_y
                w = bbox["width"] * scale
                h = bbox["height"] * scale
                
                room_group = dwg.g(id=room_id)
                room_group.add(dwg.rect(
                    insert=(x, y),
                    size=(w, h),
                    fill=fill_color,
                    fill_opacity=0.7,
                    stroke='black',
                    stroke_width=1.5
                ))
            
            # Add room label
            if "name" in room:
                bbox = room["bounding_box"]
                center_x = (bbox["x"] + bbox["width"]/2) * scale + offset_x
                center_y = (bbox["y"] + bbox["height"]/2) * scale + offset_y
                
                label = room["name"].replace("_", " ").title()
                
                room_group.add(dwg.text(
                    label,
                    insert=(center_x, center_y),
                    text_anchor="middle",
                    dominant_baseline="middle",
                    font_size="12px",
                    font_family="Arial",
                    font_weight="bold",
                    fill="black"
                ))
                
                # Add dimensions if available
                if "dimensions" in room and "square_footage" in room["dimensions"]:
                    sqft = room["dimensions"]["square_footage"]
                    dim_label = f"{sqft} sq ft"
                    
                    room_group.add(dwg.text(
                        dim_label,
                        insert=(center_x, center_y + 18),
                        text_anchor="middle",
                        dominant_baseline="middle",
                        font_size="10px",
                        font_family="Arial",
                        fill="black"
                    ))
            
            dwg.add(room_group)
        
        # 3. Draw doors/gates (red regions)
        doors = self.detect_doors_gates()
        for door in doors:
            bbox = door["bounding_box"]
            x = bbox["x"] * scale + offset_x
            y = bbox["y"] * scale + offset_y
            w = bbox["width"] * scale
            h = bbox["height"] * scale
            
            door_type = door.get("type", "door")
            is_main_door = (door_type == "main_door")
            
            # Draw door as red rectangle
            # Main door is slightly larger/more prominent
            dwg.add(dwg.rect(
                insert=(x, y),
                size=(w, h),
                fill='red',
                fill_opacity=0.9 if is_main_door else 0.7,
                stroke='darkred',
                stroke_width=3 if is_main_door else 2,
                id='main_door' if is_main_door else 'door'
            ))
            
            # Add door label
            label = "Main Door" if is_main_door else "Door"
            dwg.add(dwg.text(
                label,
                insert=(x + w/2, y + h/2),
                text_anchor="middle",
                dominant_baseline="middle",
                font_size="9px" if is_main_door else "8px",
                font_family="Arial",
                font_weight="bold",
                fill="white"
            ))
        
        # Add title
        title = f"Floor Plan - ID: {self.json_data.get('id', 'unknown')}"
        dwg.add(dwg.text(
            title,
            insert=(width/2, 30),
            text_anchor="middle",
            font_size="18px",
            font_family="Arial",
            font_weight="bold",
            fill="black"
        ))
        
        # Save
        dwg.save()
        
        return True


def process_single_floor_plan(image_path: Path, json_path: Path, output_path: Path) -> bool:
    """
    Process a single floor plan: image + JSON → SVG.
    
    Args:
        image_path: Path to PNG floor plan image
        json_path: Path to parsed JSON data
        output_path: Where to save SVG output
        
    Returns:
        Success boolean
    """
    
    try:
        # Load JSON data
        with open(json_path) as f:
            json_data = json.load(f)
        
        # Create converter
        converter = FloorPlanToSVG(image_path, json_data)
        
        # Process
        converter.load_image()
        converter.detect_rooms()
        converter.match_rooms_to_json()
        # Boundary and doors are detected inside create_svg
        converter.create_svg(output_path)
        
        return True
        
    except Exception as e:
        print(f"Error processing {image_path.name}: {e}")
        return False


def process_all_floor_plans():
    """Process all annotated floor plans to SVG."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    # Load mapping
    mapping_file = BASE_DIR / "data" / "image_annotation_mapping.json"
    if not mapping_file.exists():
        print("❌ Mapping file not found. Run create_mapping.py first!")
        return
    
    with open(mapping_file) as f:
        mapping = json.load(f)
    
    print(f"🖼️  Processing {mapping['valid_pairs']} floor plans to SVG...")
    
    # Create output directory
    svg_output_dir = BASE_DIR / "data" / "processed" / "svg"
    svg_output_dir.mkdir(parents=True, exist_ok=True)
    
    json_dir = BASE_DIR / "data" / "processed" / "json"
    
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "failed_ids": []
    }
    
    for pair in tqdm(mapping["pairs"], desc="Converting to SVG"):
        image_path = BASE_DIR / pair["image_path"]
        json_path = json_dir / f"{pair['id']}.json"
        output_path = svg_output_dir / f"{pair['id']}.svg"
        
        # Check if JSON exists
        if not json_path.exists():
            print(f"\n⚠️  JSON not found for {pair['id']}, skipping...")
            stats["failed"] += 1
            stats["failed_ids"].append(pair['id'])
            continue
        
        # Process
        success = process_single_floor_plan(image_path, json_path, output_path)
        
        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1
            stats["failed_ids"].append(pair['id'])
        
        stats["total"] += 1
    
    # Save statistics
    stats_file = BASE_DIR / "data" / "processed" / "svg_conversion_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 SVG CONVERSION SUMMARY")
    print("="*60)
    print(f"✅ Total processed: {stats['total']}")
    print(f"✅ Successful: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"❌ Failed: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    print(f"📁 Output directory: {svg_output_dir}")
    print(f"📊 Stats saved to: {stats_file}")
    print("="*60)
    
    if stats["failed_ids"]:
        print(f"\n❌ Failed IDs (first 10): {stats['failed_ids'][:10]}")


if __name__ == "__main__":
    print("🚀 Starting image-to-SVG conversion...\n")
    process_all_floor_plans()
    print("\n✅ SVG conversion complete!")

