# API Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Endpoints

### 1. Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "version": "0.1.0"
}
```

---

### 2. Parse Text
Parse natural language description to structured JSON.

```http
POST /api/v1/parse
```

**Request Body:**
```json
{
  "text": "The living room is at the north corner with the kitchen to the south. It is approximately 15 feet wide by 20 feet deep, for a total square footage of 300."
}
```

**Response:**
```json
{
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
        "adjacent_rooms": ["kitchen"],
        "directions": ["north", "south"]
      }
    ],
    "total_rooms": 1,
    "total_square_footage": 300
  },
  "confidence": 0.85,
  "raw_text": "..."
}
```

---

### 3. Generate SVG
Generate SVG floor plan from structured JSON.

```http
POST /api/v1/generate
```

**Request Body:**
```json
{
  "json": {
    "rooms": [...],
    "total_rooms": 2,
    "total_square_footage": 500
  }
}
```

**Response:**
```json
{
  "svg": "<svg>...</svg>",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "num_rooms": 2,
    "total_sqft": 500,
    "generated_with": "codet5-model"
  }
}
```

---

### 4. Edit SVG
Edit existing SVG floor plan.

```http
POST /api/v1/edit
```

**Request Body:**
```json
{
  "svg": "<svg>...</svg>",
  "changes": {
    "room_id": "room_living_room",
    "new_position": {"x": 100, "y": 100},
    "new_size": {"width": 200, "height": 150}
  }
}
```

**Response:**
```json
{
  "svg": "<svg>...</svg>",
  "success": true
}
```

---

### 5. Export SVG
Export SVG to PNG or PDF.

```http
POST /api/v1/export
```

**Request Body:**
```json
{
  "svg": "<svg>...</svg>",
  "format": "png",
  "width": 1920,
  "height": 1080
}
```

**Response:**
Binary file (PNG/PDF) with appropriate Content-Type header.

---

## Error Responses

All endpoints may return error responses:

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `500` - Internal Server Error
- `501` - Not Implemented

---

## Interactive Documentation

Visit these URLs when the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

