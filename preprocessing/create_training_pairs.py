"""
Create Training Pairs: Combine JSON and SVG into training dataset.

Creates train/validation/test splits for CodeT5 fine-tuning.

Output format (JSONL):
{
    "id": "10017",
    "input": "{...JSON...}",  # Input to model
    "output": "<svg>...</svg>",  # Expected output
    "metadata": {...}
}

Usage:
    python preprocessing/create_training_pairs.py
"""

import json
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm
import random


def create_training_pair(pair_id: str, json_path: Path, svg_path: Path) -> Dict:
    """Create a single training pair."""
    
    # Load JSON (model input)
    with open(json_path) as f:
        json_data = json.load(f)
    
    # Load SVG (model output)
    with open(svg_path) as f:
        svg_data = f.read()
    
    # Create simplified JSON for model input (remove unnecessary fields)
    model_input = {
        "rooms": json_data.get("rooms", []),
        "total_rooms": json_data.get("total_rooms", 0),
        "total_square_footage": json_data.get("total_square_footage", 0)
    }
    
    # Create training pair
    training_pair = {
        "id": pair_id,
        "input": json.dumps(model_input),
        "output": svg_data,
        "metadata": {
            "num_rooms": model_input["total_rooms"],
            "total_sqft": model_input["total_square_footage"],
            "input_length": len(json.dumps(model_input)),
            "output_length": len(svg_data)
        }
    }
    
    return training_pair


def split_dataset(pairs: List[Dict], train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """
    Split dataset into train/val/test.
    
    Args:
        pairs: List of training pairs
        train_ratio: Fraction for training (default 0.8)
        val_ratio: Fraction for validation (default 0.1)
        test_ratio: Fraction for testing (default 0.1)
    """
    
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, "Ratios must sum to 1"
    
    # Shuffle
    random.shuffle(pairs)
    
    total = len(pairs)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    train_data = pairs[:train_end]
    val_data = pairs[train_end:val_end]
    test_data = pairs[val_end:]
    
    return train_data, val_data, test_data


def save_jsonl(data: List[Dict], output_path: Path):
    """Save data in JSONL format (one JSON object per line)."""
    with open(output_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')


def create_all_training_pairs():
    """Create all training pairs and split into train/val/test."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    json_dir = BASE_DIR / "data" / "processed" / "json"
    svg_dir = BASE_DIR / "data" / "processed" / "svg"
    output_dir = BASE_DIR / "data" / "training"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔍 Finding valid JSON-SVG pairs...")
    
    # Find all JSON files that have corresponding SVG files
    valid_pairs = []
    
    for json_file in tqdm(list(json_dir.glob("*.json")), desc="Scanning"):
        svg_file = svg_dir / f"{json_file.stem}.svg"
        
        if svg_file.exists():
            valid_pairs.append({
                "id": json_file.stem,
                "json_path": json_file,
                "svg_path": svg_file
            })
    
    print(f"✅ Found {len(valid_pairs)} valid pairs")
    
    if len(valid_pairs) == 0:
        print("❌ No valid pairs found. Make sure you've run:")
        print("   1. create_mapping.py")
        print("   2. text_parser.py")
        print("   3. image_to_svg.py")
        return
    
    # Create training pairs
    print("\n📦 Creating training pairs...")
    training_pairs = []
    
    for pair_info in tqdm(valid_pairs, desc="Processing"):
        try:
            pair = create_training_pair(
                pair_info["id"],
                pair_info["json_path"],
                pair_info["svg_path"]
            )
            training_pairs.append(pair)
        except Exception as e:
            print(f"\n❌ Error creating pair {pair_info['id']}: {e}")
    
    print(f"✅ Created {len(training_pairs)} training pairs")
    
    # Split dataset
    print("\n✂️  Splitting dataset...")
    
    # Use 80% train, 10% val, 10% test
    train_data, val_data, test_data = split_dataset(
        training_pairs,
        train_ratio=0.8,
        val_ratio=0.1,
        test_ratio=0.1
    )
    
    print(f"   📊 Train: {len(train_data)} pairs")
    print(f"   📊 Validation: {len(val_data)} pairs")
    print(f"   📊 Test: {len(test_data)} pairs")
    
    # Save datasets
    print("\n💾 Saving datasets...")
    
    save_jsonl(train_data, output_dir / "train.jsonl")
    save_jsonl(val_data, output_dir / "val.jsonl")
    save_jsonl(test_data, output_dir / "test.jsonl")
    
    # Save metadata
    metadata = {
        "total_pairs": len(training_pairs),
        "train_size": len(train_data),
        "val_size": len(val_data),
        "test_size": len(test_data),
        "train_ratio": 0.8,
        "val_ratio": 0.1,
        "test_ratio": 0.1,
        "avg_input_length": sum(p["metadata"]["input_length"] for p in training_pairs) / len(training_pairs),
        "avg_output_length": sum(p["metadata"]["output_length"] for p in training_pairs) / len(training_pairs),
        "avg_rooms_per_plan": sum(p["metadata"]["num_rooms"] for p in training_pairs) / len(training_pairs)
    }
    
    metadata_file = output_dir / "dataset_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TRAINING DATASET SUMMARY")
    print("="*60)
    print(f"✅ Total pairs: {metadata['total_pairs']}")
    print(f"   📚 Train: {metadata['train_size']} ({metadata['train_size']/metadata['total_pairs']*100:.1f}%)")
    print(f"   🔍 Validation: {metadata['val_size']} ({metadata['val_size']/metadata['total_pairs']*100:.1f}%)")
    print(f"   🧪 Test: {metadata['test_size']} ({metadata['test_size']/metadata['total_pairs']*100:.1f}%)")
    print(f"\n📏 Average Lengths:")
    print(f"   Input (JSON): {metadata['avg_input_length']:.0f} characters")
    print(f"   Output (SVG): {metadata['avg_output_length']:.0f} characters")
    print(f"   Rooms per plan: {metadata['avg_rooms_per_plan']:.1f}")
    print(f"\n📁 Output directory: {output_dir}")
    print(f"   - train.jsonl")
    print(f"   - val.jsonl")
    print(f"   - test.jsonl")
    print(f"   - dataset_metadata.json")
    print("="*60)


if __name__ == "__main__":
    print("🚀 Starting training pair creation...\n")
    
    # Set random seed for reproducibility
    random.seed(42)
    
    create_all_training_pairs()
    print("\n✅ Training pairs created successfully!")
    print("\n🎯 Next step: Run model training")
    print("   python models/train_codet5.py")

