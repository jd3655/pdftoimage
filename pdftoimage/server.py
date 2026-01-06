import base64
import io
import logging
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pdf2image import convert_from_path
from PIL import Image

from markitdown_processing import MarkItDownOptions, convert_batch_to_outputs
from processing import CancellationFlag, Settings, preprocess_pil_image, process_inputs
from utils import MARKITDOWN_EXTENSIONS

LOGGER = logging.getLogger(__name__)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7860
LOG_TAIL = 200
JOB_TTL_SECONDS = 60 * 60 * 6  # 6 hours


def _image_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@dataclass
class Job:
    id: str
    status: str = "queued"
    progress: float = 0.0
    message: str = ""
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    output_zip_path: Optional[Path] = None
    cancel_flag: CancellationFlag = field(default_factory=CancellationFlag)
    workdir: Path = field(default_factory=lambda: Path(tempfile.mkdtemp(prefix="pdftoimage_job_")))
    created_at: float = field(default_factory=time.time)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def log(self, entry: str) -> None:
        with self.lock:
            self.logs.append(entry)

    def set_status(self, status: str, message: str | None = None) -> None:
        with self.lock:
            self.status = status
            if message is not None:
                self.message = message


class JobStore:
    def __init__(self) -> None:
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.Lock()

    def create(self) -> Job:
        job = Job(id=str(uuid.uuid4()))
        with self.lock:
            self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self.lock:
            return self.jobs.get(job_id)

    def cleanup_old_jobs(self) -> None:
        now = time.time()
        expired: List[str] = []
        with self.lock:
            for job_id, job in list(self.jobs.items()):
                if now - job.created_at > JOB_TTL_SECONDS:
                    expired.append(job_id)
                    if job.workdir.exists():
                        shutil.rmtree(job.workdir, ignore_errors=True)
                    if job.output_zip_path and job.output_zip_path.exists():
                        try:
                            job.output_zip_path.unlink()
                        except OSError:
                            pass
                    del self.jobs[job_id]
        if expired:
            LOGGER.debug("Cleaned up jobs: %s", ", ".join(expired))


job_store = JobStore()
app = FastAPI(title="PDF to Image API")


def _configure_cors(application: FastAPI) -> None:
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _attach_static(application: FastAPI) -> None:
    static_dir = Path(__file__).parent / "web" / "dist"
    if static_dir.exists():
        application.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


_configure_cors(app)
_attach_static(app)


def _save_upload(upload: UploadFile, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / (upload.filename or "upload")
    contents = upload.file.read()
    dest.write_bytes(contents)
    return dest


def _save_uploads(uploads: List[UploadFile] | None, target_dir: Path) -> List[str]:
    paths: List[str] = []
    if not uploads:
        return paths
    for upload in uploads:
        paths.append(str(_save_upload(upload, target_dir)))
    return paths


def _move_output(zip_path: Path, job: Job) -> Path:
    destination = job.workdir / zip_path.name
    if zip_path != destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(zip_path), destination)
    return destination


def _run_image_first_job(job: Job, file_paths: List[str], zip_path: Optional[str], settings: Settings) -> None:
    def cb(fraction: float, desc: str) -> None:
        job.progress = fraction
        job.message = desc
        job.log(f"{fraction*100:.0f}% - {desc}")

    zip_out, log_text = process_inputs(file_paths, zip_path, settings, cb, job.cancel_flag)
    job.output_zip_path = _move_output(zip_out, job)
    for line in log_text.splitlines():
        job.log(line)

    if job.cancel_flag.check():
        job.set_status("cancelled", "Cancelled")
    else:
        job.progress = 1.0
        job.set_status("done", "Completed")


def _run_markitdown_job(job: Job, file_paths: List[str], zip_path: Optional[str], options: MarkItDownOptions) -> None:
    def cb(fraction: float, desc: str) -> None:
        job.progress = fraction
        job.message = desc
        job.log(f"{fraction*100:.0f}% - {desc}")

    zip_out, _, log_text = convert_batch_to_outputs(file_paths, zip_path, options, cb)
    job.output_zip_path = _move_output(zip_out, job)
    for line in log_text.splitlines():
        job.log(line)
    job.progress = 1.0
    job.set_status("done", "Completed")


def _start_job_thread(
    job: Job,
    backend_mode: str,
    file_paths: List[str],
    zip_path: Optional[str],
    settings: Settings,
    options: MarkItDownOptions,
) -> None:
    def _runner() -> None:
        job.set_status("running", "Starting")
        try:
            if backend_mode.startswith("MarkItDown"):
                _run_markitdown_job(job, file_paths, zip_path, options)
            else:
                _run_image_first_job(job, file_paths, zip_path, settings)
        except Exception as exc:  # pragma: no cover - runtime errors
            LOGGER.exception("Job %s failed", job.id)
            job.set_status("error", "Failed")
            job.error = str(exc)
            job.log(f"Error: {exc}")

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()


@app.post("/api/jobs")
async def create_job(
    files: List[UploadFile] | None = File(default=None),
    zip_file: UploadFile | None = File(default=None),
    backend_mode: str = Form("Image-first (existing)"),
    dpi: int = Form(400),
    color_mode: str = Form("Grayscale"),
    auto_orient: bool = Form(True),
    deskew: bool = Form(True),
    deskew_sensitivity: float = Form(0.4),
    contrast_stretch: bool = Form(True),
    contrast_percent: float = Form(0.5),
    trim: bool = Form(True),
    adaptive_threshold: bool = Form(False),
    mode: str = Form("Balanced"),
    enable_plugins: bool = Form(False),
    use_docintel: bool = Form(False),
    docintel_endpoint: str = Form(""),
    docintel_key: str = Form(""),
    use_llm_descriptions: bool = Form(False),
    llm_provider: str = Form("OpenAI"),
    llm_model: str = Form(""),
    llm_api_key: str = Form(""),
    llm_prompt: str = Form(""),
    output_format: str = Form("Markdown + manifest JSON"),
    youtube_url: str = Form(""),
):
    job = job_store.create()
    inputs_dir = job.workdir / "inputs"
    file_paths = _save_uploads(files, inputs_dir)
    zip_path: Optional[str] = None
    if zip_file:
        zip_path = str(_save_upload(zip_file, inputs_dir))

    settings = Settings(
        dpi=dpi,
        grayscale=color_mode == "Grayscale",
        auto_orient=auto_orient,
        deskew=deskew,
        deskew_sensitivity=deskew_sensitivity,
        contrast_stretch=contrast_stretch,
        contrast_percent=contrast_percent,
        trim=trim,
        adaptive_threshold=adaptive_threshold,
        mode=mode,
    )
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

    _start_job_thread(job, backend_mode, file_paths, zip_path, settings, options)
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    with job.lock:
        logs_tail = "\n".join(job.logs[-LOG_TAIL:])
        has_download = bool(job.output_zip_path and job.output_zip_path.exists())
        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "error": job.error,
            "has_download": has_download,
            "logs_tail": logs_tail,
        }


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.cancel_flag.cancel()
    job.set_status("cancelled", "Cancellation requested")
    job.log("Cancellation requested")
    return {"ok": True}


@app.get("/api/jobs/{job_id}/download")
async def download_job(job_id: str):
    job = job_store.get(job_id)
    if not job or not job.output_zip_path or not job.output_zip_path.exists():
        raise HTTPException(status_code=404, detail="Output not found")
    return FileResponse(job.output_zip_path, media_type="application/zip", filename=job.output_zip_path.name)


@app.post("/api/preview")
async def preview(
    file: UploadFile = File(...),
    dpi: int = Form(400),
    color_mode: str = Form("Grayscale"),
    auto_orient: bool = Form(True),
    deskew: bool = Form(True),
    deskew_sensitivity: float = Form(0.4),
    contrast_stretch: bool = Form(True),
    contrast_percent: float = Form(0.5),
    trim: bool = Form(True),
    adaptive_threshold: bool = Form(False),
    mode: str = Form("Balanced"),
):
    temp_dir = Path(tempfile.mkdtemp(prefix="pdftoimage_preview_"))
    try:
        saved = _save_upload(file, temp_dir)
        grayscale = color_mode == "Grayscale"
        settings = Settings(
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
        if saved.suffix.lower() == ".pdf":
            pages = convert_from_path(saved, dpi=dpi, fmt="png", first_page=1, last_page=1)
            before = pages[0]
        else:
            before = Image.open(saved)
        after = preprocess_pil_image(before.copy(), settings)
        info = f"Previewing {saved.name} | Mode: {mode} | DPI: {dpi}"
        return {
            "before_png_b64": _image_to_base64(before),
            "after_png_b64": _image_to_base64(after),
            "info": info,
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/api/meta")
async def meta():
    return {"supported_extensions": sorted(MARKITDOWN_EXTENSIONS)}


@app.on_event("startup")
async def _startup() -> None:  # pragma: no cover - side effect only
    def _cleanup_loop() -> None:
        while True:
            time.sleep(600)
            job_store.cleanup_old_jobs()

    threading.Thread(target=_cleanup_loop, daemon=True).start()
