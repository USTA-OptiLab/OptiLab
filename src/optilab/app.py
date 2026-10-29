import os
import sys
from pathlib import Path

import numpy as np
import webview
from scipy import stats

from optilab import doubolfeis_metod

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
DIST_INDEX = FRONTEND_DIR / "dist" / "index.html"
DEV_SERVER_URL = "http://localhost:5173"


class Api:
    def describe(self, values):
        data = np.asarray(values, dtype=float)
        return {
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "zscores": stats.zscore(data).tolist(),
        }

    def two_phase(self, problem):
        try:
            return doubolfeis_metod.solve(problem)
        except (KeyError, ValueError, ZeroDivisionError, RuntimeError) as exc:
            return {"status": "error", "message": str(exc)}


def main():
    url = (
        DEV_SERVER_URL
        if os.environ.get("OPTILAB_DEV") or not DIST_INDEX.exists()
        else str(DIST_INDEX)
    )
    webview.create_window("OptiLab", url, js_api=Api())
    # pywebview forces the Qt backend on any KDE session regardless of what's
    # installed; we only have GTK/WebKit bindings, so pin the GTK backend.
    # On Windows/macOS let pywebview pick the native backend (WebView2/Cocoa).
    webview.start(gui="gtk" if sys.platform.startswith("linux") else None)


if __name__ == "__main__":
    main()
