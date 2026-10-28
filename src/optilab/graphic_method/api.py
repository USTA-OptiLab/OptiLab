"""pywebview bridge for the graphical method module."""

from __future__ import annotations

from typing import Any

from .solver import solve_graphical


class GraphicMethodApi:
    """API exposed to the standalone graphical-method frontend."""

    def solve_graphical(self, payload: Any) -> dict[str, Any]:
        try:
            return solve_graphical(payload)
        except (TypeError, ValueError) as error:
            return {"ok": False, "error": str(error)}
        except Exception:  # noqa: BLE001 - don't leak tracebacks into the webview
            return {
                "ok": False,
                "error": "Ocurrió un error inesperado al resolver el problema.",
            }
