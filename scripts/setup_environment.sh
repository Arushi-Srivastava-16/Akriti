#!/bin/bash

# Setup script for Akriti Floor Plan Generator
# Initializes the development environment

echo "🚀 Setting up Akriti Floor Plan Generator..."
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
echo ""
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

echo ""
echo "✅ Python setup complete!"

# Setup frontend (if Node.js is available)
echo ""
echo "Checking for Node.js..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "✅ Node.js $node_version found"
    
    echo ""
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    
    echo "✅ Frontend setup complete!"
else
    echo "⚠️  Node.js not found. Please install Node.js 18+ to run the frontend."
    echo "   Visit: https://nodejs.org/"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/processed/svg
mkdir -p data/processed/json
mkdir -p data/training
mkdir -p checkpoints
mkdir -p logs

echo ""
echo "="*60
echo "🎉 Setup Complete!"
echo "="*60
echo ""
echo "Next steps:"
echo ""
echo "1. Data Preparation:"
echo "   python preprocessing/create_mapping.py"
echo "   python preprocessing/text_parser.py"
echo "   python preprocessing/image_to_svg.py"
echo "   python preprocessing/create_training_pairs.py"
echo ""
echo "2. Model Training (requires GPU):"
echo "   python models/train_codet5.py"
echo ""
echo "3. Run Backend:"
echo "   cd backend"
echo "   python -m uvicorn main:app --reload"
echo ""
echo "4. Run Frontend (in new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "="*60

