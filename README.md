# PDF to Image & Document Converter

A local Gradio app that converts multi-page PDFs into per-page PNGs, cleans receipt images for OCR, **and now converts many document types to Markdown using Microsoft's MarkItDown**.

## Features
- Upload PDFs or images (JPG, PNG, TIFF, HEIC) and ZIP folders.
- New MarkItDown backend for document-to-markdown conversion that supports Office docs, HTML, text formats, audio metadata/transcription, EPUB, and more (via `markitdown[all]` routing).
- Structured ZIP output with per-PDF folders and receipts directory for the image-first path, plus Markdown outputs with manifest and logs for MarkItDown.
- Collision-safe naming, processing log, and manifest file.
- Preview first item before running full job (image-first pipeline).
- Balanced and aggressive processing modes with deskew, trimming, and contrast stretch.
- Optional MarkItDown plugins, Azure Document Intelligence support, LLM-assisted image descriptions, and YouTube URL ingestion.

## Processing backends
- **Image-first (existing)**: PDFs -> per-page PNGs using Poppler, images cleaned for OCR. Produces a ZIP with `receipts/`, per-PDF folders, `processing_log.txt`, and `manifest.json`.
- **MarkItDown (document-to-markdown)**: Routes each file (or YouTube URL) through MarkItDown to produce Markdown. Outputs per-item `.md` files, `manifest.json`, `markdown_manifest.json` (markdown + metadata), and `processing.log`/`processing_log.txt` packaged into a ZIP.

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Install Poppler (for PDF rendering in the image-first path):
   ```bash
   brew install poppler
   ```
   Ensure `pdftoppm` is on your `PATH` (typically `/usr/local/opt/poppler/bin` or `/opt/homebrew/opt/poppler/bin`). The MarkItDown backend can operate without Poppler for many formats.

### Optional integrations
- **Azure Document Intelligence**: Enable in the UI and provide the endpoint; set `AZURE_DOCUMENT_INTELLIGENCE_KEY` (or fill the key field) so MarkItDown can call the service.
- **LLM image descriptions**: Enable in the UI, choose OpenAI, provide a model (e.g., `gpt-4o-mini`) and API key (or set `OPENAI_API_KEY`). An optional custom prompt is supported.
- **Plugins**: Toggle "Enable MarkItDown plugins" in the UI to allow MarkItDown to run installed plugins.
- **YouTube**: Supply a YouTube URL in the MarkItDown options to ingest transcripts via MarkItDown’s YouTube support.

### HEIC support
`pillow-heif` is included; if installation fails on your platform, remove it from `requirements.txt` and re-install. HEIC files will be skipped without the plugin.

## Running the app
```bash
python app.py
```
This starts a local Gradio interface in your browser. Choose a processing backend, upload files (or a ZIP), optionally add a YouTube URL, and download the resulting ZIP.

## Output examples
- **Image-first**:
  ```
  output.zip/
    receipts/
      receipt.png
    my_pdf/
      my_pdf_page_001.png
    processing_log.txt
    manifest.json
  ```
- **MarkItDown**:
  ```
  output.zip/
    sample.md
    folder/page.md
    manifest.json
    markdown_manifest.json
    processing.log
  ```

## Troubleshooting
- **Poppler missing**: Install via Homebrew (macOS) or your package manager, then ensure the binaries are on `PATH` for the image-first flow.
- **OpenCV missing GUI deps**: The app uses headless OpenCV functions only; ensure `opencv-python` installs cleanly.
- **Large inputs**: PDFs are capped at 200 pages and total files at 500 for safety. ZIP extraction is zip-slip safe.

## Testing
```bash
pytest
```
