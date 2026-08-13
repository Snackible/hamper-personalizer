"""
Central configuration for the hamper personalizer pipeline.

LOGO_BOX was calibrated against assets/base/hamper_base_v2.png (the
teal/gold confetti box, blank circle) on 2026-08-13. Re-run calibration if
the base image changes again.

Previous calibration (pink box, assets/base/hamper_base_clean.jpg) is kept
below in comments for reference in case that image comes back into use.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- Paths -------------------------------------------------------------
BASE_IMAGE_PATH = Path(os.environ.get("BASE_IMAGE_PATH", BASE_DIR / "assets" / "base" / "hamper_base_v2.png"))
LOGOS_DIR = Path(os.environ.get("LOGOS_DIR", BASE_DIR / "assets" / "logos"))
COMPANIES_CSV = Path(os.environ.get("COMPANIES_CSV", BASE_DIR / "companies.csv"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", BASE_DIR / "output"))

# --- Logo placement box --------------------------------------------------
# Calibrated against the 6434x4595 base image. The blank blush-colored
# circle (interior, excluding the gold ring border) measured bbox
# 2886,1476 - 3800,2348 (diameter ~914x872, center ~3343,1912). Box is
# centered on that same point, sized to use most of the circle while still
# leaving margin from the gold ring (~67px horizontal, ~236px vertical).
LOGO_BOX = {
    "x": int(os.environ.get("LOGO_BOX_X", 2953)),
    "y": int(os.environ.get("LOGO_BOX_Y", 1712)),
    "width": int(os.environ.get("LOGO_BOX_WIDTH", 780)),
    "height": int(os.environ.get("LOGO_BOX_HEIGHT", 400)),
}

# Padding (px) kept between the trimmed logo and the edges of LOGO_BOX when
# centering.
LOGO_PADDING = int(os.environ.get("LOGO_PADDING", 45))

# This box lid is photographed almost perfectly straight-on - measured tilt
# was ~0.08 degrees (vs. ~2.16 degrees on the previous pink box), so no
# meaningful rotation correction is needed.
LOGO_ROTATION_DEGREES = float(os.environ.get("LOGO_ROTATION_DEGREES", 0.0))

# --- Previous calibration (pink box, hamper_base_clean.jpg, 1600x1600) ---
# LOGO_BOX = {"x": 963, "y": 745, "width": 165, "height": 54}
# LOGO_PADDING = 12
# LOGO_ROTATION_DEGREES = 2.16
