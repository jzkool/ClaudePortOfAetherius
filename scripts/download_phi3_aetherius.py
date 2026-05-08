"""Download phi3-aetherius weights from HuggingFace."""

import argparse
import os
from pathlib import Path


def download_weights(output_dir: str = "models/phi3_aetherius/weights", token: str | None = None):
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ImportError("Install huggingface_hub: pip install huggingface-hub")

    repo_id = "KingOfThoughtFleuren/phi3-aetherius"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {repo_id} to {output_path} ...")
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(output_path),
        token=token,
    )
    print(f"Weights saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download phi3-aetherius weights")
    parser.add_argument("--output-dir", default="models/phi3_aetherius/weights")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN"), help="HuggingFace token (or set HF_TOKEN env var)")
    args = parser.parse_args()
    download_weights(args.output_dir, args.token)
