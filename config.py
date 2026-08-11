"""
Central configuration for the hamper personalizer pipeline.

LOGO_BOX and GOLD_* were calibrated against assets/base/hamper_base_clean.jpg
(the wordmark-erased base image) on 2026-08-11: box wraps where "Snackible"
used to sit inside the ornate circular frame, gold values sampled from the
original branded photo (assets/base/hamper_base.jpg). Re-run
calibrate_logo_position.py if the base image changes.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- Paths -------------------------------------------------------------
# assets/base/hamper_base.jpg       = original photo, Snackible branding intact
#                                      (kept only as a reference for the gold tone)
# assets/base/hamper_base_clean.jpg = same photo with the wordmark erased -
#                                      this is the actual compositing base
BASE_IMAGE_PATH = Path(os.environ.get("BASE_IMAGE_PATH", BASE_DIR / "assets" / "base" / "hamper_base_clean.jpg"))
LOGOS_DIR = Path(os.environ.get("LOGOS_DIR", BASE_DIR / "assets" / "logos"))
COMPANIES_CSV = Path(os.environ.get("COMPANIES_CSV", BASE_DIR / "companies.csv"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", BASE_DIR / "output"))

# --- Logo placement box --------------------------------------------------
# Calibrated against the 1600x1600 base image - wraps the former "Snackible"
# wordmark + its flourish tail, inside the circular frame, clear of the
# tagline and the peacock feather decorations. Override via env vars if the
# base image ever changes.
LOGO_BOX = {
    "x": int(os.environ.get("LOGO_BOX_X", 958)),
    "y": int(os.environ.get("LOGO_BOX_Y", 740)),
    "width": int(os.environ.get("LOGO_BOX_WIDTH", 165)),
    "height": int(os.environ.get("LOGO_BOX_HEIGHT", 54)),
}

# Padding (px) kept between the trimmed logo and the edges of LOGO_BOX when
# centering, so logos don't touch the box boundary.
LOGO_PADDING = int(os.environ.get("LOGO_PADDING", 4))

# The box lid is photographed at a slight angle - measured by fitting a line
# across the lid's top edge (positive = clockwise, right edge sits lower
# than left edge in the photo). The composited logo is rotated by this much
# so it sits flush with the lid instead of looking pasted-on flat.
LOGO_ROTATION_DEGREES = float(os.environ.get("LOGO_ROTATION_DEGREES", 2.16))

# --- Gold foil recolor ---------------------------------------------------
# Each company's logo is recolored to this gold gradient (its own
# font/shape is preserved, only color changes) so it matches Snackible's
# foil branding. Sampled from the real "Snackible" wordmark: brightest 5%
# of gold pixels -> GOLD_HIGHLIGHT, darkest 5% -> GOLD_SHADOW.
GOLD_HIGHLIGHT = os.environ.get("GOLD_HIGHLIGHT", "#ECAA7C")
GOLD_SHADOW = os.environ.get("GOLD_SHADOW", "#884B1E")
