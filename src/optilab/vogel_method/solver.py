import math

DEFAULT_CONTEXT = "Problema de transporte sin descripción."


def _number(value):
    number = float(value)
    return int(number) if number.is_integer() else number


def _penalty(values, key):
    if len(values) == 1:
        return values[0]
    best = sorted(values, key=key)
    return abs(best[1] - best[0])


def solve_vogel(costs, supply, demand, maximize=False, context=""):
    """Solve a transportation problem with Vogel's approximation method.

    By default it minimizes cost. With `maximize=True` the values are
    profits: penalties use the two highest values and the highest value in
    the chosen line is picked first.

    Unbalanced problems get a dummy column (excess supply) or dummy row
    (excess demand) with zero cost, so `allocation` may be one row/column
    larger than `costs`; `dummy` says which one ("row", "column" or None).
    """
    if not isinstance(context, str):
        raise TypeError("El contexto del problema debe ser texto.")
    context = context.strip() or DEFAULT_CONTEXT
    original_rows, original_cols = len(supply), len(demand)
    # Smaller key = better value, so both objectives share the same code.
    key = (lambda v: -v) if maximize else (lambda v: v)
    costs = [[_number(c) for c in row] for row in costs]
    supply = [_number(s) for s in supply]
    demand = [_number(d) for d in demand]

    if not costs or not costs[0]:
        raise ValueError("costs must be a non-empty matrix")
    if any(len(row) != len(demand) for row in costs) or len(costs) != len(supply):
        raise ValueError("costs dimensions must match supply and demand")
    values = supply + demand + [c for row in costs for c in row]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("costs, supply and demand must be finite numbers")
    if any(v < 0 for v in values):
        raise ValueError("costs, supply and demand must be non-negative")

    dummy = None
    total_supply, total_demand = sum(supply), sum(demand)
    if total_supply != total_demand:
        if total_supply > total_demand:
            dummy = "column"
            demand.append(total_supply - total_demand)
            for row in costs:
                row.append(0.0)
        else:
            dummy = "row"
            supply.append(total_demand - total_supply)
            costs.append([0.0] * len(demand))

    n_rows, n_cols = len(supply), len(demand)
    allocation = [[0.0] * n_cols for _ in range(n_rows)]
    rows, cols = set(range(n_rows)), set(range(n_cols))
    start_supply, start_demand = supply[:], demand[:]
    steps = []

    basic_cells = []

    def assign(i, j, row_pen, col_pen, line, phase, tied=0, penalty=None):
        step = {
            "phase": phase,
            "active_rows": sorted(rows),
            "active_cols": sorted(cols),
            "row_penalties": row_pen,
            "col_penalties": col_pen,
            "supply_before": supply[:],
            "demand_before": demand[:],
            "max_penalty": penalty,
            "tied_lines": tied,
            "line": line,
        }
        qty = min(supply[i], demand[j])
        allocation[i][j] = qty
        basic_cells.append([i, j])
        supply[i] -= qty
        demand[j] -= qty
        remove_row = line[0] == "column" if phase == "direct" else supply[i] == 0
        if remove_row:
            rows.discard(i)
            crossed = ["row", i]
        else:
            cols.discard(j)
            crossed = ["column", j]
        step.update(
            {
                "cell": [i, j],
                "quantity": qty,
                "crossed": crossed,
                "supply_after": supply[:],
                "demand_after": demand[:],
            }
        )
        steps.append(step)

    while len(rows) > 1 and len(cols) > 1:
        row_pen = {
            i: _penalty([costs[i][j] for j in sorted(cols)], key) for i in sorted(rows)
        }
        col_pen = {
            j: _penalty([costs[i][j] for i in sorted(rows)], key) for j in sorted(cols)
        }
        candidates = []
        for i, penalty in row_pen.items():
            j = min(sorted(cols), key=lambda j: key(costs[i][j]))
            candidates.append(
                (penalty, -key(costs[i][j]), min(supply[i], demand[j]), "row", i, j)
            )
        for j, penalty in col_pen.items():
            i = min(sorted(rows), key=lambda i: key(costs[i][j]))
            candidates.append(
                (penalty, -key(costs[i][j]), min(supply[i], demand[j]), "column", i, j)
            )
        best = max(candidates, key=lambda candidate: candidate[:3])
        penalty, _, _, kind, i, j = best
        assign(
            i,
            j,
            row_pen,
            col_pen,
            [kind, i if kind == "row" else j],
            "penalty",
            sum(c[0] == penalty for c in candidates),
            penalty,
        )

    # Keep the original final stage: process the remaining cells in row
    # order, then by best unit value. Record it without inventing penalties.
    remaining_rows, remaining_cols = sorted(rows), sorted(cols)
    for i in remaining_rows:
        for j in sorted(remaining_cols, key=lambda j: key(costs[i][j])):
            kind = "row" if len(remaining_rows) == 1 else "column"
            assign(i, j, {}, {}, [kind, i if kind == "row" else j], "direct")

    total_cost = sum(
        allocation[i][j] * costs[i][j] for i in range(n_rows) for j in range(n_cols)
    )
    return {
        "context": context,
        "interpretation": {
            "origins": original_rows,
            "destinations": original_cols,
            "shipments": [
                {"origin": i + 1, "destination": j + 1, "quantity": allocation[i][j]}
                for i in range(original_rows)
                for j in range(original_cols)
                if allocation[i][j] > 0
            ],
            "surplus": (
                sum(allocation[i][-1] for i in range(original_rows))
                if dummy == "column"
                else 0.0
            ),
            "unmet": sum(allocation[-1]) if dummy == "row" else 0.0,
        },
        "basic_cells": basic_cells,
        "allocation": allocation,
        "total_cost": total_cost,
        "steps": steps,
        "dummy": dummy,
        "maximize": maximize,
        "costs": costs,
        "supply": start_supply,
        "demand": start_demand,
    }
