#!/usr/bin/env python3
"""
Clean React Data Extractor
Only extracts:
- react_data
- priceCurrency
- discount-value

Modes:
1) Single URL:
   python react_data_extractor.py

2) Batch CSV:
   python react_data_extractor.py input.csv

CSV required columns:
product_id,url
"""

import sys
import re
import json
import asyncio
import time
import pandas as pd

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright
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
    """
    Extract:
    - priceCurrency
    - discount-value
    """
    result = {}

    currency_match = re.search(
        r'<meta\s+itemprop="priceCurrency"\s+content="([^"]+)"',
        html,
        re.IGNORECASE,
    )
    if currency_match:
        result["priceCurrency"] = currency_match.group(1)

    discount_match = re.search(
        r'<span\s+class="discount-value"[^>]*>([^<]+)</span>',
        html,
        re.IGNORECASE,
    )

    if discount_match:
        raw = discount_match.group(1).strip()

        num = re.search(r"(\d+(?:\.\d+)?)", raw)
        if num:
            val = num.group(1)
            result["discount-value"] = float(val) if "." in val else int(val)

    return result


def extract_react_data(html: str) -> Optional[Dict[str, Any]]:
    """
    Extract JS:
    var react_data = {...}
    """
    pattern = r'(?:var|let|const)\s+react_data\s*=\s*(\{.*?\});'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except Exception:
        return None


def build_fallback_url(product_id: str) -> str:
    return f"https://www.glamira.com/catalog/product/view/id/{product_id}"


# ==========================================================
# SINGLE MODE
# ==========================================================
class ReactDataExtractor:
    def __init__(self, timeout_ms: int = TIMEOUT_MS):
        self.timeout_ms = timeout_ms

    def fetch_html(self, url: str) -> Optional[str]:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=USER_AGENT)

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms
                )

                page.wait_for_timeout(WAIT_MS)

                html = page.content()
                browser.close()
                return html

        except Exception:
            return None

    def extract_from_url(
        self,
        url: str,
        output_file: str = "output/glamira_react_data_full.json"
    ) -> Dict[str, Any]:

        html = self.fetch_html(url)

        if not html:
            return {}

        react_data = extract_react_data(html)
        metadata = extract_html_metadata(html)

        result = {
            "react_data": react_data,
            "html_metadata": metadata
        }

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return result


# ==========================================================
# BATCH CSV MODE
# ==========================================================
async def process_batch_csv(
    input_file: str,
    output_file: str = "output/react_batch.jsonl",
    max_concurrent: int = 8,
    chunk_size: int = 100
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
                    # ----------------------------------
                    # Try original URL
                    # ----------------------------------
                    html = None

                    try:
                        await page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=TIMEOUT_MS
                        )
                        await page.wait_for_timeout(WAIT_MS)
                        html = await page.content()
                    except Exception:
                        pass

                    react_data = extract_react_data(html or "")
                    valid = isinstance(react_data, dict) and bool(react_data.get("name"))

                    # ----------------------------------
                    # Fallback
                    # ----------------------------------
                    if not valid:
                        used_fallback = True
                        fallback = build_fallback_url(product_id)

                        try:
                            await page.goto(
                                fallback,
                                wait_until="domcontentloaded",
                                timeout=TIMEOUT_MS
                            )
                            await page.wait_for_timeout(WAIT_MS)

                            html = await page.content()
                            react_data = extract_react_data(html or "")
                            valid = isinstance(react_data, dict) and bool(react_data.get("name"))

                        except Exception:
                            pass

                    # ----------------------------------
                    # Metadata
                    # ----------------------------------
                    metadata = extract_html_metadata(html or "")

                    # ----------------------------------
                    # Build result
                    # ----------------------------------
                    result = {
                        "product_id": product_id,
                        "url": url,
                        "success": valid,
                        "fall_back": used_fallback,
                        "crawled_at": datetime.now().isoformat()
                    }

                    if valid:
                        wanted = [
                            "name",
                            "sku",
                            "price",
                            "product_type",
                            "gender",
                            "type_id",
                            "collection",
                        ]

                        for field in wanted:
                            if field in react_data:
                                result[field] = react_data[field]

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

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        total = len(df)
        ok = 0
        fail = 0
        processed = 0
        success_buffer = []
        error_buffer = []
        success_part = 1
        error_part = 1

        for start in range(0, total, chunk_size):
            batch_df = df.iloc[start:start + chunk_size]
            tasks = [worker(row) for _, row in batch_df.iterrows()]
            batch_results = await asyncio.gather(*tasks)

            for item in batch_results:
                processed += 1
                if item.get("success"):
                    success_buffer.append(item)
                    ok += 1
                else:
                    error_buffer.append(item)
                    fail += 1

                elapsed = max(time.time() - started_at, 1)
                rate = processed / elapsed
                remaining = total - processed
                eta_sec = int(remaining / rate) if rate > 0 else 0
                eta_min = eta_sec // 60
                eta_rem = eta_sec % 60
                pct = (processed / total) * 100
                print(f"[{processed:,}/{total:,}] {pct:5.1f}% | ok={ok:,} | fail={fail:,} | ETA={eta_min}m {eta_rem}s", flush=True)

            if success_buffer:
                chunk_path = out_dir / f"react_batch_part_{success_part:04d}.csv"
                t0 = time.time()
                pd.DataFrame(success_buffer).to_csv(chunk_path, index=False, encoding="utf-8-sig")
                took = time.time() - t0
                print(f"💾 Saved success checkpoint #{success_part}: {len(success_buffer)} rows -> {chunk_path.name} ({took:.1f}s)", flush=True)
                success_part += 1
                success_buffer = []

            if error_buffer:
                chunk_path = out_dir / f"react_batch_error_part_{error_part:04d}.csv"
                t0 = time.time()
                pd.DataFrame(error_buffer).to_csv(chunk_path, index=False, encoding="utf-8-sig")
                took = time.time() - t0
                print(f"💾 Saved error checkpoint #{error_part}: {len(error_buffer)} rows -> {chunk_path.name} ({took:.1f}s)", flush=True)
                error_part += 1
                error_buffer = []

            done = min(start + chunk_size, total)
            print(f"---- Batch completed: {done:,}/{total:,} ----", flush=True)

        await browser.close()

    print(f"✅ Batch done: {ok:,}/{total:,} success, {fail:,} failed -> {out_dir}", flush=True)


# ==========================================================
# MAIN
# ==========================================================
def main():
    input_csv = "output/products.csv"
    output_dir = "output_crawl"

    asyncio.run(
        process_batch_csv(
            input_file=input_csv,
            output_file=output_dir
        )
    )


if __name__ == "__main__":
    main()
    
    # nohup python -u src/runners/run_full_crawl.py > logs/crawl.log 2>&1 &