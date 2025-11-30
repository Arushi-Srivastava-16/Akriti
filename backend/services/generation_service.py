"""
Generation Service: Generate SVG from JSON using trained model.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Optional
import sys

# Add models directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "models"))

try:
    from inference import FloorPlanGenerator
except ImportError:
    FloorPlanGenerator = None


class GenerationService:
    """Generate SVG floor plans from JSON using CodeT5 model."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize generation service.
        
        Args:
            model_path: Path to trained model. If None, uses default path.
        """
        if model_path is None:
            # Default model path
            BASE_DIR = Path(__file__).parent.parent.parent
            model_path = BASE_DIR / "checkpoints" / "codet5-floorplan-v1" / "final_model"
        
        self.model_path = Path(model_path)
        self.generator = None
        self.model_loaded = False
        
        # Try to load model
        self.load_model()
    
    def load_model(self):
        """Load the trained model."""
        
        if FloorPlanGenerator is None:
            print("⚠️  FloorPlanGenerator not available. Install dependencies.")
            return
        
        if not self.model_path.exists():
            print(f"⚠️  Model not found at {self.model_path}")
            print("   Train the model first: python models/train_codet5.py")
            return
        
        try:
            print(f"📦 Loading model from {self.model_path}")
            self.generator = FloorPlanGenerator(str(self.model_path))
            self.model_loaded = True
            print("✅ Model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model_loaded = False
    
    def generate(self, json_data: Dict, **kwargs) -> Dict:
        """
        Generate SVG from JSON data.
        
        Args:
            json_data: Floor plan JSON
            **kwargs: Additional generation parameters
            
        Returns:
            Dict with svg code, id, and metadata
        """
        
        if not self.model_loaded or self.generator is None:
            # Fallback: generate simple placeholder SVG
            return self.generate_placeholder(json_data)
        
        try:
            # Generate SVG using model
            svg_code = self.generator.generate(json_data, **kwargs)
            
            # Create response
            generation_id = str(uuid.uuid4())
            
            return {
                "svg": svg_code,
                "id": generation_id,
                "metadata": {
                    "num_rooms": json_data.get("total_rooms", 0),
                    "total_sqft": json_data.get("total_square_footage", 0),
                    "generated_with": "codet5-model"
                }
            }
        
        except Exception as e:
            print(f"❌ Generation error: {e}")
            # Fallback to placeholder
            return self.generate_placeholder(json_data)
    
    def generate_placeholder(self, json_data: Dict) -> Dict:
        """
        Generate a simple placeholder SVG (fallback when model not available).
        
        This creates a basic SVG with rectangles for each room.
        """
        
        rooms = json_data.get("rooms", [])
        
        # SVG parameters
        width = 800
        height = 600
        margin = 50
        
        # Calculate grid layout
        num_rooms = len(rooms)
        if num_rooms == 0:
            cols = 1
        elif num_rooms <= 2:
            cols = 2
        elif num_rooms <= 4:
            cols = 2
        else:
            cols = 3
        
        rows = (num_rooms + cols - 1) // cols
        
        room_width = (width - 2 * margin) / cols - 20
        room_height = (height - 2 * margin) / rows - 20
        
        # Generate SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
            f'<text x="{width/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold">Floor Plan</text>',
        ]
        
        # Add rooms
        colors = ['#FFE5B4', '#E0F0E0', '#E0E0F0', '#F0E0E0', '#F0F0E0', '#E0F0F0']
        
        for i, room in enumerate(rooms):
            row = i // cols
            col = i % cols
            
            x = margin + col * (room_width + 20)
            y = margin + 30 + row * (room_height + 20)
            
            color = colors[i % len(colors)]
            
            svg_parts.append(
                f'<g id="room_{room["room"].replace(" ", "_")}">'
            )
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{room_width}" height="{room_height}" '
                f'fill="{color}" fill-opacity="0.7" stroke="black" stroke-width="2"/>'
            )
            
            # Room label
            room_name = room["room"].replace("_", " ").title()
            svg_parts.append(
                f'<text x="{x + room_width/2}" y="{y + room_height/2}" '
                f'text-anchor="middle" font-size="14" font-weight="bold">{room_name}</text>'
            )
            
            # Square footage if available
            if "dimensions" in room and "square_footage" in room["dimensions"]:
                sqft = room["dimensions"]["square_footage"]
                svg_parts.append(
                    f'<text x="{x + room_width/2}" y="{y + room_height/2 + 20}" '
                    f'text-anchor="middle" font-size="11">{sqft} sq ft</text>'
                )
            
            svg_parts.append('</g>')
        
        svg_parts.append('</svg>')
        
        svg_code = '\n'.join(svg_parts)
        
        generation_id = str(uuid.uuid4())
        
        return {
            "svg": svg_code,
            "id": generation_id,
            "metadata": {
                "num_rooms": num_rooms,
                "total_sqft": json_data.get("total_square_footage", 0),
                "generated_with": "placeholder"
            }
        }

