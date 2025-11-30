"""
Model Inference: Generate SVG floor plans from JSON descriptions.

Usage:
    from inference import FloorPlanGenerator
    
    generator = FloorPlanGenerator("checkpoints/codet5-floorplan-v1/final_model")
    svg = generator.generate(json_data)
"""

import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Union


class FloorPlanGenerator:
    """Generate SVG floor plans from JSON descriptions using trained CodeT5."""
    
    def __init__(self, model_path: str, device: str = None):
        """
        Initialize generator with trained model.
        
        Args:
            model_path: Path to saved model checkpoint
            device: Device to run on ('cuda' or 'cpu'). Auto-detected if None.
        """
        self.model_path = Path(model_path)
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"🚀 Loading model from {self.model_path}")
        print(f"   Device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()
        
        print(f"✅ Model loaded successfully")
    
    def generate(
        self,
        json_data: Union[Dict, str],
        num_beams: int = 5,
        max_length: int = 1024,
        temperature: float = 1.0,
        top_p: float = 0.95,
        **kwargs
    ) -> str:
        """
        Generate SVG from JSON floor plan description.
        
        Args:
            json_data: Floor plan JSON (dict or string)
            num_beams: Number of beams for beam search
            max_length: Maximum output length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            **kwargs: Additional generation parameters
            
        Returns:
            Generated SVG code as string
        """
        
        # Convert dict to string if needed
        if isinstance(json_data, dict):
            input_text = json.dumps(json_data)
        else:
            input_text = json_data
        
        # Tokenize input
        inputs = self.tokenizer(
            input_text,
            max_length=512,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_length=max_length,
                num_beams=num_beams,
                temperature=temperature,
                top_p=top_p,
                early_stopping=True,
                **kwargs
            )
        
        # Decode
        svg_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return svg_code
    
    def generate_batch(
        self,
        json_data_list: list,
        batch_size: int = 8,
        **kwargs
    ) -> list:
        """
        Generate SVGs for multiple JSON descriptions (batch processing).
        
        Args:
            json_data_list: List of JSON floor plan descriptions
            batch_size: Batch size for processing
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated SVG codes
        """
        
        results = []
        
        for i in range(0, len(json_data_list), batch_size):
            batch = json_data_list[i:i+batch_size]
            
            # Process batch
            batch_results = [self.generate(json_data, **kwargs) for json_data in batch]
            results.extend(batch_results)
        
        return results
    
    def save_svg(self, svg_code: str, output_path: str):
        """Save generated SVG to file."""
        with open(output_path, 'w') as f:
            f.write(svg_code)


def test_inference():
    """Test inference with a sample floor plan."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    # Check if model exists
    model_path = BASE_DIR / "checkpoints" / "codet5-floorplan-v1" / "final_model"
    
    if not model_path.exists():
        print("❌ Model not found. Train the model first:")
        print("   python models/train_codet5.py")
        return
    
    # Load generator
    generator = FloorPlanGenerator(str(model_path))
    
    # Sample input (from training data)
    sample_json = {
        "rooms": [
            {
                "room": "living room",
                "position": "north",
                "dimensions": {"width": 15, "depth": 20, "square_footage": 300},
                "adjacent_rooms": ["kitchen", "bedroom"]
            },
            {
                "room": "kitchen",
                "position": "south",
                "dimensions": {"width": 12, "depth": 12, "square_footage": 144},
                "adjacent_rooms": ["living room"]
            }
        ],
        "total_rooms": 2,
        "total_square_footage": 444
    }
    
    print("\n📝 Input JSON:")
    print(json.dumps(sample_json, indent=2))
    
    # Generate SVG
    print("\n🎨 Generating SVG...")
    svg_code = generator.generate(sample_json)
    
    print("\n✅ Generated SVG:")
    print(svg_code[:500] + "..." if len(svg_code) > 500 else svg_code)
    
    # Save
    output_file = BASE_DIR / "test_output.svg"
    generator.save_svg(svg_code, str(output_file))
    
    print(f"\n💾 Saved to: {output_file}")


if __name__ == "__main__":
    print("🧪 Testing inference...\n")
    test_inference()

