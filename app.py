import tempfile
from pathlib import Path
from typing import List, Optional

import gradio as gr
from PIL import Image

from processing import CancellationFlag, Settings, preprocess_pil_image, process_inputs
from utils import collect_files_from_zip, filter_supported, is_supported_file

cancel_flag = CancellationFlag()


def build_settings(
    dpi: int,
    grayscale: bool,
    auto_orient: bool,
    deskew: bool,
    deskew_sensitivity: float,
    contrast_stretch: bool,
    contrast_percent: float,
    trim: bool,
    adaptive_threshold: bool,
    mode: str,
) -> Settings:
    return Settings(
        dpi=dpi,
        grayscale=grayscale,
        auto_orient=auto_orient,
        deskew=deskew,
        deskew_sensitivity=deskew_sensitivity,
        contrast_stretch=contrast_stretch,
        contrast_percent=contrast_percent,
        trim=trim,
        adaptive_threshold=adaptive_threshold,
        mode=mode,
    )


def start_processing(
    files: List[str] | None,
    zip_file: Optional[str],
    dpi: int,
    color_mode: str,
    auto_orient: bool,
    deskew: bool,
    deskew_sensitivity: float,
    contrast_stretch: bool,
    contrast_percent: float,
    trim: bool,
    adaptive_threshold: bool,
    mode: str,
    progress=gr.Progress(track_tqdm=True),
):
    cancel_flag.cancelled = False
    grayscale = color_mode == "Grayscale"
    settings = build_settings(
        dpi,
        grayscale,
        auto_orient,
        deskew,
        deskew_sensitivity,
        contrast_stretch,
        contrast_percent,
        trim,
        adaptive_threshold,
        mode,
    )

    status_lines: List[str] = []

    def cb(fraction: float, desc: str) -> None:
        progress(fraction, desc)
        status_lines.append(f"{fraction*100:.0f}% - {desc}")

    try:
        zip_path, log_text = process_inputs(files, zip_file, settings, cb, cancel_flag)
        return zip_path, log_text
    except Exception as exc:
        return None, f"Error: {exc}\n" + "\n".join(status_lines)


def cancel_processing():
    cancel_flag.cancel()
    return "Cancellation requested. Current task will stop soon."


def _first_supported(files: List[str] | None, zip_file: Optional[str]) -> Optional[Path]:
    if files:
        filtered = filter_supported(files)
        if filtered:
            return filtered[0]
    if zip_file:
        extracted = collect_files_from_zip(zip_file)
        if extracted:
            return extracted[0]
    return None


def preview_first(files, zip_file, dpi, color_mode, auto_orient, deskew, deskew_sensitivity, contrast_stretch, contrast_percent, trim, adaptive_threshold, mode):
    target = _first_supported(files, zip_file)
    if not target:
        return None, None, "No supported files to preview."

    grayscale = color_mode == "Grayscale"
    settings = build_settings(
        dpi,
        grayscale,
        auto_orient,
        deskew,
        deskew_sensitivity,
        contrast_stretch,
        contrast_percent,
        trim,
        adaptive_threshold,
        mode,
    )

    if target.suffix.lower() == ".pdf":
        from pdf2image import convert_from_path

        pages = convert_from_path(target, dpi=dpi, fmt="png", first_page=1, last_page=1)
        before_img = pages[0]
    else:
        before_img = Image.open(target)

    after_img = preprocess_pil_image(before_img.copy(), settings)
    info = f"Previewing {target.name} | Mode: {mode} | DPI: {dpi}"
    if target.suffix.lower() == ".pdf":
        info += f" | Page size: {before_img.size[0]}x{before_img.size[1]} px"
    return before_img, after_img, info


def main():
    with gr.Blocks(title="PDF/Image to PNG Converter", theme="soft") as demo:
        gr.Markdown("## PDF & Receipt Cleaner\nUpload PDFs or images, adjust quality settings, and download a structured ZIP.")
        with gr.Row():
            with gr.Column(scale=1):
                files_input = gr.Files(label="Add Files", file_count="multiple", type="filepath", file_types=[".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic"])
                zip_input = gr.File(label="Add Folder (ZIP)", type="filepath")
                start_btn = gr.Button("Start Processing", variant="primary")
                cancel_btn = gr.Button("Cancel", variant="stop")
                output_zip = gr.File(label="Download ZIP")
            with gr.Column(scale=1):
                with gr.Tab("Settings"):
                    dpi_radio = gr.Radio([300, 400, 450, 600], value=400, label="PDF DPI")
                    color_mode = gr.Radio(["Grayscale", "Color"], value="Grayscale", label="Color mode")
                    auto_orient = gr.Checkbox(value=True, label="Auto-orient")
                    deskew = gr.Checkbox(value=True, label="Deskew")
                    deskew_sensitivity = gr.Slider(0.0, 1.0, value=0.4, label="Deskew sensitivity")
                    contrast_stretch = gr.Checkbox(value=True, label="Contrast stretch")
                    contrast_percent = gr.Slider(0.2, 2.0, value=0.5, step=0.1, label="Contrast percentile")
                    trim = gr.Checkbox(value=True, label="Trim whitespace")
                    adaptive_threshold = gr.Checkbox(value=False, label="Adaptive threshold (B/W)", info="May hurt thin fonts on digital PDFs")
                    mode = gr.Radio(["Balanced", "Aggressive for scans"], value="Balanced", label="Processing Mode")
                with gr.Tab("Preview"):
                    preview_btn = gr.Button("Preview first item")
                    with gr.Row():
                        before_img = gr.Image(label="Before", type="pil")
                        after_img = gr.Image(label="After", type="pil")
                    preview_info = gr.Markdown("Preview info will appear here")
            with gr.Column(scale=1):
                log_box = gr.Textbox(label="Logs", lines=20)

        preview_btn.click(
            preview_first,
            inputs=[
                files_input,
                zip_input,
                dpi_radio,
                color_mode,
                auto_orient,
                deskew,
                deskew_sensitivity,
                contrast_stretch,
                contrast_percent,
                trim,
                adaptive_threshold,
                mode,
            ],
            outputs=[before_img, after_img, preview_info],
        )

        start_btn.click(
            start_processing,
            inputs=[
                files_input,
                zip_input,
                dpi_radio,
                color_mode,
                auto_orient,
                deskew,
                deskew_sensitivity,
                contrast_stretch,
                contrast_percent,
                trim,
                adaptive_threshold,
                mode,
            ],
            outputs=[output_zip, log_box],
        )

        cancel_btn.click(cancel_processing, outputs=[log_box])

    demo.queue()
    demo.launch()


if __name__ == "__main__":
    main()
