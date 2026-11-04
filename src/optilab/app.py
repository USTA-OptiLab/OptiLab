import os
from pathlib import Path

import numpy as np
import webview
from scipy import stats

from optilab.vogel_method import solve_vogel

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

    def solve_vogel(self, problem):
        """Run Vogel's approximation; return JSON-safe values through pywebview."""
        try:
            if not isinstance(problem, dict):
                raise TypeError(
                    "El problema debe ser un objeto con costos, oferta y demanda."
                )
            if not isinstance(problem.get("maximize", False), bool):
                raise TypeError("El objetivo debe ser minimización o maximización.")
            result = solve_vogel(
                problem["costs"],
                problem["supply"],
                problem["demand"],
                maximize=problem.get("maximize", False),
                context=problem.get("context", ""),
            )
            return {"status": "success", "result": result}
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            return {"status": "error", "message": str(exc)}


def main():
    url = DEV_SERVER_URL if os.environ.get("OPTILAB_DEV") or not DIST_INDEX.exists() else str(DIST_INDEX)
    webview.create_window("OptiLab", url, js_api=Api())
    # pywebview forces the Qt backend on any KDE session regardless of what's
    # installed; we only have GTK/WebKit bindings, so pin the GTK backend.
    webview.start(gui="gtk")


if __name__ == "__main__":
    main()
