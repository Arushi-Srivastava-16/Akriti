# Model Training Guide

## Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA GPU with at least 8GB VRAM (recommended: 16GB+)
- **RAM**: 16GB+ system RAM
- **Storage**: 20GB+ free space

### Software Requirements
- Python 3.10+
- CUDA 11.8+ (for GPU training)
- PyTorch 2.0+

## Quick Start

### 1. Prepare Training Data

```bash
# Create mapping between images and annotations
python preprocessing/create_mapping.py

# Parse text annotations to JSON
python preprocessing/text_parser.py

# Convert images to SVG
python preprocessing/image_to_svg.py

# Create training pairs
python preprocessing/create_training_pairs.py
```

This will create:
- `data/training/train.jsonl` (~3200 pairs)
- `data/training/val.jsonl` (~400 pairs)
- `data/training/test.jsonl` (~400 pairs)

### 2. Start Training

**Default Configuration (Recommended):**
```bash
python models/train_codet5.py
```

**Small Config (For Testing):**
```bash
python models/train_codet5.py --config small
```

**Large Config (Better Results):**
```bash
python models/train_codet5.py --config large
```

### 3. Monitor Training

If using WandB (recommended):
```bash
wandb login
# Then start training
python models/train_codet5.py
```

Visit: https://wandb.ai/your-username/akriti-floorplan

## Training Configurations

### Default Config
- Batch size: 8
- Gradient accumulation: 4 (effective batch: 32)
- Epochs: 5
- Learning rate: 5e-5
- Estimated time: 3-5 hours on A100 GPU

### Small Config (Testing)
- Batch size: 2
- Gradient accumulation: 1
- Epochs: 1
- Estimated time: 30 minutes

### Large Config (Best Results)
- Batch size: 16
- Gradient accumulation: 2
- Epochs: 10
- Estimated time: 10-15 hours

## Cloud GPU Options

If you don't have a local GPU:

### 1. **RunPod** (Recommended)
- Cost: ~$0.30/hour for RTX 3090
- Easy setup, Jupyter notebooks
- Visit: https://www.runpod.io/

### 2. **Lambda Labs**
- Cost: ~$0.50/hour for A10
- Great for deep learning
- Visit: https://lambdalabs.com/

### 3. **Google Colab Pro**
- Cost: $10/month
- A100 GPUs available
- Visit: https://colab.research.google.com/

### 4. **Paperspace**
- Cost: ~$0.45/hour for A4000
- Good for prototyping
- Visit: https://www.paperspace.com/

## Expected Results

After training, you should see:

### Metrics
- **SVG Validity Rate**: >90%
- **Room Count Accuracy**: >85%
- **Validation Loss**: <1.0

### Output Files
```
checkpoints/codet5-floorplan-v1/
├── final_model/
│   ├── config.json
│   ├── pytorch_model.bin
│   └── tokenizer/
└── checkpoint-*/  (intermediate checkpoints)
```

## Evaluation

After training, evaluate the model:

```bash
python models/evaluation.py
```

This will generate:
- `models/evaluation_results.json` - Detailed metrics
- Performance comparison against baselines

## Troubleshooting

### Out of Memory (OOM)

**Solution 1: Reduce batch size**
```python
# In models/model_config.py
train_batch_size = 4  # Instead of 8
gradient_accumulation_steps = 8  # Instead of 4
```

**Solution 2: Reduce sequence length**
```python
max_input_length = 256  # Instead of 512
max_output_length = 512  # Instead of 1024
```

**Solution 3: Use fp16 training**
```python
fp16 = True  # Should be default if GPU supports it
```

### Slow Training

- Check GPU utilization: `nvidia-smi`
- Increase `dataloader_num_workers`
- Use smaller validation set
- Reduce `eval_steps` and `save_steps`

### Poor Results

1. **Check data quality:**
   ```bash
   python preprocessing/data_validator.py
   ```

2. **Increase training time:**
   - More epochs (5 → 10)
   - More training data

3. **Adjust hyperparameters:**
   - Lower learning rate (5e-5 → 3e-5)
   - Increase warmup steps (500 → 1000)

## Advanced: Fine-tuning from Checkpoint

To resume training from a checkpoint:

```python
# In train_codet5.py
trainer.train(resume_from_checkpoint="checkpoints/codet5-floorplan-v1/checkpoint-500")
```

## Next Steps

After training:

1. **Test Inference:**
   ```bash
   python models/inference.py
   ```

2. **Start Backend API:**
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

3. **Test End-to-End:**
   - Start backend
   - Start frontend
   - Generate floor plans!

