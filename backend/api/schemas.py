"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class RoomInfo(BaseModel):
    """Information about a single room."""
    room: str = Field(..., description="Room type (e.g., 'living room', 'bedroom')")
    position: Optional[str] = Field(None, description="Position (e.g., 'north', 'southeast')")
    dimensions: Optional[Dict] = Field(None, description="Dimensions including width, depth, square_footage")
    adjacent_rooms: Optional[List[str]] = Field([], description="List of adjacent room names")
    directions: Optional[List[str]] = Field([], description="Directional keywords")


class FloorPlanJSON(BaseModel):
    """Structured JSON representation of a floor plan."""
    rooms: List[RoomInfo] = Field(..., description="List of rooms")
    total_rooms: int = Field(..., description="Total number of rooms")
    total_square_footage: Optional[int] = Field(None, description="Total square footage")


class ParseRequest(BaseModel):
    """Request to parse text description."""
    text: str = Field(..., description="Natural language floor plan description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "The living room is at the north corner with the kitchen to the south. It is approximately 15 feet wide by 20 feet deep, for a total square footage of 300."
            }
        }


class ParseResponse(BaseModel):
    """Response from text parsing."""
    json: FloorPlanJSON = Field(..., description="Parsed structured data")
    confidence: float = Field(..., description="Confidence score (0-1)")
    raw_text: str = Field(..., description="Original input text")


class GenerateRequest(BaseModel):
    """Request to generate SVG from JSON."""
    json: FloorPlanJSON = Field(..., description="Structured floor plan data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "json": {
                    "rooms": [
                        {
                            "room": "living room",
                            "position": "north",
                            "dimensions": {
                                "width": 15,
                                "depth": 20,
                                "square_footage": 300
                            },
                            "adjacent_rooms": ["kitchen"]
                        }
                    ],
                    "total_rooms": 1,
                    "total_square_footage": 300
                }
            }
        }


class GenerateResponse(BaseModel):
    """Response from SVG generation."""
    svg: str = Field(..., description="Generated SVG code")
    id: str = Field(..., description="Unique ID for this generation")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")


class EditRequest(BaseModel):
    """Request to edit existing SVG."""
    svg: str = Field(..., description="Current SVG code")
    changes: Dict = Field(..., description="Changes to apply")
    
    class Config:
        json_schema_extra = {
            "example": {
                "svg": "<svg>...</svg>",
                "changes": {
                    "room_id": "room_living_room",
                    "new_position": {"x": 100, "y": 100},
                    "new_size": {"width": 200, "height": 150}
                }
            }
        }


class EditResponse(BaseModel):
    """Response from SVG editing."""
    svg: str = Field(..., description="Updated SVG code")
    success: bool = Field(..., description="Whether edit was successful")


class ExportRequest(BaseModel):
    """Request to export SVG to other formats."""
    svg: str = Field(..., description="SVG code to export")
    format: str = Field(..., description="Output format: 'png', 'pdf', or 'svg'")
    width: Optional[int] = Field(800, description="Output width in pixels")
    height: Optional[int] = Field(600, description="Output height in pixels")
    
    class Config:
        json_schema_extra = {
            "example": {
                "svg": "<svg>...</svg>",
                "format": "png",
                "width": 1920,
                "height": 1080
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

