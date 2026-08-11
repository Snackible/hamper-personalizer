# hamper-personalizer

Generates a personalized hamper product image per target company by pasting
that company's own logo into a fixed position on Snackible's base hamper
image (where the Snackible wordmark used to be), **recolored to Snackible's
gold foil gradient** - the company's own font/shape is preserved, only the
color changes to match the branding. Used to make hamper images for cold
outreach emails (e.g. pitching Deloitte with a hamper image that shows
Deloitte's own logo in gold foil).

Email sending is **not** wired up yet - this repo only handles image
generation. `POST /batch-process` and the daily cron job produce the
personalized images into `output/`; sending them out is a separate step to
be added later.

## Project structure

```
hamper_personalizer.py      Core batch engine (multiprocessing)
calibrate_logo_position.py  Draws a pixel grid to read off logo box coords
hamper_api.py                FastAPI app: /batch-process, /cron/batch-process
config.py                    Paths + LOGO_BOX + gold gradient (single source of truth)
companies.csv                company_name,logo_filename template
vercel.json                  Vercel build + cron config
assets/base/                 Base hamper images (gitignored) - see below
assets/logos/                Put real company logo files here (gitignored)
output/                      Generated personalized images land here (gitignored)
```

`assets/base/` holds two images:
- `hamper_base.jpg` - the original product photo, Snackible branding intact. Kept only as a color/position reference, not used for compositing.
- `hamper_base_clean.jpg` - the same photo with the Snackible wordmark erased from the circular frame. **This is the actual compositing base** (`BASE_IMAGE_PATH` in `config.py`) - since it has no existing branding to mask around, each company's logo pastes in cleanly with no crop/blend artifacts.

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

`assets/base/hamper_base_clean.jpg` and the `LOGO_BOX`/`GOLD_HIGHLIGHT`/
`GOLD_SHADOW` values in `config.py` are already calibrated against the real
base image - no setup needed there unless the base photo changes.

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
   - directly in `config.py` (`LOGO_BOX = {...}`, `GOLD_HIGHLIGHT`, `GOLD_SHADOW`), or
   - via env vars (`LOGO_BOX_X`, `LOGO_BOX_Y`, `LOGO_BOX_WIDTH`, `LOGO_BOX_HEIGHT`,
     `GOLD_HIGHLIGHT`, `GOLD_SHADOW`) — useful for setting them in Vercel's
     dashboard without touching code.

## Running a batch locally

```bash
python hamper_personalizer.py \
  --base assets/base/hamper_base_clean.jpg \
  --logos assets/logos \
  --csv companies.csv \
  --output output \
  --workers 8
```

All flags are optional and default to the paths in `config.py`. Each row in
`companies.csv` produces `output/<sanitized_company_name>.png`. For each
logo the engine: trims surrounding whitespace/transparency, **recolors it to
the gold foil gradient** (`GOLD_HIGHLIGHT` → `GOLD_SHADOW`, preserving the
logo's own shape/font via its alpha mask), resizes it to fit `LOGO_BOX` while
preserving aspect ratio, and centers it in the box. Companies are processed
in parallel via `ProcessPoolExecutor`.

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
   - `LOGO_BOX_X`, `LOGO_BOX_Y`, `LOGO_BOX_WIDTH`, `LOGO_BOX_HEIGHT` (the real calibrated values)
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
