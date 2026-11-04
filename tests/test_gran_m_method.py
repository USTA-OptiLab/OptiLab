import random
from fractions import Fraction

import pytest
from scipy.optimize import linprog

from optilab.app import Api
from optilab.gran_m_method import solve
from optilab.gran_m_method.solver import MNum, fmt_m

MIN_EXAMPLE = {
    "sense": "min",
    "objective": ["2/5", "1/2"],
    "constraints": [
        {"coefs": ["3/10", "1/10"], "type": "<=", "rhs": "27/10"},
        {"coefs": ["1/2", "1/2"], "type": "=", "rhs": 6},
        {"coefs": ["3/5", "2/5"], "type": ">=", "rhs": 6},
    ],
}


def _step(result, title):
    return next(s for s in result["steps"] if s["title"] == title)


def test_min_example_optimum():
    result = solve(MIN_EXAMPLE)
    assert result["status"] == "optimal"
    assert result["decision"] == {"x₁": "15/2", "x₂": "9/2"}
    assert result["z"] == "21/4"
    assert result["z_float"] == pytest.approx(5.25)
    assert not any(name.startswith("A") for name in result["solution"])


def test_min_example_intermediate_tableaus():
    result = solve(MIN_EXAMPLE)

    model = _step(result, "Modelo transformado")
    assert model["notes"][1] == "R₂: 1/2x₁ + 1/2x₂ + A₁ = 6"
    assert "columns" not in model

    initial = _step(result, "Tabla inicial")
    assert initial["columns"] == ["x₁", "x₂", "S₁", "S₃", "A₁", "A₂"]
    assert initial["objective"]["values"] == ["-2/5", "-1/2", "0", "0", "-M", "-M", "0"]

    reduced = _step(result, "Fila Z sin artificiales en la base")
    assert reduced["objective"]["values"][0] == "(11/10)M-2/5"
    assert reduced["objective"]["values"][-1] == "12M"

    first = _step(result, "Iteración 1")
    assert (first["entering"], first["leaving"]) == ("x₁", "S₁")
    assert first["pivot"] == {"row": 0, "col": 0}

    final = _step(result, "Tabla final")
    assert [r["basis"] for r in final["rows"]] == ["x₁", "S₃", "x₂"]
    assert "pivot" not in final


def test_max_penalizes_with_opposite_sign():
    result = solve(
        {
            "sense": "max",
            "objective": [3, 2],
            "constraints": [
                {"coefs": [1, 1], "type": "<=", "rhs": 4},
                {"coefs": [1, 0], "type": ">=", "rhs": 1},
            ],
        }
    )
    initial = _step(result, "Tabla inicial")
    assert initial["objective"]["values"] == ["-3", "-2", "0", "0", "M", "0"]
    assert result["status"] == "optimal"
    assert result["decision"] == {"x₁": "4", "x₂": "0"}
    assert result["z"] == "12"


def test_infeasible():
    result = solve(
        {
            "sense": "min",
            "objective": [1, 1],
            "constraints": [
                {"coefs": [1, 1], "type": "<=", "rhs": 2},
                {"coefs": [1, 1], "type": ">=", "rhs": 5},
            ],
        }
    )
    assert result["status"] == "infeasible"
    assert "z" not in result


def test_unbounded():
    result = solve(
        {
            "sense": "max",
            "objective": [1, 1],
            "constraints": [{"coefs": [1, -1], "type": ">=", "rhs": 1}],
        }
    )
    assert result["status"] == "unbounded"
    assert result["steps"][-1]["entering"] in ("x₁", "x₂")


def test_infeasible_not_mistaken_for_unbounded():
    # No positive ratio appears while A₁ is still positive; the model has no feasible point
    result = solve(
        {
            "sense": "min",
            "objective": [-5, 7, -1],
            "constraints": [
                {"coefs": [4, 1, 0], "type": "=", "rhs": 15},
                {"coefs": [2, 4, 2], "type": ">=", "rhs": -2},
                {"coefs": [0, -2, 0], "type": ">=", "rhs": 2},
            ],
        }
    )
    assert result["status"] == "infeasible"
    assert "infactible" in result["steps"][-1]["notes"][0]


def test_negative_rhs_flips_constraint():
    # -x₁ - x₂ <= -2  is  x₁ + x₂ >= 2
    result = solve(
        {
            "sense": "min",
            "objective": [1, 3],
            "constraints": [{"coefs": [-1, -1], "type": "<=", "rhs": -2}],
        }
    )
    assert result["status"] == "optimal"
    assert result["decision"] == {"x₁": "2", "x₂": "0"}
    assert result["z"] == "2"


def test_matches_scipy_on_random_problems():
    rng = random.Random(7)
    for _ in range(60):
        n, m = rng.randint(2, 3), rng.randint(2, 4)
        sense = rng.choice(["min", "max"])
        c = [rng.randint(-5, 9) for _ in range(n)]
        cons = [
            {
                "coefs": [rng.randint(-3, 6) for _ in range(n)],
                "type": rng.choice(["<=", ">=", "="]),
                "rhs": rng.randint(-4, 20),
            }
            for _ in range(m)
        ]
        a_ub, b_ub, a_eq, b_eq = [], [], [], []
        for con in cons:
            if con["type"] == "=":
                a_eq.append(con["coefs"])
                b_eq.append(con["rhs"])
            else:
                sgn = 1 if con["type"] == "<=" else -1
                a_ub.append([sgn * a for a in con["coefs"]])
                b_ub.append(sgn * con["rhs"])
        ref = linprog(
            c if sense == "min" else [-v for v in c],
            A_ub=a_ub or None,
            b_ub=b_ub or None,
            A_eq=a_eq or None,
            b_eq=b_eq or None,
            bounds=(0, None),
            method="highs",
        )
        result = solve({"sense": sense, "objective": c, "constraints": cons})
        expected = {0: "optimal", 2: "infeasible", 3: "unbounded"}[ref.status]
        assert result["status"] == expected, (sense, c, cons)
        if expected == "optimal":
            z = ref.fun if sense == "min" else -ref.fun
            assert result["z_float"] == pytest.approx(z, abs=1e-7)


def test_m_numbers_compare_exactly():
    big = MNum(Fraction(0), Fraction(1))
    huge_const = MNum(Fraction(10**12), Fraction(0))
    assert (big - huge_const).sign() == 1
    assert fmt_m(MNum(Fraction(15), Fraction(40))) == "40M+15"
    assert fmt_m(MNum(Fraction(0), Fraction(-1))) == "-M"
    assert fmt_m(MNum(Fraction(-3, 2), Fraction(1, 2))) == "(1/2)M-3/2"


@pytest.mark.parametrize(
    "bad",
    [
        {
            "sense": "sideways",
            "objective": [1],
            "constraints": [{"coefs": [1], "type": "<=", "rhs": 1}],
        },
        {
            "sense": "max",
            "objective": [],
            "constraints": [{"coefs": [], "type": "<=", "rhs": 1}],
        },
        {"sense": "max", "objective": [1], "constraints": []},
        {
            "sense": "max",
            "objective": [1],
            "constraints": [{"coefs": [1, 2], "type": "<=", "rhs": 1}],
        },
        {
            "sense": "max",
            "objective": [1],
            "constraints": [{"coefs": [1], "type": "<", "rhs": 1}],
        },
        {
            "sense": "max",
            "objective": ["abc"],
            "constraints": [{"coefs": [1], "type": "<=", "rhs": 1}],
        },
        {
            "sense": "max",
            "objective": ["1/0"],
            "constraints": [{"coefs": [1], "type": "<=", "rhs": 1}],
        },
    ],
)
def test_invalid_input_raises_and_api_reports_error(bad):
    with pytest.raises((ValueError, ZeroDivisionError)):
        solve(bad)
    response = Api().gran_m(bad)
    assert response["status"] == "error"
    assert response["message"]


def test_api_missing_keys_returns_error():
    assert Api().gran_m({"sense": "min"})["status"] == "error"


def test_api_solves():
    assert Api().gran_m(MIN_EXAMPLE)["z"] == "21/4"
