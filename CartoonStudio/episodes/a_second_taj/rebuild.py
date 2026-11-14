"""Regenerate or reuse the voices and embedded soundtrack in an editable copy."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import make_audio

def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--reuse-audio", action="store_true", help="Use the existing WAV and timing.")
    args.add_argument("--blender", default=os.environ.get("BLENDER_BIN", "blender"), help="Path to the Blender 4.3 executable.")
    args = args.parse_args()
    root = Path(__file__).resolve().parent
    if not args.reuse_audio:
        make_audio.main()
    exe = shutil.which(args.blender)
    if not exe:
        raise SystemExit("Pass --blender followed by the path to the Blender executable.")
    subprocess.run([exe, "--background", str(root / "A_Second_Taj.blend"),
                    "--python-exit-code", "1", "--python", str(root / "update_blend.py"),
                    "--", "--input-dir", str(root / "audio"), "--output", str(root / "A_Second_Taj_Remix.blend")], check=True)
    print("Ready to open in Blender:", root / "A_Second_Taj_Remix.blend")

if __name__ == "__main__":
    main()
