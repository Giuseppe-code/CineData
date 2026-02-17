#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fine-tuning BERT su Lowerated/imdb-reviews-rated (7 regressioni) SENZA Trainer (no accelerate).
Pensato per GPU con poca VRAM: batch piccolo + gradient accumulation.

Esempio (safe per shard ~2.8GB):
python finetune_lowerated_bert_pytorch.py \
  --output_dir ./out_bert_lowerated \
  --epochs 2 --max_length 128 --batch_size 2 --grad_accum 4 --fp16
"""

import argparse
import json
import math
import os
import random
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification


LABEL_ORDER = [
    "direction",
    "cinematography",
    "unique_concept",
    "story",
    "emotions",
    "characters",
    "production_design",
]


def set_all_seeds(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def pick_existing_column(columns: List[str], candidates: List[str]) -> str:
    for c in candidates:
        if c in columns:
            return c
    raise ValueError(f"Nessuna colonna trovata tra: {candidates}. Colonne disponibili: {columns}")


def resolve_columns(columns: List[str]) -> Tuple[str, Dict[str, str]]:
    # testo
    text_col = pick_existing_column(columns, ["review", "Review", "text", "Text", "sentence", "Sentence"])

    # aspetti (gestisce nomi leggermente diversi)
    mapping = {
        "direction": pick_existing_column(columns, ["Direction", "direction"]),
        "cinematography": pick_existing_column(columns, ["Cinematography", "cinematography"]),
        "unique_concept": pick_existing_column(columns, ["Unique Concept", "Unique Concepts", "unique_concept"]),
        "story": pick_existing_column(columns, ["Story", "story"]),
        "emotions": pick_existing_column(columns, ["Emotions", "emotions"]),
        "characters": pick_existing_column(columns, ["Characters", "characters"]),
        "production_design": pick_existing_column(columns, ["Production Design", "ProductionDesign", "production_design"]),
    }
    return text_col, mapping


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_name", type=str, default="Lowerated/imdb-reviews-rated")
    ap.add_argument("--model_name", type=str, default="bert-base-uncased")
    ap.add_argument("--output_dir", type=str, required=True)

    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val_size", type=float, default=0.05)

    ap.add_argument("--max_length", type=int, default=128)
    ap.add_argument("--batch_size", type=int, default=2)
    ap.add_argument("--grad_accum", type=int, default=4)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--weight_decay", type=float, default=0.01)

    ap.add_argument("--fp16", action="store_true")
    ap.add_argument("--num_workers", type=int, default=0)

    # quick check
    ap.add_argument("--max_train_samples", type=int, default=0)
    ap.add_argument("--max_eval_samples", type=int, default=0)

    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    set_all_seeds(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))

    # 1) Load dataset
    ds = load_dataset(args.dataset_name)
    if "train" not in ds:
        raise ValueError(f"Split 'train' non trovato. Split disponibili: {list(ds.keys())}")
    full = ds["train"]

    # rimuove eventuali "Unnamed: ..."
    drop_cols = [c for c in full.column_names if c.lower().startswith("unnamed")]
    if drop_cols:
        full = full.remove_columns(drop_cols)

    text_col, aspect_cols = resolve_columns(full.column_names)

    # 2) Tokenizer + labels
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)

    def add_labels(example):
        labels = []
        for k in LABEL_ORDER:
            col = aspect_cols[k]
            v = example.get(col, 0.0)
            labels.append(float(v) if v is not None else 0.0)
        example["labels"] = labels
        return example

    def tokenize_fn(batch):
        return tokenizer(
            batch[text_col],
            truncation=True,
            max_length=args.max_length,
        )

    full = full.map(add_labels, desc="Costruzione labels")
    full = full.map(tokenize_fn, batched=True, desc="Tokenizzazione")

    # 3) Split train/val
    split = full.train_test_split(test_size=args.val_size, seed=args.seed)
    train_ds = split["train"]
    eval_ds = split["test"]

    if args.max_train_samples and args.max_train_samples > 0:
        train_ds = train_ds.select(range(min(args.max_train_samples, len(train_ds))))
    if args.max_eval_samples and args.max_eval_samples > 0:
        eval_ds = eval_ds.select(range(min(args.max_eval_samples, len(eval_ds))))

    # 4) Collate (padding dinamico) + DataLoader
    def collate_fn(features):
        # separa labels
        labels = torch.stack([torch.tensor(f["labels"], dtype=torch.float32) for f in features])

        # togli labels prima del pad
        feats_wo_labels = []
        for f in features:
            feats_wo_labels.append({k: f[k] for k in f.keys() if k in ("input_ids", "attention_mask", "token_type_ids")})

        batch = tokenizer.pad(feats_wo_labels, padding=True, return_tensors="pt")
        batch["labels"] = labels
        return batch

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_fn,
        pin_memory=torch.cuda.is_available(),
    )
    eval_loader = DataLoader(
        eval_ds,
        batch_size=max(1, args.batch_size),
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_fn,
        pin_memory=torch.cuda.is_available(),
    )

    # 5) Model (regression multi-output)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(LABEL_ORDER),
        problem_type="regression",
    )
    model.to(device)

    # 6) Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    # fp16 (optional)
    use_fp16 = bool(args.fp16 and torch.cuda.is_available())
    scaler = torch.cuda.amp.GradScaler(enabled=use_fp16)

    # Utility eval
    def evaluate():
        model.eval()
        mse_sum = 0.0
        mae_sum = 0.0
        n = 0

        with torch.no_grad():
            for batch in eval_loader:
                for k in batch:
                    batch[k] = batch[k].to(device)

                with torch.cuda.amp.autocast(enabled=use_fp16):
                    out = model(**batch)
                    preds = out.logits.detach().float()
                    labels = batch["labels"].detach().float()

                diff = preds - labels
                mse_sum += float((diff * diff).mean().item())
                mae_sum += float(diff.abs().mean().item())
                n += 1

        # medie per-batch
        mse = mse_sum / max(1, n)
        mae = mae_sum / max(1, n)
        return mse, mae

    # 7) Training loop
    print("\nStarting training...")
    global_step = 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)

        running_loss = 0.0
        steps_in_epoch = 0

        for step, batch in enumerate(train_loader, start=1):
            for k in batch:
                batch[k] = batch[k].to(device)

            with torch.cuda.amp.autocast(enabled=use_fp16):
                out = model(**batch)
                loss = out.loss
                loss = loss / max(1, args.grad_accum)

            scaler.scale(loss).backward()
            running_loss += float(loss.item())
            steps_in_epoch += 1

            if step % args.grad_accum == 0:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1

                if global_step % 50 == 0:
                    print(f"Epoch {epoch} | opt_step {global_step} | loss(avg/accum) ~ {running_loss/steps_in_epoch:.4f}")

        # flush grad se restano accumulati
        if steps_in_epoch % args.grad_accum != 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            global_step += 1

        mse, mae = evaluate()
        print(f"\n[Epoch {epoch} DONE] val_mse={mse:.6f} val_mae={mae:.6f}")

        if torch.cuda.is_available():
            max_mem = torch.cuda.max_memory_allocated() / (1024 ** 2)
            print(f"GPU max_memory_allocated: {max_mem:.1f} MiB")
            torch.cuda.reset_peak_memory_stats()

    # 8) Save model + tokenizer + metadata
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    meta = {
        "label_order": LABEL_ORDER,
        "text_column": text_col,
        "aspect_columns": aspect_cols,
        "model_name": args.model_name,
        "dataset_name": args.dataset_name,
        "max_length": args.max_length,
    }
    with open(os.path.join(args.output_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # 9) Mini test inferenza
    model.eval()
    sample_text = "Great acting and characters, but the story was weak and direction felt messy."
    inputs = tokenizer(sample_text, return_tensors="pt", truncation=True, max_length=args.max_length)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits.detach().float().cpu().numpy().reshape(-1)

    print("\nSample text:", sample_text)
    print("Predictions:")
    for name, val in zip(LABEL_ORDER, logits.tolist()):
        print(f"  {name:17s}: {val:+.3f}")

    print("\nDone. Model saved to:", args.output_dir)


if __name__ == "__main__":
    main()
