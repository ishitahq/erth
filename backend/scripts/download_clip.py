#!/usr/bin/env python3
"""
Download CLIP ViT-B/32 weights into backend/models/ViT-B-32.pt

Run from the backend/ directory:
    python scripts/download_clip.py

The file is ~338 MB. It is verified against the SHA-256 hash embedded in
the OpenAI URL, matching exactly what `clip.load('ViT-B/32')` would download.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

CLIP_URL = (
    "https://openaipublic.azureedge.net/clip/models/"
    "40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt"
)
EXPECTED_SHA256 = "40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "models" / "ViT-B-32.pt"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Skip if already downloaded and valid
    if OUTPUT_PATH.exists():
        print(f"Found existing file: {OUTPUT_PATH}")
        print("Verifying SHA-256 ...", end=" ", flush=True)
        if sha256_file(OUTPUT_PATH) == EXPECTED_SHA256:
            print("OK ✓  (already up-to-date, skipping download)")
            return
        else:
            print("MISMATCH — re-downloading ...")

    print(f"Downloading CLIP ViT-B/32 (~338 MB)")
    print(f"  From : {CLIP_URL}")
    print(f"  To   : {OUTPUT_PATH}")

    try:
        with urllib.request.urlopen(CLIP_URL) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            with open(OUTPUT_PATH, "wb") as f:
                while True:
                    chunk = response.read(1 << 20)  # 1 MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        mb = downloaded / (1 << 20)
                        print(f"\r  {mb:6.1f} MB  ({pct:5.1f}%)", end="", flush=True)
        print()
    except Exception as exc:
        OUTPUT_PATH.unlink(missing_ok=True)
        print(f"\nERROR: Download failed — {exc}", file=sys.stderr)
        sys.exit(1)

    print("Verifying SHA-256 ...", end=" ", flush=True)
    actual = sha256_file(OUTPUT_PATH)
    if actual != EXPECTED_SHA256:
        OUTPUT_PATH.unlink(missing_ok=True)
        print(f"FAILED\nExpected : {EXPECTED_SHA256}\nGot      : {actual}", file=sys.stderr)
        sys.exit(1)

    print(f"OK ✓")
    print(f"\nDone! Place confirmed at: {OUTPUT_PATH}")
    print("The CLIP Stage 2 grade classification is now ready.")


if __name__ == "__main__":
    download()
