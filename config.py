"""
Central configuration for the hamper personalizer pipeline.

IMPORTANT: LOGO_BOX below is a PLACEHOLDER. Run `calibrate_logo_position.py`
against the real base hamper image to find the actual x/y/width/height of the
logo slot, then replace the values (or set the matching env vars) before
running a real batch.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- Paths -------------------------------------------------------------
# Drop the real base hamper image and real company logos into these folders
# once you have them. They are gitignored so real brand assets never get
# committed by accident.
BASE_IMAGE_PATH = Path(os.environ.get("BASE_IMAGE_PATH", BASE_DIR / "assets" / "base" / "hamper_base.png"))
LOGOS_DIR = Path(os.environ.get("LOGOS_DIR", BASE_DIR / "assets" / "logos"))
COMPANIES_CSV = Path(os.environ.get("COMPANIES_CSV", BASE_DIR / "companies.csv"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", BASE_DIR / "output"))

# --- Logo placement box --------------------------------------------------
# PLACEHOLDER COORDINATES - DO NOT USE IN PRODUCTION.
# Replace after running calibrate_logo_position.py, either here or via env
# vars (LOGO_BOX_X / LOGO_BOX_Y / LOGO_BOX_WIDTH / LOGO_BOX_HEIGHT) so the
# real coordinates can be supplied at deploy time without editing code.
LOGO_BOX = {
    "x": int(os.environ.get("LOGO_BOX_X", 0)),  # PLACEHOLDER
    "y": int(os.environ.get("LOGO_BOX_Y", 0)),  # PLACEHOLDER
    "width": int(os.environ.get("LOGO_BOX_WIDTH", 200)),  # PLACEHOLDER
    "height": int(os.environ.get("LOGO_BOX_HEIGHT", 200)),  # PLACEHOLDER
}

# Padding (px) kept between the trimmed logo and the edges of LOGO_BOX when
# centering, so logos don't touch the box boundary.
LOGO_PADDING = int(os.environ.get("LOGO_PADDING", 8))
