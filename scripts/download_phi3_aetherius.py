"""Download phi3-aetherius LoRA adapter weights from HuggingFace.

Base model: microsoft/Phi-3-medium-4k-instruct
Adapter:    KingOfThoughtFleuren/phi3-aetherius  (LoRA, r=16)
"""

import argparse
import os
from pathlib import Path


ADAPTER_REPO = "KingOfThoughtFleuren/phi3-aetherius"
BASE_MODEL_REPO = "microsoft/Phi-3-medium-4k-instruct"


def download_adapter(output_dir: str = "models/phi3_aetherius/weights", token: str | None = None):
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ImportError("Install huggingface_hub: pip install huggingface-hub")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading LoRA adapter from {ADAPTER_REPO} ...")
    snapshot_download(
        repo_id=ADAPTER_REPO,
        local_dir=str(output_path),
        token=token,
        ignore_patterns=["*.md"],
    )
    print(f"Adapter weights saved to {output_path}")
    print(f"Load with base model: {BASE_MODEL_REPO}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download phi3-aetherius LoRA adapter weights")
    parser.add_argument("--output-dir", default="models/phi3_aetherius/weights")
    parser.add_argument(
        "--token",
        default=os.environ.get("HF_TOKEN"),
        help="HuggingFace token (or set HF_TOKEN env var)",
    )
    args = parser.parse_args()
    download_adapter(args.output_dir, args.token)
