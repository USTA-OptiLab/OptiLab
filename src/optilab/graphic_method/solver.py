"""Graphical method for linear programming problems with two variables.

The solver works with the standard form:

    max/min  Z = c1*x1 + c2*x2
    subject to:
        a1*x1 + a2*x2 <=|>=|= b   (one or more constraints)
        x1 >= 0, x2 >= 0          (implicit non-negativity)

It returns every intersection point in the first quadrant (feasible or not),
the feasible region as a polygon clipped to a plotting rectangle, and the
optimal feasible vertex when one exists.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

EPS = 1e-9
FEASIBILITY_REL_TOL = 1e-7
POINT_REL_TOL = 1e-7

_OP_LABEL = {"<=": "≤", ">=": "≥", "=": "="}
_OP_ALIASES = {"<=": "<=", "≤": "<=", ">=": ">=", "≥": ">=", "=": "=", "==": "="}


@dataclass
class _Constraint:
    index: int
    a1: float
    a2: float
    op: str
    b: float

    @property
    def label(self) -> str:
        return f"R{self.index}"

    @property
    def display(self) -> str:
        lhs = _format_terms(self.a1, self.a2)
        return f"{lhs} {_OP_LABEL[self.op]} {_format_number(self.b)}"


@dataclass
class _Line:
    key: str
    label: str
    a: float
    b: float
    c: float
    constraint: _Constraint | None = None


@dataclass
class _Point:
    x: float
    y: float
    sources: list[str] = field(default_factory=list)
    feasible: bool = False
    active: list[str] = field(default_factory=list)
    label: str = ""
    z: float = 0.0
    optimal: bool = False


def _clean_zero(value: float) -> float:
    return 0.0 if abs(value) < 1e-12 else value


def _round(value: float, digits: int = 8) -> float:
    return _clean_zero(round(value, digits))


def _format_number(value: float | None, digits: int = 6) -> str:
    if value is None:
        return "—"
    if abs(value) < 1e-12:
        value = 0.0
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    if text in ("", "-0"):
        return "0"
    return text


def _format_term(coef: float, variable: str, first: bool) -> str:
    if abs(coef) < EPS:
        return ""
    magnitude = abs(coef)
    coefficient = "" if abs(magnitude - 1.0) < EPS else _format_number(magnitude)
    term = f"{coefficient}{variable}"
    if first:
        return f"-{term}" if coef < 0 else term
    return f"- {term}" if coef < 0 else f"+ {term}"


def _format_terms(a1: float, a2: float) -> str:
    left = _format_term(a1, "x₁", True)
    right = _format_term(a2, "x₂", first=not left)
    terms = " ".join(part for part in (left, right) if part)
    return terms or "0"


def _format_constraint(coef1: float, coef2: float, op: str, b: float) -> str:
    return f"{_format_terms(coef1, coef2)} {_OP_LABEL[op]} {_format_number(b)}"


def _as_float(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"El campo «{field_name}» debe ser numérico.") from None
    if not math.isfinite(number):
        raise ValueError(f"El campo «{field_name}» debe ser un número finito.")
    return number


def _same_number(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    return abs(a - b) <= rel_tol * max(1.0, abs(a), abs(b))


def _same_point(a: _Point, x: float, y: float) -> bool:
    return _same_number(a.x, x, POINT_REL_TOL) and _same_number(a.y, y, POINT_REL_TOL)


def _normalize_input(payload: Any) -> tuple[str, float, float, list[_Constraint]]:
    if not isinstance(payload, dict):
        raise TypeError("Los datos del problema no tienen el formato esperado.")

    sense = str(payload.get("sense", "")).strip().lower()
    if sense not in {"max", "min"}:
        raise ValueError(
            "Debe indicar si se maximiza o se minimiza la función objetivo."
        )

    objective = payload.get("objective")
    if not isinstance(objective, dict):
        raise TypeError("Debe indicar los coeficientes de la función objetivo.")

    c1 = _as_float(objective.get("c1"), "coeficiente de x₁")
    c2 = _as_float(objective.get("c2"), "coeficiente de x₂")
    if abs(c1) < EPS and abs(c2) < EPS:
        raise ValueError(
            "La función objetivo no puede tener ambos coeficientes en cero."
        )

    raw_constraints = payload.get("constraints")
    if not isinstance(raw_constraints, list) or not raw_constraints:
        raise ValueError("Debe ingresar al menos una restricción.")

    constraints: list[_Constraint] = []
    for position, raw in enumerate(raw_constraints, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"La restricción R{position} no tiene el formato esperado.")
        a1 = _as_float(raw.get("a1"), f"coeficiente x₁ de R{position}")
        a2 = _as_float(raw.get("a2"), f"coeficiente x₂ de R{position}")
        b = _as_float(raw.get("b"), f"lado derecho de R{position}")
        op = _OP_ALIASES.get(str(raw.get("op", "")).strip())
        if op is None:
            raise ValueError(f"La relación de R{position} debe ser ≤, ≥ o =.")
        if abs(a1) < EPS and abs(a2) < EPS:
            raise ValueError(
                f"La restricción R{position} debe tener al menos un coeficiente distinto de cero."
            )
        constraints.append(_Constraint(index=position, a1=a1, a2=a2, op=op, b=b))

    return sense, c1, c2, constraints


def _build_lines(constraints: list[_Constraint]) -> list[_Line]:
    lines = [
        _Line(
            key=constraint.label,
            label=constraint.label,
            a=constraint.a1,
            b=constraint.a2,
            c=constraint.b,
            constraint=constraint,
        )
        for constraint in constraints
    ]
    lines.append(_Line(key="x1", label="x₁ = 0", a=1.0, b=0.0, c=0.0))
    lines.append(_Line(key="x2", label="x₂ = 0", a=0.0, b=1.0, c=0.0))
    return lines


def _line_intersection(line1: _Line, line2: _Line) -> tuple[float, float] | None:
    determinant = line1.a * line2.b - line2.a * line1.b
    tolerance = 1e-9 * max(
        1.0,
        abs(line1.a),
        abs(line1.b),
        abs(line2.a),
        abs(line2.b),
    )
    if abs(determinant) <= tolerance:
        return None
    x = (line1.c * line2.b - line2.c * line1.b) / determinant
    y = (line1.a * line2.c - line2.a * line1.c) / determinant
    return _clean_zero(x), _clean_zero(y)


def _satisfies_constraints(x: float, y: float, constraints: list[_Constraint]) -> bool:
    if x < -FEASIBILITY_REL_TOL or y < -FEASIBILITY_REL_TOL:
        return False
    for constraint in constraints:
        lhs = constraint.a1 * x + constraint.a2 * y
        tolerance = FEASIBILITY_REL_TOL * max(1.0, abs(lhs), abs(constraint.b))
        slack = lhs - constraint.b
        if constraint.op == "<=" and slack > tolerance:
            return False
        if constraint.op == ">=" and slack < -tolerance:
            return False
        if constraint.op == "=" and abs(slack) > tolerance:
            return False
    return True


def _active_constraints(
    x: float, y: float, constraints: list[_Constraint]
) -> list[str]:
    active = []
    for constraint in constraints:
        lhs = constraint.a1 * x + constraint.a2 * y
        tolerance = FEASIBILITY_REL_TOL * max(1.0, abs(lhs), abs(constraint.b))
        if abs(lhs - constraint.b) <= tolerance:
            active.append(constraint.label)
    if abs(x) <= FEASIBILITY_REL_TOL:
        active.append("x₁ = 0")
    if abs(y) <= FEASIBILITY_REL_TOL:
        active.append("x₂ = 0")
    return active


def _source(line: _Line) -> str:
    return line.constraint.label if line.constraint else line.label


def _collect_points(lines: list[_Line], constraints: list[_Constraint]) -> list[_Point]:
    points: list[_Point] = []
    for index, line1 in enumerate(lines):
        for line2 in lines[index + 1 :]:
            intersection = _line_intersection(line1, line2)
            if intersection is None:
                continue
            x, y = intersection
            if x < -FEASIBILITY_REL_TOL or y < -FEASIBILITY_REL_TOL:
                continue
            x = max(0.0, x)
            y = max(0.0, y)
            source = f"{_source(line1)} ∩ {_source(line2)}"
            existing = next(
                (point for point in points if _same_point(point, x, y)), None
            )
            if existing is None:
                points.append(_Point(x=x, y=y, sources=[source]))
            elif source not in existing.sources:
                existing.sources.append(source)

    for point in points:
        point.feasible = _satisfies_constraints(point.x, point.y, constraints)
        point.active = _active_constraints(point.x, point.y, constraints)

    points.sort(key=lambda point: (round(point.x, 9), round(point.y, 9)))
    for position, point in enumerate(points, start=1):
        point.label = f"P{position}"
    return points


def _intercepts(constraints: list[_Constraint]) -> list[dict[str, Any]]:
    result = []
    for constraint in constraints:
        x_intercept = (
            _clean_zero(constraint.b / constraint.a1)
            if abs(constraint.a1) >= EPS
            else None
        )
        y_intercept = (
            _clean_zero(constraint.b / constraint.a2)
            if abs(constraint.a2) >= EPS
            else None
        )

        if x_intercept is None:
            x_calc = "No hay corte con el eje x₁: la restricción no depende de x₁."
        else:
            expression = f"{_format_term(constraint.a1, 'x₁', True)} = {_format_number(constraint.b)}"
            outside = " (fuera del primer cuadrante)" if x_intercept < 0 else ""
            x_calc = (
                f"x₂ = 0 → {expression} → x₁ = {_format_number(x_intercept)}"
                f" → ({_format_number(x_intercept)}, 0){outside}"
            )

        if y_intercept is None:
            y_calc = "No hay corte con el eje x₂: la restricción no depende de x₂."
        else:
            expression = f"{_format_term(constraint.a2, 'x₂', True)} = {_format_number(constraint.b)}"
            outside = " (fuera del primer cuadrante)" if y_intercept < 0 else ""
            y_calc = (
                f"x₁ = 0 → {expression} → x₂ = {_format_number(y_intercept)}"
                f" → (0, {_format_number(y_intercept)}){outside}"
            )

        result.append(
            {
                "label": constraint.label,
                "equation": constraint.display,
                "a1": constraint.a1,
                "a2": constraint.a2,
                "op": constraint.op,
                "b": constraint.b,
                "x_intercept": None if x_intercept is None else _round(x_intercept),
                "y_intercept": None if y_intercept is None else _round(y_intercept),
                "x_calc": x_calc,
                "y_calc": y_calc,
            }
        )
    return result


def _plot_bounds(
    points: list[_Point], intercepts: list[dict[str, Any]]
) -> tuple[float, float]:
    x_values = [point.x for point in points if point.x >= 0]
    y_values = [point.y for point in points if point.y >= 0]
    for intercept in intercepts:
        x_value = intercept["x_intercept"]
        y_value = intercept["y_intercept"]
        if x_value is not None and x_value >= 0:
            x_values.append(float(x_value))
        if y_value is not None and y_value >= 0:
            y_values.append(float(y_value))

    x_max = max(x_values, default=10.0)
    y_max = max(y_values, default=10.0)
    if x_max <= 0:
        x_max = 10.0
    if y_max <= 0:
        y_max = 10.0
    # A square view keeps small problems legible and gives unbounded regions
    # enough room to show the direction in which they extend.
    side = max(1.0, max(x_max, y_max) * 1.18)
    return side, side


def _clip_polygon(
    polygon: list[tuple[float, float]], a: float, b: float, c: float
) -> list[tuple[float, float]]:
    """Clip a polygon against the half-plane a*x + b*y <= c."""
    if not polygon:
        return []

    def inside(point: tuple[float, float]) -> bool:
        lhs = a * point[0] + b * point[1]
        tolerance = 1e-9 * max(1.0, abs(lhs), abs(c))
        return lhs <= c + tolerance

    def intersection(
        start: tuple[float, float], end: tuple[float, float]
    ) -> tuple[float, float]:
        denominator = a * (end[0] - start[0]) + b * (end[1] - start[1])
        if abs(denominator) < 1e-12:
            return end
        amount = (c - a * start[0] - b * start[1]) / denominator
        amount = max(0.0, min(1.0, amount))
        return (
            start[0] + amount * (end[0] - start[0]),
            start[1] + amount * (end[1] - start[1]),
        )

    output: list[tuple[float, float]] = []
    previous = polygon[-1]
    previous_inside = inside(previous)
    for current in polygon:
        current_inside = inside(current)
        if current_inside:
            if not previous_inside:
                output.append(intersection(previous, current))
            output.append(current)
        elif previous_inside:
            output.append(intersection(previous, current))
        previous = current
        previous_inside = current_inside
    return _clean_polygon(output)


def _clean_polygon(
    polygon: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    cleaned: list[tuple[float, float]] = []
    for point in polygon:
        candidate = (_clean_zero(point[0]), _clean_zero(point[1]))
        if not cleaned or not _same_point(
            _Point(x=cleaned[-1][0], y=cleaned[-1][1]),
            candidate[0],
            candidate[1],
        ):
            cleaned.append(candidate)
    if len(cleaned) > 1 and _same_point(
        _Point(x=cleaned[0][0], y=cleaned[0][1]), cleaned[-1][0], cleaned[-1][1]
    ):
        cleaned.pop()
    return cleaned


def _polygon_area(polygon: list[tuple[float, float]]) -> float:
    area = 0.0
    for index, point in enumerate(polygon):
        next_point = polygon[(index + 1) % len(polygon)]
        area += point[0] * next_point[1] - next_point[0] * point[1]
    return abs(area) / 2.0


def _farthest_pair(
    polygon: list[tuple[float, float]],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    best_pair = None
    best_distance = -1.0
    for index, first in enumerate(polygon):
        for second in polygon[index + 1 :]:
            distance = math.hypot(first[0] - second[0], first[1] - second[1])
            if distance > best_distance:
                best_distance = distance
                best_pair = (first, second)
    return best_pair if best_distance > 1e-9 else None


def _feasible_region(
    constraints: list[_Constraint], x_max: float, y_max: float
) -> dict[str, Any]:
    polygon = [(0.0, 0.0), (x_max, 0.0), (x_max, y_max), (0.0, y_max)]
    for constraint in constraints:
        if constraint.op in {"<=", "="}:
            polygon = _clip_polygon(polygon, constraint.a1, constraint.a2, constraint.b)
        if constraint.op in {">=", "="}:
            polygon = _clip_polygon(
                polygon, -constraint.a1, -constraint.a2, -constraint.b
            )
        if not polygon:
            break

    polygon = _clean_polygon(polygon)
    if not polygon:
        return {
            "type": "empty",
            "polygon": [],
            "segment": None,
            "point": None,
        }

    if len(polygon) == 1:
        return {
            "type": "point",
            "polygon": [],
            "segment": None,
            "point": [_round(polygon[0][0]), _round(polygon[0][1])],
        }

    area = _polygon_area(polygon)
    tolerance = 1e-8 * max(1.0, x_max * y_max)
    if len(polygon) == 2 or area <= tolerance:
        pair = _farthest_pair(polygon)
        return {
            "type": "segment",
            "polygon": [],
            "segment": (
                None
                if pair is None
                else [
                    [_round(pair[0][0]), _round(pair[0][1])],
                    [_round(pair[1][0]), _round(pair[1][1])],
                ]
            ),
            "point": None,
        }

    return {
        "type": "area",
        "polygon": [[_round(x), _round(y)] for x, y in polygon],
        "segment": None,
        "point": None,
    }


def _clip_line_to_rect(
    a: float, b: float, c: float, x_max: float, y_max: float
) -> list[list[float]] | None:
    points: list[tuple[float, float]] = []

    def add(x: float, y: float) -> None:
        tolerance = 1e-9 * max(1.0, x_max, y_max)
        if (
            -tolerance <= x <= x_max + tolerance
            and -tolerance <= y <= y_max + tolerance
        ):
            candidate = (
                min(max(x, 0.0), x_max),
                min(max(y, 0.0), y_max),
            )
            if not any(
                _same_number(candidate[0], point[0])
                and _same_number(candidate[1], point[1])
                for point in points
            ):
                points.append(candidate)

    if abs(b) >= EPS:
        for x in (0.0, x_max):
            add(x, (c - a * x) / b)
    if abs(a) >= EPS:
        for y in (0.0, y_max):
            add((c - b * y) / a, y)

    if len(points) < 2:
        return None
    pair = _farthest_pair(points)
    if pair is None:
        return None
    return [
        [_round(pair[0][0]), _round(pair[0][1])],
        [_round(pair[1][0]), _round(pair[1][1])],
    ]


def _recession_rays(constraints: list[_Constraint]) -> list[tuple[float, float]]:
    candidates: list[tuple[float, float]] = [(1.0, 0.0), (0.0, 1.0)]
    for constraint in constraints:
        norm = math.hypot(constraint.a1, constraint.a2)
        if norm >= EPS:
            candidates.append((constraint.a2 / norm, -constraint.a1 / norm))
            candidates.append((-constraint.a2 / norm, constraint.a1 / norm))

    directions: list[tuple[float, float]] = []
    for dx, dy in candidates:
        norm = math.hypot(dx, dy)
        if norm < EPS:
            continue
        direction = (dx / norm, dy / norm)
        if direction[0] < -FEASIBILITY_REL_TOL or direction[1] < -FEASIBILITY_REL_TOL:
            continue
        if not _is_recession_direction(direction, constraints):
            continue
        if any(
            _same_number(direction[0], existing[0], 1e-7)
            and _same_number(direction[1], existing[1], 1e-7)
            for existing in directions
        ):
            continue
        directions.append(direction)
    return directions


def _is_recession_direction(
    direction: tuple[float, float], constraints: list[_Constraint]
) -> bool:
    dx, dy = direction
    for constraint in constraints:
        lhs = constraint.a1 * dx + constraint.a2 * dy
        tolerance = FEASIBILITY_REL_TOL
        if constraint.op == "<=" and lhs > tolerance:
            return False
        if constraint.op == ">=" and lhs < -tolerance:
            return False
        if constraint.op == "=" and abs(lhs) > tolerance:
            return False
    return True


def _unbounded_direction(
    sense: str,
    c1: float,
    c2: float,
    rays: list[tuple[float, float]],
) -> tuple[float, float] | None:
    tolerance = 1e-9 * max(1.0, math.hypot(c1, c2))
    for direction in rays:
        slope = c1 * direction[0] + c2 * direction[1]
        if sense == "max" and slope > tolerance:
            return direction
        if sense == "min" and slope < -tolerance:
            return direction
    return None


def _evaluation_detail(c1: float, c2: float, point: _Point) -> str:
    parts: list[str] = []
    if abs(c1) >= EPS:
        term = f"{_format_number(abs(c1))}({_format_number(point.x)})"
        parts.append(f"-{term}" if c1 < 0 else term)
    if abs(c2) >= EPS:
        term = f"{_format_number(abs(c2))}({_format_number(point.y)})"
        if not parts:
            parts.append(f"-{term}" if c2 < 0 else term)
        else:
            parts.append(f"- {term}" if c2 < 0 else f"+ {term}")
    expression = " ".join(parts) or "0"
    detail = f"Z({point.label}) = {expression} = {_format_number(point.z)}"
    if not point.feasible:
        detail += " → no satisface todas las restricciones"
    return detail


def _point_payload(point: _Point) -> dict[str, Any]:
    return {
        "label": point.label,
        "x1": _round(point.x),
        "x2": _round(point.y),
        "z": _round(point.z),
        "feasible": point.feasible,
        "optimal": point.optimal,
        "is_vertex": point.feasible,
        "sources": point.sources,
        "active": point.active,
    }


def solve_graphical(payload: Any) -> dict[str, Any]:
    """Solve a two-variable linear program with the graphical method."""
    sense, c1, c2, constraints = _normalize_input(payload)
    lines = _build_lines(constraints)
    intercepts = _intercepts(constraints)
    points = _collect_points(lines, constraints)

    for point in points:
        point.z = _clean_zero(c1 * point.x + c2 * point.y)

    feasible_points = [point for point in points if point.feasible]
    x_max, y_max = _plot_bounds(points, intercepts)
    region = _feasible_region(constraints, x_max, y_max)
    rays = _recession_rays(constraints)
    unbounded_direction = None

    if not feasible_points:
        status = "infeasible"
    else:
        unbounded_direction = _unbounded_direction(sense, c1, c2, rays)
        status = "unbounded" if unbounded_direction is not None else "optimal"

    optimal_point: _Point | None = None
    optimal_points: list[_Point] = []
    if status == "optimal" and feasible_points:
        best_value = (
            max(point.z for point in feasible_points)
            if sense == "max"
            else min(point.z for point in feasible_points)
        )
        tolerance = FEASIBILITY_REL_TOL * max(1.0, abs(best_value))
        optimal_points = [
            point for point in feasible_points if abs(point.z - best_value) <= tolerance
        ]
        for point in optimal_points:
            point.optimal = True
        optimal_point = optimal_points[0]

    chart_lines = []
    for constraint in constraints:
        segment = _clip_line_to_rect(
            constraint.a1, constraint.a2, constraint.b, x_max, y_max
        )
        if segment is not None:
            chart_lines.append(
                {
                    "label": constraint.label,
                    "equation": constraint.display,
                    "points": segment,
                }
            )

    objective_line = None
    if optimal_point is not None:
        objective_segment = _clip_line_to_rect(c1, c2, optimal_point.z, x_max, y_max)
        if objective_segment is not None:
            objective_line = {
                "z": _round(optimal_point.z),
                "points": objective_segment,
            }

    steps: list[dict[str, str]] = [
        {
            "title": "Modelo",
            "detail": (
                f"{'Max' if sense == 'max' else 'Min'} Z = {_format_terms(c1, c2)}"
            ),
        },
        {
            "title": "No negatividad",
            "detail": "Se asume x₁ ≥ 0 y x₂ ≥ 0.",
        },
    ]
    for intercept in intercepts:
        steps.append(
            {
                "title": f"Cortes de {intercept['label']}",
                "detail": (
                    f"{intercept['equation']}\n"
                    f"{intercept['x_calc']}\n"
                    f"{intercept['y_calc']}"
                ),
            }
        )
    for point in points:
        steps.append(
            {
                "title": f"Evaluación de {point.label}",
                "detail": _evaluation_detail(c1, c2, point),
            }
        )

    if status == "optimal" and optimal_point is not None:
        if len(optimal_points) > 1:
            labels = ", ".join(point.label for point in optimal_points)
            steps.append(
                {
                    "title": "Conclusión",
                    "detail": (
                        "Hay múltiples soluciones óptimas: "
                        f"{labels}. Todas alcanzan Z = {_format_number(optimal_point.z)}."
                    ),
                }
            )
        else:
            steps.append(
                {
                    "title": "Conclusión",
                    "detail": (
                        "El "
                        f"{'mayor' if sense == 'max' else 'menor'} valor de Z "
                        f"se alcanza en {optimal_point.label} = "
                        f"({_format_number(optimal_point.x)}, "
                        f"{_format_number(optimal_point.y)}), con "
                        f"Z = {_format_number(optimal_point.z)}."
                    ),
                }
            )
    elif status == "infeasible":
        steps.append(
            {
                "title": "Conclusión",
                "detail": "No existe ningún punto que satisfaga todas las restricciones.",
            }
        )
    else:
        steps.append(
            {
                "title": "Conclusión",
                "detail": (
                    "La función objetivo puede "
                    f"{'crecer' if sense == 'max' else 'disminuir'} "
                    "indefinidamente dentro de la región factible."
                ),
            }
        )

    return {
        "ok": True,
        "status": status,
        "objective": {
            "sense": sense,
            "c1": c1,
            "c2": c2,
            "equation": f"{'Max' if sense == 'max' else 'Min'} Z = {_format_terms(c1, c2)}",
        },
        "constraints": [
            {
                "label": constraint.label,
                "a1": constraint.a1,
                "a2": constraint.a2,
                "op": constraint.op,
                "b": constraint.b,
                "equation": constraint.display,
            }
            for constraint in constraints
        ],
        "intercepts": intercepts,
        "points": [_point_payload(point) for point in points],
        "vertices": [_point_payload(point) for point in feasible_points],
        "region": {
            **region,
            "bounded": not rays,
            "clipped": bool(rays),
            "plot": {"xMax": _round(x_max), "yMax": _round(y_max)},
        },
        "lines": chart_lines,
        "objective_line": objective_line,
        "rays": [
            {"dx": _round(direction[0]), "dy": _round(direction[1])}
            for direction in rays
        ],
        "unbounded_direction": (
            None
            if unbounded_direction is None
            else {
                "dx": _round(unbounded_direction[0]),
                "dy": _round(unbounded_direction[1]),
            }
        ),
        "optimal": (
            None
            if optimal_point is None
            else {
                "label": optimal_point.label,
                "x1": _round(optimal_point.x),
                "x2": _round(optimal_point.y),
                "z": _round(optimal_point.z),
                "active": optimal_point.active,
            }
        ),
        "optimal_points": [
            {
                "label": point.label,
                "x1": _round(point.x),
                "x2": _round(point.y),
                "z": _round(point.z),
            }
            for point in optimal_points
        ],
        "steps": steps,
    }
