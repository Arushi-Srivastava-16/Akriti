"""
Test Text Parser
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.text_parser import FloorPlanTextParser


def test_parse_sentence():
    """Test parsing a single sentence."""
    parser = FloorPlanTextParser()
    
    sentence = "The living room is at the north corner. It is approximately 15 feet wide by 20 feet deep, for a total square footage of 300."
    
    result = parser.parse_sentence(sentence)
    
    assert result["room"] == "living room"
    assert result["position"] == "north"
    assert result["dimensions"]["width"] == 15
    assert result["dimensions"]["depth"] == 20
    assert result["dimensions"]["square_footage"] == 300
    
    print("✅ test_parse_sentence passed")


def test_parse_description():
    """Test parsing complete description."""
    parser = FloorPlanTextParser()
    
    text = """The living room is at the north corner. It is approximately 15 feet wide by 20 feet deep, for a total square footage of 300. The kitchen is to the south. It is approximately 12 feet wide by 12 feet deep, for a total square footage of 144."""
    
    result = parser.parse_description(text)
    
    assert result["total_rooms"] == 2
    assert result["total_square_footage"] == 444
    assert len(result["rooms"]) == 2
    
    print("✅ test_parse_description passed")


def test_confidence_score():
    """Test confidence scoring."""
    parser = FloorPlanTextParser()
    
    # Good description (should have high confidence)
    good_text = "The living room is at the north corner. It is approximately 15 feet wide by 20 feet deep, for a total square footage of 300."
    result, confidence = parser.parse(good_text)
    assert confidence > 0.6
    
    # Poor description (should have lower confidence)
    poor_text = "There is a room."
    result, confidence = parser.parse(poor_text)
    assert confidence < 0.8
    
    print("✅ test_confidence_score passed")


if __name__ == "__main__":
    print("🧪 Running parser tests...\n")
    
    test_parse_sentence()
    test_parse_description()
    test_confidence_score()
    
    print("\n✅ All tests passed!")

