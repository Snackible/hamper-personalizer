"""
Calibration helper: draws a labeled pixel grid over the base hamper image so
you can read off the x/y/width/height of the fixed logo box by eye, then plug
those values into config.py (LOGO_BOX) or the matching LOGO_BOX_* env vars.

Usage:
    python calibrate_logo_position.py --base assets/base/hamper_base.png --step 50
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config

GRID_COLOR = (255, 0, 0, 160)
LABEL_COLOR = (255, 0, 0, 255)


def draw_grid(base_image_path: Path, step: int, output_path: Path) -> None:
    base = Image.open(base_image_path).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.load_default()
    except Exception:  # noqa: BLE001
        font = None

    width, height = base.size

    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill=GRID_COLOR, width=1)
        draw.text((x + 2, 2), str(x), fill=LABEL_COLOR, font=font)

    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=GRID_COLOR, width=1)
        draw.text((2, y + 2), str(y), fill=LABEL_COLOR, font=font)

    combined = Image.alpha_composite(base, overlay).convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(output_path, format="PNG")
    print(f"Grid overlay saved to: {output_path}")
    print(f"Base image size: {width}x{height}")
    print("Read off the top-left corner (x, y) and the width/height of the logo slot,")
    print("then set LOGO_BOX in config.py or the LOGO_BOX_X / LOGO_BOX_Y / "
          "LOGO_BOX_WIDTH / LOGO_BOX_HEIGHT env vars.")


def main():
    parser = argparse.ArgumentParser(description="Draw a calibration grid over the base hamper image.")
    parser.add_argument("--base", type=Path, default=config.BASE_IMAGE_PATH, help="Base hamper image path")
    parser.add_argument("--step", type=int, default=50, help="Grid spacing in pixels")
    parser.add_argument("--output", type=Path, default=Path("calibration_grid.png"), help="Output file path")
    args = parser.parse_args()

    if not args.base.exists():
        raise SystemExit(f"Base image not found: {args.base}. Drop it in assets/base/ or pass --base.")

    draw_grid(args.base, args.step, args.output)


if __name__ == "__main__":
    main()
