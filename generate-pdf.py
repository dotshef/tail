"""HTML → PDF 변환 스크립트 (Playwright)

Usage:
    python generate-pdf.py <lang> <스토리명>

Example:
    python generate-pdf.py en 여우와 두루미
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if len(sys.argv) != 3:
    print("Usage: python generate-pdf.py <lang> <story_name>")
    sys.exit(1)

lang = sys.argv[1]
story = sys.argv[2]

base = Path("c:/D/tail")
html_path = base / "tail-pdf" / lang / f"{story}.html"
pdf_path = base / "tail-pdf" / lang / f"{story}.pdf"

if not html_path.exists():
    print(f"Error: {html_path} not found")
    sys.exit(1)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(html_path.as_uri(), wait_until="networkidle")
    page.pdf(
        path=str(pdf_path),
        format="A5",
        margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
        print_background=True,
    )
    browser.close()
    print(f"PDF generated: {pdf_path} ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")
