"""Pair the source camera previews with the same frames in the published movie."""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def compare(folder):
    shots = json.loads((folder / "shots.json").read_text(encoding="utf-8"))
    select = "+".join(f"eq(n,{s['frame'] - 1})" for s in shots)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ROOT / "final/A_Second_Taj.mp4"),
                    "-vf", f"select='{select}',scale=512:288", "-fps_mode", "vfr",
                    str(folder / "film-%02d.png")], check=True)
    width, height, label = 512, 288, 35
    sheet = Image.new("RGB", (2 * width, label + (height + label) * len(shots)), "#18212b")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("DejaVuSans.ttf", 18)
    draw.text((10, 7), "Blender camera", font=font, fill="white")
    draw.text((width + 10, 7), "Published film", font=font, fill="white")
    for index, shot in enumerate(shots):
        y = label + index * (height + label)
        title = f"{shot['camera']}     |     {shot['time']:.2f}s     |     {shot['speaker']}"
        draw.text((10, y + 6), title, font=font, fill="white")
        for column, name in enumerate((shot["image"], f"film-{index + 1:02d}.png")):
            with Image.open(folder / name) as img:
                sheet.paste(img.convert("RGB").resize((width, height)), (column * width, y + label))
    sheet.save(folder / "camera-comparison.jpg", quality=90)


if __name__ == "__main__":
    compare(Path(sys.argv[1]))
