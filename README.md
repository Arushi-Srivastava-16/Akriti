# Akriti: AI-Powered Floor Plan Generator

Generate professional floor plans from natural language descriptions using deep learning.

## 🏗️ Architecture

```
Text Description → Parser → JSON → CodeT5 Model → SVG → Interactive Editor → Export
```

## 📊 Dataset

- **Total Images**: 80,788 floor plans
- **Annotated**: 4,003 text descriptions
- **Training Pipeline**: JSON ↔ SVG pairs

## 🚀 Features

- **Natural Language Input**: Describe your floor plan in plain English
- **AI Generation**: Fine-tuned CodeT5 model generates precise SVG floor plans
- **Interactive Editor**: Drag, resize, and modify rooms visually
- **Multi-format Export**: PNG, PDF, SVG output
- **Real-time Preview**: See changes instantly

## 📁 Project Structure

```
├── data/                   # Dataset (80k images, 4k annotations)
├── preprocessing/          # Data preparation scripts
├── models/                 # Training & inference
├── backend/                # FastAPI server
├── frontend/               # React application
├── tests/                  # Unit & integration tests
└── docs/                   # Documentation
```

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- CUDA-capable GPU (for training)

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/Akriti.git
cd Akriti

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

## 📚 Usage

### 1. Data Preparation

```bash
# Create image-annotation mapping
python preprocessing/create_mapping.py

# Parse text annotations to JSON
python preprocessing/text_parser.py

# Convert images to SVG
python preprocessing/image_to_svg.py

# Create training pairs
python preprocessing/create_training_pairs.py
```

### 2. Model Training

```bash
# Fine-tune CodeT5
python models/train_codet5.py --config models/model_config.py

# Monitor with WandB
wandb login
```

### 3. Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to use the application.

## 🔬 Model Performance

- **SVG Validity Rate**: >90%
- **Room Count Accuracy**: >85%
- **Dimension Accuracy**: RMSE <10%
- **Generation Time**: <5 seconds

## 📖 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Dataset: [Source Attribution]
- CodeT5: Salesforce Research
- Icons: [Icon Source]

## 📧 Contact

For questions or collaboration: [your.email@example.com]

---

**Status**: 🚧 In Development (Phase 1: MVP)

