# hello-world

Coffee dial-in helper for logging espresso experiments from photos.

## What this tool does

`coffee_dialin_tool.py` reads:
- a photo of your coffee bag, and
- a photo of your Breville espresso maker screen,

then extracts data and appends a row to a CSV spreadsheet with these columns:

- Coffee Brand
- Flavor Name
- Region(s)
- Taste Notes
- Grand Size
- Grind Time
- Re-buy?
- Review Notes

> Note: The requested column name is kept as **"Grand Size"** to match your schema exactly.

## Requirements

- Python 3.9+
- Optional but recommended: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

If Tesseract is not installed, you can still pass `--bag-text` and `--screen-text` manually.

## Usage

### 1) Run with images (OCR)

```bash
python3 coffee_dialin_tool.py \
  --bag-image ./photos/beans.jpg \
  --screen-image ./photos/breville-screen.jpg \
  --csv ./espresso_reviews.csv
```

### 2) Run with manually supplied text

```bash
python3 coffee_dialin_tool.py \
  --bag-text "Acme Roasters\nVelvet Moon\nOrigin: Colombia\nNotes: Chocolate, Citrus" \
  --screen-text "Grind Size 14 Time 18.5s" \
  --csv ./espresso_reviews.csv
```

The tool prompts you to confirm/edit values before saving the row.

## Output

A CSV file (default: `espresso_reviews.csv`) containing one row per brew review.
