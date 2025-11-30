"""
FastAPI Main Application Entry Point.

Starts the Akriti Floor Plan Generator API server.

Usage:
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .api.routes import router

# Create FastAPI app
app = FastAPI(
    title="Akriti Floor Plan Generator API",
    description="Generate professional floor plans from natural language descriptions using AI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Akriti Floor Plan Generator API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "parse": "POST /api/v1/parse - Parse text to JSON",
            "generate": "POST /api/v1/generate - Generate SVG from JSON",
            "edit": "POST /api/v1/edit - Edit existing SVG",
            "export": "POST /api/v1/export - Export SVG to PNG/PDF",
            "health": "GET /api/v1/health - Health check"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("="*60)
    print("🚀 Akriti Floor Plan Generator API")
    print("="*60)
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("\n👋 Shutting down Akriti API...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

