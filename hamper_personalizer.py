"""
Core batch engine: pastes each company's logo, as-is, into a fixed box on
the base hamper image.

Usage:
    python hamper_personalizer.py \
        --base assets/base/hamper_base_v2.png \
        --logos assets/logos \
        --csv companies.csv \
        --output output \
        --workers 8

All arguments are optional and fall back to config.py defaults.
"""
import argparse
import csv
import multiprocessing
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

import config

SAFE_NAME_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class JobResult:
    company_name: str
    logo_filename: str
    output_path: Optional[str]
    success: bool
    error: Optional[str] = None


def sanitize_filename(company_name: str) -> str:
    slug = SAFE_NAME_RE.sub("_", company_name.strip().lower()).strip("_")
    return slug or "unnamed_company"


def trim_whitespace(logo: Image.Image) -> Image.Image:
    """Crop a logo down to its non-transparent / non-white content, and make
    sure the result is actually transparent outside that content."""
    rgba = logo.convert("RGBA")
    alpha = rgba.getchannel("A")

    if alpha.getextrema() != (255, 255):
        # Has real transparency - trim to the alpha bounding box.
        bbox = alpha.getbbox()
    else:
        # Fully opaque (e.g. flattened PNG/JPEG on white) - there's no real
        # alpha to crop to, so derive one from near-white pixels and apply
        # it, otherwise the white background stays opaque and shows up as a
        # solid block once pasted onto the base image.
        gray = rgba.convert("L")
        mask = Image.eval(gray, lambda p: 255 if p < 250 else 0)
        rgba.putalpha(mask)
        bbox = mask.getbbox()

    if bbox is None:
        return rgba
    return rgba.crop(bbox)


def fit_and_center(logo: Image.Image, box_w: int, box_h: int, padding: int,
                    rotation_degrees: float = 0.0) -> Image.Image:
    """Resize `logo` to fit within (box_w, box_h) minus padding, preserving
    aspect ratio, rotate to match the box's natural tilt, then place it
    centered on a transparent box_w x box_h canvas."""
    target_w = max(box_w - 2 * padding, 1)
    target_h = max(box_h - 2 * padding, 1)

    resized = logo.copy()
    resized.thumbnail((target_w, target_h), Image.LANCZOS)

    if rotation_degrees:
        # PIL rotates counter-clockwise for positive angles; our convention
        # is positive = clockwise (matching the measured box tilt), so negate.
        resized = resized.rotate(-rotation_degrees, expand=True, resample=Image.BICUBIC)
        # rotating with expand=True can grow the bounding box past the
        # padded target - shrink back down so the result never spills past
        # the intended margin (and thus never crowds the decorative border).
        if resized.width > target_w or resized.height > target_h:
            resized.thumbnail((target_w, target_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    # Center by visual weight (alpha-weighted centroid), not bounding box -
    # a bold letter (e.g. "D") reads heavier than a thin trailing mark (e.g.
    # a period), so bounding-box centering alone can still look off-center.
    centroid_x, centroid_y = alpha_centroid(resized)
    offset_x = round(box_w / 2 - centroid_x)
    offset_y = round(box_h / 2 - centroid_y)
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas


def alpha_centroid(img: Image.Image) -> tuple[float, float]:
    """Alpha-weighted centroid of `img`, falling back to its geometric
    center if fully transparent."""
    alpha = img.getchannel("A")
    w, h = alpha.size
    data = alpha.load()
    total = sx = sy = 0
    for y in range(h):
        for x in range(w):
            a = data[x, y]
            if a:
                total += a
                sx += x * a
                sy += y * a
    if total == 0:
        return w / 2, h / 2
    return sx / total, sy / total


def build_personalized_image(base_image_path: Path, logo_path: Path, box: dict, padding: int,
                              rotation_degrees: float) -> Image.Image:
    base = Image.open(base_image_path).convert("RGBA")
    logo = Image.open(logo_path)

    trimmed = trim_whitespace(logo)
    fitted = fit_and_center(trimmed, box["width"], box["height"], padding, rotation_degrees)

    result = base.copy()
    result.paste(fitted, (box["x"], box["y"]), fitted)
    return result


def process_row(args: tuple) -> JobResult:
    (company_name, logo_filename, base_image_path, logos_dir,
     output_dir, box, padding, rotation_degrees) = args

    logo_path = Path(logos_dir) / logo_filename
    if not logo_path.exists():
        return JobResult(company_name, logo_filename, None, False,
                          error=f"logo file not found: {logo_path}")

    try:
        result_image = build_personalized_image(Path(base_image_path), logo_path, box, padding,
                                                  rotation_degrees)
        output_path = Path(output_dir) / f"{sanitize_filename(company_name)}.pdf"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if result_image.mode == "RGBA":
            result_image = result_image.convert("RGB")
        result_image.save(output_path, format="PDF")

        return JobResult(company_name, logo_filename, str(output_path), True)
    except Exception as exc:  # noqa: BLE001 - surfaced in the batch summary
        return JobResult(company_name, logo_filename, None, False, error=str(exc))


def read_companies(csv_path: Path) -> list[tuple[str, str]]:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_name = (row.get("company_name") or "").strip()
            logo_filename = (row.get("logo_filename") or "").strip()
            if not company_name or not logo_filename:
                continue
            rows.append((company_name, logo_filename))
    return rows


def run_batch(base_image_path: Path, logos_dir: Path, csv_path: Path,
              output_dir: Path, box: dict, padding: int, workers: int,
              rotation_degrees: float = config.LOGO_ROTATION_DEGREES) -> list[JobResult]:
    if not base_image_path.exists():
        raise FileNotFoundError(f"base image not found: {base_image_path}")
    if not csv_path.exists():
        raise FileNotFoundError(f"companies CSV not found: {csv_path}")

    rows = read_companies(csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    job_args = [
        (company_name, logo_filename, str(base_image_path), str(logos_dir),
         str(output_dir), box, padding, rotation_degrees)
        for company_name, logo_filename in rows
    ]

    results: list[JobResult] = []
    if not job_args:
        return results

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_row, args) for args in job_args]
        for future in as_completed(futures):
            results.append(future.result())

    return results


def main():
    parser = argparse.ArgumentParser(description="Batch-generate personalized hamper images.")
    parser.add_argument("--base", type=Path, default=config.BASE_IMAGE_PATH, help="Base hamper image path")
    parser.add_argument("--logos", type=Path, default=config.LOGOS_DIR, help="Folder of company logo files")
    parser.add_argument("--csv", type=Path, default=config.COMPANIES_CSV, help="companies.csv path")
    parser.add_argument("--output", type=Path, default=config.OUTPUT_DIR, help="Output folder")
    parser.add_argument("--workers", type=int, default=max(multiprocessing.cpu_count() - 1, 1),
                         help="Parallel worker processes")
    args = parser.parse_args()

    try:
        results = run_batch(args.base, args.logos, args.csv, args.output,
                             config.LOGO_BOX, config.LOGO_PADDING, args.workers)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    print(f"Processed {len(results)} companies: {len(succeeded)} succeeded, {len(failed)} failed.")
    for r in failed:
        print(f"  FAILED  {r.company_name} ({r.logo_filename}): {r.error}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
