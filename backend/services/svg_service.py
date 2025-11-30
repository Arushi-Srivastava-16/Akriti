"""
SVG Service: Manipulate and edit SVG files.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Optional
import re


class SVGService:
    """Manipulate and edit SVG floor plans."""
    
    @staticmethod
    def parse_svg(svg_code: str) -> Optional[ET.Element]:
        """Parse SVG string to XML element."""
        try:
            return ET.fromstring(svg_code)
        except ET.ParseError as e:
            print(f"Error parsing SVG: {e}")
            return None
    
    @staticmethod
    def svg_to_string(svg_element: ET.Element) -> str:
        """Convert XML element back to SVG string."""
        return ET.tostring(svg_element, encoding='unicode')
    
    @staticmethod
    def validate_svg(svg_code: str) -> tuple[bool, Optional[str]]:
        """
        Validate SVG code.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            root = ET.fromstring(svg_code)
            
            if 'svg' not in root.tag.lower():
                return False, "Not a valid SVG element"
            
            if len(root) == 0:
                return False, "Empty SVG"
            
            return True, None
            
        except ET.ParseError as e:
            return False, f"Parse error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    @staticmethod
    def edit_room(svg_code: str, changes: Dict) -> tuple[str, bool]:
        """
        Edit a room in the SVG.
        
        Args:
            svg_code: Original SVG code
            changes: Dict with edit parameters:
                - room_id: ID of room to edit
                - new_position: {x, y}
                - new_size: {width, height}
                - new_color: RGB color
        
        Returns:
            (modified_svg, success)
        """
        
        try:
            root = SVGService.parse_svg(svg_code)
            if root is None:
                return svg_code, False
            
            room_id = changes.get("room_id")
            if not room_id:
                return svg_code, False
            
            # Find room group
            room_group = root.find(f".//*[@id='{room_id}']")
            if room_group is None:
                return svg_code, False
            
            # Find rectangle in group
            rect = room_group.find('.//rect')
            if rect is None:
                return svg_code, False
            
            # Apply changes
            if "new_position" in changes:
                pos = changes["new_position"]
                rect.set("x", str(pos["x"]))
                rect.set("y", str(pos["y"]))
            
            if "new_size" in changes:
                size = changes["new_size"]
                rect.set("width", str(size["width"]))
                rect.set("height", str(size["height"]))
            
            if "new_color" in changes:
                rect.set("fill", changes["new_color"])
            
            # Convert back to string
            modified_svg = SVGService.svg_to_string(root)
            
            return modified_svg, True
            
        except Exception as e:
            print(f"Error editing SVG: {e}")
            return svg_code, False
    
    @staticmethod
    def get_room_info(svg_code: str, room_id: str) -> Optional[Dict]:
        """
        Extract information about a specific room from SVG.
        
        Returns:
            Dict with room position, size, etc.
        """
        
        try:
            root = SVGService.parse_svg(svg_code)
            if root is None:
                return None
            
            # Find room
            room_group = root.find(f".//*[@id='{room_id}']")
            if room_group is None:
                return None
            
            # Find rectangle
            rect = room_group.find('.//rect')
            if rect is None:
                return None
            
            info = {
                "id": room_id,
                "position": {
                    "x": float(rect.get("x", 0)),
                    "y": float(rect.get("y", 0))
                },
                "size": {
                    "width": float(rect.get("width", 0)),
                    "height": float(rect.get("height", 0))
                },
                "color": rect.get("fill", "")
            }
            
            return info
            
        except Exception as e:
            print(f"Error getting room info: {e}")
            return None
    
    @staticmethod
    def list_rooms(svg_code: str) -> list:
        """
        List all rooms in the SVG.
        
        Returns:
            List of room IDs
        """
        
        try:
            root = SVGService.parse_svg(svg_code)
            if root is None:
                return []
            
            # Find all groups with IDs starting with "room_"
            rooms = []
            for element in root.iter():
                element_id = element.get("id", "")
                if element_id.startswith("room_"):
                    rooms.append(element_id)
            
            return rooms
            
        except Exception as e:
            print(f"Error listing rooms: {e}")
            return []

