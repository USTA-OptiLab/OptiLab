"""Núcleo del Simplex (primal de dos fases y dual) con aritmética exacta.

Módulo privado de ``optilab.primal_dual``.
"""

from fractions import Fraction

from ._model import Problem


def _pivot(T, obj, basis, r, j):
    piv = T[r][j]
    T[r] = [v / piv for v in T[r]]
    for i in range(len(T)):
        if i != r and T[i][j] != 0:
            f = T[i][j]
            T[i] = [a - f * b for a, b in zip(T[i], T[r])]
    if obj[j] != 0:
        f = obj[j]
        obj[:] = [a - f * b for a, b in zip(obj, T[r])]
    basis[r] = j


def _build_obj(T, basis, c):
    obj = list(c) + [Fraction(0)]
    for i, bj in enumerate(basis):
        f = obj[bj]
        if f != 0:
            obj = [a - f * b for a, b in zip(obj, T[i])]
    return obj


def _primal(T, obj, basis, allowed):
    """Simplex primal (regla de Bland para evitar ciclos)."""
    while True:
        j = next((j for j in allowed if obj[j] < 0), None)
        if j is None:
            return "optimal"
        best = None
        for i in range(len(T)):
            if T[i][j] > 0:
                ratio = T[i][-1] / T[i][j]
                if (
                    best is None
                    or ratio < best[0]
                    or (ratio == best[0] and basis[i] < basis[best[1]])
                ):
                    best = (ratio, i)
        if best is None:
            return "unbounded"
        _pivot(T, obj, basis, best[1], j)


def _dual(T, obj, basis, ncols):
    """Simplex dual: parte de una base dual-factible (costos reducidos >= 0)."""
    while True:
        neg = [i for i in range(len(T)) if T[i][-1] < 0]
        if not neg:
            return "optimal"
        r = min(neg, key=lambda i: basis[i])
        cand = [j for j in range(ncols) if T[r][j] < 0]
        if not cand:
            return "infeasible"
        j = min(cand, key=lambda j: (obj[j] / (-T[r][j]), j))
        _pivot(T, obj, basis, r, j)


# ----------------------------------------------------------- estandarización
def _standardize(p):
    """Lleva el problema a: min c'x, Ax (<=,>=,=) b con x>=0 y añade holguras."""
    mapping = []  # por variable original: lista de (columna, coeficiente)
    cost = []
    col = 0
    for j, s in enumerate(p.signs):
        if s == ">=0":
            mapping.append([(col, Fraction(1))])
            col += 1
        elif s == "<=0":
            mapping.append([(col, Fraction(-1))])
            col += 1
        else:
            mapping.append([(col, Fraction(1)), (col + 1, Fraction(-1))])
            col += 2
    n_struct = col
    cost = [Fraction(0)] * n_struct
    sgn = 1 if p.sense == "min" else -1
    for j, lst in enumerate(mapping):
        for cj, coef in lst:
            cost[cj] = sgn * p.c[j] * coef

    n_ineq = sum(1 for _, t, _ in p.cons if t != "=")
    total = n_struct + n_ineq
    cost = cost + [Fraction(0)] * n_ineq
    A, b, types, slack = [], [], [], []
    k = n_struct
    for a, t, rhs in p.cons:
        row = [Fraction(0)] * total
        for j, lst in enumerate(mapping):
            for cj, coef in lst:
                row[cj] += a[j] * coef
        if t == "<=":
            row[k] = Fraction(1)
            slack.append(k)
            k += 1
        elif t == ">=":
            row[k] = Fraction(-1)
            slack.append(k)
            k += 1
        else:
            slack.append(None)
        A.append(row)
        b.append(rhs)
        types.append(t)
    return A, b, cost, types, slack, mapping, total


def _extract(p, mapping, T, basis, total):
    vals = [Fraction(0)] * total
    for i, bj in enumerate(basis):
        vals[bj] = T[i][-1]
    x = [sum(coef * vals[cj] for cj, coef in lst) for lst in mapping]
    z = sum(cj * xj for cj, xj in zip(p.c, x))
    return x, z


def solve(p):
    """Devuelve dict: status ('optimal' | 'infeasible' | 'unbounded'), x, z, method."""
    A, b, cost, types, slack, mapping, total = _standardize(p)
    m = len(A)

    # --- Caso 1: base de holguras dual-factible -> SIMPLEX DUAL
    if m > 0 and all(t != "=" for t in types) and all(cj >= 0 for cj in cost):
        T = []
        basis = []
        for i in range(m):
            row, rhs = list(A[i]), b[i]
            if types[i] == ">=":
                row = [-v for v in row]
                rhs = -rhs
            T.append(row + [rhs])
            basis.append(slack[i])
        obj = _build_obj(T, basis, cost)
        st = _dual(T, obj, basis, total)
        if st != "optimal":
            return {"status": st}
        x, z = _extract(p, mapping, T, basis, total)
        return {"status": "optimal", "x": x, "z": z, "method": "Simplex dual"}

    # --- Caso 2: SIMPLEX PRIMAL de dos fases
    rows, rhs_l, basis, art_rows = [], [], [], []
    for i in range(m):
        row, rhs = list(A[i]), b[i]
        if rhs < 0:
            row = [-v for v in row]
            rhs = -rhs
        rows.append(row)
        rhs_l.append(rhs)
        s = slack[i]
        if s is not None and row[s] == 1:
            basis.append(s)
        else:
            basis.append(None)
            art_rows.append(i)
    n_art = len(art_rows)
    T = []
    for i in range(m):
        art = [Fraction(0)] * n_art
        if basis[i] is None:
            art[art_rows.index(i)] = Fraction(1)
            basis[i] = total + art_rows.index(i)
        T.append(rows[i] + art + [rhs_l[i]])
    ncols = total + n_art

    if n_art > 0:  # Fase 1
        c1 = [Fraction(0)] * total + [Fraction(1)] * n_art
        obj = _build_obj(T, basis, c1)
        _primal(T, obj, basis, range(ncols))
        if obj[-1] != 0:
            return {"status": "infeasible"}
        dead = []
        for i in range(m):
            if basis[i] >= total:
                j = next((j for j in range(total) if T[i][j] != 0), None)
                if j is None:
                    dead.append(i)
                else:
                    _pivot(T, obj, basis, i, j)
        for i in sorted(dead, reverse=True):
            del T[i]
            del basis[i]
        T = [r[:total] + [r[-1]] for r in T]

    obj = _build_obj(T, basis, cost)  # Fase 2
    st = _primal(T, obj, basis, range(total))
    if st != "optimal":
        return {"status": st}
    x, z = _extract(p, mapping, T, basis, total)
    return {
        "status": "optimal",
        "x": x,
        "z": z,
        "method": "Simplex primal (dos fases)" if n_art else "Simplex primal",
    }


def build_dual(p):
    """Construye el dual de un problema general (primal -> dual)."""
    m, n = len(p.cons), p.n
    if p.sense == "max":
        ysign = {"<=": ">=0", ">=": "<=0", "=": "libre"}
        csign = {">=0": ">=", "<=0": "<=", "libre": "="}
        dsense = "min"
    else:
        ysign = {">=": ">=0", "<=": "<=0", "=": "libre"}
        csign = {">=0": "<=", "<=0": ">=", "libre": "="}
        dsense = "max"
    signs = [ysign[t] for _, t, _ in p.cons]
    cons = []
    for j in range(n):
        col = [p.cons[i][0][j] for i in range(m)]
        cons.append((col, csign[p.signs[j]], p.c[j]))
    return Problem(
        dsense,
        [b for _, _, b in p.cons],
        cons,
        signs,
        names=[f"y{i + 1}" for i in range(m)],
    )
