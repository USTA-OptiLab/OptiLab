from fractions import Fraction

import pytest

from optilab.simplex import SimplexSolver, fmt_frac, parse_fraction


def test_parse_and_format_fractions():
    assert parse_fraction(3) == Fraction(3, 1)
    assert parse_fraction("2.5") == Fraction(5, 2)
    assert parse_fraction("3/4") == Fraction(3, 4)
    assert fmt_frac(Fraction(6, 2)) == "3"
    assert fmt_frac(Fraction(5, 2)) == "5/2"


def test_simplex_example_1_classic_max():
    # Max Z = 3*x1 + 5*x2
    # R1: 1*x1 <= 4
    # R2: 2*x2 <= 12
    # R3: 3*x1 + 2*x2 <= 18
    # Optimal: x1=2, x2=6, Z=36
    solver = SimplexSolver(
        objective="max",
        c=[3, 5],
        constraints=[
            {"lhs": [1, 0], "sign": "<=", "rhs": 4},
            {"lhs": [0, 2], "sign": "<=", "rhs": 12},
            {"lhs": [3, 2], "sign": "<=", "rhs": 18},
        ],
        var_names=["x1", "x2"],
    )
    res = solver.solve()
    assert res["status"] == "optimal"
    assert len(res["steps"]) >= 2
    rep = res["final_report"]
    assert rep["z_optimal"]["frac"] == "36"
    assert rep["variables"]["x1"]["frac"] == "2"
    assert rep["variables"]["x2"]["frac"] == "6"
    assert rep["all_satisfied"] is True


def test_simplex_example_2_minimization():
    # Min Z = -1*x1 - 2*x2
    # R1: x1 + x2 <= 4
    # R2: x1 + 3*x2 <= 6
    # Optimal: x1=3, x2=1, Z=-5
    solver = SimplexSolver(
        objective="min",
        c=[-1, -2],
        constraints=[
            {"lhs": [1, 1], "sign": "<=", "rhs": 4},
            {"lhs": [1, 3], "sign": "<=", "rhs": 6},
        ],
        var_names=["x1", "x2"],
    )
    res = solver.solve()
    assert res["status"] == "optimal"
    rep = res["final_report"]
    assert rep["z_optimal"]["frac"] == "-5"
    assert rep["variables"]["x1"]["frac"] == "3"
    assert rep["variables"]["x2"]["frac"] == "1"


def test_simplex_example_3_alternative_optima():
    # Max Z = 2*x1 + 4*x2
    # R1: x1 + 2*x2 <= 8
    # R2: x1 <= 6
    # R3: x2 <= 3
    solver = SimplexSolver(
        objective="max",
        c=[2, 4],
        constraints=[
            {"lhs": [1, 2], "sign": "<=", "rhs": 8},
            {"lhs": [1, 0], "sign": "<=", "rhs": 6},
            {"lhs": [0, 1], "sign": "<=", "rhs": 3},
        ],
        var_names=["x1", "x2"],
    )
    res = solver.solve()
    assert res["status"] == "optimal"
    rep = res["final_report"]
    assert rep["z_optimal"]["frac"] == "16"
    assert rep["alternative_optima"]["has_alternatives"] is True


def test_simplex_example_5_unbounded():
    # Max Z = 2*x1 + x2
    # R1: x1 - x2 <= 3
    solver = SimplexSolver(
        objective="max",
        c=[2, 1],
        constraints=[
            {"lhs": [1, -1], "sign": "<=", "rhs": 3},
        ],
        var_names=["x1", "x2"],
    )
    res = solver.solve()
    assert res["status"] == "unbounded"


def test_simplex_two_phase():
    # Min Z = 2*x1 + 3*x2
    # R1: x1 + x2 >= 5
    # R2: x1 <= 4
    solver = SimplexSolver(
        objective="min",
        c=[2, 3],
        constraints=[
            {"lhs": [1, 1], "sign": ">=", "rhs": 5},
            {"lhs": [1, 0], "sign": "<=", "rhs": 4},
        ],
        var_names=["x1", "x2"],
    )
    res = solver.solve()
    assert res["status"] == "optimal"
    rep = res["final_report"]
    assert rep["variables"]["x1"]["frac"] == "4"
    assert rep["variables"]["x2"]["frac"] == "1"
    assert rep["z_optimal"]["frac"] == "11"


def test_analyze_problem_context():
    from optilab.simplex import analyze_problem_context

    text_max = "Una fábrica produce mesas y sillas. Cada mesa genera una ganancia de $3 y cada silla $5. Horas de corte 4, horas de ensamble 12. Se desea maximizar la utilidad total."
    res = analyze_problem_context(text_max)
    assert res["objective"] == "max"
    assert "$" in res["objective_unit"]
    assert len(res["suggested_vars"]) >= 1

    text_min = "Una empresa desea minimizar el costo total de transporte y flete de dos ingredientes perecederos."
    res_min = analyze_problem_context(text_min)
    assert res_min["objective"] == "min"


def test_simplex_with_context_and_conclusion():
    context = {
        "title": "Producción de Muebles",
        "statement": "Una empresa fabrica mesas y sillas para maximizar su utilidad.",
        "objective_name": "Utilidad neta",
        "objective_unit": "$",
        "var_descriptions": ["Mesas", "Sillas"],
        "var_units": ["mesas", "sillas"],
        "constraint_descriptions": [
            "Horas de corte",
            "Horas de ensamble",
            "Horas de acabado",
        ],
        "constraint_units": ["horas", "horas", "horas"],
    }
    solver = SimplexSolver(
        objective="max",
        c=[3, 5],
        constraints=[
            {"lhs": [1, 0], "sign": "<=", "rhs": 4},
            {"lhs": [0, 2], "sign": "<=", "rhs": 12},
            {"lhs": [3, 2], "sign": "<=", "rhs": 18},
        ],
        var_names=["x1", "x2"],
        context=context,
    )
    res = solver.solve()
    assert res["status"] == "optimal"
    conc = res["final_report"]["contextual_conclusion"]
    assert conc is not None
    assert conc["status"] == "optimal"
    assert "Utilidad neta" in conc["headline"]
    assert "36 $" in conc["optimal_value_text"]
    assert len(conc["plan_of_action"]) == 2
    assert conc["plan_of_action"][0]["description"] == "Mesas"
    assert conc["plan_of_action"][0]["value_frac"] == "2"
    assert conc["plan_of_action"][1]["description"] == "Sillas"
    assert conc["plan_of_action"][1]["value_frac"] == "6"
    assert len(conc["resource_diagnosis"]) == 3


def _solve(objective, c, rows):
    return SimplexSolver(
        objective=objective,
        c=c,
        constraints=[{"lhs": a, "sign": s, "rhs": b} for a, s, b in rows],
    ).solve()


def test_degenerate_artificial_is_pivoted_out_of_basis():
    # Phase 1 ends with an artificial variable basic at level 0; it must be
    # pivoted out, otherwise phase 2 reports a point violating R2.
    res = _solve(
        "max", [-3, 3], [([1, 3], "=", 2), ([5, 6], "=", 7), ([6, 0], "<=", 6)]
    )
    assert res["status"] == "optimal"
    report = res["final_report"]
    assert report["z_optimal"]["frac"] == "-2"
    assert {k: v["frac"] for k, v in report["variables"].items()} == {
        "x1": "1",
        "x2": "1/3",
    }
    assert report["all_satisfied"] is True


def test_degenerate_artificial_does_not_fake_unbounded():
    res = _solve(
        "min",
        [2, 5],
        [
            ([1, 1], "<=", 10),
            ([6, -2], "<=", 6),
            ([-2, 6], ">=", 14),
            ([3, -1], ">=", 3),
        ],
    )
    assert res["status"] == "optimal"
    assert res["final_report"]["z_optimal"]["frac"] == "19"


def test_redundant_equality_constraint_is_dropped_in_phase_two():
    res = _solve("max", [1, 1], [([1, 1], "=", 2), ([2, 2], "=", 4), ([1, 0], "<=", 1)])
    assert res["status"] == "optimal"
    assert res["final_report"]["z_optimal"]["frac"] == "2"


def test_matches_linprog_on_random_mixed_problems():
    import random

    from scipy.optimize import linprog

    rng = random.Random(7)
    checked = 0
    for _ in range(300):
        n, m = rng.choice([2, 3]), rng.randint(2, 4)
        sense = rng.choice(["max", "min"])
        c = [rng.randint(-3, 9) for _ in range(n)]
        rows = [
            (
                [rng.randint(-2, 6) for _ in range(n)],
                rng.choice(["<=", "<=", ">=", "="]),
                rng.randint(1, 20),
            )
            for _ in range(m)
        ]
        a_ub, b_ub, a_eq, b_eq = [], [], [], []
        for a, s, b in rows:
            if s == "<=":
                a_ub.append(a)
                b_ub.append(b)
            elif s == ">=":
                a_ub.append([-x for x in a])
                b_ub.append(-b)
            else:
                a_eq.append(a)
                b_eq.append(b)
        ref = linprog(
            [-x for x in c] if sense == "max" else c,
            A_ub=a_ub or None,
            b_ub=b_ub or None,
            A_eq=a_eq or None,
            b_eq=b_eq or None,
            bounds=(0, None),
            method="highs",
        )
        res = _solve(sense, c, rows)
        if ref.status == 0:
            expected = -ref.fun if sense == "max" else ref.fun
            assert res["status"] == "optimal", (sense, c, rows)
            z = Fraction(res["final_report"]["z_optimal"]["frac"])
            assert float(z) == pytest.approx(expected), (sense, c, rows)
            assert res["final_report"]["all_satisfied"] is True, (sense, c, rows)
        elif ref.status == 2:
            assert res["status"] == "infeasible", (sense, c, rows)
        elif ref.status == 3:
            assert res["status"] == "unbounded", (sense, c, rows)
        else:
            continue
        checked += 1
    assert checked > 250
