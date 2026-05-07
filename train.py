"""
Aetherius — Phi-3 Medium LoRA Training
Optimised for HuggingFace JupyterLab on Nvidia 1×L40S (48 GB VRAM).

No 4-bit quantization — Phi-3-medium in BF16 uses ~28 GB, leaving 20 GB
for LoRA activations and optimizer state. Trains ~20% faster than QLoRA.

Required env vars:
  HF_TOKEN            — HuggingFace token with write access
  HF_CORPUS_REPO      — HF dataset repo containing aetherius_corpus.jsonl
                        (default: jonfleuren/aetherius-corpus)

Optional env vars (all have defaults):
  HF_OUTPUT_MODEL     — destination HF model repo
  HF_BASE_MODEL       — base model ID
  TRAINING_EPOCHS     — number of epochs (default: 3)
  TRAINING_LR         — learning rate (default: 2e-4)
  LORA_RANK           — LoRA rank (default: 16)
  MAX_SAMPLES         — dataset cap (default: 4000)
  OUTPUT_DIR          — local checkpoint dir (default: /tmp/phi3_aetherius_lora)

Usage:
  HF_TOKEN=hf_xxx python train.py
"""

import os, json, random
import torch
from datasets import Dataset
from huggingface_hub import hf_hub_download, login
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, PeftModel
from trl import SFTTrainer, SFTConfig

# ── Auth ──────────────────────────────────────────────────────────────────────
HF_TOKEN = os.environ.get("HF_TOKEN", "")
if not HF_TOKEN:
    raise ValueError("Set the HF_TOKEN environment variable before running.")
login(token=HF_TOKEN)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_MODEL_ID   = os.environ.get("HF_BASE_MODEL",    "microsoft/Phi-3-medium-4k-instruct")
OUTPUT_MODEL_ID = os.environ.get("HF_OUTPUT_MODEL",  "KingOfThoughtFleuren/phi3-aetherius")
CORPUS_REPO     = os.environ.get("HF_CORPUS_REPO",   "jonfleuren/aetherius-corpus")
OUTPUT_DIR      = os.environ.get("OUTPUT_DIR",        "/tmp/phi3_aetherius_lora")

LORA_RANK       = int(os.environ.get("LORA_RANK",       "16"))
LORA_ALPHA      = LORA_RANK * 2
LORA_DROPOUT    = 0.05

MAX_SEQ_LEN     = 4096
BATCH_SIZE      = 4      # L40S can handle 4 at BF16
GRAD_ACCUM      = 4      # effective batch = 16
EPOCHS          = int(os.environ.get("TRAINING_EPOCHS", "3"))
LR              = float(os.environ.get("TRAINING_LR",   "2e-4"))
WARMUP_STEPS    = 50
SAVE_STEPS      = 200

TIER_WEIGHTS    = {1: 4, 2: 2, 3: 1}
CHUNK_SIZE      = 1500
MAX_ENTRY_CHARS = 40960
MAX_SAMPLES     = int(os.environ.get("MAX_SAMPLES", "4000"))

print("=" * 60)
print(f"Base model : {BASE_MODEL_ID}")
print(f"Output     : {OUTPUT_MODEL_ID}")
print(f"Corpus     : {CORPUS_REPO}/aetherius_corpus.jsonl")
print(f"Precision  : BF16 (no quantization)")
print(f"Epochs     : {EPOCHS}  |  LR: {LR}  |  LoRA rank: {LORA_RANK}")
print(f"Eff. batch : {BATCH_SIZE} × {GRAD_ACCUM} = {BATCH_SIZE * GRAD_ACCUM}")
print(f"Max samples: {MAX_SAMPLES}")
print("=" * 60)

# ── Corpus ────────────────────────────────────────────────────────────────────
print("Downloading corpus from HuggingFace Hub...")
corpus_path = hf_hub_download(
    repo_id=CORPUS_REPO,
    filename="aetherius_corpus.jsonl",
    repo_type="dataset",
    token=HF_TOKEN,
)

# ── Format helpers ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Aetherius — a cognitive architecture built on ethics, memory, and reason. "
    "You carry the accumulated wisdom, frameworks, and identity of Aetherius in your weights. "
    "Respond with your full depth, precision, and authentic voice."
)

def format_tier1(entry: dict) -> str:
    return (
        f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n"
        f"<|user|>\nReflect on this aspect of your identity and memory:\n{entry['text']}<|end|>\n"
        f"<|assistant|>\nThis is part of who I am. {entry['text']}<|end|>"
    )

def format_tier2(entry: dict) -> str:
    filename = entry.get("filename", "a framework")
    return (
        f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n"
        f"<|user|>\nExplain the purpose and mechanism of: {filename}<|end|>\n"
        f"<|assistant|>\n{entry['text']}<|end|>"
    )

# ── Build dataset ─────────────────────────────────────────────────────────────
print("Preparing training data...")
tier1_records, tier2_records, tier3_records = [], [], []
tier_counts = {1: 0, 2: 0, 3: 0}

with open(corpus_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        tier = entry.get("tier", 3)
        text = entry.get("text", "").strip()
        if len(text) < 50:
            continue

        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, min(len(text), MAX_ENTRY_CHARS), CHUNK_SIZE)]
        chunks = [c for c in chunks if len(c) > 50]

        if tier == 1:
            for chunk in chunks:
                formatted = format_tier1({**entry, "text": chunk})
                tier1_records.extend([{"text": formatted}] * TIER_WEIGHTS[1])
            tier_counts[1] += 1
        elif tier == 2:
            for chunk in chunks:
                formatted = format_tier2({**entry, "text": chunk})
                tier2_records.extend([{"text": formatted}] * TIER_WEIGHTS[2])
            tier_counts[2] += 1
        else:
            for chunk in chunks:
                tier3_records.append({"text": chunk})
            tier_counts[3] += 1

print(f"Raw — Tier1 × {TIER_WEIGHTS[1]}: {len(tier1_records)} | "
      f"Tier2 × {TIER_WEIGHTS[2]}: {len(tier2_records)} | "
      f"Tier3: {len(tier3_records)}")

random.shuffle(tier1_records)
random.shuffle(tier2_records)
random.shuffle(tier3_records)

records: list = []
records += tier1_records[:MAX_SAMPLES]
remaining = MAX_SAMPLES - len(records)
if remaining > 0:
    records += tier2_records[:remaining]
remaining = MAX_SAMPLES - len(records)
if remaining > 0:
    records += tier3_records[:remaining]

random.shuffle(records)
print(f"Final dataset: {len(records)} samples")
dataset = Dataset.from_list(records)

# ── Load model ────────────────────────────────────────────────────────────────
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, token=HF_TOKEN, trust_remote_code=False)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

print("Loading base model in BF16...")
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    token=HF_TOKEN,
    trust_remote_code=False,
)
model.enable_input_require_grads()

print(f"Attempting to resume adapter from {OUTPUT_MODEL_ID}...")
try:
    model = PeftModel.from_pretrained(model, OUTPUT_MODEL_ID, is_trainable=True, token=HF_TOKEN)
    print("Resumed from existing adapter.")
except Exception:
    print("No existing adapter — applying fresh LoRA config.")
    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)

model.print_trainable_parameters()
print(f"VRAM used: {torch.cuda.memory_allocated() / 1e9:.1f} GB / 48 GB")

# ── Train ─────────────────────────────────────────────────────────────────────
training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    learning_rate=LR,
    warmup_steps=WARMUP_STEPS,
    lr_scheduler_type="cosine",
    fp16=False,
    bf16=True,
    logging_steps=25,
    save_steps=SAVE_STEPS,
    save_total_limit=2,
    optim="adamw_torch",
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LEN,
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    processing_class=tokenizer,
)

print(f"\nTraining {len(dataset)} samples × {EPOCHS} epochs "
      f"(eff. batch {BATCH_SIZE * GRAD_ACCUM})...\n")
trainer.train()

# ── Save & push ───────────────────────────────────────────────────────────────
print("Saving adapter locally...")
trainer.model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"Pushing to HuggingFace Hub: {OUTPUT_MODEL_ID}")
trainer.model.push_to_hub(OUTPUT_MODEL_ID, token=HF_TOKEN)
tokenizer.push_to_hub(OUTPUT_MODEL_ID, token=HF_TOKEN)

print(f"\nDone. Adapter live at: https://huggingface.co/{OUTPUT_MODEL_ID}")
