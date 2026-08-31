#!/usr/bin/env python3
"""Generate native application icon files from the maintained JPEG logo."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "源代码" / "源代码" / "images" / "window.jpg"
OUTPUT = ROOT / "build-assets"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image = Image.open(SOURCE).convert("RGBA")
    side = max(image.size)
    square = Image.new("RGBA", (side, side), "white")
    square.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    square = square.resize((1024, 1024), Image.Resampling.LANCZOS)

    square.save(
        OUTPUT / "MindMap.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    square.save(OUTPUT / "MindMap.icns", format="ICNS")


if __name__ == "__main__":
    main()
