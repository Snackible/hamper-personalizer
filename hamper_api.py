"""
FastAPI wrapper around the batch engine.

Endpoints:
    POST /batch-process        Trigger a batch run on demand.
    GET  /cron/batch-process   Same batch run, wired up for Vercel Cron.

Local dev:
    uvicorn hamper_api:app --reload

Note: email sending (SendGrid/SMTP) is intentionally NOT wired up yet - these
endpoints only regenerate personalized images into OUTPUT_DIR.
"""
import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import config
from hamper_personalizer import run_batch

app = FastAPI(title="Hamper Personalizer")


class BatchResponse(BaseModel):
    processed: int
    succeeded: int
    failed: int
    errors: list[dict]


def _run_batch_job() -> BatchResponse:
    try:
        results = run_batch(
            base_image_path=config.BASE_IMAGE_PATH,
            logos_dir=config.LOGOS_DIR,
            csv_path=config.COMPANIES_CSV,
            output_dir=config.OUTPUT_DIR,
            box=config.LOGO_BOX,
            padding=config.LOGO_PADDING,
            workers=int(os.environ.get("BATCH_WORKERS", 4)),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    return BatchResponse(
        processed=len(results),
        succeeded=len(succeeded),
        failed=len(failed),
        errors=[{"company_name": r.company_name, "error": r.error} for r in failed],
    )


@app.post("/batch-process", response_model=BatchResponse)
def batch_process() -> BatchResponse:
    return _run_batch_job()


@app.get("/cron/batch-process", response_model=BatchResponse)
def cron_batch_process(authorization: str | None = Header(default=None)) -> BatchResponse:
    """Vercel Cron hits this with `Authorization: Bearer <CRON_SECRET>` when
    the CRON_SECRET env var is configured on the project. See:
    https://vercel.com/docs/cron-jobs/manage-cron-jobs#securing-cron-jobs
    """
    cron_secret = os.environ.get("CRON_SECRET")
    if cron_secret:
        expected = f"Bearer {cron_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    return _run_batch_job()
