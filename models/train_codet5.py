"""
Train CodeT5 Model for Floor Plan Generation.

Fine-tunes CodeT5 to generate SVG floor plans from JSON descriptions.

Usage:
    python models/train_codet5.py
    python models/train_codet5.py --config small  # For testing
    python models/train_codet5.py --config large  # For better results
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback
)
from datasets import load_dataset
import wandb
from tqdm import tqdm

from model_config import default_config, small_config, large_config


class FloorPlanDataset(Dataset):
    """Dataset for floor plan JSON → SVG pairs."""
    
    def __init__(self, file_path: str, tokenizer, max_input_length: int, max_output_length: int):
        """
        Load dataset from JSONL file.
        
        Args:
            file_path: Path to .jsonl file
            tokenizer: Tokenizer for encoding
            max_input_length: Max tokens for input (JSON)
            max_output_length: Max tokens for output (SVG)
        """
        self.tokenizer = tokenizer
        self.max_input_length = max_input_length
        self.max_output_length = max_output_length
        
        # Load data
        self.examples = []
        with open(file_path) as f:
            for line in f:
                self.examples.append(json.loads(line))
        
        print(f"Loaded {len(self.examples)} examples from {file_path}")
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Tokenize input (JSON)
        input_text = example["input"]
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_input_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        # Tokenize output (SVG)
        output_text = example["output"]
        output_encoding = self.tokenizer(
            output_text,
            max_length=self.max_output_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": input_encoding["input_ids"].squeeze(),
            "attention_mask": input_encoding["attention_mask"].squeeze(),
            "labels": output_encoding["input_ids"].squeeze()
        }


def setup_training(config):
    """Setup model, tokenizer, and datasets."""
    
    print(f"🚀 Setting up training with config: {config.wandb_run_name}")
    
    # Set seed for reproducibility
    torch.manual_seed(config.seed)
    
    # Load tokenizer and model
    print(f"📦 Loading model: {config.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(config.model_name)
    
    print(f"   Model parameters: {model.num_parameters():,}")
    
    # Load datasets
    BASE_DIR = Path(__file__).parent.parent
    
    print("📚 Loading datasets...")
    train_dataset = FloorPlanDataset(
        BASE_DIR / config.train_file,
        tokenizer,
        config.max_input_length,
        config.max_output_length
    )
    
    val_dataset = FloorPlanDataset(
        BASE_DIR / config.val_file,
        tokenizer,
        config.max_input_length,
        config.max_output_length
    )
    
    return model, tokenizer, train_dataset, val_dataset


def train(config):
    """Main training function."""
    
    # Setup
    model, tokenizer, train_dataset, val_dataset = setup_training(config)
    
    # Initialize WandB
    if config.use_wandb:
        wandb.init(
            project=config.wandb_project,
            name=config.wandb_run_name,
            config=vars(config)
        )
    
    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.train_batch_size,
        per_device_eval_batch_size=config.eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        weight_decay=config.weight_decay,
        warmup_steps=config.warmup_steps,
        logging_dir=config.logging_dir,
        logging_steps=config.logging_steps,
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        evaluation_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=config.fp16 and torch.cuda.is_available(),
        dataloader_num_workers=config.dataloader_num_workers,
        report_to="wandb" if config.use_wandb else "none",
        save_total_limit=3,  # Keep only 3 best checkpoints
        predict_with_generate=True,
        generation_max_length=config.max_output_length,
        generation_num_beams=config.num_beams,
    )
    
    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True
    )
    
    # Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)]
    )
    
    # Train
    print("\n🎯 Starting training...\n")
    trainer.train()
    
    # Save final model
    final_model_dir = Path(config.output_dir) / "final_model"
    final_model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving final model to {final_model_dir}")
    trainer.save_model(final_model_dir)
    tokenizer.save_pretrained(final_model_dir)
    
    # Evaluate on validation set
    print("\n📊 Final evaluation on validation set...")
    eval_results = trainer.evaluate()
    
    print("\n" + "="*60)
    print("📊 TRAINING COMPLETE")
    print("="*60)
    for key, value in eval_results.items():
        print(f"   {key}: {value:.4f}")
    print(f"\n📁 Model saved to: {final_model_dir}")
    print("="*60)
    
    if config.use_wandb:
        wandb.finish()
    
    return trainer, eval_results


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(description="Train CodeT5 for floor plan generation")
    parser.add_argument(
        "--config",
        type=str,
        default="default",
        choices=["default", "small", "large"],
        help="Configuration preset to use"
    )
    parser.add_argument(
        "--no-wandb",
        action="store_true",
        help="Disable Weights & Biases logging"
    )
    
    args = parser.parse_args()
    
    # Select config
    if args.config == "small":
        config = small_config
    elif args.config == "large":
        config = large_config
    else:
        config = default_config
    
    if args.no_wandb:
        config.use_wandb = False
    
    # Check GPU
    if torch.cuda.is_available():
        print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("⚠️  No GPU detected. Training will be slow.")
        print("   Consider using a GPU instance (RunPod, Lambda Labs, Colab Pro)")
        config.fp16 = False
    
    # Train
    train(config)


if __name__ == "__main__":
    main()

