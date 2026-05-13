#!/usr/bin/env python3
"""Convert presentation.html slides to a multi-page PDF.

Usage:
    python scripts/slides_to_pdf.py                          # default paths
    python scripts/slides_to_pdf.py presentation.html out.pdf
    python scripts/slides_to_pdf.py --width 1920 --height 1080 ...

Requires:
    pip install playwright pillow
    playwright install chromium
"""

import asyncio
import io
import sys
from argparse import ArgumentParser
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright


async def capture_slides(html_path: Path, width: int, height: int) -> list[Image.Image]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})

        await page.goto(html_path.as_uri())
        await page.wait_for_load_state("networkidle")

        total: int = await page.evaluate(
            "document.querySelectorAll('.slide').length"
        )
        print(f"Found {total} slides at {width}×{height}")

        images: list[Image.Image] = []
        for i in range(total):
            # Directly toggle .active — avoids relying on the scoped go() function
            await page.evaluate(f"""
                document.querySelectorAll('.slide').forEach((s, j) => {{
                    s.classList.toggle('active', j === {i});
                }});
            """)
            await page.wait_for_timeout(120)  # let CSS transitions settle
            png_bytes = await page.screenshot(type="png")
            images.append(Image.open(io.BytesIO(png_bytes)).convert("RGB"))
            print(f"  [{i+1:02d}/{total}] captured")

        await browser.close()
    return images


def save_pdf(images: list[Image.Image], out_path: Path) -> None:
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        resolution=150,
    )
    print(f"Saved → {out_path}  ({len(images)} pages)")


async def main() -> None:
    parser = ArgumentParser(description="Export HTML slides to PDF")
    parser.add_argument("html",  nargs="?", default="presentation.html")
    parser.add_argument("pdf",   nargs="?", default="presentation.pdf")
    parser.add_argument("--width",  type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args()

    html_path = Path(args.html).resolve()
    out_path  = Path(args.pdf).resolve()

    if not html_path.exists():
        sys.exit(f"File not found: {html_path}")

    images = await capture_slides(html_path, args.width, args.height)
    save_pdf(images, out_path)


if __name__ == "__main__":
    asyncio.run(main())
