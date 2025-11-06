import os
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import json
import pathlib
from tqdm import tqdm
import pandas as pd
import numpy as np
import argparse
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from transformers import (
    get_linear_schedule_with_warmup,
    BertForSequenceClassification,
    AutoTokenizer
)
from torch.optim import AdamW
from sklearn.metrics import roc_auc_score
from datasets import load_dataset

# ------------------------- Logging -------------------------
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ------------------------- Config -------------------------
@dataclass
class TrainingConfig:
    max_seq_len: int = 64
    epochs: int = 3                    # 3 epochs as requested
    batch_size: int = 32               # fast but reasonable
    learning_rate: float = 3e-5
    patience: int = 1                  # early-stop if val acc doesn't improve
    max_grad_norm: float = 1.0
    warmup_ratio: float = 0.0
    model_path: str = 'prajjwal1/bert-tiny'   # very small, very fast
    num_labels: int = 2
    if_save_model: bool = False        # skip saving for speed
    out_dir: str = './run_fast'

    def validate(self) -> None:
        if self.max_seq_len <= 0:
            raise ValueError("max_seq_len must be positive")
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if not (0.0 < self.learning_rate):
            raise ValueError("learning_rate must be > 0")

# ------------------------- Dataset -------------------------
class DataPrecessForSentence(Dataset):
    """
    Tokenizes sentences with the provided tokenizer.
    If 'similarity' (label) column is missing, produces dummy labels (zeros),
    which are ignored during inference.
    """
    def __init__(self, bert_tokenizer: AutoTokenizer, df: pd.DataFrame, max_seq_len: int = 64):
        self.bert_tokenizer = bert_tokenizer
        self.max_seq_len = max_seq_len

        self.sentences = df['s1'].astype(str).tolist()
        if 'similarity' in df.columns:
            self.labels = df['similarity'].astype(int).tolist()
        else:
            self.labels = [0] * len(self.sentences)  # dummy labels for test split

        enc = self.bert_tokenizer(
            self.sentences,
            padding='max_length',
            truncation=True,
            max_length=self.max_seq_len,
            return_tensors='pt'
        )
        self.input_ids = enc['input_ids']
        self.attention_mask = enc['attention_mask']
        # For single-sentence classification, token_type_ids are valid but all zeros for many models
        self.token_type_ids = enc.get('token_type_ids', torch.zeros_like(self.input_ids))

        self.labels_tensor = torch.tensor(self.labels, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.sentences)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        return (
            self.input_ids[idx],
            self.attention_mask[idx],
            self.token_type_ids[idx],
            self.labels_tensor[idx]
        )

# ------------------------- Model -------------------------
class BertClassifier(nn.Module):
    def __init__(self, model_path: str, num_labels: int, requires_grad: bool = True):
        super().__init__()
        try:
            self.bert = BertForSequenceClassification.from_pretrained(
                model_path,
                num_labels=num_labels
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        except Exception as e:
            logger.error(f"Failed to load BERT model/tokenizer: {e}")
            raise

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        for param in self.bert.parameters():
            param.requires_grad = requires_grad

    def forward(
        self,
        batch_seqs: torch.Tensor,
        batch_seq_masks: torch.Tensor,
        batch_seq_segments: torch.Tensor,
        labels: Optional[torch.Tensor] = None
    ) -> Tuple[Optional[torch.Tensor], torch.Tensor, torch.Tensor]:
        outputs = self.bert(
            input_ids=batch_seqs,
            attention_mask=batch_seq_masks,
            token_type_ids=batch_seq_segments,
            labels=labels
        )
        loss = outputs.loss if labels is not None else None
        logits = outputs.logits
        probabilities = nn.functional.softmax(logits, dim=-1)
        return loss, logits, probabilities

# ------------------------- Trainer -------------------------
class BertTrainer:
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.config.validate()
        self.model = BertClassifier(config.model_path, config.num_labels)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def _prepare_data(
        self,
        train_df: pd.DataFrame,
        dev_df: pd.DataFrame,
        test_df: pd.DataFrame
    ) -> Tuple[DataLoader, DataLoader, DataLoader]:
        train_data = DataPrecessForSentence(
            self.model.tokenizer, train_df, max_seq_len=self.config.max_seq_len
        )
        dev_data = DataPrecessForSentence(
            self.model.tokenizer, dev_df, max_seq_len=self.config.max_seq_len
        )
        test_data = DataPrecessForSentence(
            self.model.tokenizer, test_df, max_seq_len=self.config.max_seq_len
        )
        train_loader = DataLoader(train_data, shuffle=True, batch_size=self.config.batch_size)
        dev_loader   = DataLoader(dev_data,   shuffle=False, batch_size=self.config.batch_size)
        test_loader  = DataLoader(test_data,  shuffle=False, batch_size=self.config.batch_size)
        return train_loader, dev_loader, test_loader

    def _prepare_optimizer(self, num_training_steps: int) -> Tuple[AdamW, Any]:
        no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']
        param_optimizer = list(self.model.named_parameters())
        optimizer_grouped_parameters = [
            {
                'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
                'weight_decay': 0.01
            },
            {
                'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
                'weight_decay': 0.0
            }
        ]
        optimizer = AdamW(optimizer_grouped_parameters, lr=self.config.learning_rate)
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=int(num_training_steps * self.config.warmup_ratio),
            num_training_steps=num_training_steps
        )
        return optimizer, scheduler

    def _initialize_training_stats(self) -> Dict[str, List]:
        return {
            'epochs_count': [],
            'train_losses': [],
            'train_accuracies': [],
            'valid_losses': [],
            'valid_accuracies': [],
            'valid_aucs': []
        }

    def _update_training_stats(
        self,
        training_stats: Dict[str, List],
        epoch: int,
        train_metrics: Dict[str, float],
        val_metrics: Dict[str, float]
    ) -> None:
        training_stats['epochs_count'].append(epoch)
        training_stats['train_losses'].append(train_metrics['loss'])
        training_stats['train_accuracies'].append(train_metrics['accuracy'])
        training_stats['valid_losses'].append(val_metrics['loss'])
        training_stats['valid_accuracies'].append(val_metrics['accuracy'])
        training_stats['valid_aucs'].append(val_metrics['auc'])

        logger.info(
            f"Training - Loss: {train_metrics['loss']:.4f}, Accuracy: {train_metrics['accuracy'] * 100:.2f}%"
        )
        logger.info(
            f"Validation - Loss: {val_metrics['loss']:.4f}, Accuracy: {val_metrics['accuracy'] * 100:.2f}%, AUC: {val_metrics['auc']:.4f}"
        )

    def _save_checkpoint(
        self,
        target_dir: str,
        epoch: int,
        optimizer: AdamW,
        best_score: float,
        training_stats: Dict[str, List]
    ) -> None:
        checkpoint = {
            "epoch": epoch,
            "model": self.model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "best_score": best_score,
            **training_stats
        }
        torch.save(checkpoint, os.path.join(target_dir, "best.pth.tar"))
        logger.info("Model saved successfully")

    def _load_checkpoint(
        self,
        checkpoint_path: str,
        optimizer: AdamW,
        training_stats: Dict[str, List]
    ) -> float:
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        self.model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        for key in training_stats:
            training_stats[key] = checkpoint[key]
        logger.info(f"Loaded checkpoint from epoch {checkpoint['epoch']}")
        return checkpoint["best_score"]

    def _train_epoch(
        self,
        train_loader: DataLoader,
        optimizer: AdamW,
        scheduler: Any
    ) -> Dict[str, float]:
        self.model.train()
        total_loss = 0.0
        correct_preds = 0
        total_examples = 0

        for batch in tqdm(train_loader, desc="Training"):
            batch = tuple(t.to(self.device) for t in batch)
            input_ids, attention_mask, token_type_ids, labels = batch

            optimizer.zero_grad()
            loss, _, probabilities = self.model(input_ids, attention_mask, token_type_ids, labels)

            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()
            preds = probabilities.argmax(dim=1)
            correct_preds += (preds == labels).sum().item()
            total_examples += labels.size(0)

        return {
            'loss': total_loss / max(len(train_loader), 1),
            'accuracy': correct_preds / max(total_examples, 1)
        }

    def _validate_epoch(self, dev_loader: DataLoader) -> Tuple[Dict[str, float], List[float]]:
        self.model.eval()
        total_loss = 0.0
        correct_preds = 0
        total_examples = 0
        all_probs = []
        all_labels = []

        with torch.no_grad():
            for batch in tqdm(dev_loader, desc="Validating"):
                batch = tuple(t.to(self.device) for t in batch)
                input_ids, attention_mask, token_type_ids, labels = batch

                loss, _, probabilities = self.model(input_ids, attention_mask, token_type_ids, labels)

                total_loss += loss.item()
                preds = probabilities.argmax(dim=1)
                correct_preds += (preds == labels).sum().item()
                total_examples += labels.size(0)
                all_probs.extend(probabilities[:, 1].detach().cpu().numpy())
                all_labels.extend(labels.detach().cpu().numpy())

        # AUC can fail if only one class present; guard it.
        try:
            auc = roc_auc_score(all_labels, all_probs)
        except ValueError:
            auc = float('nan')

        metrics = {
            'loss': total_loss / max(len(dev_loader), 1),
            'accuracy': correct_preds / max(total_examples, 1),
            'auc': auc
        }
        return metrics, all_probs

    def _evaluate_test_set(
        self,
        test_loader: DataLoader,
        target_dir: str,
        epoch: int
    ) -> None:
        self.model.eval()
        all_probs = []
        with torch.no_grad():
            for batch in tqdm(test_loader, desc="Testing"):
                batch = tuple(t.to(self.device) for t in batch)
                input_ids, attention_mask, token_type_ids, _ = batch
                _, _, probabilities = self.model(input_ids, attention_mask, token_type_ids, labels=None)
                all_probs.extend(probabilities[:, 1].detach().cpu().numpy())

        test_prediction = pd.DataFrame({'prob_1': all_probs})
        test_prediction['prob_0'] = 1 - test_prediction['prob_1']
        test_prediction['prediction'] = (test_prediction['prob_1'] >= test_prediction['prob_0']).astype(int)

        output_path = os.path.join(target_dir, f"test_prediction_epoch_{epoch}.csv")
        test_prediction.to_csv(output_path, index=False)
        logger.info(f"Test predictions saved to {output_path}")

    def train_and_evaluate(
        self,
        train_df: pd.DataFrame,
        dev_df: pd.DataFrame,
        test_df: pd.DataFrame,
        target_dir: str,
        checkpoint: Optional[str] = None
    ) -> None:
        try:
            os.makedirs(target_dir, exist_ok=True)

            train_loader, dev_loader, test_loader = self._prepare_data(train_df, dev_df, test_df)
            total_training_steps = len(train_loader) * self.config.epochs
            optimizer, scheduler = self._prepare_optimizer(total_training_steps)

            training_stats = self._initialize_training_stats()
            best_score = 0.0
            patience_counter = 0

            if checkpoint:
                best_score = self._load_checkpoint(checkpoint, optimizer, training_stats)

            for epoch in range(1, self.config.epochs + 1):
                logger.info(f"===== Training epoch {epoch}/{self.config.epochs} =====")
                train_metrics = self._train_epoch(train_loader, optimizer, scheduler)
                val_metrics, _ = self._validate_epoch(dev_loader)
                self._update_training_stats(training_stats, epoch, train_metrics, val_metrics)

                if val_metrics['accuracy'] > best_score:
                    best_score = val_metrics['accuracy']
                    patience_counter = 0
                    if self.config.if_save_model:
                        self._save_checkpoint(target_dir, epoch, optimizer, best_score, training_stats)
                    self._evaluate_test_set(test_loader, target_dir, epoch)
                else:
                    patience_counter += 1
                    if patience_counter >= self.config.patience:
                        logger.info("Early stopping triggered")
                        break

            final_infos = {
                "sentiment": {
                    "means": {
                        "best_acc": best_score
                    }
                }
            }
            with open(os.path.join(self.config.out_dir, "final_info.json"), "w") as f:
                json.dump(final_infos, f)

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

# ------------------------- Utils -------------------------
def set_seed(seed: int = 42) -> None:
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)

# ------------------------- Main -------------------------
def main(out_dir):
    try:
        config = TrainingConfig(out_dir=out_dir)
        pathlib.Path(config.out_dir).mkdir(parents=True, exist_ok=True)

        logger.info("Loading GLUE/SST-2 full dataset...")
        dataset = load_dataset("glue", "sst2")

        # Use FULL datasets (no sampling)
        train_df = dataset["train"].to_pandas()[["label", "sentence"]]
        dev_df   = dataset["validation"].to_pandas()[["label", "sentence"]]
        test_df  = dataset["test"].to_pandas()[["sentence"]]

        # Rename to expected columns
        train_df.columns = ["similarity", "s1"]
        dev_df.columns   = ["similarity", "s1"]
        test_df.rename(columns={"sentence": "s1"}, inplace=True)  # no 'similarity' on test

        set_seed(42)

        trainer = BertTrainer(config)
        trainer.train_and_evaluate(train_df, dev_df, test_df, "./output/Bert/")

    except Exception as e:
        logger.error(f"Program failed: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", type=str, default="run_full_sst2")
    args = parser.parse_args()
    main(args.out_dir)
