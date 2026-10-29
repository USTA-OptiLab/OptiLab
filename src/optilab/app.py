"""Shell pywebview de OptiLab. `Api` es la única superficie puente frontend ↔ Python."""

import os
from pathlib import Path

from optilab.primal_dual import solve_request

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"


class Api:
    def solve_primal_dual(self, payload):
        """Primal → dual → resolver el dual. Nunca propaga excepciones al puente JS."""
        try:
            return {"status": "ok", **solve_request(payload)}
        except (ValueError, ZeroDivisionError) as exc:
            return {"status": "error", "message": str(exc)}


def main():
    import webview

    url = os.environ.get("OPTILAB_DEV_URL") or str(DIST)
    webview.create_window("OptiLab", url, js_api=Api(), width=1100, height=800, min_size=(760, 560))
    webview.start(http_server=True)


if __name__ == "__main__":
    main()
