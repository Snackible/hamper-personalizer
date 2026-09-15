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
# hamper_base_v3_clean.jpg (2026-09-15): same teal/gold confetti box, but a
# newer square (1600x1600) product render with the wordmark freshly erased
# from the circle - NOT simply a resize of hamper_base_v2.png (different
# aspect ratio), so LOGO_BOX below was recalibrated from scratch against it.
BASE_IMAGE_PATH = Path(os.environ.get("BASE_IMAGE_PATH", BASE_DIR / "assets" / "base" / "hamper_base_v3_clean.jpg"))
# The orange-background hamper is reserved for white/light logos, which would
# not have enough contrast against the blush circle in the default image.
LIGHT_LOGO_BASE_IMAGE_PATH = Path(os.environ.get(
    "LIGHT_LOGO_BASE_IMAGE_PATH", BASE_DIR / "assets" / "base" / "hamper_base_light_logos.png"
))
LOGOS_DIR = Path(os.environ.get("LOGOS_DIR", BASE_DIR / "assets" / "logos"))
COMPANIES_CSV = Path(os.environ.get("COMPANIES_CSV", BASE_DIR / "companies.csv"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", BASE_DIR / "output"))

# --- Logo placement box --------------------------------------------------
# Calibrated against the 1600x1600 hamper_base_v3_clean.jpg. The blank
# blush-colored circle (interior, excluding the gold ring border) measured
# bbox 718,589 - 944,806 (diameter ~226x217, center ~831,697.5). Box is
# centered on that same point, sized to use most of the circle while still
# leaving margin from the gold ring.
LOGO_BOX = {
    "x": int(os.environ.get("LOGO_BOX_X", 736)),
    "y": int(os.environ.get("LOGO_BOX_Y", 645)),
    "width": int(os.environ.get("LOGO_BOX_WIDTH", 190)),
    "height": int(os.environ.get("LOGO_BOX_HEIGHT", 105)),
}

# Padding (px) kept between the trimmed logo and the edges of LOGO_BOX when
# centering.
LOGO_PADDING = int(os.environ.get("LOGO_PADDING", 12))

# This box lid is photographed straight-on, consistent with the previous
# base image - no meaningful rotation correction needed.
LOGO_ROTATION_DEGREES = float(os.environ.get("LOGO_ROTATION_DEGREES", 0.0))

# Calibrated against hamper_base_light_logos.png (1080x1080). The teal
# circular panel on the box lid occupies this square; the gold border remains
# visible when LOGO_PADDING is applied.
LIGHT_LOGO_BOX = {
    "x": int(os.environ.get("LIGHT_LOGO_BOX_X", 465)),
    "y": int(os.environ.get("LIGHT_LOGO_BOX_Y", 377)),
    "width": int(os.environ.get("LIGHT_LOGO_BOX_WIDTH", 150)),
    "height": int(os.environ.get("LIGHT_LOGO_BOX_HEIGHT", 150)),
}
LIGHT_LOGO_PADDING = int(os.environ.get("LIGHT_LOGO_PADDING", 15))
LIGHT_LOGO_ROTATION_DEGREES = float(os.environ.get("LIGHT_LOGO_ROTATION_DEGREES", 0.0))

# Disabled by default so every output uses the original, unchanged mother
# image. Set LIGHT_LOGO_CONTRAST_OUTLINE=true only if contrast treatment is
# explicitly requested again.
LIGHT_LOGO_CONTRAST_OUTLINE = os.environ.get("LIGHT_LOGO_CONTRAST_OUTLINE", "false").lower() in {
    "1", "true", "yes", "on"
}

# Used only when LIGHT_LOGO_CONTRAST_OUTLINE is enabled. Pure white is 255.
LIGHT_LOGO_LUMINANCE_THRESHOLD = float(os.environ.get("LIGHT_LOGO_LUMINANCE_THRESHOLD", 150))

# --- Previous calibrations, kept for reference -------------------------
# Teal box, hamper_base_v2.png, 6434x4595:
# LOGO_BOX = {"x": 2953, "y": 1712, "width": 780, "height": 400}
# LOGO_PADDING = 45
#
# Pink box, hamper_base_clean.jpg, 1600x1600:
# LOGO_BOX = {"x": 963, "y": 745, "width": 165, "height": 54}
# LOGO_PADDING = 12
# LOGO_ROTATION_DEGREES = 2.16
