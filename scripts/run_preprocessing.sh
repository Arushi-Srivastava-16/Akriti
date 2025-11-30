#!/bin/bash

# Run all preprocessing scripts in sequence
# This processes the 4k annotated images from the 80k total

echo "🚀 Starting data preprocessing pipeline..."
echo ""

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Step 1: Create mapping
echo "="*60
echo "Step 1/4: Creating image-annotation mapping..."
echo "="*60
python preprocessing/create_mapping.py
if [ $? -ne 0 ]; then
    echo "❌ Mapping creation failed"
    exit 1
fi

# Step 2: Parse text
echo ""
echo "="*60
echo "Step 2/4: Parsing text annotations to JSON..."
echo "="*60
python preprocessing/text_parser.py
if [ $? -ne 0 ]; then
    echo "❌ Text parsing failed"
    exit 1
fi

# Step 3: Convert to SVG
echo ""
echo "="*60
echo "Step 3/4: Converting images to SVG..."
echo "="*60
echo "⚠️  This may take a while (processing ~4000 images)..."
python preprocessing/image_to_svg.py
if [ $? -ne 0 ]; then
    echo "❌ SVG conversion failed"
    exit 1
fi

# Step 4: Create training pairs
echo ""
echo "="*60
echo "Step 4/4: Creating training pairs..."
echo "="*60
python preprocessing/create_training_pairs.py
if [ $? -ne 0 ]; then
    echo "❌ Training pair creation failed"
    exit 1
fi

# Validate data
echo ""
echo "="*60
echo "Validating processed data..."
echo "="*60
python preprocessing/data_validator.py

echo ""
echo "="*60
echo "🎉 Data preprocessing complete!"
echo "="*60
echo ""
echo "Next steps:"
echo "1. Review the statistics in data/processed/"
echo "2. Train the model: python models/train_codet5.py"
echo "3. Or start the backend: cd backend && python -m uvicorn main:app --reload"
echo ""

