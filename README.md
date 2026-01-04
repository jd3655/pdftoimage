# PDF to Image Converter

A local Gradio app that converts multi-page PDFs into per-page PNGs and cleans receipt images for OCR.

## Features
- Upload PDFs or images (JPG, PNG, TIFF, HEIC) and ZIP folders.
- Structured ZIP output with per-PDF folders and receipts directory.
- Collision-safe naming, processing log, and manifest file.
- Preview first item before running full job.
- Balanced and aggressive processing modes with deskew, trimming, and contrast stretch.

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Install Poppler (for PDF rendering):
   ```bash
   brew install poppler
   ```
   Ensure `pdftoppm` is on your `PATH` (typically `/usr/local/opt/poppler/bin` or `/opt/homebrew/opt/poppler/bin`).

### HEIC support
`pillow-heif` is included; if installation fails on your platform, remove it from `requirements.txt` and re-install. HEIC files will be skipped without the plugin.

## Running the app
```bash
python app.py
```
This starts a local Gradio interface in your browser.

## Troubleshooting
- **Poppler missing**: Install via Homebrew (macOS) or your package manager, then ensure the binaries are on `PATH`.
- **OpenCV missing GUI deps**: The app uses headless OpenCV functions only; ensure `opencv-python` installs cleanly.
- **Large inputs**: PDFs are capped at 200 pages and total files at 500 for safety.

## Testing
```bash
pytest
```
