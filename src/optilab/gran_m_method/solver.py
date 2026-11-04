"""Método de la Gran M con aritmética exacta (fracciones).

Convenciones de la tabla (las mismas del curso):

- Cada restricción ``≤`` suma una holgura Sᵢ (básica); ``≥`` resta un exceso Sᵢ
  y suma una artificial Aₖ; ``=`` sólo suma una artificial Aₖ.
- Fila Z escrita como ecuación ``Z - Σcⱼxⱼ ± ΣM·Aₖ = 0``: MIN penaliza con
  ``+M`` (coeficiente ``-M`` en la fila) y MAX con ``-M`` (coeficiente ``+M``).
- Entra el coeficiente más positivo de la fila Z en MIN (el más negativo en
  MAX); termina cuando ya no hay candidatos. Razón mínima ``K / aᵢⱼ`` sólo
  con ``aᵢⱼ > 0``.
- Si al terminar una artificial sigue básica con valor positivo, el problema
  es infactible.

Los números de la fila Z son de la forma ``a + b·M`` y se comparan de forma
exacta (primero ``b``, luego ``a``), sin sustituir M por un número grande.
"""

from dataclasses import dataclass
from fractions import Fraction

SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
MAX_ITERATIONS = 100
ZERO = Fraction(0)
ONE = Fraction(1)


def _sub(i):
    return str(i).translate(SUBSCRIPTS)


def _frac(value):
    # str() first so JS floats like 0.1 become 1/10, not their binary expansion
    return Fraction(str(value).strip())


def fmt(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class MNum:
    """Número ``const + m·M`` con M simbólico y arbitrariamente grande."""

    const: Fraction = ZERO
    m: Fraction = ZERO

    def __add__(self, other):
        return MNum(self.const + other.const, self.m + other.m)

    def __sub__(self, other):
        return MNum(self.const - other.const, self.m - other.m)

    def __neg__(self):
        return MNum(-self.const, -self.m)

    def scale(self, k):
        return MNum(self.const * k, self.m * k)

    def sign(self):
        """Signo exacto: el término en M domina a la constante."""
        for part in (self.m, self.const):
            if part:
                return 1 if part > 0 else -1
        return 0


def fmt_m(value):
    if value.m == 0:
        return fmt(value.const)
    if value.m == 1:
        coef = "M"
    elif value.m == -1:
        coef = "-M"
    elif value.m.denominator == 1:
        coef = f"{fmt(value.m)}M"
    else:
        coef = f"({fmt(value.m)})M"
    if value.const == 0:
        return coef
    return f"{coef}{'+' if value.const > 0 else '-'}{fmt(abs(value.const))}"


def _signed(value):
    return f"({fmt(value)})"


def _parse(problem):
    sense = str(problem.get("sense", "max")).lower()
    if sense not in ("max", "min"):
        raise ValueError("sense debe ser 'max' o 'min'")

    objective = [_frac(v) for v in problem["objective"]]
    if not objective:
        raise ValueError("La función objetivo no tiene variables")
    constraints = problem["constraints"]
    if not constraints:
        raise ValueError("Se necesita al menos una restricción")

    rows = []
    for i, con in enumerate(constraints):
        coefs = [_frac(v) for v in con["coefs"]]
        if len(coefs) != len(objective):
            raise ValueError(f"R{_sub(i + 1)} debe tener {len(objective)} coeficientes")
        kind = con["type"]
        if kind not in ("<=", ">=", "="):
            raise ValueError(f"Tipo de restricción inválido en R{_sub(i + 1)}: {kind}")
        rhs = _frac(con["rhs"])
        if rhs < 0:
            # K debe ser no negativo: multiplicamos por -1 e invertimos el sentido
            coefs = [-a for a in coefs]
            rhs = -rhs
            kind = {"<=": ">=", ">=": "<=", "=": "="}[kind]
        rows.append((coefs, kind, rhs))
    return sense, objective, rows


class GranMSolver:
    def __init__(self, problem):
        self.problem = problem
        self.sense, self.c, parsed = _parse(problem)
        n = self.n = len(self.c)
        self.m = len(parsed)
        self.steps = []

        self.columns = [f"x{_sub(j + 1)}" for j in range(n)]
        slack_col, art_col = {}, {}
        for i, (_, kind, _) in enumerate(parsed):
            if kind != "=":
                slack_col[i] = len(self.columns)
                self.columns.append(f"S{_sub(i + 1)}")
        for i, (_, kind, _) in enumerate(parsed):
            if kind != "<=":
                art_col[i] = len(self.columns)
                self.columns.append(f"A{_sub(len(art_col))}")
        self.artificial_cols = list(art_col.values())

        width = len(self.columns)
        self.tableau, self.basis, self.equations = [], [], []
        for i, (coefs, kind, rhs) in enumerate(parsed):
            row = [ZERO] * (width + 1)
            row[:n] = coefs
            if kind == "<=":
                row[slack_col[i]] = ONE
                self.basis.append(slack_col[i])
            else:
                if kind == ">=":
                    row[slack_col[i]] = -ONE
                row[art_col[i]] = ONE
                self.basis.append(art_col[i])
            row[-1] = rhs
            self.tableau.append(row)
            self.equations.append(self._equation(row))

        penalty = MNum(ZERO, -ONE if self.sense == "min" else ONE)
        self.obj = [MNum(-c) for c in self.c]
        self.obj += [MNum() for _ in range(width - n)]
        for col in self.artificial_cols:
            self.obj[col] = penalty
        self.obj.append(MNum())

    # ------------------------------------------------------------------ helpers
    def _equation(self, row):
        text = ""
        for name, coef in zip(self.columns, row[:-1], strict=True):
            if coef == 0:
                continue
            magnitude = "" if abs(coef) == 1 else fmt(abs(coef))
            text += f" {'-' if coef < 0 else '+'} {magnitude}{name}"
        return f"{text.removeprefix(' +').strip()} = {fmt(row[-1])}"

    def _snapshot(self, title, notes=None, operations=None, table=True, **extra):
        step = {
            "title": title,
            "notes": notes or [],
            "operations": operations or [],
            **extra,
        }
        if table:
            step["columns"] = list(self.columns)
            step["objective"] = {"label": "Z", "values": [fmt_m(v) for v in self.obj]}
            step["rows"] = [
                {"basis": self.columns[self.basis[i]], "values": [fmt(v) for v in row]}
                for i, row in enumerate(self.tableau)
            ]
        self.steps.append(step)
        return step

    def _eliminate_artificials(self):
        """Hace cero en la fila Z las artificiales que están en la base."""
        ops = []
        for i, col in enumerate(self.basis):
            if col not in self.artificial_cols:
                continue
            factor = -self.obj[col]
            self.obj = [
                o + factor.scale(a)
                for o, a in zip(self.obj, self.tableau[i], strict=True)
            ]
            ops.append(f"Z ← Z + ({fmt_m(factor)})·R{_sub(i + 1)}")
        return ops

    def _artificial_is_positive(self):
        return any(
            col in self.artificial_cols and self.tableau[i][-1] > 0
            for i, col in enumerate(self.basis)
        )

    def _is_feasible(self):
        """Factibilidad exacta: resuelve con Z = 0, que nunca es no acotado."""
        feasibility = GranMSolver(
            {**self.problem, "sense": "min", "objective": [0] * self.n}
        )
        return feasibility.solve()["status"] == "optimal"

    def _choose_entering(self):
        # MIN: gana el más positivo; MAX: el más negativo. Empate: primera columna.
        direction = 1 if self.sense == "min" else -1
        best = None
        for j in range(len(self.columns)):
            v = self.obj[j].scale(direction)
            if v.sign() > 0 and (best is None or (v - best[1]).sign() > 0):
                best = (j, v)
        return None if best is None else best[0]

    def _ratios(self, col):
        ratios = []
        for i, row in enumerate(self.tableau):
            a = row[col]
            entry = {"basis": self.columns[self.basis[i]]}
            if a > 0:
                entry["ratio"] = row[-1] / a
                entry["text"] = f"{fmt(row[-1])} / {fmt(a)} = {fmt(row[-1] / a)}"
            else:
                entry["ratio"] = None
                entry["text"] = f"coeficiente {fmt(a)} → no participa"
            ratios.append(entry)
        return ratios

    def _pivot(self, r, col):
        ops = []
        pivot = self.tableau[r][col]
        if pivot != 1:
            self.tableau[r] = [v / pivot for v in self.tableau[r]]
            ops.append(f"R{_sub(r + 1)} ← R{_sub(r + 1)} / {_signed(pivot)}")
        pr = self.tableau[r]
        for i, row in enumerate(self.tableau):
            factor = -row[col]
            if i == r or factor == 0:
                continue
            self.tableau[i] = [v + factor * p for v, p in zip(row, pr, strict=True)]
            ops.append(
                f"R{_sub(i + 1)} ← R{_sub(i + 1)} + {_signed(factor)}·R{_sub(r + 1)}"
            )
        factor = -self.obj[col]
        if factor.sign() != 0:
            self.obj = [o + factor.scale(p) for o, p in zip(self.obj, pr, strict=True)]
            ops.append(f"Z ← Z + ({fmt_m(factor)})·R{_sub(r + 1)}")
        self.basis[r] = col
        return ops

    # -------------------------------------------------------------------- solve
    def solve(self):
        sign = "+" if self.sense == "min" else "-"
        penalty_terms = "".join(
            f" {sign} M{self.columns[c]}" for c in self.artificial_cols
        )
        self._snapshot(
            "Modelo transformado",
            notes=[f"R{_sub(i + 1)}: {eq}" for i, eq in enumerate(self.equations)]
            + [
                "Z = "
                + " + ".join(f"{fmt(c)}x{_sub(j + 1)}" for j, c in enumerate(self.c))
                + penalty_terms
            ],
            table=False,
        )

        self._snapshot("Tabla inicial")
        if any(col in self.artificial_cols for col in self.basis):
            ops = self._eliminate_artificials()
            self._snapshot(
                "Fila Z sin artificiales en la base",
                notes=["Se eliminan de la fila Z las artificiales básicas."],
                operations=ops,
            )

        for iteration in range(1, MAX_ITERATIONS + 1):
            col = self._choose_entering()
            if col is None:
                break
            ratios = self._ratios(col)
            candidates = [
                (e["ratio"], i) for i, e in enumerate(ratios) if e["ratio"] is not None
            ]
            for e in ratios:
                e["ratio"] = None if e["ratio"] is None else fmt(e["ratio"])
            if not candidates:
                # Con una artificial positiva aún en la base, la dirección no acotada
                # puede ser un artificio de M: hay que confirmar que el modelo es factible.
                infeasible = self._artificial_is_positive() and not self._is_feasible()
                verdict = (
                    "el problema es infactible (ninguna solución cumple todas las restricciones)."
                    if infeasible
                    else "la solución es no acotada."
                )
                self._snapshot(
                    f"Iteración {iteration}",
                    notes=[
                        f"Entra {self.columns[col]}; sin coeficientes positivos, {verdict}"
                    ],
                    pivot={"row": None, "col": col},
                    entering=self.columns[col],
                    ratios=ratios,
                )
                return self._result("infeasible" if infeasible else "unbounded")
            _, row = min(candidates)
            entering, leaving = self.columns[col], self.columns[self.basis[row]]
            step = self._snapshot(
                f"Iteración {iteration}",
                notes=[f"Entra {entering}, sale {leaving}."],
                pivot={"row": row, "col": col},
                entering=entering,
                leaving=leaving,
                ratios=ratios,
            )
            step["operations"] = self._pivot(row, col)
        else:
            raise RuntimeError(
                f"No se alcanzó el óptimo en {MAX_ITERATIONS} iteraciones (posible ciclado)"
            )

        self._snapshot("Tabla final")
        return self._result("optimal")

    def _result(self, status):
        result = {"status": status, "steps": self.steps}
        if status != "optimal":
            return result

        values = {name: ZERO for name in self.columns}
        for i, col in enumerate(self.basis):
            values[self.columns[col]] = self.tableau[i][-1]

        if any(values[self.columns[c]] > 0 for c in self.artificial_cols):
            self.steps[-1]["notes"].append(
                "Una artificial quedó básica con valor positivo: el problema es infactible."
            )
            result["status"] = "infeasible"
            return result

        z = self.obj[-1].const
        result["z"] = fmt(z)
        result["z_float"] = float(z)
        result["decision"] = {n: fmt(values[n]) for n in self.columns[: self.n]}
        result["solution"] = {
            n: fmt(v)
            for n, v in values.items()
            if n not in {self.columns[c] for c in self.artificial_cols}
        }
        return result


def solve(problem):
    """Resuelve ``{"sense", "objective", "constraints": [{"coefs", "type", "rhs"}]}``."""
    return GranMSolver(problem).solve()
