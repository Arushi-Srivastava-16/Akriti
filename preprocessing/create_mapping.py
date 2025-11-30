"""
Create mapping between annotations and images.
Only processes the 4k annotated images from the 80k total.

Usage:
    python preprocessing/create_mapping.py
"""

import os
import json
from pathlib import Path
from tqdm import tqdm

# Paths
BASE_DIR = Path(__file__).parent.parent
ANNOTATIONS_DIR = BASE_DIR / "data" / "raw" / "annotations"
IMAGES_DIR = BASE_DIR / "data" / "raw" / "images"
OUTPUT_FILE = BASE_DIR / "data" / "image_annotation_mapping.json"


def create_mapping():
    """Create mapping between annotation files and their corresponding images."""
    
    print("🔍 Scanning annotation files...")
    annotation_files = sorted(ANNOTATIONS_DIR.glob("*.txt"))
    
    print(f"📊 Found {len(annotation_files)} annotation files")
    
    mapping = {
        "total_annotations": len(annotation_files),
        "valid_pairs": 0,
        "missing_images": 0,
        "pairs": []
    }
    
    missing_images = []
    
    for annotation_file in tqdm(annotation_files, desc="Creating mapping"):
        # Extract ID from annotation filename (e.g., "10017.txt" -> "10017")
        annotation_id = annotation_file.stem
        
        # Look for corresponding image
        image_file = IMAGES_DIR / f"{annotation_id}.png"
        
        if image_file.exists():
            mapping["pairs"].append({
                "id": annotation_id,
                "annotation_path": str(annotation_file.relative_to(BASE_DIR)),
                "image_path": str(image_file.relative_to(BASE_DIR)),
                "annotation_size": annotation_file.stat().st_size,
                "image_size": image_file.stat().st_size
            })
            mapping["valid_pairs"] += 1
        else:
            missing_images.append(annotation_id)
            mapping["missing_images"] += 1
    
    # Save mapping
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 MAPPING SUMMARY")
    print("="*60)
    print(f"✅ Valid pairs: {mapping['valid_pairs']}")
    print(f"❌ Missing images: {mapping['missing_images']}")
    print(f"📁 Output saved to: {OUTPUT_FILE}")
    
    if missing_images:
        print(f"\n⚠️  Missing image IDs (first 10): {missing_images[:10]}")
        missing_file = BASE_DIR / "data" / "missing_images.txt"
        with open(missing_file, 'w') as f:
            f.write('\n'.join(missing_images))
        print(f"   Full list saved to: {missing_file}")
    
    print("="*60)
    
    return mapping


def verify_sample_pairs(num_samples=5):
    """Verify a few sample pairs to ensure data quality."""
    
    print(f"\n🔬 Verifying {num_samples} sample pairs...")
    
    with open(OUTPUT_FILE) as f:
        mapping = json.load(f)
    
    import random
    samples = random.sample(mapping["pairs"], min(num_samples, len(mapping["pairs"])))
    
    for i, pair in enumerate(samples, 1):
        print(f"\n--- Sample {i}: ID {pair['id']} ---")
        
        # Read annotation
        annotation_path = BASE_DIR / pair["annotation_path"]
        with open(annotation_path) as f:
            text = f.read().strip()
        
        print(f"📝 Annotation (first 150 chars):")
        print(f"   {text[:150]}...")
        print(f"📏 Full length: {len(text)} characters")
        print(f"🖼️  Image: {pair['image_path']}")
        print(f"💾 Image size: {pair['image_size'] / 1024:.1f} KB")


if __name__ == "__main__":
    print("🚀 Starting mapping creation process...\n")
    
    # Create mapping
    mapping = create_mapping()
    
    # Verify samples
    verify_sample_pairs(num_samples=5)
    
    print("\n✅ Mapping creation complete!")
    print(f"   Use this mapping to process only the {mapping['valid_pairs']} annotated images.")

