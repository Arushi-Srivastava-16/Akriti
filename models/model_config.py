"""
Model Configuration for CodeT5 Fine-tuning.

Hyperparameters and settings for training.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelConfig:
    """Configuration for model training."""
    
    # Model
    model_name: str = "Salesforce/codet5-base"  # Pre-trained CodeT5
    
    # Training data
    train_file: str = "data/training/train.jsonl"
    val_file: str = "data/training/val.jsonl"
    test_file: str = "data/training/test.jsonl"
    
    # Tokenization
    max_input_length: int = 512   # Max length for JSON input
    max_output_length: int = 1024  # Max length for SVG output
    
    # Training hyperparameters
    learning_rate: float = 5e-5
    train_batch_size: int = 8
    eval_batch_size: int = 8
    gradient_accumulation_steps: int = 4  # Effective batch size = 8 * 4 = 32
    num_epochs: int = 5
    warmup_steps: int = 500
    weight_decay: float = 0.01
    
    # Optimization
    adam_epsilon: float = 1e-8
    max_grad_norm: float = 1.0
    
    # Scheduler
    lr_scheduler_type: str = "linear"
    
    # Evaluation
    eval_steps: int = 100  # Evaluate every N steps
    save_steps: int = 500  # Save checkpoint every N steps
    logging_steps: int = 50
    
    # Early stopping
    early_stopping_patience: int = 3  # Stop if no improvement for N evaluations
    
    # Output
    output_dir: str = "checkpoints/codet5-floorplan-v1"
    logging_dir: str = "logs/codet5-floorplan-v1"
    
    # Hardware
    fp16: bool = True  # Use mixed precision (if GPU supports it)
    dataloader_num_workers: int = 4
    
    # Reproducibility
    seed: int = 42
    
    # WandB (experiment tracking)
    use_wandb: bool = True
    wandb_project: str = "akriti-floorplan"
    wandb_run_name: str = "codet5-base-v1"
    
    # Generation (for validation)
    num_beams: int = 5  # Beam search
    temperature: float = 1.0
    top_p: float = 0.95
    
    def __post_init__(self):
        """Create output directories."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logging_dir).mkdir(parents=True, exist_ok=True)


# Default config
default_config = ModelConfig()


# Small config (for testing/debugging)
small_config = ModelConfig(
    train_batch_size=2,
    eval_batch_size=2,
    gradient_accumulation_steps=1,
    num_epochs=1,
    eval_steps=10,
    save_steps=20,
    logging_steps=5,
    output_dir="checkpoints/codet5-floorplan-small",
    wandb_run_name="codet5-small-test"
)


# Large config (if you have more compute)
large_config = ModelConfig(
    train_batch_size=16,
    eval_batch_size=16,
    gradient_accumulation_steps=2,  # Effective batch size = 32
    num_epochs=10,
    max_input_length=768,
    max_output_length=1536,
    output_dir="checkpoints/codet5-floorplan-large",
    wandb_run_name="codet5-large-v1"
)

