"""
Text Parser: Convert natural language floor plan descriptions to structured JSON.

Input: "The balcony is at the north corner..."
Output: {
    "rooms": [...],
    "relationships": [...],
    "dimensions": {...}
}

Usage:
    python preprocessing/text_parser.py
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm


class FloorPlanTextParser:
    """Parse natural language floor plan descriptions into structured JSON."""
    
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
    
    # Positional relationships
    RELATIONSHIPS = [
        'to the', 'at the', 'in the', 'on the', 'with the', 'adjacent to',
        'next to', 'beside', 'near', 'across from'
    ]
    
    def __init__(self):
        """Initialize the parser with regex patterns."""
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup regex patterns for parsing."""
        
        # Pattern to match room mentions
        room_types_pattern = '|'.join(self.ROOM_TYPES)
        self.room_pattern = re.compile(
            rf'\b(?:the\s+)?({room_types_pattern})\b',
            re.IGNORECASE
        )
        
        # Pattern to match dimensions: "X feet wide by Y feet deep"
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
        
        # Extract room type (usually the first room mentioned is the main subject)
        room_matches = self.room_pattern.findall(sentence)
        if room_matches:
            result["room"] = room_matches[0].lower()
            
            # Other rooms mentioned are adjacent
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
            # Use first direction as primary position
            if not result["position"]:
                result["position"] = direction_matches[0].lower()
        
        # Extract positional relationships
        for rel in self.RELATIONSHIPS:
            if rel in sentence.lower():
                # This room has a relationship to others
                pass  # Already captured in adjacent_rooms
        
        return result
    
    def parse_description(self, text: str) -> Dict:
        """Parse complete floor plan description."""
        
        # Split into sentences (each typically describes one room)
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        rooms = []
        
        for sentence in sentences:
            parsed = self.parse_sentence(sentence)
            
            # Only add if we found a room
            if parsed["room"]:
                rooms.append(parsed)
        
        # Build structured output
        result = {
            "rooms": rooms,
            "total_rooms": len(rooms),
            "raw_text": text
        }
        
        # Calculate total square footage
        total_sqft = sum(
            r["dimensions"].get("square_footage", 0) 
            for r in rooms
        )
        result["total_square_footage"] = total_sqft
        
        return result
    
    def validate_parsed_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate parsed data quality."""
        
        errors = []
        
        if data["total_rooms"] == 0:
            errors.append("No rooms detected")
        
        rooms_with_dims = sum(
            1 for r in data["rooms"] 
            if r["dimensions"].get("width") and r["dimensions"].get("depth")
        )
        
        if rooms_with_dims < data["total_rooms"] * 0.5:
            errors.append(f"Only {rooms_with_dims}/{data['total_rooms']} rooms have dimensions")
        
        if data["total_square_footage"] == 0:
            errors.append("No square footage information")
        
        is_valid = len(errors) == 0
        return is_valid, errors


def process_all_annotations():
    """Process all annotation files and save as JSON."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    # Load mapping
    mapping_file = BASE_DIR / "data" / "image_annotation_mapping.json"
    if not mapping_file.exists():
        print("❌ Mapping file not found. Run create_mapping.py first!")
        return
    
    with open(mapping_file) as f:
        mapping = json.load(f)
    
    print(f"📊 Processing {mapping['valid_pairs']} annotations...")
    
    # Create output directory
    json_output_dir = BASE_DIR / "data" / "processed" / "json"
    json_output_dir.mkdir(parents=True, exist_ok=True)
    
    parser = FloorPlanTextParser()
    
    stats = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "errors": []
    }
    
    for pair in tqdm(mapping["pairs"], desc="Parsing"):
        annotation_path = BASE_DIR / pair["annotation_path"]
        
        # Read annotation
        with open(annotation_path) as f:
            text = f.read().strip()
        
        # Parse
        try:
            parsed_data = parser.parse_description(text)
            parsed_data["id"] = pair["id"]
            parsed_data["source_annotation"] = pair["annotation_path"]
            parsed_data["source_image"] = pair["image_path"]
            
            # Validate
            is_valid, errors = parser.validate_parsed_data(parsed_data)
            
            if is_valid:
                stats["valid"] += 1
            else:
                stats["invalid"] += 1
                stats["errors"].append({
                    "id": pair["id"],
                    "errors": errors
                })
            
            # Save regardless (we can filter later)
            output_file = json_output_dir / f"{pair['id']}.json"
            with open(output_file, 'w') as f:
                json.dump(parsed_data, f, indent=2)
            
            stats["total"] += 1
            
        except Exception as e:
            print(f"\n❌ Error processing {pair['id']}: {e}")
            stats["invalid"] += 1
    
    # Save statistics
    stats_file = BASE_DIR / "data" / "processed" / "parsing_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 PARSING SUMMARY")
    print("="*60)
    print(f"✅ Total processed: {stats['total']}")
    print(f"✅ Valid: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"⚠️  Invalid: {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
    print(f"📁 Output directory: {json_output_dir}")
    print(f"📊 Stats saved to: {stats_file}")
    print("="*60)
    
    # Show sample errors
    if stats["errors"]:
        print(f"\n⚠️  Sample validation errors (first 5):")
        for error in stats["errors"][:5]:
            print(f"   ID {error['id']}: {', '.join(error['errors'])}")


if __name__ == "__main__":
    print("🚀 Starting text parsing process...\n")
    process_all_annotations()
    print("\n✅ Parsing complete!")

