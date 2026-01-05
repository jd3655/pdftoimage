from pathlib import Path
from typing import List, Optional

import gradio as gr
from PIL import Image

from markitdown_processing import MarkItDownOptions, convert_batch_to_outputs
from processing import CancellationFlag, Settings, preprocess_pil_image, process_inputs
from utils import MARKITDOWN_EXTENSIONS, collect_files_from_zip, filter_supported, is_supported_file

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
    backend_mode: str,
    enable_plugins: bool,
    use_docintel: bool,
    docintel_endpoint: str,
    docintel_key: str,
    use_llm_descriptions: bool,
    llm_provider: str,
    llm_model: str,
    llm_api_key: str,
    llm_prompt: str,
    output_format: str,
    youtube_url: str,
    progress=gr.Progress(track_tqdm=True),
):
    cancel_flag.cancelled = False
    status_lines: List[str] = []

    def cb(fraction: float, desc: str) -> None:
        progress(fraction, desc)
        status_lines.append(f"{fraction*100:.0f}% - {desc}")

    if backend_mode.startswith("MarkItDown"):
        options = MarkItDownOptions(
            enable_plugins=enable_plugins,
            use_docintel=use_docintel,
            docintel_endpoint=docintel_endpoint or None,
            docintel_key=docintel_key or None,
            use_llm_descriptions=use_llm_descriptions,
            llm_provider=llm_provider or None,
            llm_model=llm_model or None,
            llm_prompt=llm_prompt or None,
            llm_api_key=llm_api_key or None,
            output_format=output_format,
            youtube_url=youtube_url or None,
        )
        try:
            zip_path, _, log_text = convert_batch_to_outputs(files, zip_file, options, cb)
            return str(zip_path), log_text
        except Exception as exc:
            return None, f"Error: {exc}\n" + "\n".join(status_lines)
    else:
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
        try:
            zip_path, log_text = process_inputs(files, zip_file, settings, cb, cancel_flag)
            return str(zip_path), log_text
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


def preview_first(files, zip_file, dpi, color_mode, auto_orient, deskew, deskew_sensitivity, contrast_stretch, contrast_percent, trim, adaptive_threshold, mode, backend_mode):
    if backend_mode.startswith("MarkItDown"):
        return None, None, "Preview is only available for Image-first processing."
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
        backend_mode = gr.Radio(
            ["Image-first (existing)", "MarkItDown (document-to-markdown)"],
            value="Image-first (existing)",
            label="Processing Backend",
        )
        accepted_types = sorted(MARKITDOWN_EXTENSIONS)
        with gr.Row():
            with gr.Column(scale=1):
                files_input = gr.Files(
                    label="Add Files",
                    file_count="multiple",
                    type="filepath",
                    file_types=accepted_types,
                )
                zip_input = gr.File(label="Add Folder (ZIP)", type="filepath")
                start_btn = gr.Button("Start Processing", variant="primary")
                cancel_btn = gr.Button("Cancel", variant="stop")
                output_zip = gr.File(label="Download ZIP")
            with gr.Column(scale=1):
                with gr.Tab("Settings"):
                    gr.Markdown("### Image-first options")
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
                    with gr.Accordion("MarkItDown options", open=False):
                        enable_plugins = gr.Checkbox(value=False, label="Enable MarkItDown plugins")
                        use_docintel = gr.Checkbox(value=False, label="Use Azure Document Intelligence")
                        docintel_endpoint = gr.Textbox(label="Document Intelligence endpoint", visible=False)
                        docintel_key = gr.Textbox(label="Document Intelligence key (env override)", type="password", visible=False)
                        use_llm_descriptions = gr.Checkbox(value=False, label="Use LLM for image descriptions")
                        llm_provider = gr.Dropdown(
                            ["OpenAI"],
                            value="OpenAI",
                            label="LLM Provider",
                            visible=False,
                        )
                        llm_model = gr.Textbox(label="LLM model", placeholder="gpt-4o-mini", visible=False)
                        llm_api_key = gr.Textbox(label="LLM API key (optional, uses env if empty)", type="password", visible=False)
                        llm_prompt = gr.Textbox(label="Custom LLM prompt (optional)", lines=3, visible=False)
                        output_format = gr.Radio(
                            ["Markdown only", "Markdown + manifest JSON"],
                            value="Markdown + manifest JSON",
                            label="Output format",
                        )
                        youtube_url = gr.Textbox(label="YouTube URL (optional)", placeholder="https://youtube.com/...")
                with gr.Tab("Preview"):
                    preview_btn = gr.Button("Preview first item")
                    with gr.Row():
                        before_img = gr.Image(label="Before", type="pil")
                        after_img = gr.Image(label="After", type="pil")
                    preview_info = gr.Markdown("Preview info will appear here")
            with gr.Column(scale=1):
                log_box = gr.Textbox(label="Logs", lines=20)

        use_docintel.change(
            lambda enabled: [gr.update(visible=enabled), gr.update(visible=enabled)],
            inputs=use_docintel,
            outputs=[docintel_endpoint, docintel_key],
        )
        use_llm_descriptions.change(
            lambda enabled: [
                gr.update(visible=enabled),
                gr.update(visible=enabled),
                gr.update(visible=enabled),
                gr.update(visible=enabled),
            ],
            inputs=use_llm_descriptions,
            outputs=[llm_provider, llm_model, llm_api_key, llm_prompt],
        )

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
                backend_mode,
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
                backend_mode,
                enable_plugins,
                use_docintel,
                docintel_endpoint,
                docintel_key,
                use_llm_descriptions,
                llm_provider,
                llm_model,
                llm_api_key,
                llm_prompt,
                output_format,
                youtube_url,
            ],
            outputs=[output_zip, log_box],
        )

        cancel_btn.click(cancel_processing, outputs=[log_box])

    demo.queue()
    demo.launch()


if __name__ == "__main__":
    main()
