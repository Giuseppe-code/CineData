# Training: BERT Film Review Aspect Analysis

Fine-tuning di `bert-base-uncased` sul dataset 
[Lowerated/imdb-reviews-rated](https://huggingface.co/datasets/Lowerated/imdb-reviews-rated)
per predire 7 aspetti qualitativi di film.

Puoi scaricare il modello già pronto o effettuare tu il training.
## Output labels

| Label | Descrizione |
|-------|-------------|
| `direction` | Qualità della regia |
| `cinematography` | Fotografia |
| `unique_concept` | Originalità |
| `story` | Trama |
| `emotions` | Impatto emotivo |
| `characters` | Personaggi |
| `production_design` | Design produzione |

## Installazione dei requirements
```bash
pip install -r requirements_training.txt
```

## Download modello pre-trainato

Ora puoi scaricare il modello da HuggingFace:
```bash
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='Giusex04/cinedata-bert-film-aspects',
    local_dir='../models/cinedata_bert_film'
)
"
```


## Training completo
```bash
python finetune_lowerated_bert_pytorch.py \
  --output_dir ./models/quickcheck_model \
  --epochs 2 \
  --max_length 128 \
  --batch_size 2 \
  --grad_accum 4 \
  --fp16
```

## Quick check (10-15 min)
```bash
python finetune_lowerated_bert_pytorch.py \
  --output_dir ./models/quickcheck_model \
  --epochs 1 \
  --max_length 128 \
  --batch_size 2 \
  --grad_accum 4 \
  --fp16 \
  --max_train_samples 4000 \
  --max_eval_samples 500
```
