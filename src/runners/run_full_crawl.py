#!/usr/bin/env python3
"""
Clean React Data Extractor

Retry logic:
- Original URL: 3 tries
- Fallback URL: 3 tries

With attempt logs.
"""

import re
import json
import asyncio
import time
import pandas as pd

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright


# ==========================================================
# CONFIG
# ==========================================================
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

TIMEOUT_MS = 20000
WAIT_MS = 2500


# ==========================================================
# HELPERS
# ==========================================================
def extract_html_metadata(html: str) -> Dict[str, Any]:
    result = {}

    m = re.search(
        r'<meta\s+itemprop="priceCurrency"\s+content="([^"]+)"',
        html,
        re.IGNORECASE
    )
    if m:
        result["priceCurrency"] = m.group(1)

    m = re.search(
        r'<span\s+class="discount-value"[^>]*>([^<]+)</span>',
        html,
        re.IGNORECASE
    )
    if m:
        raw = m.group(1).strip()
        num = re.search(r"(\d+(?:\.\d+)?)", raw)

        if num:
            val = num.group(1)
            result["discount-value"] = float(val) if "." in val else int(val)

    return result


def extract_react_data(html: str) -> Optional[Dict[str, Any]]:
    pattern = r'(?:var|let|const)\s+react_data\s*=\s*(\{.*?\});'
    m = re.search(pattern, html, re.DOTALL)

    if not m:
        return None

    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def build_fallback_url(product_id: str) -> str:
    return f"https://www.glamira.com/catalog/product/view/id/{product_id}"


async def fetch_with_retry(page, url, product_id, label, retries=3):
    for attempt in range(1, retries + 1):
        try:
            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=TIMEOUT_MS
            )

            await page.wait_for_timeout(WAIT_MS)
            html = await page.content()

            print(
                f"[{product_id}] {label} try {attempt}/{retries} success",
                flush=True
            )

            return html

        except Exception:
            print(
                f"[{product_id}] {label} try {attempt}/{retries} failed",
                flush=True
            )

            if attempt == retries:
                return None

            await page.wait_for_timeout(1000 * attempt)


# ==========================================================
# BATCH
# ==========================================================
async def process_batch_csv(
    input_file="output/products.csv",
    output_dir="output_crawl",
    max_concurrent=8,
    chunk_size=100
):
    df = pd.read_csv(input_file)

    sem = asyncio.Semaphore(max_concurrent)
    started_at = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        async def worker(row):
            async with sem:
                product_id = str(row["product_id"])
                url = str(row["url"])
                used_fallback = False

                page = await browser.new_page(user_agent=USER_AGENT)

                try:
                    html = await fetch_with_retry(
                        page, url, product_id, "original", 3
                    )

                    react_data = extract_react_data(html or "")
                    valid = isinstance(react_data, dict) and bool(
                        react_data.get("name")
                    )

                    if not valid:
                        used_fallback = True

                        fallback = build_fallback_url(product_id)

                        html = await fetch_with_retry(
                            page, fallback, product_id, "fallback", 3
                        )

                        react_data = extract_react_data(html or "")
                        valid = isinstance(react_data, dict) and bool(
                            react_data.get("name")
                        )

                    metadata = extract_html_metadata(html or "")

                    result = {
                        "product_id": product_id,
                        "url": url,
                        "success": valid,
                        "fall_back": used_fallback,
                        "crawled_at": datetime.now().isoformat()
                    }

                    if valid:
                        for key in [
                            "name",
                            "sku",
                            "price",
                            "product_type",
                            "gender",
                            "type_id",
                            "collection",
                        ]:
                            if key in react_data:
                                result[key] = react_data[key]

                    result.update(metadata)
                    return result

                except Exception as e:
                    return {
                        "product_id": product_id,
                        "url": url,
                        "success": False,
                        "fall_back": used_fallback,
                        "error": str(e),
                        "crawled_at": datetime.now().isoformat()
                    }

                finally:
                    await page.close()

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        total = len(df)
        ok = fail = processed = 0
        success_part = error_part = 1

        for start in range(0, total, chunk_size):
            batch = df.iloc[start:start + chunk_size]

            tasks = [worker(row) for _, row in batch.iterrows()]
            results = await asyncio.gather(*tasks)

            success_rows = []
            error_rows = []

            for item in results:
                processed += 1

                if item["success"]:
                    ok += 1
                    success_rows.append(item)
                else:
                    fail += 1
                    error_rows.append(item)

                elapsed = max(time.time() - started_at, 1)
                rate = processed / elapsed
                remain = total - processed
                eta = int(remain / rate)

                print(
                    f"[{processed:,}/{total:,}] "
                    f"{processed/total*100:5.1f}% | "
                    f"ok={ok:,} | fail={fail:,} | "
                    f"ETA={eta//60}m {eta%60}s",
                    flush=True
                )

            if success_rows:
                pd.DataFrame(success_rows).to_csv(
                    f"{output_dir}/react_batch_part_{success_part:04d}.csv",
                    index=False,
                    encoding="utf-8-sig"
                )
                success_part += 1

            if error_rows:
                pd.DataFrame(error_rows).to_csv(
                    f"{output_dir}/react_batch_error_part_{error_part:04d}.csv",
                    index=False,
                    encoding="utf-8-sig"
                )
                error_part += 1

        await browser.close()

    print(
        f"✅ Done: success={ok:,} fail={fail:,}",
        flush=True
    )


# ==========================================================
# MAIN
# ==========================================================
def main():
    # Project root: .../prj5-gcp
    BASE_DIR = Path(__file__).resolve().parents[2]

    INPUT_FILE = BASE_DIR / "output" / "products.csv"
    OUTPUT_DIR = BASE_DIR / "output_crawl"

    print(f"Input file : {INPUT_FILE}")
    print(f"Output dir : {OUTPUT_DIR}")

    asyncio.run(
        process_batch_csv(
            input_file=str(INPUT_FILE),
            output_dir=str(OUTPUT_DIR),
            max_concurrent=8,
            chunk_size=100,
        )
    )

if __name__ == "__main__":
    main()
    
    # nohup python -u src/runners/run_full_crawl.py > logs/crawl.log 2>&1 &