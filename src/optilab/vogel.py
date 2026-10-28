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
    start_supply, start_demand = supply[:], demand[:]
    steps = []

    while rows and cols:
        row_pen = {i: _penalty([costs[i][j] for j in cols]) for i in rows}
        col_pen = {j: _penalty([costs[i][j] for i in rows]) for j in cols}

        # Candidates ordered by penalty (high), line min cost (low), rows
        # before columns, then index, so ties resolve deterministically.
        candidates = [
            (-p, min(costs[i][j] for j in cols), 0, i) for i, p in row_pen.items()
        ] + [(-p, min(costs[i][j] for i in rows), 1, j) for j, p in col_pen.items()]
        best = min(candidates)
        _, _, is_col, idx = best
        tied = sum(1 for c in candidates if c[0] == best[0])

        if is_col:
            i = min(rows, key=lambda r: (costs[r][idx], r))
            j = idx
        else:
            i = idx
            j = min(cols, key=lambda c: (costs[idx][c], c))

        step = {
            "active_rows": sorted(rows),
            "active_cols": sorted(cols),
            "row_penalties": {r: row_pen[r] for r in sorted(row_pen)},
            "col_penalties": {c: col_pen[c] for c in sorted(col_pen)},
            "supply_before": supply[:],
            "demand_before": demand[:],
            "max_penalty": -best[0],
            "tied_lines": tied,
            "line": ["column" if is_col else "row", idx],
        }

        qty = min(supply[i], demand[j])
        allocation[i][j] = qty
        supply[i] -= qty
        demand[j] -= qty

        # On a tie only one line is dropped, so the other stays with zero
        # residual and still gets a (zero) basic cell: the degenerate case.
        if math.isclose(supply[i], 0.0, abs_tol=1e-12):
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

    total_cost = sum(
        allocation[i][j] * costs[i][j] for i in range(n_rows) for j in range(n_cols)
    )
    return {
        "allocation": allocation,
        "total_cost": total_cost,
        "steps": steps,
        "dummy": dummy,
        "costs": costs,
        "supply": start_supply,
        "demand": start_demand,
    }


def _labels(result):
    n_rows, n_cols = len(result["supply"]), len(result["demand"])
    rows = [f"S{i + 1}" for i in range(n_rows)]
    cols = [f"D{j + 1}" for j in range(n_cols)]
    if result["dummy"] == "row":
        rows[-1] = "Dummy"
    elif result["dummy"] == "column":
        cols[-1] = "Dummy"
    return rows, cols


def _print_step(n, step, result, row_names, col_names):
    w = 8
    costs = result["costs"]
    print(f"  Step {n}")
    header = "".ljust(w) + "".join(col_names[j].rjust(w) for j in step["active_cols"])
    print("    " + header + "Supply".rjust(w) + "Penalty".rjust(w))
    for i in step["active_rows"]:
        cells = "".join(f"{costs[i][j]:g}".rjust(w) for j in step["active_cols"])
        print(
            "    "
            + row_names[i].ljust(w)
            + cells
            + f"{step['supply_before'][i]:g}".rjust(w)
            + f"{step['row_penalties'][i]:g}".rjust(w)
        )
    print(
        "    "
        + "Demand".ljust(w)
        + "".join(f"{step['demand_before'][j]:g}".rjust(w) for j in step["active_cols"])
    )
    print(
        "    "
        + "Penalty".ljust(w)
        + "".join(f"{step['col_penalties'][j]:g}".rjust(w) for j in step["active_cols"])
    )

    kind, idx = step["line"]
    names = row_names if kind == "row" else col_names
    i, j = step["cell"]
    line = f"    Highest penalty: {step['max_penalty']:g} ({kind} {names[idx]})."
    if step["tied_lines"] > 1:
        line += (
            f" Tie among {step['tied_lines']} lines: chose the one with the lowest"
            " cost, then rows before columns, then the first index."
        )
    print(line)
    print(
        f"    Lowest cost in that {kind}: cell ({row_names[i]}, {col_names[j]})"
        f" = {result['costs'][i][j]:g}"
    )
    print(
        f"    Assign min({step['supply_before'][i]:g}, {step['demand_before'][j]:g})"
        f" = {step['quantity']:g} to ({row_names[i]}, {col_names[j]})"
    )
    ckind, cidx = step["crossed"]
    cname = (row_names if ckind == "row" else col_names)[cidx]
    reason = "supply exhausted" if ckind == "row" else "demand covered"
    print(f"    Crossed out: {ckind} {cname} ({reason})")
    left_s = ", ".join(
        f"{row_names[r]}={step['supply_after'][r]:g}" for r in step["active_rows"]
    )
    left_d = ", ".join(
        f"{col_names[c]}={step['demand_after'][c]:g}" for c in step["active_cols"]
    )
    print(f"    Remaining supply: {left_s} | demand: {left_d}\n")


def _print_result(title, result):
    row_names, col_names = _labels(result)
    print(title)
    if result["dummy"]:
        total_s, total_d = sum(result["supply"]), sum(result["demand"])
        print(
            f"  Unbalanced problem: added a dummy {result['dummy']} with zero costs"
            f" (supply and demand now both {max(total_s, total_d):g})."
        )
    print()
    for n, step in enumerate(result["steps"], 1):
        _print_step(n, step, result, row_names, col_names)
    print("  Final allocation")
    print("    " + "".ljust(8) + "".join(c.rjust(8) for c in col_names))
    for name, row in zip(row_names, result["allocation"]):
        print("    " + name.ljust(8) + "".join(f"{q:g}".rjust(8) for q in row))
    print(f"  Total cost: {result['total_cost']:g}\n")


def _ask_number(prompt, kind=float, minimum=0):
    while True:
        try:
            value = kind(input(prompt).strip())
        except ValueError:
            print("  invalid number, try again")
            continue
        if value < minimum:
            print(f"  must be >= {minimum:g}")
            continue
        return value


def _ask_list(prompt, length):
    while True:
        try:
            values = [float(x) for x in input(prompt).replace(",", " ").split()]
        except ValueError:
            print("  invalid number, try again")
            continue
        if len(values) != length:
            print(f"  expected {length} values, got {len(values)}")
        elif any(v < 0 for v in values):
            print("  values must be >= 0")
        else:
            return values


def _solve_user_problem():
    n_rows = _ask_number("Number of sources (rows): ", int, 1)
    n_cols = _ask_number("Number of destinations (columns): ", int, 1)
    supply = _ask_list(f"Supply ({n_rows} values): ", n_rows)
    demand = _ask_list(f"Demand ({n_cols} values): ", n_cols)
    costs = [
        _ask_list(f"Costs of source {i + 1} ({n_cols} values): ", n_cols)
        for i in range(n_rows)
    ]
    _print_result("Solution", solve_vogel(costs, supply, demand))


def _run_examples():
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


def main():
    while True:
        print("Vogel approximation method")
        print("  1. Examples")
        print("  2. Solve an exercise")
        print("  0. Exit")
        choice = input("Option: ").strip()
        if choice == "1":
            _run_examples()
        elif choice == "2":
            _solve_user_problem()
        elif choice == "0":
            return
        else:
            print("  invalid option\n")


if __name__ == "__main__":
    main()
