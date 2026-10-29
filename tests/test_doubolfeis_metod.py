import pytest

from optilab.app import Api
from optilab.doubolfeis_metod import solve

WORKED_EXAMPLE = {
    "sense": "max",
    "objective": [5, 8],
    "constraints": [
        {"coefs": [2, 1], "type": "=", "rhs": 12},
        {"coefs": [1, 1], "type": ">=", "rhs": 8},
        {"coefs": [0, 1], "type": "<=", "rhs": 8},
    ],
}


def _step(result, title):
    return next(s for s in result["steps"] if s["title"] == title)


def test_worked_example_optimum():
    result = solve(WORKED_EXAMPLE)
    assert result["status"] == "optimal"
    assert result["decision"] == {"x₁": "2", "x₂": "8"}
    assert result["solution"]["S₂"] == "2"
    assert result["z"] == "74"


def test_worked_example_intermediate_tableaus():
    result = solve(WORKED_EXAMPLE)

    reduced = _step(result, "Fase 1 · Fila r reducida")
    assert reduced["objective"]["values"] == ["3", "2", "0", "-1", "0", "0", "0", "20"]

    it1 = _step(result, "Fase 1 · Iteración 1")
    assert (it1["entering"], it1["leaving"]) == ("x₁", "A₁")
    assert it1["objective"]["values"] == ["0", "1/2", "0", "-1", "0", "-3/2", "0", "2"]

    end1 = _step(result, "Fase 1 · Final")
    assert [r["basis"] for r in end1["rows"]] == ["x₁", "x₂", "S₃"]
    assert end1["objective"]["values"][-1] == "0"

    start2 = _step(result, "Fase 2 · Tabla inicial (función original visible)")
    assert start2["columns"] == ["x₁", "x₂", "S₁", "S₂", "S₃"]
    assert start2["objective"]["values"] == ["-5", "-8", "0", "0", "0", "0"]

    canon = _step(result, "Fase 2 · Fila Z en forma canónica")
    assert canon["objective"]["values"] == ["0", "0", "0", "-11", "0", "52"]

    it2 = _step(result, "Fase 2 · Iteración 1")
    assert (it2["entering"], it2["leaving"]) == ("S₂", "S₃")
    assert it2["objective"]["values"] == ["0", "0", "0", "0", "11/2", "74"]


def test_minimization():
    # MIN Z = 2x1 + 3x2  s.a.  x1 + x2 >= 4,  x1 + 3x2 >= 6
    result = solve(
        {
            "sense": "min",
            "objective": [2, 3],
            "constraints": [
                {"coefs": [1, 1], "type": ">=", "rhs": 4},
                {"coefs": [1, 3], "type": ">=", "rhs": 6},
            ],
        }
    )
    assert result["status"] == "optimal"
    assert result["decision"] == {"x₁": "3", "x₂": "1"}
    assert result["z"] == "9"


def test_infeasible():
    result = solve(
        {
            "sense": "max",
            "objective": [1, 1],
            "constraints": [
                {"coefs": [1, 1], "type": "<=", "rhs": 2},
                {"coefs": [1, 1], "type": ">=", "rhs": 5},
            ],
        }
    )
    assert result["status"] == "infeasible"


def test_unbounded():
    result = solve(
        {
            "sense": "max",
            "objective": [1, 1],
            "constraints": [{"coefs": [1, -1], "type": ">=", "rhs": 1}],
        }
    )
    assert result["status"] == "unbounded"


def test_only_slacks_skips_phase_one():
    result = solve(
        {
            "sense": "max",
            "objective": [3, 5],
            "constraints": [
                {"coefs": [1, 0], "type": "<=", "rhs": 4},
                {"coefs": [0, 2], "type": "<=", "rhs": 12},
                {"coefs": [3, 2], "type": "<=", "rhs": 18},
            ],
        }
    )
    assert result["steps"][0]["title"] == "Fase 1 · No es necesaria"
    assert result["decision"] == {"x₁": "2", "x₂": "6"}
    assert result["z"] == "36"


def test_fraction_strings_and_negative_rhs():
    # -x1 - x2 <= -2  equivale a  x1 + x2 >= 2
    result = solve(
        {
            "sense": "min",
            "objective": ["1/2", 1],
            "constraints": [{"coefs": [-1, -1], "type": "<=", "rhs": -2}],
        }
    )
    assert result["decision"] == {"x₁": "2", "x₂": "0"}
    assert result["z"] == "1"


def test_invalid_input():
    with pytest.raises(ValueError):
        solve(
            {
                "sense": "max",
                "objective": [1],
                "constraints": [{"coefs": [1, 2], "type": "<=", "rhs": 1}],
            }
        )


def test_api_two_phase_reports_errors():
    assert Api().two_phase(WORKED_EXAMPLE)["z"] == "74"
    assert Api().two_phase({"objective": [], "constraints": []})["status"] == "error"


def test_objective_note_formats_negative_coefficients():
    result = solve(
        {
            "sense": "max",
            "objective": [-5, 7],
            "constraints": [{"coefs": [1, 1], "type": "<=", "rhs": 4}],
        }
    )
    start2 = _step(result, "Fase 2 · Tabla inicial (función original visible)")
    assert start2["notes"][:2] == ["MAX Z = −5x₁ + 7x₂", "Z + 5x₁ − 7x₂ = 0"]
