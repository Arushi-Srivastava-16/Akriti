"""
Model Evaluation: Evaluate trained model on test set.

Metrics:
- SVG validity rate
- Room count accuracy
- Dimension accuracy
- BLEU score (structural similarity)

Usage:
    python models/evaluation.py
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from tqdm import tqdm
from collections import Counter

from inference import FloorPlanGenerator


class FloorPlanEvaluator:
    """Evaluate floor plan generation quality."""
    
    def __init__(self, model_path: str):
        """Initialize evaluator with trained model."""
        self.generator = FloorPlanGenerator(model_path)
        self.results = {
            "total": 0,
            "svg_valid": 0,
            "svg_invalid": 0,
            "room_count_exact": 0,
            "room_count_close": 0,  # Within 1 room
            "dimension_errors": [],
            "generation_errors": []
        }
    
    def is_valid_svg(self, svg_code: str) -> Tuple[bool, str]:
        """
        Check if generated SVG is valid.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Try to parse as XML
            root = ET.fromstring(svg_code)
            
            # Check if it's actually an SVG
            if 'svg' not in root.tag.lower():
                return False, "Not an SVG element"
            
            # Check if it has content
            if len(root) == 0:
                return False, "Empty SVG"
            
            return True, ""
            
        except ET.ParseError as e:
            return False, f"Parse error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    def evaluate_room_count(self, ground_truth: Dict, generated_svg: str) -> Dict:
        """
        Evaluate room count accuracy.
        
        Args:
            ground_truth: Original JSON with room data
            generated_svg: Generated SVG code
            
        Returns:
            Evaluation metrics
        """
        gt_room_count = ground_truth.get("total_rooms", 0)
        
        # Count rooms in generated SVG (simplified - count room groups)
        generated_room_count = generated_svg.count('id="room_')
        
        is_exact = (gt_room_count == generated_room_count)
        is_close = abs(gt_room_count - generated_room_count) <= 1
        
        return {
            "gt_count": gt_room_count,
            "generated_count": generated_room_count,
            "is_exact": is_exact,
            "is_close": is_close,
            "error": abs(gt_room_count - generated_room_count)
        }
    
    def evaluate_dimensions(self, ground_truth: Dict, generated_svg: str) -> Dict:
        """
        Evaluate dimension accuracy (if extractable from SVG).
        
        Note: This is a simplified check - full geometric analysis would be more complex.
        """
        gt_total_sqft = ground_truth.get("total_square_footage", 0)
        
        # For now, just record ground truth
        # Full implementation would extract dimensions from SVG
        
        return {
            "gt_total_sqft": gt_total_sqft,
            # "generated_total_sqft": ...,  # Would need SVG parsing
            # "error": ...
        }
    
    def evaluate_single(self, example: Dict) -> Dict:
        """Evaluate a single example."""
        
        result = {
            "id": example["id"],
            "success": False
        }
        
        try:
            # Parse input JSON
            input_data = json.loads(example["input"])
            
            # Generate SVG
            generated_svg = self.generator.generate(input_data)
            
            # Check SVG validity
            is_valid, error_msg = self.is_valid_svg(generated_svg)
            result["svg_valid"] = is_valid
            result["svg_error"] = error_msg
            
            if is_valid:
                self.results["svg_valid"] += 1
                
                # Evaluate room count
                room_eval = self.evaluate_room_count(input_data, generated_svg)
                result["room_count"] = room_eval
                
                if room_eval["is_exact"]:
                    self.results["room_count_exact"] += 1
                if room_eval["is_close"]:
                    self.results["room_count_close"] += 1
                
                # Evaluate dimensions
                dim_eval = self.evaluate_dimensions(input_data, generated_svg)
                result["dimensions"] = dim_eval
                
                result["success"] = True
            else:
                self.results["svg_invalid"] += 1
            
        except Exception as e:
            result["error"] = str(e)
            self.results["generation_errors"].append({
                "id": example["id"],
                "error": str(e)
            })
        
        self.results["total"] += 1
        
        return result
    
    def evaluate_dataset(self, test_file: Path) -> Dict:
        """Evaluate entire test dataset."""
        
        print(f"📊 Evaluating on {test_file}")
        
        # Load test data
        test_examples = []
        with open(test_file) as f:
            for line in f:
                test_examples.append(json.loads(line))
        
        print(f"   Found {len(test_examples)} test examples")
        
        # Evaluate each example
        detailed_results = []
        
        for example in tqdm(test_examples, desc="Evaluating"):
            result = self.evaluate_single(example)
            detailed_results.append(result)
        
        # Calculate final metrics
        metrics = self.calculate_metrics()
        
        return {
            "metrics": metrics,
            "detailed_results": detailed_results
        }
    
    def calculate_metrics(self) -> Dict:
        """Calculate final evaluation metrics."""
        
        total = self.results["total"]
        
        if total == 0:
            return {}
        
        metrics = {
            "total_examples": total,
            "svg_validity_rate": self.results["svg_valid"] / total,
            "room_count_exact_accuracy": self.results["room_count_exact"] / total,
            "room_count_close_accuracy": self.results["room_count_close"] / total,
            "generation_error_rate": len(self.results["generation_errors"]) / total
        }
        
        return metrics


def evaluate_model():
    """Main evaluation function."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    # Model path
    model_path = BASE_DIR / "checkpoints" / "codet5-floorplan-v1" / "final_model"
    
    if not model_path.exists():
        print("❌ Model not found. Train the model first:")
        print("   python models/train_codet5.py")
        return
    
    # Test file
    test_file = BASE_DIR / "data" / "training" / "test.jsonl"
    
    if not test_file.exists():
        print("❌ Test file not found. Run data preparation first:")
        print("   python preprocessing/create_training_pairs.py")
        return
    
    # Evaluate
    print("🚀 Starting evaluation...\n")
    
    evaluator = FloorPlanEvaluator(str(model_path))
    results = evaluator.evaluate_dataset(test_file)
    
    # Save results
    output_file = BASE_DIR / "models" / "evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    metrics = results["metrics"]
    
    print("\n" + "="*60)
    print("📊 EVALUATION RESULTS")
    print("="*60)
    print(f"Total examples: {metrics['total_examples']}")
    print(f"\n✅ SVG Validity Rate: {metrics['svg_validity_rate']*100:.1f}%")
    print(f"✅ Room Count Accuracy (Exact): {metrics['room_count_exact_accuracy']*100:.1f}%")
    print(f"✅ Room Count Accuracy (±1): {metrics['room_count_close_accuracy']*100:.1f}%")
    print(f"❌ Generation Error Rate: {metrics['generation_error_rate']*100:.1f}%")
    print(f"\n📁 Detailed results saved to: {output_file}")
    print("="*60)
    
    # Check if meets targets
    print("\n🎯 Target Metrics (from architecture):")
    print(f"   SVG Validity: >90% {'✅' if metrics['svg_validity_rate'] > 0.9 else '❌'}")
    print(f"   Room Count Accuracy: >85% {'✅' if metrics['room_count_exact_accuracy'] > 0.85 else '❌'}")


if __name__ == "__main__":
    evaluate_model()

