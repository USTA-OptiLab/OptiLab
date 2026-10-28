import math


def _penalty(costs):
    if len(costs) == 1:
        return costs[0]
    low = sorted(costs)
    return low[1] - low[0]


def solve_vogel(costs, supply, demand):
    """Solve a transportation problem with Vogel's approximation method.

    Unbalanced problems get a dummy column (excess supply) or dummy row
    (excess demand) with zero cost, so `allocation` may be one row/column
    larger than `costs`; `dummy` says which one ("row", "column" or None).
    """
    costs = [[float(c) for c in row] for row in costs]
    supply = [float(s) for s in supply]
    demand = [float(d) for d in demand]

    if not costs or not costs[0]:
        raise ValueError("costs must be a non-empty matrix")
    if any(len(row) != len(demand) for row in costs) or len(costs) != len(supply):
        raise ValueError("costs dimensions must match supply and demand")
    if any(v < 0 for v in supply + demand) or any(c < 0 for row in costs for c in row):
        raise ValueError("costs, supply and demand must be non-negative")

    dummy = None
    total_supply, total_demand = sum(supply), sum(demand)
    if not math.isclose(total_supply, total_demand):
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
    steps = []

    while rows and cols:
        row_pen = {i: _penalty([costs[i][j] for j in cols]) for i in rows}
        col_pen = {j: _penalty([costs[i][j] for i in rows]) for j in cols}

        # Candidates ordered by penalty (high), line min cost (low), rows
        # before columns, then index, so ties resolve deterministically.
        candidates = [
            (-p, min(costs[i][j] for j in cols), 0, i) for i, p in row_pen.items()
        ] + [(-p, min(costs[i][j] for i in rows), 1, j) for j, p in col_pen.items()]
        _, _, is_col, idx = min(candidates)

        if is_col:
            i = min(rows, key=lambda r: (costs[r][idx], r))
            j = idx
        else:
            i = idx
            j = min(cols, key=lambda c: (costs[idx][c], c))

        qty = min(supply[i], demand[j])
        allocation[i][j] = qty
        supply[i] -= qty
        demand[j] -= qty
        steps.append(
            {
                "row_penalties": {r: row_pen[r] for r in sorted(row_pen)},
                "col_penalties": {c: col_pen[c] for c in sorted(col_pen)},
                "cell": [i, j],
                "quantity": qty,
            }
        )

        # On a tie only one line is dropped, so the other stays with zero
        # residual and still gets a (zero) basic cell: the degenerate case.
        if math.isclose(supply[i], 0.0, abs_tol=1e-12):
            rows.discard(i)
        else:
            cols.discard(j)

    total_cost = sum(
        allocation[i][j] * costs[i][j] for i in range(n_rows) for j in range(n_cols)
    )
    return {
        "allocation": allocation,
        "total_cost": total_cost,
        "steps": steps,
        "dummy": dummy,
    }


def _print_result(title, result):
    print(title)
    for row in result["allocation"]:
        print("  " + "  ".join(f"{q:g}".rjust(6) for q in row))
    print(f"  total cost: {result['total_cost']:g}  dummy: {result['dummy']}\n")


if __name__ == "__main__":
    _print_result(
        "Balanced",
        solve_vogel(
            [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
            [7, 9, 18],
            [5, 8, 7, 14],
        ),
    )
    _print_result(
        "Unbalanced (excess supply)",
        solve_vogel([[4, 6, 8], [5, 3, 7]], [30, 40], [20, 15, 10]),
    )
    _print_result(
        "Degenerate",
        solve_vogel([[2, 3], [4, 1]], [10, 10], [10, 10]),
    )
