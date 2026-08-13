# hamper-personalizer

Generates a personalized hamper product image per target company by pasting
that company's own logo, as-is (its own colors/font), into a fixed blank
spot on Snackible's base hamper image. Used to make hamper images for cold
outreach emails (e.g. pitching Deloitte with a hamper image that shows
Deloitte's own logo).

Email sending is **not** wired up yet - this repo only handles image
generation. `POST /batch-process` and the daily cron job produce the
personalized images into `output/`; sending them out is a separate step to
be added later.

## Project structure

```
hamper_personalizer.py      Core batch engine (multiprocessing)
calibrate_logo_position.py  Draws a pixel grid to read off logo box coords
hamper_api.py                FastAPI app: /batch-process, /cron/batch-process
config.py                    Paths + LOGO_BOX (single source of truth)
companies.csv                company_name,logo_filename template
vercel.json                  Vercel build + cron config
assets/base/                 Base hamper image (gitignored) - see below
assets/logos/                Put real company logo files here (gitignored)
output/                      Generated personalized images land here (gitignored)
```

`assets/base/hamper_base_v2.png` is the active compositing base
(`BASE_IMAGE_PATH` in `config.py`) - it has a blank circular spot built into
the photo itself, so each company's logo pastes in cleanly with no
crop/blend artifacts. Older base images may still be present in that folder
from earlier calibration passes; `config.py` notes which one is live.

## Local setup

Requires Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Drop your real assets in place:
- Company logo files → `assets/logos/`
- Fill in `companies.csv` with `company_name,logo_filename` rows matching the logo files

`assets/base/hamper_base_v2.png` and the `LOGO_BOX` values in `config.py`
are already calibrated against the real base image - no setup needed there
unless the base photo changes.

## Calibrating the logo box position (only if the base image changes)

If you swap in a different/updated base hamper photo, recalibrate:

1. Put the new base image somewhere under `assets/base/`.
2. Run the calibration helper:

   ```bash
   python calibrate_logo_position.py --base assets/base/<your_image> --step 50
   ```

   This writes `calibration_grid.png` — the base image with a labeled pixel
   grid overlaid (grid lines every `--step` pixels).
3. Open `calibration_grid.png` and read off the top-left corner (x, y) and
   the width/height of the box where the logo should go.
4. Set the real values, either:
   - directly in `config.py` (`LOGO_BOX = {...}`), or
   - via env vars (`LOGO_BOX_X`, `LOGO_BOX_Y`, `LOGO_BOX_WIDTH`, `LOGO_BOX_HEIGHT`) —
     useful for setting them in Vercel's dashboard without touching code.
5. If the box lid is photographed at an angle, measure the tilt (fit a line
   across the lid's top edge) and set `LOGO_ROTATION_DEGREES` so the
   composited logo sits flush with the lid instead of flat.

## Running a batch locally

```bash
python hamper_personalizer.py \
  --base assets/base/hamper_base_v2.png \
  --logos assets/logos \
  --csv companies.csv \
  --output output \
  --workers 8
```

All flags are optional and default to the paths in `config.py`. Each row in
`companies.csv` produces `output/<sanitized_company_name>.pdf`. For each
logo the engine: trims surrounding whitespace/transparency, resizes it to
fit `LOGO_BOX` while preserving aspect ratio, rotates it to match the box's
tilt if any, and centers it in the box by visual weight (not just bounding
box, so a bold letterform doesn't throw off the centering). The logo's own
colors are kept as-is - no recoloring. Companies are processed in parallel
via `ProcessPoolExecutor`.

## Running the API locally

```bash
uvicorn hamper_api:app --reload
```

Trigger a batch run:

```bash
curl -X POST http://127.0.0.1:8000/batch-process
```

Both endpoints return a JSON summary: `processed`, `succeeded`, `failed`, and
a list of per-company `errors`.

## Deploying to Vercel

1. Install the Vercel CLI and log in: `npm i -g vercel`, then `vercel login`.
2. From this repo: `vercel link` to associate the project.
3. In the Vercel dashboard, set environment variables for the project:
   - `LOGO_BOX_X`, `LOGO_BOX_Y`, `LOGO_BOX_WIDTH`, `LOGO_BOX_HEIGHT`, `LOGO_ROTATION_DEGREES` (the real calibrated values)
   - `CRON_SECRET` — a random secret string; Vercel automatically sends it as
     `Authorization: Bearer <CRON_SECRET>` when it calls the cron endpoint,
     and `hamper_api.py` verifies it.
   - Optionally `BASE_IMAGE_PATH`, `LOGOS_DIR`, `COMPANIES_CSV`, `OUTPUT_DIR`,
     `BATCH_WORKERS` if you need to override the defaults.
4. Deploy: `vercel --prod` (confirm with the user before running this — it
   pushes a live deployment).

`vercel.json` already wires up the cron job:

```json
{
  "crons": [{ "path": "/cron/batch-process", "schedule": "0 6 * * *" }]
}
```

This calls `GET /cron/batch-process` daily at 06:00 UTC. Adjust the cron
schedule as needed — note Vercel's Hobby plan limits cron jobs to once per
day; Pro plans allow finer-grained schedules.

### Note on serverless limits

Vercel serverless functions have execution time limits (10s on Hobby, up to
60s+ on Pro with configuration). For 100+ images/day this may need a longer
function timeout (`maxDuration` in `vercel.json`) or moving batch processing
off Vercel entirely if it grows further — not addressed yet, flagging for
later.

## Assets

The base hamper image, real company logos, and the calibrated `LOGO_BOX`
coordinates are provided separately and are gitignored — this repo ships
with placeholders only (`config.py`, `companies.csv` template).
