# Quick Start Guide

Get Akriti up and running in minutes!

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher (for frontend)
- 20GB+ free disk space
- (Optional) NVIDIA GPU for model training

## 🚀 Quick Setup

### 1. Clone and Setup

```bash
# Navigate to the project
cd /Users/arushisrivastava/Documents/GitHub/Akriti

# Run setup script
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh

# Or manual setup:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Prepare Data

You have 80k images and 4k annotations. Let's process the annotated ones:

```bash
# Step 1: Create mapping (which images have annotations)
python preprocessing/create_mapping.py

# Step 2: Parse text annotations to structured JSON
python preprocessing/text_parser.py

# Step 3: Convert images to SVG (this may take a while)
python preprocessing/image_to_svg.py

# Step 4: Create training pairs for the model
python preprocessing/create_training_pairs.py
```

Expected output:
- ~4000 JSON files in `data/processed/json/`
- ~4000 SVG files in `data/processed/svg/`
- Training data in `data/training/` (train/val/test splits)

### 3. Start Backend (Without Training First)

You can start the backend even before training the model. It will use a placeholder SVG generator:

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

Open: http://localhost:8000/docs

### 4. Start Frontend

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

### 5. Test the System

1. Go to http://localhost:5173
2. Click "Load Example" or enter your own description
3. Click "Generate Floor Plan"
4. See your floor plan appear!
5. Export as PNG/PDF

## 🧠 Model Training (Optional but Recommended)

To get better results, train the CodeT5 model:

### Option A: Local GPU

```bash
python models/train_codet5.py
```

**Requirements:**
- NVIDIA GPU with 8GB+ VRAM
- 3-5 hours training time

### Option B: Cloud GPU (Recommended)

1. **Rent GPU on RunPod/Lambda Labs**
   - RunPod: https://www.runpod.io/ (~$0.30/hour)
   - Lambda Labs: https://lambdalabs.com/ (~$0.50/hour)

2. **Upload code and data**
   ```bash
   # Create a zip of necessary files
   zip -r akriti.zip . -x "data/raw/*" "frontend/node_modules/*" ".git/*"
   ```

3. **Train on cloud**
   ```bash
   # On the cloud machine
   unzip akriti.zip
   pip install -r requirements.txt
   python models/train_codet5.py
   ```

4. **Download trained model**
   ```bash
   # Download checkpoints/codet5-floorplan-v1/final_model/
   # Place in your local checkpoints/ folder
   ```

### Verify Training

After training:
```bash
# Test inference
python models/inference.py

# Evaluate on test set
python models/evaluation.py
```

## 📊 Data Pipeline Overview

```
Raw Data (80k images + 4k annotations)
           ↓
create_mapping.py  → Creates mapping (4k pairs)
           ↓
text_parser.py     → Parses text to JSON (4k files)
           ↓
image_to_svg.py    → Converts images to SVG (4k files)
           ↓
create_training_pairs.py → Creates train/val/test splits
           ↓
Training Data Ready! (train.jsonl, val.jsonl, test.jsonl)
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
python -m uvicorn backend.main:app --port 8001
```

### Frontend won't start
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Data processing fails
```bash
# Check data exists
ls data/raw/images/ | wc -l    # Should show ~80k
ls data/raw/annotations/ | wc -l  # Should show ~4k

# Run validation
python preprocessing/data_validator.py
```

### Out of memory during training
- Use smaller config: `python models/train_codet5.py --config small`
- Reduce batch size in `models/model_config.py`
- Use cloud GPU with more memory

## 📚 Next Steps

1. **Read the full documentation:**
   - Architecture: `docs/architecture.md`
   - API Reference: `docs/api_reference.md`
   - Training Guide: `docs/training_guide.md`

2. **Customize the system:**
   - Modify parser rules in `preprocessing/text_parser.py`
   - Adjust model hyperparameters in `models/model_config.py`
   - Customize UI in `frontend/src/components/`

3. **Contribute:**
   - Report issues
   - Add features
   - Improve documentation

## 🎯 Success Checklist

- [ ] Data mapping created (4k pairs)
- [ ] Text parsed to JSON (4k files)
- [ ] Images converted to SVG (4k files)
- [ ] Training data split (80/10/10)
- [ ] Backend API running (http://localhost:8000)
- [ ] Frontend running (http://localhost:5173)
- [ ] Can generate floor plans from text
- [ ] Can export floor plans as PNG
- [ ] (Optional) Model trained and loaded
- [ ] (Optional) Evaluation metrics >85% accuracy

## 💡 Tips

- Start with the placeholder generator (no training needed)
- Train the model later for better results
- Use cloud GPUs for faster training
- Monitor training with WandB
- Test with the example descriptions first
- Customize the UI colors/layout to your preference

## 📞 Need Help?

- Check `docs/` folder for detailed guides
- Review example data in `data/raw/`
- Look at test files in `tests/`
- Examine training logs in `logs/`

---

**Ready to build amazing floor plans? Let's go! 🚀**

