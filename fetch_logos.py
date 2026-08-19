"""
Fetches company logos programmatically instead of via AI web browsing, so a
large company list doesn't burn AI usage searching for logos one at a time.
This is a plain script - running it costs nothing beyond normal internet
bandwidth, no matter how many companies are in the list.

Tries, per company, in order:
  1. Wikidata's structured "logo image" property (P154) - most accurate,
     works for any company with a Wikidata entry. Rendered via Wikimedia
     Commons' thumbnail API so SVG sources come back as a raster image
     Pillow can actually open.
  2. Wikipedia's page-image API - a looser fallback (the article's lead
     image, not guaranteed to be the logo specifically).
  3. A favicon service, using the domain Clearbit's autocomplete API can
     still resolve even though its old free logo endpoint was shut down -
     low quality, but works for almost any company with a real website.

Anything none of these find is left for manual sourcing and reported at
the end.

Usage:
    python fetch_logos.py --names company_names.txt
"""
import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Optional

import requests

import config
from hamper_personalizer import sanitize_filename

CLEARBIT_SUGGEST_URL = "https://autocomplete.clearbit.com/v1/companies/suggest"
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
FAVICON_URL = "https://www.google.com/s2/favicons"
USER_AGENT = "hamper-personalizer-logo-fetch/1.0 (internal tool)"

HEADERS = {"User-Agent": USER_AGENT}


def fetch_clearbit_domain(company_name: str) -> Optional[str]:
    try:
        resp = requests.get(CLEARBIT_SUGGEST_URL, params={"query": company_name},
                             headers=HEADERS, timeout=10)
        resp.raise_for_status()
        results = resp.json()
    except Exception:  # noqa: BLE001
        return None
    return results[0].get("domain") if results else None


def fetch_via_wikidata(company_name: str) -> Optional[str]:
    """Look up the company's Wikidata entity, read its P154 (logo image)
    claim if set, and resolve that Commons file to a raster thumbnail URL."""
    try:
        resp = requests.get(WIKIDATA_SEARCH_URL, params={
            "action": "wbsearchentities", "search": company_name,
            "language": "en", "format": "json", "type": "item", "limit": 1,
        }, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        matches = resp.json().get("search", [])
        if not matches:
            return None
        qid = matches[0]["id"]

        resp = requests.get(WIKIDATA_ENTITY_URL.format(qid=qid), headers=HEADERS, timeout=10)
        resp.raise_for_status()
        claims = resp.json()["entities"][qid].get("claims", {})
        logo_claim = claims.get("P154")
        if not logo_claim:
            return None
        commons_filename = logo_claim[0]["mainsnak"]["datavalue"]["value"]

        resp = requests.get(COMMONS_API_URL, params={
            "action": "query", "titles": f"File:{commons_filename}",
            "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 800, "format": "json",
        }, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            imageinfo = page.get("imageinfo")
            if imageinfo:
                return imageinfo[0].get("thumburl") or imageinfo[0].get("url")
    except Exception:  # noqa: BLE001
        return None
    return None


def fetch_via_wikipedia_thumbnail(company_name: str) -> Optional[str]:
    try:
        resp = requests.get(WIKIPEDIA_API_URL, params={
            "action": "query", "titles": company_name, "prop": "pageimages",
            "format": "json", "pithumbsize": 500,
        }, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            thumbnail = page.get("thumbnail")
            if thumbnail:
                return thumbnail.get("source")
    except Exception:  # noqa: BLE001
        return None
    return None


def fetch_via_favicon(domain: Optional[str]) -> Optional[str]:
    if not domain:
        return None
    return f"{FAVICON_URL}?domain={domain}&sz=256"


def guess_extension(url: str) -> str:
    lower = url.lower().split("?")[0]
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if lower.endswith(ext):
            return ext
    return ".png"


def download_image(url: str, dest_path: Path) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        if len(resp.content) < 200:  # suspiciously small - likely a broken placeholder
            return False
        dest_path.write_bytes(resp.content)
        return True
    except Exception:  # noqa: BLE001
        return False


def fetch_logo_for_company(company_name: str, logos_dir: Path) -> tuple[Optional[str], str]:
    """Returns (logo_filename, method)."""
    domain = fetch_clearbit_domain(company_name)

    for method_name, url in (
        ("wikidata", fetch_via_wikidata(company_name)),
        ("wikipedia", fetch_via_wikipedia_thumbnail(company_name)),
        ("favicon", fetch_via_favicon(domain)),
    ):
        if not url:
            continue
        filename = f"{sanitize_filename(company_name)}{guess_extension(url)}"
        if download_image(url, logos_dir / filename):
            return filename, method_name
    return None, "failed"


def update_companies_csv(csv_path: Path, rows: list[tuple[str, str]]) -> None:
    existing_names = set()
    file_exists = csv_path.exists()
    if file_exists:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_names.add(row["company_name"].strip().lower())

    new_rows = [(name, filename) for name, filename in rows
                if name.strip().lower() not in existing_names]
    if not new_rows:
        return

    with open(csv_path, "a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["company_name", "logo_filename"])
        writer.writerows(new_rows)


def main():
    parser = argparse.ArgumentParser(description="Fetch company logos programmatically (no AI browsing).")
    parser.add_argument("--names", type=Path, required=True, help="Text file, one company name per line")
    parser.add_argument("--logos", type=Path, default=config.LOGOS_DIR)
    parser.add_argument("--csv", type=Path, default=config.COMPANIES_CSV)
    args = parser.parse_args()

    if not args.names.exists():
        print(f"Error: {args.names} not found", file=sys.stderr)
        sys.exit(1)

    company_names = [line.strip() for line in args.names.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.logos.mkdir(parents=True, exist_ok=True)

    succeeded_rows = []
    failed_names = []

    for company_name in company_names:
        filename, method = fetch_logo_for_company(company_name, args.logos)
        if filename:
            print(f"  OK      {company_name} -> {filename} (via {method})")
            succeeded_rows.append((company_name, filename))
        else:
            print(f"  FAILED  {company_name} (no logo found via any method)")
            failed_names.append(company_name)
        time.sleep(0.2)  # be polite to the free APIs

    if succeeded_rows:
        update_companies_csv(args.csv, succeeded_rows)

    print(f"\nFetched {len(succeeded_rows)}/{len(company_names)} logos.")
    if failed_names:
        print("Need manual logos for:")
        for name in failed_names:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
