import os
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import time
import json
import pathlib
from tqdm import tqdm
import pandas as pd
import numpy as np
import argparse
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
import math
from transformers import (
    get_linear_schedule_with_warmup,
    BertForSequenceClassification,
    AutoTokenizer
)
from transformers.models.bert.modeling_bert import BertSelfAttention, BertConfig
from torch.optim import AdamW
from sklearn.metrics import roc_auc_score
from datasets import load_dataset

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    max_seq_len: int = 32      # smaller sequence length
    epochs: int = 1            # only 1 epoch
    batch_size: int = 8        # smaller batch size
    learning_rate: float = 3e-5
    patience: int = 1
    max_grad_norm: float = 1.0
    warmup_ratio: float = 0.0
    model_path: str = 'prajjwal1/bert-tiny'   # <<< much smaller model
    num_labels: int = 2
    if_save_model: bool = False              # disable saving to speed up
    out_dir: str = './run_fast'


    def validate(self) -> None:
        if self.max_seq_len <= 0:
            raise ValueError("max_seq_len must be positive")
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if not (0.0 < self.learning_rate):
            raise ValueError("learning_rate must be between 0 and 1")


class DataPrecessForSentence(Dataset):
    def __init__(self, bert_tokenizer: AutoTokenizer, df: pd.DataFrame, max_seq_len: int = 50):
        self.bert_tokenizer = bert_tokenizer
        self.max_seq_len = max_seq_len
        self.input_ids, self.attention_mask, self.token_type_ids, self.labels = self._get_input(df)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        return (
            self.input_ids[idx],
            self.attention_mask[idx],
            self.token_type_ids[idx],
            self.labels[idx]
        )

    def _get_input(self, df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        sentences = df['s1'].values
        labels = df['similarity'].values

        tokens_seq = list(map(self.bert_tokenizer.tokenize, sentences))
        result = list(map(self._truncate_and_pad, tokens_seq))

        input_ids = torch.tensor([i[0] for i in result], dtype=torch.long)
        attention_mask = torch.tensor([i[1] for i in result], dtype=torch.long)
        token_type_ids = torch.tensor([i[2] for i in result], dtype=torch.long)
        labels = torch.tensor(labels, dtype=torch.long)

        return input_ids, attention_mask, token_type_ids, labels

    def _truncate_and_pad(self, tokens_seq: List[str]) -> Tuple[List[int], List[int], List[int]]:
        tokens_seq = ['[CLS]'] + tokens_seq[:self.max_seq_len - 1]
        padding_length = self.max_seq_len - len(tokens_seq)

        input_ids = self.bert_tokenizer.convert_tokens_to_ids(tokens_seq)
        input_ids += [0] * padding_length
        attention_mask = [1] * len(tokens_seq) + [0] * padding_length
        token_type_ids = [0] * self.max_seq_len

        return input_ids, attention_mask, token_type_ids


class SemanticGatingModule(nn.Module):
    """
    A small, learnable 'similarity module' that takes token embeddings (as query/key layers)
    and outputs a similarity score for each query-key pair.
    """
    def __init__(self, config: BertConfig):
        super().__init__()
        self.num_attention_heads = config.num_attention_heads
        self.hidden_size = config.hidden_size
        self.attention_head_size = self.hidden_size // self.num_attention_heads
        
        # Learnable linear layers to project query and key for semantic gating
        self.query_g = nn.Linear(config.hidden_size, config.hidden_size)
        self.key_g = nn.Linear(config.hidden_size, config.hidden_size)
        
        # Scaling factor for the gating scores, similar to standard attention
        self.scale_factor = 1.0 / (self.attention_head_size ** 0.5)

    def forward(self, query_layer: torch.Tensor, key_layer: torch.Tensor) -> torch.Tensor:
        # query_layer, key_layer shapes: (batch_size, num_heads, seq_len, head_dim)
        batch_size, num_heads, seq_len, head_dim = query_layer.shape
        
        # Reshape to (batch_size, seq_len, hidden_size) for linear layers
        query_layer_flat = query_layer.permute(0, 2, 1, 3).reshape(batch_size, seq_len, self.hidden_size)
        key_layer_flat = key_layer.permute(0, 2, 1, 3).reshape(batch_size, seq_len, self.hidden_size)

        # Apply linear layers
        query_g_proj = self.query_g(query_layer_flat) # (batch_size, seq_len, hidden_size)
        key_g_proj = self.key_g(key_layer_flat)       # (batch_size, seq_len, hidden_size)
        
        # Reshape back to (batch_size, num_heads, seq_len, head_dim) for dot product
        query_g_proj = query_g_proj.reshape(batch_size, seq_len, num_heads, head_dim).permute(0, 2, 1, 3)
        key_g_proj = key_g_proj.reshape(batch_size, seq_len, num_heads, head_dim).permute(0, 2, 1, 3)

        # Compute semantic gating scores using dot product
        # (B, N_h, S, H_d) @ (B, N_h, H_d, S) -> (B, N_h, S, S)
        gating_scores = torch.matmul(query_g_proj, key_g_proj.transpose(-1, -2))
        
        # Scale the gating scores and apply sigmoid for gating factors between 0 and 1
        gating_scores = torch.sigmoid(gating_scores * self.scale_factor)

        return gating_scores


class GatedBertSelfAttention(BertSelfAttention):
    """
    Custom BertSelfAttention layer that incorporates a SemanticGatingModule
    to gate attention weights before softmax.
    """
    def __init__(self, config: BertConfig):
        super().__init__(config)
        self.semantic_gating_module = SemanticGatingModule(config)

    def _transpose_for_scores(self, x: torch.Tensor) -> torch.Tensor:
        """
        Transposes a tensor from (batch_size, seq_len, hidden_size) to (batch_size, num_heads, seq_len, head_dim)
        """
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.FloatTensor] = None,
        head_mask: Optional[torch.FloatTensor] = None,
        encoder_hidden_states: Optional[torch.FloatTensor] = None,
        encoder_attention_mask: Optional[torch.FloatTensor] = None,
        past_key_values: Optional[Tuple[Tuple[torch.FloatTensor]]] = None,
        output_attentions: Optional[bool] = False,
        cache_position: Optional[torch.LongTensor] = None,
        **kwargs, # Add **kwargs to absorb any additional arguments
    ) -> Tuple[torch.Tensor]:
        mixed_query_layer = self.query(hidden_states)

        is_cross_attention = encoder_hidden_states is not None

        if is_cross_attention and past_key_values is not None:
            key_layer = past_key_values[0]
            value_layer = past_key_values[1]
            attention_mask = encoder_attention_mask
        elif is_cross_attention:
            key_layer = self._transpose_for_scores(self.key(encoder_hidden_states))
            value_layer = self._transpose_for_scores(self.value(encoder_hidden_states))
            attention_mask = encoder_attention_mask
        elif past_key_values is not None:
            key_layer = self._transpose_for_scores(self.key(hidden_states))
            value_layer = self._transpose_for_scores(self.value(hidden_states))
            key_layer = torch.cat([past_key_values[0], key_layer], dim=2)
            value_layer = torch.cat([past_key_values[1], value_layer], dim=2)
        else:
            key_layer = self._transpose_for_scores(self.key(hidden_states))
            value_layer = self._transpose_for_scores(self.value(hidden_states))

        query_layer = self._transpose_for_scores(mixed_query_layer)

        if self.is_decoder:
            if is_cross_attention and past_key_values is not None:
                past_key_values = (key_layer, value_layer)
            elif not is_cross_attention and past_key_values is not None:
                past_key_values = (key_layer, value_layer)

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))

        # --- Semantic Gating: apply gating scores before standard scaling and softmax ---
        gating_scores = self.semantic_gating_module(query_layer, key_layer)
        attention_scores = attention_scores + gating_scores # Change to additive gating
        # --------------------------------------------------------------------------------

        attention_scores = attention_scores / math.sqrt(self.attention_head_size)

        if attention_mask is not None:
            attention_scores = attention_scores + attention_mask

        # Normalize the attention scores to probabilities.
        attention_probs = nn.functional.softmax(attention_scores, dim=-1)

        attention_probs = self.dropout(attention_probs)

        if head_mask is not None:
            attention_probs = attention_probs * head_mask

        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(new_context_layer_shape)

        outputs = (context_layer, attention_probs) if output_attentions else (context_layer,)

        if self.is_decoder:
            outputs = outputs + (past_key_values,)
        return outputs


class BertClassifier(nn.Module):
    def __init__(self, model_path: str, num_labels: int, requires_grad: bool = True):
        super().__init__()
        try:
            self.bert = BertForSequenceClassification.from_pretrained(
                model_path,
                num_labels=num_labels
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            raise

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        for param in self.bert.parameters():
            param.requires_grad = requires_grad
            
        # --- Inject GatedBertSelfAttention into the BERT model ---
        bert_config = self.bert.bert.config
        for i, layer_module in enumerate(self.bert.bert.encoder.layer):
            original_self_attention = layer_module.attention.self
            gated_self_attention = GatedBertSelfAttention(bert_config)
            
            # Load state_dict to preserve pre-trained weights for the common parts
            gated_self_attention.load_state_dict(original_self_attention.state_dict(), strict=False)
            
            layer_module.attention.self = gated_self_attention
            logger.info(f"Replaced BertSelfAttention in layer {i} with GatedBertSelfAttention.")
        # --- End Injection ---

    def forward(
            self,
            batch_seqs: torch.Tensor,
            batch_seq_masks: torch.Tensor,
            batch_seq_segments: torch.Tensor,
            labels: Optional[torch.Tensor] = None
    ) -> Tuple[Optional[torch.Tensor], torch.Tensor, torch.Tensor]:

        # Get the full model output
        outputs = self.bert(
            input_ids=batch_seqs,
            attention_mask=batch_seq_masks,
            token_type_ids=batch_seq_segments,
            labels=labels
        )

        # Check if we are in training/validation or inference mode
        if labels is not None:
            # Labels were provided, so loss is computed
            loss = outputs.loss
            logits = outputs.logits
        else:
            # Labels were not provided (inference), so no loss
            loss = None
            logits = outputs.logits

        probabilities = nn.functional.softmax(logits, dim=-1)

        # Return loss (which can be None), logits, and probabilities
        return loss, logits, probabilities


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
            self.model.tokenizer,
            train_df,
            max_seq_len=self.config.max_seq_len
        )
        train_loader = DataLoader(
            train_data,
            shuffle=True,
            batch_size=self.config.batch_size
        )

        dev_data = DataPrecessForSentence(
            self.model.tokenizer,
            dev_df,
            max_seq_len=self.config.max_seq_len
        )
        dev_loader = DataLoader(
            dev_data,
            shuffle=False,
            batch_size=self.config.batch_size
        )

        test_data = DataPrecessForSentence(
            self.model.tokenizer,
            test_df,
            max_seq_len=self.config.max_seq_len
        )
        test_loader = DataLoader(
            test_data,
            shuffle=False,
            batch_size=self.config.batch_size
        )

        return train_loader, dev_loader, test_loader

    def _prepare_optimizer(self, num_training_steps: int) -> Tuple[AdamW, Any]:
        param_optimizer = list(self.model.named_parameters())
        no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']
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

        optimizer = AdamW(
            optimizer_grouped_parameters,
            lr=self.config.learning_rate
        )

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
            f"Training - Loss: {train_metrics['loss']:.4f}, "
            f"Accuracy: {train_metrics['accuracy'] * 100:.2f}%"
        )
        logger.info(
            f"Validation - Loss: {val_metrics['loss']:.4f}, "
            f"Accuracy: {val_metrics['accuracy'] * 100:.2f}%, "
            f"AUC: {val_metrics['auc']:.4f}"
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
        torch.save(
            checkpoint,
            os.path.join(target_dir, "best.pth.tar")
        )
        logger.info("Model saved successfully")

    def _load_checkpoint(
            self,
            checkpoint_path: str,
            optimizer: AdamW,
            training_stats: Dict[str, List]
    ) -> float:
        checkpoint = torch.load(checkpoint_path)
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
        total_loss = 0
        correct_preds = 0

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
            correct_preds += (probabilities.argmax(dim=1) == labels).sum().item()

        return {
            'loss': total_loss / len(train_loader),
            'accuracy': correct_preds / len(train_loader.dataset)
        }

    def _validate_epoch(self, dev_loader: DataLoader) -> Tuple[Dict[str, float], List[float]]:
        self.model.eval()
        total_loss = 0
        correct_preds = 0
        all_probs = []
        all_labels = []

        with torch.no_grad():
            for batch in tqdm(dev_loader, desc="Validating"):
                batch = tuple(t.to(self.device) for t in batch)
                input_ids, attention_mask, token_type_ids, labels = batch

                loss, _, probabilities = self.model(input_ids, attention_mask, token_type_ids, labels)

                total_loss += loss.item()
                correct_preds += (probabilities.argmax(dim=1) == labels).sum().item()
                all_probs.extend(probabilities[:, 1].cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        metrics = {
            'loss': total_loss / len(dev_loader),
            'accuracy': correct_preds / len(dev_loader.dataset),
            'auc': roc_auc_score(all_labels, all_probs)
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
                # dummy labels removed
                _, _, probabilities = self.model(input_ids, attention_mask, token_type_ids, labels=None)
                all_probs.extend(probabilities[:, 1].cpu().numpy())

        # generate predictions only
        test_prediction = pd.DataFrame({'prob_1': all_probs})
        test_prediction['prob_0'] = 1 - test_prediction['prob_1']
        test_prediction['prediction'] = test_prediction.apply(
            lambda x: 0 if x['prob_0'] > x['prob_1'] else 1,
            axis=1
        )

        output_path = os.path.join(target_dir, f"test_prediction_epoch_{epoch}.csv")
        test_prediction.to_csv(output_path, index=False)
        logger.info(f"Test predictions saved to {output_path}")

        test_prediction = pd.DataFrame({'prob_1': all_probs})
        test_prediction['prob_0'] = 1 - test_prediction['prob_1']
        test_prediction['prediction'] = test_prediction.apply(
            lambda x: 0 if (x['prob_0'] > x['prob_1']) else 1,
            axis=1
        )

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

            train_loader, dev_loader, test_loader = self._prepare_data(
                train_df, dev_df, test_df
            )

            optimizer, scheduler = self._prepare_optimizer(
                len(train_loader) * self.config.epochs
            )

            training_stats = self._initialize_training_stats()
            best_score = 0.0
            patience_counter = 0

            if checkpoint:
                best_score = self._load_checkpoint(checkpoint, optimizer, training_stats)

            for epoch in range(1, self.config.epochs + 1):
                logger.info(f"Training epoch {epoch}")

                # Train
                train_metrics = self._train_epoch(train_loader, optimizer, scheduler)

                # Val
                val_metrics, _ = self._validate_epoch(dev_loader)

                self._update_training_stats(training_stats, epoch, train_metrics, val_metrics)

                # Saving / Early stopping
                if val_metrics['accuracy'] > best_score:
                    best_score = val_metrics['accuracy']
                    patience_counter = 0
                    if self.config.if_save_model:
                        self._save_checkpoint(
                            target_dir,
                            epoch,
                            optimizer,
                            best_score,
                            training_stats
                        )
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


def set_seed(seed: int = 42) -> None:
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)


def main(out_dir):
    try:
        config = TrainingConfig(out_dir=out_dir)
        pathlib.Path(config.out_dir).mkdir(parents=True, exist_ok=True)

        logger.info("Loading small sample of dataset...")
        dataset = load_dataset("glue", "sst2")

        # Take only 200 samples from train, 100 from val, 100 from test
        train_df = dataset["train"].to_pandas().sample(200, random_state=42)[["label", "sentence"]]
        dev_df = dataset["validation"].to_pandas().sample(100, random_state=42)[["label", "sentence"]]
        test_df = dataset["test"].to_pandas().sample(100, random_state=42)[["label", "sentence"]]

        train_df.columns = ["similarity", "s1"]
        dev_df.columns = ["similarity", "s1"]
        test_df.columns = ["similarity", "s1"]

        set_seed(42)

        trainer = BertTrainer(config)
        trainer.train_and_evaluate(train_df, dev_df, test_df, "./output/Bert/")

    except Exception as e:
        logger.error(f"Program failed: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", type=str, default="run_0")
    args = parser.parse_args()
    main(args.out_dir)
