"""
Data Validator: Check data quality before training.

Validates:
- JSON structure correctness
- SVG validity
- Training pair completeness
- Data distribution

Usage:
    python preprocessing/data_validator.py
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET
from tqdm import tqdm
from collections import Counter


class DataValidator:
    """Validate processed data quality."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_json(self, json_path: Path) -> Tuple[bool, List[str]]:
        """Validate JSON structure."""
        errors = []
        
        try:
            with open(json_path) as f:
                data = json.load(f)
            
            # Check required fields
            if "rooms" not in data:
                errors.append("Missing 'rooms' field")
            
            if "total_rooms" not in data:
                errors.append("Missing 'total_rooms' field")
            
            # Validate rooms
            if "rooms" in data:
                if len(data["rooms"]) == 0:
                    errors.append("No rooms found")
                
                for i, room in enumerate(data["rooms"]):
                    if "room" not in room:
                        errors.append(f"Room {i}: missing 'room' field")
                    
                    if "dimensions" in room:
                        dims = room["dimensions"]
                        if "square_footage" in dims and dims["square_footage"] <= 0:
                            errors.append(f"Room {i}: invalid square footage")
        
        except json.JSONDecodeError as e:
            errors.append(f"JSON decode error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return len(errors) == 0, errors
    
    def validate_svg(self, svg_path: Path) -> Tuple[bool, List[str]]:
        """Validate SVG structure and syntax."""
        errors = []
        
        try:
            # Parse XML
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            # Check it's actually an SVG
            if 'svg' not in root.tag.lower():
                errors.append("Not a valid SVG file")
            
            # Check for basic structure
            if len(root) == 0:
                errors.append("Empty SVG (no elements)")
            
            # Check file size (shouldn't be too small or too large)
            file_size = svg_path.stat().st_size
            if file_size < 100:
                errors.append("SVG file too small (likely incomplete)")
            if file_size > 1_000_000:  # 1MB
                errors.append("SVG file too large (likely corrupt)")
        
        except ET.ParseError as e:
            errors.append(f"XML parse error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return len(errors) == 0, errors
    
    def validate_pair(self, json_path: Path, svg_path: Path) -> Tuple[bool, List[str]]:
        """Validate a JSON-SVG pair."""
        errors = []
        
        # Validate JSON
        json_valid, json_errors = self.validate_json(json_path)
        if not json_valid:
            errors.extend([f"JSON: {e}" for e in json_errors])
        
        # Validate SVG
        svg_valid, svg_errors = self.validate_svg(svg_path)
        if not svg_valid:
            errors.extend([f"SVG: {e}" for e in svg_errors])
        
        # Check consistency (e.g., number of rooms matches)
        try:
            with open(json_path) as f:
                json_data = json.load(f)
            
            with open(svg_path) as f:
                svg_content = f.read()
            
            # Basic consistency check
            num_rooms_json = json_data.get("total_rooms", 0)
            # Count room groups in SVG (simplified check)
            num_rooms_svg = svg_content.count('id="room_')
            
            if abs(num_rooms_json - num_rooms_svg) > 2:  # Allow small mismatch
                errors.append(f"Room count mismatch: JSON={num_rooms_json}, SVG={num_rooms_svg}")
        
        except Exception as e:
            errors.append(f"Consistency check error: {e}")
        
        return len(errors) == 0, errors


def validate_all_data():
    """Validate all processed data."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    json_dir = BASE_DIR / "data" / "processed" / "json"
    svg_dir = BASE_DIR / "data" / "processed" / "svg"
    
    print("🔍 Validating processed data...")
    
    validator = DataValidator()
    
    stats = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "errors": {},
        "room_count_distribution": Counter(),
        "sqft_distribution": []
    }
    
    # Get all JSON files
    json_files = list(json_dir.glob("*.json"))
    
    for json_file in tqdm(json_files, desc="Validating"):
        svg_file = svg_dir / f"{json_file.stem}.svg"
        
        if not svg_file.exists():
            stats["invalid"] += 1
            stats["errors"][json_file.stem] = ["SVG file missing"]
            continue
        
        # Validate pair
        is_valid, errors = validator.validate_pair(json_file, svg_file)
        
        if is_valid:
            stats["valid"] += 1
            
            # Collect statistics
            try:
                with open(json_file) as f:
                    data = json.load(f)
                
                num_rooms = data.get("total_rooms", 0)
                stats["room_count_distribution"][num_rooms] += 1
                
                sqft = data.get("total_square_footage", 0)
                if sqft > 0:
                    stats["sqft_distribution"].append(sqft)
            except:
                pass
        else:
            stats["invalid"] += 1
            stats["errors"][json_file.stem] = errors
        
        stats["total"] += 1
    
    # Calculate statistics
    if stats["sqft_distribution"]:
        stats["avg_sqft"] = sum(stats["sqft_distribution"]) / len(stats["sqft_distribution"])
        stats["min_sqft"] = min(stats["sqft_distribution"])
        stats["max_sqft"] = max(stats["sqft_distribution"])
    
    # Save validation report
    report_file = BASE_DIR / "data" / "processed" / "validation_report.json"
    with open(report_file, 'w') as f:
        # Convert Counter to dict for JSON serialization
        report_data = {**stats}
        report_data["room_count_distribution"] = dict(stats["room_count_distribution"])
        del report_data["sqft_distribution"]  # Too large for JSON
        json.dump(report_data, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    print(f"✅ Total validated: {stats['total']}")
    print(f"✅ Valid: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"❌ Invalid: {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
    
    if stats["room_count_distribution"]:
        print(f"\n📊 Room Count Distribution:")
        for num_rooms in sorted(stats["room_count_distribution"].keys()):
            count = stats["room_count_distribution"][num_rooms]
            bar = "█" * int(count / stats['total'] * 50)
            print(f"   {num_rooms} rooms: {count:3d} {bar}")
    
    if stats.get("avg_sqft"):
        print(f"\n📏 Square Footage Statistics:")
        print(f"   Average: {stats['avg_sqft']:.0f} sq ft")
        print(f"   Range: {stats['min_sqft']:.0f} - {stats['max_sqft']:.0f} sq ft")
    
    print(f"\n📁 Validation report saved to: {report_file}")
    
    if stats["errors"]:
        print(f"\n❌ Sample errors (first 5):")
        for file_id in list(stats["errors"].keys())[:5]:
            errors = stats["errors"][file_id]
            print(f"   {file_id}: {errors[0]}")
    
    print("="*60)
    
    return stats


if __name__ == "__main__":
    print("🚀 Starting data validation...\n")
    validate_all_data()
    print("\n✅ Validation complete!")

