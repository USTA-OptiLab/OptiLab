"""Conversión entre el payload JSON del frontend y los objetos del solver."""

from fractions import Fraction

from ._model import Problem


def parse_number(v):
    """Acepta int, float o texto ('3', '2.5', '2,5', '1/3')."""
    text = str(v).replace(",", ".").strip()
    if not text:
        raise ValueError("Hay campos numéricos vacíos.")
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        raise ValueError(
            f"Número inválido: '{v}'. Use enteros, decimales o fracciones (ej: 3, 2.5, 1/3)."
        )


def fmt(v):
    v = Fraction(v)
    text = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return {"frac": text, "value": float(v)}


def problem_from_payload(data):
    try:
        c = [parse_number(v) for v in data["c"]]
        cons = [
            ([parse_number(v) for v in r["a"]], r["type"], parse_number(r["b"]))
            for r in data["cons"]
        ]
        return Problem(data["sense"], c, cons, data["signs"])
    except (KeyError, TypeError):
        raise ValueError("Datos del problema incompletos.")


def _term(coef, name, first):
    sign = "-" if coef < 0 else "+"
    mag = abs(coef)
    body = name if mag == 1 else f"{fmt(mag)['frac']}{name}"
    if first:
        return f"-{body}" if coef < 0 else body
    return f" {sign} {body}"


def _expr(coefs, names):
    out = ""
    for coef, name in zip(coefs, names):
        if coef != 0:
            out += _term(coef, name, not out)
    return out or "0"


def describe(p):
    """Texto legible del problema: objetivo, restricciones y signos."""
    return {
        "objective": f"{p.sense} Z = {_expr(p.c, p.names)}",
        "constraints": [
            f"{_expr(a, p.names)} {t} {fmt(b)['frac']}" for a, t, b in p.cons
        ],
        "signs": [
            f"{name} {s if s != 'libre' else 'libre'}"
            for name, s in zip(p.names, p.signs)
        ],
    }


def result_to_dict(p, res):
    out = {"status": res["status"]}
    if res["status"] == "optimal":
        out["method"] = res["method"]
        out["z"] = fmt(res["z"])
        out["vars"] = [{"name": n, **fmt(v)} for n, v in zip(p.names, res["x"])]
    return out
