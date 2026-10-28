"""Método de las Dos Fases con aritmética exacta (fracciones).

Convenciones de la tabla (las mismas del curso):

- Fase 1: ``r - ΣAᵢ = 0``. Entra el mayor coeficiente positivo de la fila r;
  termina cuando no quedan positivos. Si ``r > 0`` el problema es infactible.
- Fase 2: ``Z - Σcⱼxⱼ = 0``. En MAX entra el coeficiente más negativo de la
  fila Z (en MIN, el más positivo); termina cuando ya no hay candidatos.
- Razón mínima ``K / aᵢⱼ`` sólo con ``aᵢⱼ > 0``.

Cada tabla intermedia se guarda como un paso para poder mostrar el
procedimiento completo en el frontend.
"""

from fractions import Fraction

SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
MAX_ITERATIONS = 100


def _sub(i):
    return str(i).translate(SUBSCRIPTS)


def _frac(value):
    # str() first so JS floats like 0.1 become 1/10, not their binary expansion
    return Fraction(str(value).strip())


def fmt(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _signed(value):
    return f"({fmt(value)})"


class TwoPhaseSolver:
    def __init__(self, problem):
        self.sense = problem.get("sense", "max").lower()
        if self.sense not in ("max", "min"):
            raise ValueError("sense debe ser 'max' o 'min'")

        self.c = [_frac(v) for v in problem["objective"]]
        n = len(self.c)
        if n == 0:
            raise ValueError("La función objetivo no tiene variables")
        constraints = problem["constraints"]
        if not constraints:
            raise ValueError("Se necesita al menos una restricción")

        self.n = n
        self.m = len(constraints)
        self.steps = []

        # Columnas: x₁..xₙ, S₁..Sₘ (una por restricción, como en el curso), A's
        self.columns = [f"x{_sub(j + 1)}" for j in range(n)]
        self.columns += [f"S{_sub(i + 1)}" for i in range(self.m)]
        self.artificial_cols = []

        rows, kinds = [], []
        for i, con in enumerate(constraints):
            coefs = [_frac(v) for v in con["coefs"]]
            if len(coefs) != n:
                raise ValueError(f"R{_sub(i + 1)} debe tener {n} coeficientes")
            kind = con["type"]
            if kind not in ("<=", ">=", "="):
                raise ValueError(
                    f"Tipo de restricción inválido en R{_sub(i + 1)}: {kind}"
                )
            rhs = _frac(con["rhs"])
            if rhs < 0:
                # K debe ser no negativo: multiplicamos por -1 e invertimos el sentido
                coefs = [-a for a in coefs]
                rhs = -rhs
                kind = {"<=": ">=", ">=": "<=", "=": "="}[kind]
            rows.append((coefs, rhs))
            kinds.append(kind)

        artificial_of_row = {}
        for i, kind in enumerate(kinds):
            if kind != "<=":
                artificial_of_row[i] = len(self.columns)
                self.artificial_cols.append(len(self.columns))
                self.columns.append(f"A{_sub(i + 1)}")

        width = len(self.columns)
        self.tableau = []
        self.basis = []
        for i, ((coefs, rhs), kind) in enumerate(zip(rows, kinds, strict=True)):
            row = [Fraction(0)] * (width + 1)
            row[:n] = coefs
            slack = n + i
            if kind == "<=":
                row[slack] = Fraction(1)
                self.basis.append(slack)
            else:
                if kind == ">=":
                    row[slack] = Fraction(-1)
                row[artificial_of_row[i]] = Fraction(1)
                self.basis.append(artificial_of_row[i])
            row[-1] = rhs
            self.tableau.append(row)

        self.kinds = kinds
        self.obj_label = "r"
        self.obj = [Fraction(0)] * (width + 1)

    # ------------------------------------------------------------------ helpers
    def _row_label(self, i):
        return self.columns[self.basis[i]]

    def _snapshot(self, phase, title, notes=None, operations=None, **extra):
        self.steps.append(
            {
                "phase": phase,
                "title": title,
                "notes": notes or [],
                "operations": operations or [],
                "columns": list(self.columns),
                "objective": {
                    "label": self.obj_label,
                    "values": [fmt(v) for v in self.obj],
                },
                "rows": [
                    {"basis": self._row_label(i), "values": [fmt(v) for v in row]}
                    for i, row in enumerate(self.tableau)
                ],
                **extra,
            }
        )

    def _combine_into_objective(self, row_indices, label):
        """Hace cero en la fila objetivo las columnas de las variables básicas dadas."""
        terms, ops = [], []
        for i in row_indices:
            col = self.basis[i]
            factor = -self.obj[col]
            if factor == 0:
                continue
            row = self.tableau[i]
            self.obj = [o + factor * a for o, a in zip(self.obj, row, strict=True)]
            terms.append(f"{_signed(factor)}R{self._row_label(i)}")
        if terms:
            ops.append(f"{label} = " + " + ".join(terms) + f" + {label}")
        return ops

    def _choose_entering(self, phase):
        candidates = [
            j
            for j in range(len(self.columns))
            if j not in self.basis and not (phase == 2 and j in self.artificial_cols)
        ]
        want_positive = phase == 1 or self.sense == "min"
        best = None
        for j in candidates:
            v = self.obj[j]
            is_candidate = v > 0 if want_positive else v < 0
            if is_candidate and (best is None or abs(v) > abs(self.obj[best])):
                best = j
        return best

    def _ratios(self, col):
        ratios = []
        for i, row in enumerate(self.tableau):
            a = row[col]
            entry = {"basis": self._row_label(i), "coef": fmt(a)}
            if a > 0:
                entry["ratio"] = fmt(row[-1] / a)
                entry["text"] = f"{fmt(row[-1])} / {fmt(a)} = {fmt(row[-1] / a)}"
            else:
                entry["ratio"] = None
                entry["text"] = f"coeficiente {fmt(a)} → no participa"
            ratios.append(entry)
        return ratios

    def _choose_leaving(self, col):
        best = None
        for i, row in enumerate(self.tableau):
            if row[col] > 0:
                ratio = row[-1] / row[col]
                if best is None or ratio < best[0]:
                    best = (ratio, i)
        return None if best is None else best[1]

    def _pivot(self, r, col):
        ops = []
        pivot = self.tableau[r][col]
        leaving_label = self._row_label(r)
        self.tableau[r] = [v / pivot for v in self.tableau[r]]
        ops.append(f"R{leaving_label} nueva = R{leaving_label} / {_signed(pivot)}")
        self.basis[r] = col
        pr = self.tableau[r]

        factor = -self.obj[col]
        if factor != 0:
            self.obj = [o + factor * p for o, p in zip(self.obj, pr, strict=True)]
            ops.append(f"{self.obj_label} = {_signed(factor)}Rp + {self.obj_label}")
        for i, row in enumerate(self.tableau):
            if i == r:
                continue
            factor = -row[col]
            if factor == 0:
                ops.append(f"R{self._row_label(i)} permanece igual (ya tiene 0)")
                continue
            self.tableau[i] = [v + factor * p for v, p in zip(row, pr, strict=True)]
            ops.append(
                f"R{self._row_label(i)} = {_signed(factor)}Rp + R{self._row_label(i)}"
            )
        return ops

    def _iterate(self, phase):
        iteration = 0
        while True:
            col = self._choose_entering(phase)
            if col is None:
                return "done"
            iteration += 1
            if iteration > MAX_ITERATIONS:
                raise RuntimeError("Se superó el número máximo de iteraciones")
            ratios = self._ratios(col)
            r = self._choose_leaving(col)
            entering = self.columns[col]
            if r is None:
                self._snapshot(
                    phase,
                    f"Fase {phase} · Iteración {iteration}",
                    notes=[
                        f"Entra {entering}, pero ningún coeficiente de su columna es positivo.",
                        "El problema es no acotado.",
                    ],
                    entering=entering,
                    ratios=ratios,
                )
                return "unbounded"
            leaving = self._row_label(r)
            pivot = self.tableau[r][col]
            criterion = (
                "mayor coeficiente positivo de la fila r"
                if phase == 1
                else (
                    "coeficiente más negativo de la fila Z"
                    if self.sense == "max"
                    else "coeficiente más positivo de la fila Z"
                )
            )
            notes = [
                f"Entra {entering} ({criterion}: {fmt(self.obj[col])}).",
                f"Menor razón = {ratios[r]['ratio']} → sale {leaving}.",
                f"Elemento pivote: {fmt(pivot)}.",
            ]
            ops = self._pivot(r, col)
            self._snapshot(
                phase,
                f"Fase {phase} · Iteración {iteration}",
                notes=notes,
                operations=ops,
                entering=entering,
                leaving=leaving,
                ratios=ratios,
                pivot={"row": r, "col": col},
            )

    def _drive_out_artificials(self):
        """Saca de la base artificiales que quedaron en nivel 0 al terminar la Fase 1."""
        i = 0
        while i < len(self.tableau):
            if self.basis[i] not in self.artificial_cols:
                i += 1
                continue
            label = self._row_label(i)
            col = next(
                (
                    j
                    for j in range(len(self.columns))
                    if j not in self.artificial_cols and self.tableau[i][j] != 0
                ),
                None,
            )
            if col is None:
                del self.tableau[i]
                del self.basis[i]
                self._snapshot(
                    1,
                    "Fase 1 · Restricción redundante",
                    notes=[
                        f"{label} sigue en la base con valor 0 y su fila es redundante: se elimina."
                    ],
                )
                continue
            ops = self._pivot(i, col)
            self._snapshot(
                1,
                "Fase 1 · Sacar artificial de la base",
                notes=[
                    f"{label} quedó en la base con valor 0; entra {self.columns[col]} para reemplazarla."
                ],
                operations=ops,
                entering=self.columns[col],
                leaving=label,
                pivot={"row": i, "col": col},
            )
            i += 1

    # -------------------------------------------------------------------- solve
    def solve(self):
        if self.artificial_cols:
            self._phase_one()
            if self.obj[-1] != 0:
                return self._result("infeasible")
            self._drive_out_artificials()
            self._remove_artificials()
        else:
            self.steps.append(
                {
                    "phase": 1,
                    "title": "Fase 1 · No es necesaria",
                    "notes": [
                        "Todas las restricciones son ≤: las holguras ya forman una base factible."
                    ],
                    "operations": [],
                }
            )

        status = self._phase_two()
        return self._result(status)

    def _phase_one(self):
        self.obj_label = "r"
        width = len(self.columns) + 1
        self.obj = [Fraction(0)] * width
        for j in self.artificial_cols:
            self.obj[j] = Fraction(-1)
        names = " − ".join(self.columns[j] for j in self.artificial_cols)
        self._snapshot(
            1,
            "Fase 1 · Tabla inicial",
            notes=[
                "MIN r = " + " + ".join(self.columns[j] for j in self.artificial_cols),
                f"r − {names} = 0",
                "Base inicial: " + ", ".join(self._row_label(i) for i in range(self.m)),
            ],
        )
        rows = [
            i for i in range(len(self.tableau)) if self.basis[i] in self.artificial_cols
        ]
        ops = self._combine_into_objective(rows, "r")
        self._snapshot(
            1,
            "Fase 1 · Fila r reducida",
            notes=["Las artificiales básicas deben tener coeficiente 0 en la fila r."],
            operations=ops,
        )
        status = self._iterate(1)
        r_value = self.obj[-1]
        if status == "unbounded":  # no ocurre en Fase 1 (r ≥ 0), por seguridad
            raise RuntimeError("Fase 1 no acotada")
        if r_value != 0:
            self._snapshot(
                1,
                "Fase 1 · Final",
                notes=[f"r = {fmt(r_value)} > 0 → el problema original es infactible."],
            )
        else:
            self._snapshot(
                1,
                "Fase 1 · Final",
                notes=[
                    "r = 0 → encontramos una solución básica factible.",
                    "Base: "
                    + ", ".join(self._row_label(i) for i in range(len(self.tableau))),
                ],
            )

    def _remove_artificials(self):
        keep = [j for j in range(len(self.columns)) if j not in self.artificial_cols]
        remap = {old: new for new, old in enumerate(keep)}
        self.columns = [self.columns[j] for j in keep]
        self.tableau = [[row[j] for j in keep] + [row[-1]] for row in self.tableau]
        self.basis = [remap[b] for b in self.basis]
        self.artificial_cols = []

    def _phase_two(self):
        self.obj_label = "Z"
        width = len(self.columns) + 1
        self.obj = [Fraction(0)] * width
        for j, cj in enumerate(self.c):
            self.obj[j] = -cj
        terms = " ".join(
            f"{'−' if cj > 0 else '+'} {fmt(abs(cj))}{self.columns[j]}"
            for j, cj in enumerate(self.c)
            if cj != 0
        )
        objective = " + ".join(
            f"{fmt(cj)}{self.columns[j]}" for j, cj in enumerate(self.c)
        )
        self._snapshot(
            2,
            "Fase 2 · Tabla inicial (función original visible)",
            notes=[
                f"{self.sense.upper()} Z = {objective}",
                f"Z {terms} = 0",
                "Se eliminan la fila r y las columnas artificiales; se conserva la base.",
            ],
        )
        ops = self._combine_into_objective(range(len(self.tableau)), "Z")
        self._snapshot(
            2,
            "Fase 2 · Fila Z en forma canónica",
            notes=["Las variables básicas deben tener coeficiente 0 en la fila Z."],
            operations=ops or ["La fila Z ya es compatible con la base."],
        )
        status = self._iterate(2)
        if status == "done":
            self._snapshot(
                2,
                "Fase 2 · Tabla final",
                notes=[
                    "No quedan coeficientes "
                    + ("negativos" if self.sense == "max" else "positivos")
                    + " en Z → solución óptima."
                ],
            )
            return "optimal"
        return status

    def _result(self, status):
        result = {"status": status, "steps": self.steps}
        if status == "optimal":
            values = {name: Fraction(0) for name in self.columns}
            for i, b in enumerate(self.basis):
                values[self.columns[b]] = self.tableau[i][-1]
            result["solution"] = {name: fmt(v) for name, v in values.items()}
            result["decision"] = {
                name: fmt(values[name]) for name in self.columns[: self.n]
            }
            result["z"] = fmt(self.obj[-1])
            result["z_float"] = float(self.obj[-1])
        return result


def solve(problem):
    """Resuelve un problema de PL con el Método de las Dos Fases.

    ``problem`` = ``{"sense": "max"|"min", "objective": [c₁, ...],
    "constraints": [{"coefs": [...], "type": "<="|">="|"=", "rhs": b}, ...]}``.
    Los números pueden ser int, float o cadenas como ``"1/2"``.
    """
    return TwoPhaseSolver(problem).solve()
