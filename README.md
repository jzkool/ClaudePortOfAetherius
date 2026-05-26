# ClaudePortOfAetherius
Running Aetherius using Claude's api's. Proving model agnostic capability

## Model Weights

### phi3-aetherius
Phi-3 weights adapted for the Aetherius architecture, hosted on HuggingFace at
[KingOfThoughtFleuren/phi3-aetherius](https://huggingface.co/KingOfThoughtFleuren/phi3-aetherius).

**Download weights:**
```bash
pip install -r requirements.txt
# Set your HuggingFace token if the repo is private
export HF_TOKEN=your_token_here
python scripts/download_phi3_aetherius.py
```

Weights are saved to `models/phi3_aetherius/weights/` (excluded from git via `.gitignore`).

## Setup

```bash
pip install -r requirements.txt
```
