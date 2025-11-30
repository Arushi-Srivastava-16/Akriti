"""
API Routes for Akriti Backend.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import io
import uuid

from ..api.schemas import (
    ParseRequest, ParseResponse,
    GenerateRequest, GenerateResponse,
    EditRequest, EditResponse,
    ExportRequest,
    HealthResponse,
    ErrorResponse,
    FloorPlanJSON
)
from ..services.parser_service import ParserService
from ..services.generation_service import GenerationService
from ..services.svg_service import SVGService

# Initialize services
parser_service = ParserService()
generation_service = GenerationService()
svg_service = SVGService()

# Create router
router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status."""
    return {
        "status": "ok",
        "model_loaded": generation_service.model_loaded,
        "version": "0.1.0"
    }


@router.post("/parse", response_model=ParseResponse)
async def parse_text(request: ParseRequest):
    """
    Parse natural language floor plan description to structured JSON.
    
    Example:
        POST /api/v1/parse
        {
            "text": "The living room is at the north corner..."
        }
    """
    
    try:
        # Parse text
        parsed_data, confidence = parser_service.parse(request.text)
        
        # Convert to response model
        floor_plan_json = FloorPlanJSON(**parsed_data)
        
        return ParseResponse(
            json=floor_plan_json,
            confidence=confidence,
            raw_text=request.text
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_svg(request: GenerateRequest):
    """
    Generate SVG floor plan from structured JSON.
    
    Example:
        POST /api/v1/generate
        {
            "json": {
                "rooms": [...],
                "total_rooms": 2,
                "total_square_footage": 500
            }
        }
    """
    
    try:
        # Convert to dict
        json_data = request.json.dict()
        
        # Generate SVG
        result = generation_service.generate(json_data)
        
        return GenerateResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@router.post("/edit", response_model=EditResponse)
async def edit_svg(request: EditRequest):
    """
    Edit existing SVG floor plan.
    
    Example:
        POST /api/v1/edit
        {
            "svg": "<svg>...</svg>",
            "changes": {
                "room_id": "room_living_room",
                "new_position": {"x": 100, "y": 100}
            }
        }
    """
    
    try:
        # Validate SVG
        is_valid, error = svg_service.validate_svg(request.svg)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid SVG: {error}")
        
        # Apply edits
        modified_svg, success = svg_service.edit_room(request.svg, request.changes)
        
        return EditResponse(
            svg=modified_svg,
            success=success
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edit error: {str(e)}")


@router.post("/export")
async def export_svg(request: ExportRequest):
    """
    Export SVG to PNG or PDF.
    
    Example:
        POST /api/v1/export
        {
            "svg": "<svg>...</svg>",
            "format": "png",
            "width": 1920,
            "height": 1080
        }
    """
    
    try:
        # Validate format
        if request.format not in ["png", "pdf", "svg"]:
            raise HTTPException(status_code=400, detail="Format must be 'png', 'pdf', or 'svg'")
        
        # For SVG, just return it
        if request.format == "svg":
            return Response(
                content=request.svg,
                media_type="image/svg+xml",
                headers={"Content-Disposition": "attachment; filename=floorplan.svg"}
            )
        
        # For PNG/PDF, we'd need cairosvg or similar
        # For now, return a placeholder response
        try:
            import cairosvg
            
            if request.format == "png":
                output = cairosvg.svg2png(
                    bytestring=request.svg.encode('utf-8'),
                    output_width=request.width,
                    output_height=request.height
                )
                
                return Response(
                    content=output,
                    media_type="image/png",
                    headers={"Content-Disposition": "attachment; filename=floorplan.png"}
                )
            
            elif request.format == "pdf":
                output = cairosvg.svg2pdf(
                    bytestring=request.svg.encode('utf-8'),
                    output_width=request.width,
                    output_height=request.height
                )
                
                return Response(
                    content=output,
                    media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=floorplan.pdf"}
                )
        
        except ImportError:
            # cairosvg not installed
            raise HTTPException(
                status_code=501,
                detail="PNG/PDF export requires cairosvg. Install with: pip install cairosvg"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.get("/rooms/{svg_id}")
async def list_rooms(svg_id: str):
    """
    List all rooms in an SVG.
    
    Note: In production, you'd retrieve SVG from database using svg_id.
    For now, this is a placeholder.
    """
    return {
        "svg_id": svg_id,
        "rooms": []
    }

