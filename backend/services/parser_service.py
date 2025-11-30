"""
Parser Service: Parse natural language descriptions to structured JSON.
"""

import re
from typing import Dict, List, Tuple


class ParserService:
    """Parse natural language floor plan descriptions."""
    
    # Room type keywords
    ROOM_TYPES = [
        'balcony', 'bathroom', 'bedroom', 'closet', 'common room', 
        'dining room', 'hallway', 'kitchen', 'living room', 'master room',
        'master bedroom', 'laundry', 'pantry', 'study', 'garage', 'patio',
        'foyer', 'mudroom', 'office', 'den'
    ]
    
    # Directional keywords
    DIRECTIONS = [
        'north', 'south', 'east', 'west', 'northeast', 'northwest',
        'southeast', 'southwest', 'center', 'middle'
    ]
    
    def __init__(self):
        """Initialize parser with regex patterns."""
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup regex patterns for parsing."""
        
        # Pattern to match room mentions
        room_types_pattern = '|'.join(self.ROOM_TYPES)
        self.room_pattern = re.compile(
            rf'\b(?:the\s+)?({room_types_pattern})\b',
            re.IGNORECASE
        )
        
        # Pattern to match dimensions
        self.dimension_pattern = re.compile(
            r'approximately\s+(\d+)\s+feet\s+wide\s+by\s+(\d+)\s+feet\s+deep',
            re.IGNORECASE
        )
        
        # Pattern to match square footage
        self.sqft_pattern = re.compile(
            r'total square footage of\s+(\d+)',
            re.IGNORECASE
        )
        
        # Pattern to match directions
        directions_pattern = '|'.join(self.DIRECTIONS)
        self.direction_pattern = re.compile(
            rf'\b({directions_pattern})\b',
            re.IGNORECASE
        )
    
    def parse_sentence(self, sentence: str) -> Dict:
        """Parse a single sentence describing one room."""
        
        result = {
            "room": None,
            "position": None,
            "dimensions": {},
            "adjacent_rooms": [],
            "directions": []
        }
        
        # Extract room type
        room_matches = self.room_pattern.findall(sentence)
        if room_matches:
            result["room"] = room_matches[0].lower()
            if len(room_matches) > 1:
                result["adjacent_rooms"] = [r.lower() for r in room_matches[1:]]
        
        # Extract dimensions
        dim_match = self.dimension_pattern.search(sentence)
        if dim_match:
            width, depth = dim_match.groups()
            result["dimensions"]["width"] = int(width)
            result["dimensions"]["depth"] = int(depth)
        
        # Extract square footage
        sqft_match = self.sqft_pattern.search(sentence)
        if sqft_match:
            result["dimensions"]["square_footage"] = int(sqft_match.group(1))
        
        # Extract directions
        direction_matches = self.direction_pattern.findall(sentence)
        if direction_matches:
            result["directions"] = [d.lower() for d in direction_matches]
            if not result["position"]:
                result["position"] = direction_matches[0].lower()
        
        return result
    
    def parse(self, text: str) -> Tuple[Dict, float]:
        """
        Parse complete floor plan description.
        
        Returns:
            (parsed_data, confidence_score)
        """
        
        # Split into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        rooms = []
        
        for sentence in sentences:
            parsed = self.parse_sentence(sentence)
            if parsed["room"]:
                rooms.append(parsed)
        
        # Build structured output
        result = {
            "rooms": rooms,
            "total_rooms": len(rooms),
            "total_square_footage": sum(
                r["dimensions"].get("square_footage", 0) 
                for r in rooms
            )
        }
        
        # Calculate confidence score
        confidence = self.calculate_confidence(result, text)
        
        return result, confidence
    
    def calculate_confidence(self, parsed_data: Dict, original_text: str) -> float:
        """
        Calculate confidence score for parsed data.
        
        Score based on:
        - Number of rooms detected
        - Completeness of room information
        - Presence of dimensions
        """
        
        if parsed_data["total_rooms"] == 0:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Points for detecting rooms
        score += parsed_data["total_rooms"] * 0.3
        max_score += parsed_data["total_rooms"] * 0.3
        
        # Points for room details
        for room in parsed_data["rooms"]:
            max_score += 0.3
            
            if room.get("position"):
                score += 0.1
            
            if room.get("dimensions"):
                score += 0.1
                
                if "square_footage" in room["dimensions"]:
                    score += 0.1
        
        # Normalize to 0-1
        confidence = min(score / max_score if max_score > 0 else 0, 1.0)
        
        return round(confidence, 2)

