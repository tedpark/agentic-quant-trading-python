from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.serving.model_registry import build_checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a toy checkpoint for the serving demo.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--model-version", default="demo-v2")
    parser.add_argument("--input-dim", type=int, default=3)
    args = parser.parse_args()

    args.path.parent.mkdir(parents=True, exist_ok=True)
    build_checkpoint(
        args.path,
        model_version=args.model_version,
        input_dim=args.input_dim,
    )
    print(f"created checkpoint: {args.path}")


if __name__ == "__main__":
    main()
