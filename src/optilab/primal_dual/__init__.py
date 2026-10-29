"""Método primal → dual: construye el dual de un PL y lo resuelve (Simplex exacto).

Entrada principal: ``solve(problem)``. ``solve_request(payload)`` es la versión
para el frontend (dict JSON in / dict JSON out).
"""

from . import _core, _io
from ._model import Problem


def build_dual(problem):
    """Construye el problema dual de un PL general."""
    return _core.build_dual(problem)


def solve(problem, verify=False):
    """Primal → dual → resolver el dual.

    Devuelve ``{"dual": Problem, "result": dict}``; con ``verify=True`` agrega
    ``"primal_result"`` (el primal resuelto directamente, para comprobar dualidad fuerte).
    """
    dual = _core.build_dual(problem)
    out = {"dual": dual, "result": _core.solve(dual)}
    if verify:
        out["primal_result"] = _core.solve(problem)
    return out


def solve_request(payload):
    """Payload JSON del frontend → respuesta JSON-safe. Lanza ValueError si hay datos inválidos."""
    problem = _io.problem_from_payload(payload)
    out = solve(problem, verify=bool(payload.get("verify")))
    resp = {
        "primal": _io.describe(problem),
        "dual": _io.describe(out["dual"]),
        "result": _io.result_to_dict(out["dual"], out["result"]),
    }
    if "primal_result" in out:
        resp["primal_result"] = _io.result_to_dict(problem, out["primal_result"])
    return resp


__all__ = ["Problem", "build_dual", "solve", "solve_request"]
