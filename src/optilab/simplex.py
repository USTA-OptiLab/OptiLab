"""Educational Simplex Algorithm with Step-by-Step Tableaus and Explanations.

Supports:
- Primal Simplex and Two-Phase Simplex (for <=, >=, and = constraints).
- Exact Fraction arithmetic (fractions.Fraction) with human-readable fraction and decimal formatting.
- Bland's Rule for cycle prevention.
- Step-by-step recording of tableaus, optimality checks, ratio tests, pivot choices,
  and row operations (Gauss-Jordan).
- Solution verification, degeneracy, alternative optima, and sensitivity analysis (shadow prices).
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any


def parse_fraction(val: Any) -> Fraction:
    """Safely converts ints, floats, or string representations to a Fraction."""
    if isinstance(val, Fraction):
        return val
    if isinstance(val, (int, float)):
        return Fraction(str(val))
    s = str(val).strip().replace(",", ".")
    if not s:
        return Fraction(0)
    if "/" in s:
        num, den = s.split("/", 1)
        return Fraction(int(num.strip()), int(den.strip()))
    return Fraction(s)


def fmt_frac(x: Fraction | float) -> str:
    """Formats a number as a clean fraction string (e.g. '5', '3/2', '-1/4')."""
    f = Fraction(x)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def fmt_dec(x: Fraction | float, decimals: int = 4) -> str:
    """Formats a number as decimal string with approximation symbol if repeating."""
    f = Fraction(x)
    val = float(f)
    if f.denominator == 1 or abs(val - round(val, decimals)) < 1e-9:
        return f"{val:.{decimals}f}".rstrip("0").rstrip(".")
    return f"≈ {val:.{decimals}f}"


def fmt_cell(x: Fraction | float) -> dict[str, Any]:
    """Returns both fraction and decimal representation for UI display."""
    f = Fraction(x)
    return {
        "frac": fmt_frac(f),
        "dec": fmt_dec(f),
        "float": float(f),
        "num": f.numerator,
        "den": f.denominator,
    }


def invert_matrix(m: list[list[Fraction]]) -> list[list[Fraction]]:
    """Inverts a square matrix of Fractions using Gauss-Jordan elimination."""
    n = len(m)
    a = [list(m[i]) + [Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    for c in range(n):
        pivot_row = next((r for r in range(c, n) if a[r][c] != 0), None)
        if pivot_row is None:
            raise ValueError("Matriz singular no invertible.")
        a[c], a[pivot_row] = a[pivot_row], a[c]
        pv = a[c][c]
        a[c] = [v / pv for v in a[c]]
        for r in range(n):
            if r != c and a[r][c] != 0:
                factor = a[r][c]
                a[r] = [a[r][k] - factor * a[c][k] for k in range(2 * n)]
    return [row[n:] for row in a]


def analyze_problem_context(text: str) -> dict[str, Any]:
    """Analyzes natural language exercise text to infer objective, variable names, units, and constraints."""
    t = text.lower()

    # 1. Determine objective sense (max vs min)
    max_terms = [
        "maximi",
        "utilidad",
        "ganancia",
        "beneficio",
        "ingreso",
        "lucro",
        "rendimiento",
        "venta",
        "retorno",
        "mayor",
    ]
    min_terms = [
        "minimi",
        "costo",
        "gasto",
        "pérdida",
        "perdida",
        "tiempo",
        "merma",
        "distancia",
        "recorrido",
        "menor",
        "consumo",
    ]

    max_scores = sum(t.count(k) for k in max_terms)
    min_scores = sum(t.count(k) for k in min_terms)

    objective = "min" if min_scores > max_scores else "max"

    if objective == "max":
        obj_name = "Ganancia / Utilidad total"
        if "ingreso" in t:
            obj_name = "Ingreso total"
        elif "beneficio" in t:
            obj_name = "Beneficio neto"
        elif "rendimiento" in t:
            obj_name = "Rendimiento total"
    else:
        obj_name = "Costo total de operación"
        if "tiempo" in t:
            obj_name = "Tiempo total requerido"
        elif "gasto" in t:
            obj_name = "Gasto total"
        elif "distancia" in t:
            obj_name = "Distancia total"

    # Unit detection
    obj_unit = "$"
    if "dólar" in t or "dolar" in t or "usd" in t or "$" in text:
        obj_unit = "$"
    elif "euro" in t or "€" in text:
        obj_unit = "€"
    elif "sol" in t or "s/." in t:
        obj_unit = "S/."
    elif "hora" in t and objective == "min":
        obj_unit = "horas"
    elif "minuto" in t and objective == "min":
        obj_unit = "min"
    elif "peso" in t:
        obj_unit = "$"

    # Candidate variable names extraction
    var_candidates: list[str] = []
    prod_pattern = re.search(
        r"(?:produce|fabrica|elabora|vende|confecciona|ofrece|prepara|comercializa|utiliza)\s+([a-záéíóúñ\s,y]+?)(?:\.|\;|\,|\s+con|\s+para|\s+cada|\s+en|\s+utilizando|\s+sujeto)",
        t,
    )
    if prod_pattern:
        raw_items = prod_pattern.group(1).replace(" y ", ",").replace(" e ", ",")
        for item in raw_items.split(","):
            cleaned = item.strip()
            cleaned = re.sub(
                r"^(dos|tres|cuatro|cinco|artículos de tipo|productos?|tipos? de|unidades? de)\s+",
                "",
                cleaned,
            )
            if (
                cleaned
                and len(cleaned) > 2
                and cleaned not in ["dos", "tres", "varios"]
            ):
                var_candidates.append(cleaned.capitalize())

    # Resource / Constraint names extraction
    constraint_candidates: list[str] = []
    res_matches = re.findall(
        r"(?:horas?\s+de\s+([a-záéíóúñ]+)|departamento\s+de\s+([a-záéíóúñ]+)|taller\s+de\s+([a-záéíóúñ]+)|materia\s+prima\s+([a-záéíóúñ]+)|disponibilidad\s+de\s+([a-záéíóúñ]+)|máquina\s+([a-záéíóúñ\d]+))",
        t,
    )
    for match in res_matches:
        for m in match:
            if m and len(m) > 2:
                constraint_candidates.append(f"Horas / Capacidad de {m.capitalize()}")

    return {
        "objective": objective,
        "objective_name": obj_name,
        "objective_unit": obj_unit,
        "suggested_vars": var_candidates[:6],
        "suggested_constraints": list(dict.fromkeys(constraint_candidates))[:6],
        "analysis_summary": (
            f"Se identificó sentido de {'MAXIMIZACIÓN' if objective == 'max' else 'MINIMIZACIÓN'} "
            f"enfocado en '{obj_name}' ({obj_unit})."
        ),
    }


def generate_contextual_conclusion(
    status: str,
    objective: str,
    z_optimal: dict[str, Any] | None,
    variables: dict[str, dict[str, Any]],
    substitutions: list[dict[str, Any]],
    shadow_prices: list[dict[str, Any]],
    context: dict[str, Any] | None,
    var_names: list[str],
) -> dict[str, Any]:
    """Generates an executive, business-tailored conclusion answering the real-world problem context."""
    ctx = context or {}
    statement = ctx.get("statement", "").strip()
    title = ctx.get("title", "").strip() or "Problema de Optimización Lineal"
    obj_name = ctx.get("objective_name", "").strip() or (
        "Ganancia / Utilidad total"
        if objective == "max"
        else "Costo total de operación"
    )
    obj_unit = ctx.get("objective_unit", "").strip() or "$"

    var_descriptions = ctx.get("var_descriptions") or []
    var_units = ctx.get("var_units") or []
    constraint_descriptions = ctx.get("constraint_descriptions") or []
    constraint_units = ctx.get("constraint_units") or []

    # Case 1: Infeasible
    if status == "infeasible":
        return {
            "status": "infeasible",
            "title": title,
            "statement": statement,
            "headline": f"Infactibilidad: Conflicto en los Requerimientos de {obj_name}",
            "executive_summary": (
                "El modelo no posee solución factible. Esto significa que las metas mínimas exigidas "
                "y los límites de recursos disponibles entran en contradicción directa. "
                "Con las condiciones y disponibilidades actuales, es matemáticamente imposible "
                "cumplir todas las restricciones al mismo tiempo."
            ),
            "recommendation": (
                "Para hacer viable el problema, se debe revisar el planteamiento: reducir las metas o "
                "demandas mínimas, o bien aumentar la dotación de los recursos limitantes."
            ),
            "plan_of_action": [],
            "resource_diagnosis": [],
            "limiting_resources": [],
            "slack_resources": [],
            "sensitivity_insights": [],
        }

    # Case 2: Unbounded
    if status == "unbounded":
        return {
            "status": "unbounded",
            "title": title,
            "statement": statement,
            "headline": f"Problema No Acotado: {obj_name} Crece Indefinidamente",
            "executive_summary": (
                f"El modelo indica que la función objetivo ({obj_name}) puede incrementarse sin límite finito "
                f"sin infringir ninguna de las restricciones planteadas."
            ),
            "recommendation": (
                "En una situación real de negocio, obtener ganancias infinitas o beneficios ilimitados no es posible. "
                "Este resultado evidencia que el ejercicio carece de al menos una restricción limitante crucial "
                "(por ejemplo, un techo a la demanda del mercado, presupuesto tope o capacidad física máxima)."
            ),
            "plan_of_action": [],
            "resource_diagnosis": [],
            "limiting_resources": [],
            "slack_resources": [],
            "sensitivity_insights": [],
        }

    # Case 3: Optimal Solution
    verb = "maximizar" if objective == "max" else "minimizar"
    z_str = z_optimal.get("frac", "0") if z_optimal else "0"
    z_dec = z_optimal.get("dec", z_str) if z_optimal else z_str

    plan_of_action = []
    var_summary_parts = []
    for i, v_name in enumerate(var_names):
        v_data = variables.get(v_name, {"frac": "0", "dec": "0"})
        v_val_str = v_data.get("frac", "0")
        v_val_dec = v_data.get("dec", v_val_str)
        v_desc = (
            var_descriptions[i]
            if i < len(var_descriptions) and var_descriptions[i]
            else f"Variable {v_name}"
        )
        v_unit = var_units[i] if i < len(var_units) and var_units[i] else "unidades"

        plan_of_action.append(
            {
                "var": v_name,
                "description": v_desc,
                "value_frac": v_val_str,
                "value_dec": v_val_dec,
                "unit": v_unit,
                "action_text": f"Fabricar / Asignar {v_val_str} {v_unit} de '{v_desc}' ({v_name}).",
            }
        )
        var_summary_parts.append(f"{v_val_str} {v_unit} de {v_desc}")

    joined_vars = ", ".join(var_summary_parts)
    executive_summary = (
        f"Para {verb} exitosamente la {obj_name}, la solución óptima determina que se deben "
        f"{'fabricar' if 'produc' in obj_name.lower() or 'ganan' in obj_name.lower() else 'asignar'} "
        f"{joined_vars}, logrando un valor óptimo de {obj_name} igual a {z_str} {obj_unit} ({z_dec} {obj_unit})."
    )

    resource_diagnosis = []
    limiting_resources = []
    slack_resources = []

    for i, sub in enumerate(substitutions):
        r_label = sub.get("label", f"R{i + 1}")
        r_desc = (
            constraint_descriptions[i]
            if i < len(constraint_descriptions) and constraint_descriptions[i]
            else f"Restricción {r_label}"
        )
        r_unit = (
            constraint_units[i]
            if i < len(constraint_units) and constraint_units[i]
            else "unidades"
        )
        is_active = sub.get("is_active", False)
        lhs = sub.get("lhs", "0")
        rhs = sub.get("rhs", "0")
        sign = sub.get("sign", "<=")
        slack_val = sub.get("slack_value", "0")

        if is_active:
            if sign == "<=":
                status_desc = "Recurso AGOTADO al 100% (Cuello de botella)"
                detail_desc = (
                    f"Se consumió la totalidad de las {rhs} {r_unit} disponibles. "
                    f"Representa un recurso limitante crítico que frena un mayor beneficio."
                )
            elif sign == ">=":
                status_desc = "Requisito mínimo alcanzado con exactitud"
                detail_desc = f"Se cumplió de forma justa la meta mínima de {rhs} {r_unit} sin excedente."
            else:
                status_desc = "Restricción de igualdad estricta cumplida"
                detail_desc = (
                    f"Se cumple de manera exacta la igualdad ({rhs} {r_unit})."
                )
            limiting_resources.append(r_desc)
        else:
            if sign == "<=":
                status_desc = (
                    f"Recurso con HOLGURA (Capacidad ociosa: {slack_val} {r_unit})"
                )
                detail_desc = (
                    f"Se utilizaron {lhs} {r_unit} de las {rhs} {r_unit} disponibles. "
                    f"Quedan sin utilizar {slack_val} {r_unit}."
                )
            elif sign == ">=":
                status_desc = (
                    f"Requisito superado con EXCEDENTE ({slack_val} {r_unit} extras)"
                )
                detail_desc = (
                    f"Se produjeron/asignaron {lhs} {r_unit}, superando el mínimo de {rhs} {r_unit} "
                    f"en {slack_val} {r_unit}."
                )
            else:
                status_desc = f"Diferencia de {slack_val} {r_unit}"
                detail_desc = f"Lado izquierdo = {lhs}, lado derecho = {rhs}."
            slack_resources.append(r_desc)

        resource_diagnosis.append(
            {
                "constraint": r_label,
                "description": r_desc,
                "is_active": is_active,
                "status_title": status_desc,
                "detail": detail_desc,
                "usage_ratio": f"{lhs} / {rhs} {r_unit}",
                "slack": slack_val,
                "unit": r_unit,
                "sign": sign,
            }
        )

    sensitivity_insights = []
    for sp in shadow_prices:
        c_label = sp.get("constraint", "")
        c_idx = next(
            (k for k, sub in enumerate(substitutions) if sub.get("label") == c_label),
            -1,
        )
        r_desc = (
            constraint_descriptions[c_idx]
            if c_idx >= 0
            and c_idx < len(constraint_descriptions)
            and constraint_descriptions[c_idx]
            else c_label
        )
        r_unit = (
            constraint_units[c_idx]
            if c_idx >= 0 and c_idx < len(constraint_units) and constraint_units[c_idx]
            else "unidad"
        )
        price_val = sp.get("price", "0")
        price_flt = sp.get("price_float", 0.0)

        if abs(price_flt) > 1e-6:
            takeaway = (
                f"Por cada {r_unit} adicional disponible en '{r_desc}', la {obj_name} "
                f"mejorará en {price_val} {obj_unit}. Se recomienda evaluar adquirir o contratar más capacidad en este recurso."
            )
        else:
            takeaway = (
                f"El recurso '{r_desc}' tiene un precio sombra de 0 {obj_unit}. "
                f"No es rentable pagar por capacidad adicional aquí, dado que actualmente existe holgura no aprovechada."
            )

        sensitivity_insights.append(
            {
                "constraint": c_label,
                "description": r_desc,
                "shadow_price": price_val,
                "unit": f"{obj_unit}/{r_unit}",
                "recommendation": takeaway,
            }
        )

    return {
        "status": "optimal",
        "title": title,
        "statement": statement,
        "headline": f"Conclusión del Ejercicio: Estrategia Óptima para {verb.capitalize()} {obj_name}",
        "executive_summary": executive_summary,
        "optimal_value_text": f"{z_str} {obj_unit}",
        "optimal_value_dec": f"{z_dec} {obj_unit}",
        "plan_of_action": plan_of_action,
        "resource_diagnosis": resource_diagnosis,
        "limiting_resources": limiting_resources,
        "slack_resources": slack_resources,
        "sensitivity_insights": sensitivity_insights,
    }


class SimplexSolver:
    def __init__(
        self,
        objective: str,
        c: list[Any],
        constraints: list[dict[str, Any]],
        var_names: list[str] | None = None,
        var_bounds: list[str] | None = None,
        max_iterations: int = 100,
        context: dict[str, Any] | None = None,
    ):
        """Initializes a Linear Programming model.

        objective: 'max' | 'min'
        c: coefficients of objective function [c1, c2, ...]
        constraints: list of dicts: {'lhs': [...], 'sign': '<=' | '>=' | '=', 'rhs': b}
        var_names: optional names ['x1', 'x2', ...]
        var_bounds: optional per-variable signs ['>=0', '<=0', 'libre']
        context: optional business/exercise context dictionary
        """
        self.objective = objective.strip().lower()
        if self.objective not in ("max", "min"):
            raise ValueError("El objetivo debe ser 'max' o 'min'.")

        self.context = context or {}

        self.num_orig_vars = len(c)
        self.var_names = (
            [name.strip() for name in var_names]
            if var_names
            else [f"x{i + 1}" for i in range(self.num_orig_vars)]
        )
        self.var_bounds = (
            [b.strip().lower() for b in var_bounds]
            if var_bounds
            else [">=0"] * self.num_orig_vars
        )
        self.c_orig = [parse_fraction(v) for v in c]
        self.raw_constraints = []
        for r in constraints:
            lhs = [parse_fraction(v) for v in r["lhs"]]
            sign = r.get("sign", "<=").strip()
            rhs = parse_fraction(r["rhs"])
            self.raw_constraints.append({"lhs": lhs, "sign": sign, "rhs": rhs})

        self.max_iterations = max_iterations
        self.steps: list[dict[str, Any]] = []

    def solve(self) -> dict[str, Any]:
        """Runs the Simplex algorithm and records step-by-step progress."""
        self.steps = []

        # 1. Variable transformation for non-standard bounds (<=0 or free)
        std_cols: list[tuple[str, int, Fraction]] = []
        # (name, orig_index, multiplier)
        var_transformation_notes = []

        for j, name in enumerate(self.var_names):
            cond = self.var_bounds[j]
            if cond == ">=0":
                std_cols.append((name, j, Fraction(1)))
            elif cond == "<=0":
                std_cols.append((f"{name}'", j, Fraction(-1)))
                var_transformation_notes.append(
                    f"{name} ≤ 0 se sustituye por {name} = -{name}' con {name}' ≥ 0"
                )
            elif cond in ("libre", "free"):
                std_cols.append((f"{name}+", j, Fraction(1)))
                std_cols.append((f"{name}-", j, Fraction(-1)))
                var_transformation_notes.append(
                    f"{name} libre se sustituye por {name} = {name}+ - {name}- con {name}+, {name}- ≥ 0"
                )
            else:
                std_cols.append((name, j, Fraction(1)))

        std_var_names = [col[0] for col in std_cols]

        # In standard maximization form:
        # If min Z, max Z' = -Z (c' = -c)
        sgn = 1 if self.objective == "max" else -1
        c_std = [sgn * self.c_orig[j] * mult for (_, j, mult) in std_cols]

        # 2. Normalize constraints so that b >= 0
        norm_constraints = []
        norm_notes = []
        for i, r in enumerate(self.raw_constraints, 1):
            lhs_std = [r["lhs"][j] * mult for (_, j, mult) in std_cols]
            sign = r["sign"]
            rhs = r["rhs"]

            if rhs < 0 or (rhs == 0 and sign == ">="):
                lhs_std = [-v for v in lhs_std]
                rhs = -rhs
                sign = "<=" if sign == ">=" else (">=" if sign == "<=" else "=")
                norm_notes.append(
                    f"R{i} tenía lado derecho negativo: se multiplicó por -1 invirtiendo a '{sign}' con B={fmt_frac(rhs)}."
                )

            norm_constraints.append(
                {
                    "orig_idx": i - 1,
                    "lhs": lhs_std,
                    "sign": sign,
                    "rhs": rhs,
                }
            )

        # 3. Determine if Two-Phase Simplex is required
        needs_phase1 = any(r["sign"] in (">=", "=") for r in norm_constraints)

        if not needs_phase1:
            return self._solve_primal(
                std_cols,
                std_var_names,
                c_std,
                norm_constraints,
                var_transformation_notes,
                norm_notes,
            )
        else:
            return self._solve_two_phase(
                std_cols,
                std_var_names,
                c_std,
                norm_constraints,
                var_transformation_notes,
                norm_notes,
            )

    def _solve_primal(
        self,
        std_cols: list[tuple[str, int, Fraction]],
        std_var_names: list[str],
        c_std: list[Fraction],
        norm_constraints: list[dict[str, Any]],
        var_transformation_notes: list[str],
        norm_notes: list[str],
    ) -> dict[str, Any]:
        """Direct primal simplex when all normalized constraints are '<='."""
        num_std_vars = len(std_var_names)
        num_rows = len(norm_constraints)

        col_names = list(std_var_names)
        slack_names = [f"s{i + 1}" for i in range(num_rows)]
        col_names.extend(slack_names)
        num_cols = len(col_names)

        # Tableau structure: Row 0 is Z row (-c_j), Rows 1..m are constraints
        # T[row][col], last column is RHS (B)
        t_matrix = [[Fraction(0)] * (num_cols + 1) for _ in range(num_rows + 1)]

        # Row 0: Z - sum(c_j * x_j) = 0 => entries are -c_j
        for j in range(num_std_vars):
            t_matrix[0][j] = -c_std[j]

        basis: list[int] = []  # Indices of basic variable columns for rows 1..m
        for i, r in enumerate(norm_constraints, 1):
            for j in range(num_std_vars):
                t_matrix[i][j] = r["lhs"][j]
            # Slack variable has +1
            slack_col_idx = num_std_vars + (i - 1)
            t_matrix[i][slack_col_idx] = Fraction(1)
            t_matrix[i][-1] = r["rhs"]
            basis.append(slack_col_idx)

        # Keep initial matrix snapshot for sensitivity
        initial_submatrix = [
            [t_matrix[i][j] for j in range(num_cols)] for i in range(1, num_rows + 1)
        ]
        c_full = list(c_std) + [Fraction(0)] * num_rows

        z_label = "Z" if self.objective == "max" else "Z'"

        # Record Initial Tableau (Step 0)
        iter_num = 0
        status = "continue"

        while iter_num <= self.max_iterations:
            # Check optimality
            row0 = t_matrix[0]
            neg_indices = [j for j in range(num_cols) if row0[j] < 0]

            is_optimal = len(neg_indices) == 0

            if is_optimal:
                status = "optimal"
                self._record_step(
                    step_index=iter_num,
                    phase=None,
                    title=f"Tabla {iter_num} - Solución Óptima Alcanzada",
                    t_matrix=t_matrix,
                    col_names=col_names,
                    basis=basis,
                    z_label=z_label,
                    optimality_check={
                        "is_optimal": True,
                        "explanation": (
                            f"En la fila F0 ({z_label}), todos los coeficientes son ≥ 0. "
                            f"No es posible mejorar el valor de la función objetivo. La tabla es ÓPTIMA."
                        ),
                        "candidates": [],
                    },
                    pivot=None,
                    status="optimal",
                )
                break

            # Bland's Rule: choose lowest index among negative coefficients
            entering_col = min(neg_indices)
            entering_var = col_names[entering_col]
            entering_val = row0[entering_col]

            # Minimum ratio test
            ratios: list[dict[str, Any]] = []
            valid_ratios: dict[int, Fraction] = {}

            for i in range(1, num_rows + 1):
                coeff = t_matrix[i][entering_col]
                rhs_val = t_matrix[i][-1]
                row_basis_var = col_names[basis[i - 1]]

                if coeff > 0:
                    ratio = rhs_val / coeff
                    valid_ratios[i] = ratio
                    ratios.append(
                        {
                            "row": i,
                            "base_var": row_basis_var,
                            "rhs": fmt_frac(rhs_val),
                            "coeff": fmt_frac(coeff),
                            "ratio": fmt_frac(ratio),
                            "valid": True,
                            "note": f"{fmt_frac(rhs_val)} / {fmt_frac(coeff)} = {fmt_frac(ratio)}",
                        }
                    )
                else:
                    ratios.append(
                        {
                            "row": i,
                            "base_var": row_basis_var,
                            "rhs": fmt_frac(rhs_val),
                            "coeff": fmt_frac(coeff),
                            "ratio": "-",
                            "valid": False,
                            "note": (
                                f"Entrada ({fmt_frac(coeff)}) ≤ 0: descartada. "
                                f"Incrementar {entering_var} no disminuye la variable básica {row_basis_var}."
                            ),
                        }
                    )

            if not valid_ratios:
                status = "unbounded"
                self._record_step(
                    step_index=iter_num,
                    phase=None,
                    title=f"Tabla {iter_num} - Problema No Acotado",
                    t_matrix=t_matrix,
                    col_names=col_names,
                    basis=basis,
                    z_label=z_label,
                    optimality_check={
                        "is_optimal": False,
                        "explanation": (
                            f"F0 tiene coeficientes negativos ({entering_var}={fmt_frac(entering_val)}), "
                            f"pero en su columna NO existe ninguna entrada positiva (> 0)."
                        ),
                        "candidates": [
                            {"var": col_names[j], "val": fmt_frac(row0[j])}
                            for j in neg_indices
                        ],
                    },
                    pivot=None,
                    status="unbounded",
                )
                break

            # Minimum ratio with Bland tie-breaker (lowest index in basis)
            min_ratio_val = min(valid_ratios.values())
            tied_rows = [
                i for i, r_val in valid_ratios.items() if r_val == min_ratio_val
            ]
            leaving_row = min(tied_rows, key=lambda i: basis[i - 1])
            leaving_var = col_names[basis[leaving_row - 1]]
            pivot_val = t_matrix[leaving_row][entering_col]

            is_degenerate_step = min_ratio_val == 0 or len(tied_rows) > 1
            tie_explanation = ""
            if len(tied_rows) > 1:
                tie_explanation = (
                    f"¡Empate en el cociente mínimo ({fmt_frac(min_ratio_val)}) entre las filas "
                    f"{', '.join('F' + str(i) for i in tied_rows)}! "
                    f"Por la regla de Bland, sale la variable básica con menor subíndice/columna: {leaving_var}."
                )

            # Record detailed row operations before updating
            row_operations = self._calculate_row_operations(
                t_matrix, col_names, leaving_row, entering_col, pivot_val
            )

            pivot_info = {
                "entering_var": entering_var,
                "entering_col": entering_col,
                "entering_cost": fmt_frac(entering_val),
                "leaving_var": leaving_var,
                "leaving_row": leaving_row,
                "pivot_row_label": f"F{leaving_row}",
                "pivot_val": fmt_frac(pivot_val),
                "min_ratio": fmt_frac(min_ratio_val),
                "ratios": ratios,
                "is_degenerate": is_degenerate_step,
                "tie_explanation": tie_explanation,
                "row_operations": row_operations,
            }

            self._record_step(
                step_index=iter_num,
                phase=None,
                title=f"Tabla {iter_num} - Iteración {iter_num} (Entra {entering_var}, Sale {leaving_var})",
                t_matrix=[row[:] for row in t_matrix],
                col_names=col_names,
                basis=list(basis),
                z_label=z_label,
                optimality_check={
                    "is_optimal": False,
                    "explanation": (
                        "F0 tiene coeficientes negativos: "
                        + ", ".join(
                            f"{col_names[j]}={fmt_frac(row0[j])}" for j in neg_indices
                        )
                        + f". Siguiendo la regla de Bland, se selecciona la columna más a la izquierda: entra {entering_var}."
                    ),
                    "candidates": [
                        {"var": col_names[j], "val": fmt_frac(row0[j])}
                        for j in neg_indices
                    ],
                },
                pivot=pivot_info,
                status="continue",
            )

            # Perform Gauss-Jordan pivot
            self._apply_pivot(t_matrix, leaving_row, entering_col, pivot_val)
            basis[leaving_row - 1] = entering_col
            iter_num += 1

        if iter_num > self.max_iterations and status == "continue":
            status = "iteration_limit"

        # Build final report
        final_report = self._build_final_report(
            status=status,
            t_matrix=t_matrix,
            col_names=col_names,
            basis=basis,
            std_cols=std_cols,
            std_var_names=std_var_names,
            initial_submatrix=initial_submatrix,
            c_full=c_full,
            var_transformation_notes=var_transformation_notes,
            norm_notes=norm_notes,
        )

        return {
            "method": "primal",
            "status": status,
            "steps": self.steps,
            "final_report": final_report,
        }

    def _solve_two_phase(
        self,
        std_cols: list[tuple[str, int, Fraction]],
        std_var_names: list[str],
        c_std: list[Fraction],
        norm_constraints: list[dict[str, Any]],
        var_transformation_notes: list[str],
        norm_notes: list[str],
    ) -> dict[str, Any]:
        """Two-Phase Simplex algorithm when artificial variables are needed."""
        num_std_vars = len(std_var_names)
        num_rows = len(norm_constraints)

        # Count slacks, surpluses, and artificials
        col_names = list(std_var_names)
        col_types: list[str] = ["var"] * num_std_vars

        slack_count = 0
        surplus_count = 0
        art_count = 0

        constraint_vars: list[dict[str, Any]] = []

        for i, r in enumerate(norm_constraints):
            sign = r["sign"]
            info: dict[str, Any] = {"slack": None, "surplus": None, "art": None}
            if sign == "<=":
                slack_count += 1
                name = f"s{slack_count}"
                col_names.append(name)
                col_types.append("slack")
                info["slack"] = len(col_names) - 1
            elif sign == ">=":
                surplus_count += 1
                s_name = f"e{surplus_count}"
                col_names.append(s_name)
                col_types.append("surplus")
                info["surplus"] = len(col_names) - 1

                art_count += 1
                a_name = f"a{art_count}"
                col_names.append(a_name)
                col_types.append("artificial")
                info["art"] = len(col_names) - 1
            elif sign == "=":
                art_count += 1
                a_name = f"a{art_count}"
                col_names.append(a_name)
                col_types.append("artificial")
                info["art"] = len(col_names) - 1

            constraint_vars.append(info)

        num_cols = len(col_names)

        # Build initial tableau
        # Rows 1..m
        t_matrix = [[Fraction(0)] * (num_cols + 1) for _ in range(num_rows + 1)]
        basis: list[int] = []

        for i, r in enumerate(norm_constraints, 1):
            info = constraint_vars[i - 1]
            for j in range(num_std_vars):
                t_matrix[i][j] = r["lhs"][j]

            if info["slack"] is not None:
                t_matrix[i][info["slack"]] = Fraction(1)
                basis.append(info["slack"])
            if info["surplus"] is not None:
                t_matrix[i][info["surplus"]] = Fraction(-1)
            if info["art"] is not None:
                t_matrix[i][info["art"]] = Fraction(1)
                basis.append(info["art"])

            t_matrix[i][-1] = r["rhs"]

        # -------------------------------------------------------------
        # PHASE 1: Minimize W = sum(artificial variables)
        # As max -W = -sum(a_i) => W' + sum(a_i) = 0
        # In canonical form, subtract constraint rows having artificial basic vars
        # -------------------------------------------------------------
        art_indices = [idx for idx, t in enumerate(col_types) if t == "artificial"]

        # Initially set F0 with +1 on artificial variables (for max -W, row0 has +1 under a_i)
        for a_idx in art_indices:
            t_matrix[0][a_idx] = Fraction(1)

        # Canonicalize F0 by subtracting pivot rows corresponding to artificial basic variables
        for i, b_idx in enumerate(basis, 1):
            if b_idx in art_indices:
                factor = t_matrix[0][b_idx]
                if factor != 0:
                    for j in range(num_cols + 1):
                        t_matrix[0][j] -= factor * t_matrix[i][j]

        iter_num = 0
        phase1_optimal = False

        while iter_num <= self.max_iterations:
            row0 = t_matrix[0]
            neg_indices = [j for j in range(num_cols) if row0[j] < 0]

            if not neg_indices:
                phase1_optimal = True
                self._record_step(
                    step_index=iter_num,
                    phase=1,
                    title=f"Fase 1 - Tabla {iter_num}: Óptimo de Fase 1",
                    t_matrix=[row[:] for row in t_matrix],
                    col_names=col_names,
                    basis=list(basis),
                    z_label="-W",
                    optimality_check={
                        "is_optimal": True,
                        "explanation": (
                            "En la fila F0 de la Fase 1 (-W), no hay coeficientes negativos. "
                            "Se alcanzó el óptimo de la Fase 1."
                        ),
                        "candidates": [],
                    },
                    pivot=None,
                    status="continue",
                )
                break

            entering_col = min(neg_indices)
            entering_var = col_names[entering_col]
            entering_val = row0[entering_col]

            # Ratio test
            valid_ratios: dict[int, Fraction] = {}
            ratios: list[dict[str, Any]] = []

            for i in range(1, num_rows + 1):
                coeff = t_matrix[i][entering_col]
                rhs_val = t_matrix[i][-1]
                row_basis_var = col_names[basis[i - 1]]

                if coeff > 0:
                    ratio = rhs_val / coeff
                    valid_ratios[i] = ratio
                    ratios.append(
                        {
                            "row": i,
                            "base_var": row_basis_var,
                            "rhs": fmt_frac(rhs_val),
                            "coeff": fmt_frac(coeff),
                            "ratio": fmt_frac(ratio),
                            "valid": True,
                            "note": f"{fmt_frac(rhs_val)} / {fmt_frac(coeff)} = {fmt_frac(ratio)}",
                        }
                    )
                else:
                    ratios.append(
                        {
                            "row": i,
                            "base_var": row_basis_var,
                            "rhs": fmt_frac(rhs_val),
                            "coeff": fmt_frac(coeff),
                            "ratio": "-",
                            "valid": False,
                            "note": f"Entrada ({fmt_frac(coeff)}) ≤ 0: descartada.",
                        }
                    )

            if not valid_ratios:
                # Unbounded in Phase 1
                self._record_step(
                    step_index=iter_num,
                    phase=1,
                    title=f"Fase 1 - Tabla {iter_num}: No Acotado",
                    t_matrix=[row[:] for row in t_matrix],
                    col_names=col_names,
                    basis=list(basis),
                    z_label="-W",
                    optimality_check={
                        "is_optimal": False,
                        "explanation": "No acotado en Fase 1.",
                        "candidates": [],
                    },
                    pivot=None,
                    status="unbounded",
                )
                break

            min_ratio_val = min(valid_ratios.values())
            tied_rows = [
                i for i, r_val in valid_ratios.items() if r_val == min_ratio_val
            ]
            leaving_row = min(tied_rows, key=lambda i: basis[i - 1])
            leaving_var = col_names[basis[leaving_row - 1]]
            pivot_val = t_matrix[leaving_row][entering_col]

            row_operations = self._calculate_row_operations(
                t_matrix, col_names, leaving_row, entering_col, pivot_val
            )

            pivot_info = {
                "entering_var": entering_var,
                "entering_col": entering_col,
                "entering_cost": fmt_frac(entering_val),
                "leaving_var": leaving_var,
                "leaving_row": leaving_row,
                "pivot_row_label": f"F{leaving_row}",
                "pivot_val": fmt_frac(pivot_val),
                "min_ratio": fmt_frac(min_ratio_val),
                "ratios": ratios,
                "is_degenerate": (min_ratio_val == 0 or len(tied_rows) > 1),
                "tie_explanation": "",
                "row_operations": row_operations,
            }

            self._record_step(
                step_index=iter_num,
                phase=1,
                title=f"Fase 1 - Iteración {iter_num} (Entra {entering_var}, Sale {leaving_var})",
                t_matrix=[row[:] for row in t_matrix],
                col_names=col_names,
                basis=list(basis),
                z_label="-W",
                optimality_check={
                    "is_optimal": False,
                    "explanation": f"F0 de Fase 1 contiene coeficientes negativos. Entra {entering_var}.",
                    "candidates": [
                        {"var": col_names[j], "val": fmt_frac(row0[j])}
                        for j in neg_indices
                    ],
                },
                pivot=pivot_info,
                status="continue",
            )

            self._apply_pivot(t_matrix, leaving_row, entering_col, pivot_val)
            basis[leaving_row - 1] = entering_col
            iter_num += 1

        # Check feasibility: W value in B column of F0 must be 0
        w_val = -t_matrix[0][-1]  # since F0 was max -W
        if phase1_optimal and w_val > 0:
            conclusion = generate_contextual_conclusion(
                status="infeasible",
                objective=self.objective,
                z_optimal=None,
                variables={},
                substitutions=[],
                shadow_prices=[],
                context=self.context,
                var_names=self.var_names,
            )
            final_report = {
                "status": "infeasible",
                "message": (
                    f"El problema es INFACTIBLE. Al término de la Fase 1, la suma mínima de "
                    f"las variables artificiales es W = {fmt_frac(w_val)} > 0. "
                    f"No existe ninguna región factible que satisfaga todas las restricciones simultáneamente."
                ),
                "contextual_conclusion": conclusion,
            }
            return {
                "method": "two_phase",
                "status": "infeasible",
                "steps": self.steps,
                "final_report": final_report,
            }

        # -------------------------------------------------------------
        # PHASE 2: Eliminate artificial columns and restore original Z
        # -------------------------------------------------------------
        # Filter out artificial columns (or zero them out)
        keep_cols = [j for j in range(num_cols) if col_types[j] != "artificial"]
        p2_col_names = [col_names[j] for j in keep_cols]
        num_p2_cols = len(p2_col_names)

        # Mapping from old col to new col
        old_to_new = {old_idx: new_idx for new_idx, old_idx in enumerate(keep_cols)}

        # Drive artificial variables that stayed basic (at level 0) out of the
        # basis with a real pivot on a non-artificial column. If the row has no
        # such column it is a redundant constraint and is dropped.
        redundant_rows: set[int] = set()
        for i in range(num_rows):
            if basis[i] in old_to_new:
                continue
            entering = next((c for c in keep_cols if t_matrix[i + 1][c] != 0), None)
            if entering is None:
                redundant_rows.add(i)
                continue
            self._apply_pivot(t_matrix, i + 1, entering, t_matrix[i + 1][entering])
            basis[i] = entering

        kept_rows = [i for i in range(num_rows) if i not in redundant_rows]
        num_p2_rows = len(kept_rows)
        p2_basis = [old_to_new[basis[i]] for i in kept_rows]

        # Create Phase 2 matrix
        p2_matrix = [[Fraction(0)] * (num_p2_cols + 1) for _ in range(num_p2_rows + 1)]
        for new_i, old_i in enumerate(kept_rows, 1):
            for new_idx, old_idx in enumerate(keep_cols):
                p2_matrix[new_i][new_idx] = t_matrix[old_i + 1][old_idx]
            p2_matrix[new_i][-1] = t_matrix[old_i + 1][-1]

        # Restore original objective coefficients in Row 0
        z_label = "Z" if self.objective == "max" else "Z'"
        for j in range(num_std_vars):
            p2_matrix[0][j] = -c_std[j]

        # Canonicalize Phase 2 Row 0 with respect to current basis
        for i, b_col in enumerate(p2_basis, 1):
            factor = p2_matrix[0][b_col]
            if factor != 0:
                for j in range(num_p2_cols + 1):
                    p2_matrix[0][j] -= factor * p2_matrix[i][j]

        # Continue Phase 2 iterations
        status = "continue"
        p2_iter = 0

        while p2_iter <= self.max_iterations:
            row0 = p2_matrix[0]
            neg_indices = [j for j in range(num_p2_cols) if row0[j] < 0]

            if not neg_indices:
                status = "optimal"
                self._record_step(
                    step_index=iter_num,
                    phase=2,
                    title=f"Fase 2 - Tabla {p2_iter}: Solución Óptima Alcanzada",
                    t_matrix=p2_matrix,
                    col_names=p2_col_names,
                    basis=p2_basis,
                    z_label=z_label,
                    optimality_check={
                        "is_optimal": True,
                        "explanation": (
                            f"En la fila F0 ({z_label}), todos los coeficientes son ≥ 0. "
                            f"La solución es ÓPTIMA."
                        ),
                        "candidates": [],
                    },
                    pivot=None,
                    status="optimal",
                )
                break

            entering_col = min(neg_indices)
            entering_var = p2_col_names[entering_col]
            entering_val = row0[entering_col]

            valid_ratios = {}
            ratios = []

            for i in range(1, num_p2_rows + 1):
                coeff = p2_matrix[i][entering_col]
                rhs_val = p2_matrix[i][-1]
                row_basis_var = p2_col_names[p2_basis[i - 1]]

                if coeff > 0:
                    ratio = rhs_val / coeff
                    valid_ratios[i] = ratio
                    ratios.append(
                        {
                            "row": i,
                            "base_var": row_basis_var,
                            "rhs": fmt_frac(rhs_val),
                            "coeff": fmt_frac(coeff),
                            "ratio": fmt_frac(ratio),
                            "valid": True,
                            "note": f"{fmt_frac(rhs_val)} / {fmt_frac(coeff)} = {fmt_frac(ratio)}",
                        }
                    )
                else:
                    ratios.append(
                        {
                            "row": i,
                            "base_var": row_basis_var,
                            "rhs": fmt_frac(rhs_val),
                            "coeff": fmt_frac(coeff),
                            "ratio": "-",
                            "valid": False,
                            "note": f"Entrada ({fmt_frac(coeff)}) ≤ 0: descartada.",
                        }
                    )

            if not valid_ratios:
                status = "unbounded"
                self._record_step(
                    step_index=iter_num,
                    phase=2,
                    title=f"Fase 2 - Tabla {p2_iter}: No Acotado",
                    t_matrix=p2_matrix,
                    col_names=p2_col_names,
                    basis=p2_basis,
                    z_label=z_label,
                    optimality_check={
                        "is_optimal": False,
                        "explanation": f"Columna {entering_var} no tiene entradas positivas: problema NO ACOTADO.",
                        "candidates": [],
                    },
                    pivot=None,
                    status="unbounded",
                )
                break

            min_ratio_val = min(valid_ratios.values())
            tied_rows = [
                i for i, r_val in valid_ratios.items() if r_val == min_ratio_val
            ]
            leaving_row = min(tied_rows, key=lambda i: p2_basis[i - 1])
            leaving_var = p2_col_names[p2_basis[leaving_row - 1]]
            pivot_val = p2_matrix[leaving_row][entering_col]

            row_operations = self._calculate_row_operations(
                p2_matrix, p2_col_names, leaving_row, entering_col, pivot_val
            )

            pivot_info = {
                "entering_var": entering_var,
                "entering_col": entering_col,
                "entering_cost": fmt_frac(entering_val),
                "leaving_var": leaving_var,
                "leaving_row": leaving_row,
                "pivot_row_label": f"F{leaving_row}",
                "pivot_val": fmt_frac(pivot_val),
                "min_ratio": fmt_frac(min_ratio_val),
                "ratios": ratios,
                "is_degenerate": (min_ratio_val == 0 or len(tied_rows) > 1),
                "tie_explanation": "",
                "row_operations": row_operations,
            }

            self._record_step(
                step_index=iter_num,
                phase=2,
                title=f"Fase 2 - Iteración {p2_iter} (Entra {entering_var}, Sale {leaving_var})",
                t_matrix=[row[:] for row in p2_matrix],
                col_names=p2_col_names,
                basis=list(p2_basis),
                z_label=z_label,
                optimality_check={
                    "is_optimal": False,
                    "explanation": f"F0 contiene coeficientes negativos. Entra {entering_var}.",
                    "candidates": [
                        {"var": p2_col_names[j], "val": fmt_frac(row0[j])}
                        for j in neg_indices
                    ],
                },
                pivot=pivot_info,
                status="continue",
            )

            self._apply_pivot(p2_matrix, leaving_row, entering_col, pivot_val)
            p2_basis[leaving_row - 1] = entering_col
            iter_num += 1
            p2_iter += 1

        # Final report
        final_report = self._build_final_report(
            status=status,
            t_matrix=p2_matrix,
            col_names=p2_col_names,
            basis=p2_basis,
            std_cols=std_cols,
            std_var_names=std_var_names,
            initial_submatrix=None,
            c_full=None,
            var_transformation_notes=var_transformation_notes,
            norm_notes=norm_notes,
        )

        return {
            "method": "two_phase",
            "status": status,
            "steps": self.steps,
            "final_report": final_report,
        }

    def _calculate_row_operations(
        self,
        t_matrix: list[list[Fraction]],
        col_names: list[str],
        leaving_row: int,
        entering_col: int,
        pivot_val: Fraction,
    ) -> list[dict[str, Any]]:
        """Calculates step-by-step arithmetic details for row operations."""
        ops = []
        n_cols = len(col_names)

        # 1. Pivot row normalization: F_r <- F_r / pivot_val
        old_p_row = t_matrix[leaving_row][:]
        new_p_row = [v / pivot_val for v in old_p_row]

        details_pivot = []
        for j in range(n_cols):
            details_pivot.append(
                {
                    "var": col_names[j],
                    "calc": f"{fmt_frac(old_p_row[j])} / {fmt_frac(pivot_val)}",
                    "result": fmt_frac(new_p_row[j]),
                }
            )
        details_pivot.append(
            {
                "var": "B",
                "calc": f"{fmt_frac(old_p_row[-1])} / {fmt_frac(pivot_val)}",
                "result": fmt_frac(new_p_row[-1]),
            }
        )

        ops.append(
            {
                "row_idx": leaving_row,
                "row_label": f"F{leaving_row}",
                "type": "normalize",
                "formula": (
                    f"F{leaving_row} ← F{leaving_row} / ({fmt_frac(pivot_val)})"
                    if pivot_val != 1
                    else f"F{leaving_row} (el pivote ya es 1, no cambia)"
                ),
                "details": details_pivot,
            }
        )

        # 2. Elimination on other rows
        for i in range(len(t_matrix)):
            if i == leaving_row:
                continue
            factor = t_matrix[i][entering_col]
            if factor == 0:
                ops.append(
                    {
                        "row_idx": i,
                        "row_label": f"F{i}",
                        "type": "unchanged",
                        "formula": f"F{i}: ya tiene 0 en la columna de entrada ({col_names[entering_col]}); no cambia.",
                        "details": [],
                    }
                )
            else:
                old_row = t_matrix[i][:]
                new_row = [
                    old_row[j] - factor * new_p_row[j] for j in range(len(old_row))
                ]
                details_elim = []
                for j in range(n_cols):
                    details_elim.append(
                        {
                            "var": col_names[j],
                            "calc": f"{fmt_frac(old_row[j])} - ({fmt_frac(factor)}) × ({fmt_frac(new_p_row[j])})",
                            "result": fmt_frac(new_row[j]),
                        }
                    )
                details_elim.append(
                    {
                        "var": "B",
                        "calc": f"{fmt_frac(old_row[-1])} - ({fmt_frac(factor)}) × ({fmt_frac(new_p_row[-1])})",
                        "result": fmt_frac(new_row[-1]),
                    }
                )

                ops.append(
                    {
                        "row_idx": i,
                        "row_label": f"F{i}",
                        "type": "eliminate",
                        "formula": f"F{i} ← F{i} - ({fmt_frac(factor)}) × F{leaving_row}",
                        "details": details_elim,
                    }
                )

        return ops

    def _apply_pivot(
        self,
        t_matrix: list[list[Fraction]],
        leaving_row: int,
        entering_col: int,
        pivot_val: Fraction,
    ) -> None:
        """Applies Gauss-Jordan pivoting in-place."""
        # Normalize pivot row
        t_matrix[leaving_row] = [v / pivot_val for v in t_matrix[leaving_row]]

        # Eliminate in all other rows
        p_row = t_matrix[leaving_row]
        for i in range(len(t_matrix)):
            if i == leaving_row:
                continue
            factor = t_matrix[i][entering_col]
            if factor != 0:
                t_matrix[i] = [
                    t_matrix[i][j] - factor * p_row[j] for j in range(len(t_matrix[i]))
                ]

    def _record_step(
        self,
        step_index: int,
        phase: int | None,
        title: str,
        t_matrix: list[list[Fraction]],
        col_names: list[str],
        basis: list[int],
        z_label: str,
        optimality_check: dict[str, Any],
        pivot: dict[str, Any] | None,
        status: str,
    ) -> None:
        """Saves a structured snapshot of a tableau state."""
        num_rows = len(t_matrix)
        rows_data = []

        for i in range(num_rows):
            row_label = f"F{i}"
            base_var = z_label if i == 0 else col_names[basis[i - 1]]
            cells = [fmt_cell(v) for v in t_matrix[i]]
            rows_data.append(
                {
                    "row_idx": i,
                    "row_label": row_label,
                    "base_var": base_var,
                    "cells": cells,
                    "rhs": fmt_cell(t_matrix[i][-1]),
                }
            )

        self.steps.append(
            {
                "step_index": step_index,
                "phase": phase,
                "title": title,
                "headers": ["Fila", "Base"] + col_names + ["B"],
                "col_names": col_names,
                "z_label": z_label,
                "rows": rows_data,
                "z_val": fmt_cell(t_matrix[0][-1]),
                "basis_vars": [col_names[idx] for idx in basis],
                "optimality_check": optimality_check,
                "pivot": pivot,
                "status": status,
            }
        )

    def _build_final_report(
        self,
        status: str,
        t_matrix: list[list[Fraction]],
        col_names: list[str],
        basis: list[int],
        std_cols: list[tuple[str, int, Fraction]],
        std_var_names: list[str],
        initial_submatrix: list[list[Fraction]] | None,
        c_full: list[Fraction] | None,
        var_transformation_notes: list[str],
        norm_notes: list[str],
    ) -> dict[str, Any]:
        """Constructs a comprehensive post-optimal analysis report."""
        if status != "optimal":
            conclusion = generate_contextual_conclusion(
                status=status,
                objective=self.objective,
                z_optimal=None,
                variables={},
                substitutions=[],
                shadow_prices=[],
                context=self.context,
                var_names=self.var_names,
            )
            return {
                "status": status,
                "message": (
                    "El problema es no acotado: la función objetivo puede crecer sin límite."
                    if status == "unbounded"
                    else "No se alcanzó una solución óptima."
                ),
                "contextual_conclusion": conclusion,
            }

        # Retrieve current variable values from the final tableau
        var_values: dict[str, Fraction] = {name: Fraction(0) for name in col_names}
        for i, b_idx in enumerate(basis, 1):
            var_name = col_names[b_idx]
            var_values[var_name] = t_matrix[i][-1]

        # Calculate values for original decision variables
        orig_x: dict[str, Fraction] = {name: Fraction(0) for name in self.var_names}
        for col_name, orig_idx, mult in std_cols:
            orig_var_name = self.var_names[orig_idx]
            orig_x[orig_var_name] += mult * var_values.get(col_name, Fraction(0))

        # Optimal Z value
        z_internal = t_matrix[0][-1]
        z_optimal = z_internal if self.objective == "max" else -z_internal

        # Substitution verification in original constraints
        substitutions = []
        all_satisfied = True

        for i, r in enumerate(self.raw_constraints, 1):
            lhs_val = sum(
                r["lhs"][j] * orig_x[self.var_names[j]]
                for j in range(self.num_orig_vars)
            )
            rhs_val = r["rhs"]
            sign = r["sign"]

            satisfied = (
                lhs_val <= rhs_val
                if sign == "<="
                else (lhs_val >= rhs_val if sign == ">=" else lhs_val == rhs_val)
            )
            all_satisfied = all_satisfied and satisfied

            slack_diff = rhs_val - lhs_val if sign == "<=" else lhs_val - rhs_val
            is_active = lhs_val == rhs_val

            terms_expr = (
                " + ".join(
                    f"({fmt_frac(r['lhs'][j])})×({fmt_frac(orig_x[self.var_names[j]])})"
                    for j in range(self.num_orig_vars)
                    if r["lhs"][j] != 0
                )
                or "0"
            )

            substitutions.append(
                {
                    "index": i,
                    "label": f"R{i}",
                    "expression": f"{terms_expr} = {fmt_frac(lhs_val)} {sign} {fmt_frac(rhs_val)}",
                    "lhs": fmt_frac(lhs_val),
                    "sign": sign,
                    "rhs": fmt_frac(rhs_val),
                    "satisfied": satisfied,
                    "is_active": is_active,
                    "slack_value": fmt_frac(slack_diff),
                    "status_text": (
                        "Restricción ACTIVA (recurso agotado)"
                        if is_active
                        else f"Holgura/Exceso = {fmt_frac(slack_diff)}"
                    ),
                }
            )

        # Degeneracy check
        degenerate_vars = [
            col_names[basis[i - 1]]
            for i in range(1, len(basis) + 1)
            if t_matrix[i][-1] == 0
        ]
        is_degenerate = len(degenerate_vars) > 0
        degeneracy_msg = (
            f"Solución degenerada: las variables básicas {', '.join(degenerate_vars)} tienen valor 0."
            if is_degenerate
            else "Solución no degenerada: todas las variables básicas son estrictamente positivas (> 0)."
        )

        # Alternative optima check: non-basic variable with coefficient 0 in F0
        alt_candidates = [
            col_names[j]
            for j in range(len(col_names))
            if j not in basis and t_matrix[0][j] == 0
        ]
        has_alternatives = len(alt_candidates) > 0
        alt_msg = (
            f"Existen infinitas soluciones óptimas alternativas: las variables no básicas "
            f"{', '.join(alt_candidates)} tienen costo reducido 0 en F0."
            if has_alternatives
            else "El punto óptimo encontrado es ÚNICO."
        )

        # Sensitivity analysis / Shadow prices (Precios Sombra)
        shadow_prices = []
        if initial_submatrix and c_full and len(basis) == len(initial_submatrix):
            try:
                m_size = len(basis)
                # Form basis matrix B from initial columns corresponding to optimal basis
                b_mat = [
                    [initial_submatrix[r][basis[k]] for k in range(m_size)]
                    for r in range(m_size)
                ]
                b_inv = invert_matrix(b_mat)
                c_b = [c_full[j] for j in basis]
                # Simplex multipliers y = c_B * B^(-1)
                y = [
                    sum(c_b[k] * b_inv[k][r] for k in range(m_size))
                    for r in range(m_size)
                ]

                for i, r in enumerate(self.raw_constraints, 1):
                    # For simple <= constraint, shadow price is y[i-1]
                    p = y[i - 1] if self.objective == "max" else -y[i - 1]
                    shadow_prices.append(
                        {
                            "constraint": f"R{i}",
                            "price": fmt_frac(p),
                            "price_float": float(p),
                            "interpretation": (
                                f"Por cada unidad adicional en el lado derecho de R{i}, "
                                f"Z aumentará en {fmt_frac(p)} unidades (mientras la base actual permanezca factible)."
                            ),
                        }
                    )
            except (ValueError, ZeroDivisionError):
                shadow_prices = []

        # Generate executive contextual conclusion
        conclusion = generate_contextual_conclusion(
            status="optimal",
            objective=self.objective,
            z_optimal=fmt_cell(z_optimal),
            variables={name: fmt_cell(orig_x[name]) for name in self.var_names},
            substitutions=substitutions,
            shadow_prices=shadow_prices,
            context=self.context,
            var_names=self.var_names,
        )

        return {
            "status": "optimal",
            "objective": self.objective,
            "z_optimal": fmt_cell(z_optimal),
            "variables": {name: fmt_cell(orig_x[name]) for name in self.var_names},
            "all_variables": {name: fmt_cell(var_values[name]) for name in col_names},
            "substitutions": substitutions,
            "all_satisfied": all_satisfied,
            "degeneracy": {
                "is_degenerate": is_degenerate,
                "message": degeneracy_msg,
                "vars": degenerate_vars,
            },
            "alternative_optima": {
                "has_alternatives": has_alternatives,
                "message": alt_msg,
                "candidates": alt_candidates,
            },
            "shadow_prices": shadow_prices,
            "transformation_notes": var_transformation_notes,
            "normalization_notes": norm_notes,
            "contextual_conclusion": conclusion,
        }
