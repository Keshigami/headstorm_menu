"""Draw 5 synthetic menus into samples/ (plus ground_truth.json).  uv run python generate_samples.py [--n 5]"""
from __future__ import annotations

import argparse
from pathlib import Path

from menusync.samples import generate

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "samples")
    a = ap.parse_args()
    for p in generate(a.out, a.n):
        print(f"wrote {p}")
