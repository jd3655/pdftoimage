import threading
import time
import webbrowser

import uvicorn

from .server import DEFAULT_HOST, DEFAULT_PORT


def _open_browser(url: str) -> None:
    time.sleep(1)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> None:
    url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
    print("Starting pdftoimage local web app...")
    print(f"Opening {url} in your browser. Press Ctrl+C to stop.")
    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()
    uvicorn.run("pdftoimage.server:app", host=DEFAULT_HOST, port=DEFAULT_PORT, log_level="info")


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
