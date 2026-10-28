"""Run the graphical method page in its own pywebview window."""

from __future__ import annotations

import os
from pathlib import Path

import webview

from .api import GraphicMethodApi

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"
DIST_PAGE = FRONTEND_DIR / "dist" / "graphic-method.html"
DEV_PAGE = "http://localhost:5173/graphic-method.html"


def main() -> None:
    url = (
        DEV_PAGE
        if os.environ.get("OPTILAB_DEV") or not DIST_PAGE.exists()
        else str(DIST_PAGE)
    )
    webview.create_window(
        "OptiLab · Método Gráfico",
        url,
        js_api=GraphicMethodApi(),
        width=1440,
        height=920,
        min_size=(1000, 700),
    )
    webview.start(gui="gtk", http_server=True)


if __name__ == "__main__":
    main()
