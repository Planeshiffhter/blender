#!/usr/bin/env python3
"""Check scaffold directories, character identities and uncompressed .blend headers.

This structural check does not certify rigs, animation, materials, or render quality.
"""

import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    errors = []
    expected_ids = {"C01_maya", "C02_arjun", "C03_neha", "C04_kabir"}
    try:
        characters = json.loads((root / "config/characters.json").read_text())["characters"]
        ids = [character["id"] for character in characters]
        if len(ids) != 4 or set(ids) != expected_ids:
            errors.append("characters.json must contain each of the four character IDs exactly once")
        for character in characters:
            relative_path = character["master_blend"]
            path = (root / relative_path).resolve()
            if not path.is_relative_to(root) or path.suffix != ".blend":
                errors.append(f"Invalid master path: {relative_path}")
            elif not path.is_file():
                errors.append(f"Missing master: {relative_path}")
            else:
                with path.open("rb") as blend:
                    header = blend.read(12)
                if len(header) != 12 or header[:7] != b"BLENDER":
                    errors.append(f"Invalid or compressed .blend header: {relative_path}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Cannot validate character configuration: {exc}")

    for directory in (
        "assets/animations/body", "assets/animations/face", "assets/animations/cameras",
        "assets/environments/kitchen", "assets/environments/cafe",
        "assets/environments/supermarket", "assets/environments/street",
        "assets/props", "assets/voices", "assets/looks",
        "episodes/EP001/audio", "episodes/EP001/shots", "episodes/EP001/renders",
        "episodes/EP001/final",
    ):
        if not (root / directory).is_dir():
            errors.append(f"Missing directory: {directory}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Asset structure passed: four character masters and all asset/output directories exist.")
    print("Rigging, animation and render readiness require validation in Blender.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
