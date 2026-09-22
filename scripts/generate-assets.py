"""Validate the active Zecpass public asset set.

The production interface uses the curated target references in public/; this
command keeps the asset workflow deterministic without regenerating protocol art.
"""
from pathlib import Path

REQUIRED = ("hero.webp", "token.webp", "stack.webp", "network.webp", "icon.svg", "apple-icon.png")
root = Path(__file__).resolve().parents[1] / "public"
missing = [name for name in REQUIRED if not (root / name).exists()]
if missing:
    raise SystemExit(f"Missing active Zecpass assets: {', '.join(missing)}")
print(f"Validated {len(REQUIRED)} active Zecpass assets in {root}")
