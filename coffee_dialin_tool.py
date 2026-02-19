#!/usr/bin/env python3
"""Coffee dial-in recorder.

Reads text from coffee bag and espresso machine screen images, infers dial-in
fields, and appends a row to a CSV log.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
from pathlib import Path

HEADERS = [
    "Coffee Brand",
    "Flavor Name",
    "Region(s)",
    "Taste Notes",
    "Grand Size",
    "Grind Time",
    "Re-buy?",
    "Review Notes",
]


def run_tesseract(image_path: Path) -> str:
    """Extract text from an image via Tesseract OCR."""
    if shutil.which("tesseract") is None:
        raise RuntimeError(
            "Tesseract is not installed. Install it or use --bag-text/--screen-text."
        )

    cmd = ["tesseract", str(image_path), "stdout", "--psm", "6"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"tesseract failed on {image_path}: {result.stderr.strip()}")
    return result.stdout.strip()


def parse_screen_text(screen_text: str) -> tuple[str, str]:
    """Try to infer grind size and grind time from machine OCR text."""
    grind_size = ""
    grind_time = ""

    # common patterns like "Grind Size 14" or "Size: 14"
    size_match = re.search(r"(?:grind\s*size|size)\s*[:\-]?\s*(\d{1,2})", screen_text, re.I)
    if size_match:
        grind_size = size_match.group(1)
    else:
        # fallback to likely standalone small integer
        fallback_size = re.findall(r"\b([1-2]?\d)\b", screen_text)
        if fallback_size:
            grind_size = fallback_size[0]

    # patterns like "Time 18.5" or "18.5s"
    time_match = re.search(
        r"(?:grind\s*time|time)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)",
        screen_text,
        re.I,
    )
    if not time_match:
        time_match = re.search(r"\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:s|sec|seconds)\b", screen_text, re.I)
    if time_match:
        grind_time = time_match.group(1)

    return grind_size, grind_time


def parse_bag_text(bag_text: str) -> tuple[str, str, str, str]:
    """Heuristic parser for coffee bag details."""
    lines = [ln.strip() for ln in bag_text.splitlines() if ln.strip()]

    coffee_brand = lines[0] if lines else ""
    flavor_name = lines[1] if len(lines) > 1 else ""

    region_patterns = [
        r"(?:region|origin|origins?)\s*[:\-]\s*(.+)",
        r"(ethiopia|colombia|guatemala|kenya|brazil|peru|rwanda|honduras|nicaragua)",
    ]
    region = ""
    for ln in lines:
        for pat in region_patterns:
            m = re.search(pat, ln, re.I)
            if m:
                region = m.group(1) if m.lastindex else m.group(0)
                break
        if region:
            break

    taste = ""
    for ln in lines:
        m = re.search(r"(?:notes?|taste\s*notes?)\s*[:\-]\s*(.+)", ln, re.I)
        if m:
            taste = m.group(1)
            break

    return coffee_brand, flavor_name, region, taste


def prompt_if_missing(label: str, value: str) -> str:
    if value:
        return value
    return input(f"{label}: ").strip()


def append_row(csv_path: Path, row: dict[str, str]) -> None:
    csv_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        if not csv_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Record espresso dial-in data from coffee bag + espresso machine screen photos"
        )
    )
    parser.add_argument("--bag-image", type=Path, help="Path to coffee bag photo")
    parser.add_argument("--screen-image", type=Path, help="Path to machine screen photo")
    parser.add_argument(
        "--bag-text",
        type=str,
        default="",
        help="Optional extracted text for bag image (skip OCR for bag)",
    )
    parser.add_argument(
        "--screen-text",
        type=str,
        default="",
        help="Optional extracted text for machine screen image (skip OCR for screen)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("espresso_reviews.csv"),
        help="Output CSV path",
    )

    args = parser.parse_args()

    if not args.bag_text and not args.bag_image:
        parser.error("Provide --bag-image or --bag-text")
    if not args.screen_text and not args.screen_image:
        parser.error("Provide --screen-image or --screen-text")

    bag_text = args.bag_text
    if not bag_text and args.bag_image:
        bag_text = run_tesseract(args.bag_image)

    screen_text = args.screen_text
    if not screen_text and args.screen_image:
        screen_text = run_tesseract(args.screen_image)

    coffee_brand, flavor_name, regions, taste_notes = parse_bag_text(bag_text)
    grind_size, grind_time = parse_screen_text(screen_text)

    print("\nPlease confirm/correct extracted fields (press Enter to keep value):")
    coffee_brand = prompt_if_missing("Coffee Brand", coffee_brand)
    flavor_name = prompt_if_missing("Flavor Name", flavor_name)
    regions = prompt_if_missing("Region(s)", regions)
    taste_notes = prompt_if_missing("Taste Notes", taste_notes)
    grind_size = prompt_if_missing("Grand Size", grind_size)
    grind_time = prompt_if_missing("Grind Time", grind_time)
    rebuy = prompt_if_missing("Re-buy? (yes/no)", "")
    review_notes = prompt_if_missing("Review Notes", "")

    row = {
        "Coffee Brand": coffee_brand,
        "Flavor Name": flavor_name,
        "Region(s)": regions,
        "Taste Notes": taste_notes,
        "Grand Size": grind_size,
        "Grind Time": grind_time,
        "Re-buy?": rebuy,
        "Review Notes": review_notes,
    }

    append_row(args.csv, row)
    print(f"\nSaved to {args.csv}")


if __name__ == "__main__":
    main()
