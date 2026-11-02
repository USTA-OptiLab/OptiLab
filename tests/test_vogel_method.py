import json

import pytest

from optilab.app import Api
from optilab.vogel_method import solve_vogel


def test_balanced_minimization():
    result = solve_vogel(
        [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
        [7, 9, 18],
        [5, 8, 7, 14],
    )
    assert result["dummy"] is None
    assert result["total_cost"] == pytest.approx(779)
    assert [sum(row) for row in result["allocation"]] == [7, 9, 18]
    assert [sum(row[j] for row in result["allocation"]) for j in range(4)] == [
        5,
        8,
        7,
        14,
    ]
    assert result["steps"]
    assert "row_penalties" in result["steps"][0]


def test_unbalanced_problem_uses_dummy_column():
    result = solve_vogel([[4, 6, 8], [5, 3, 7]], [30, 40], [20, 15, 10])
    assert result["dummy"] == "column"
    assert result["demand"][-1] == pytest.approx(25)
    assert result["total_cost"] == pytest.approx(210)


def test_unbalanced_problem_uses_dummy_row():
    result = solve_vogel([[3, 6], [8, 2]], [5, 5], [6, 9])
    assert result["dummy"] == "row"
    assert result["supply"][-1] == pytest.approx(5)
    assert len(result["allocation"]) == 3


def test_maximization_uses_profits():
    result = solve_vogel(
        [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
        [7, 9, 18],
        [5, 8, 7, 14],
        maximize=True,
    )
    assert result["maximize"] is True
    assert result["total_cost"] == pytest.approx(1548)


@pytest.mark.parametrize(
    ("costs", "supply", "demand"),
    [
        ([[1, 2]], [3, 4], [3, 4]),
        ([[1, -2]], [3], [1, 2]),
        ([[float("inf")]], [1], [1]),
        ([], [], []),
    ],
)
def test_invalid_inputs_raise_value_error(costs, supply, demand):
    with pytest.raises(ValueError):
        solve_vogel(costs, supply, demand)


@pytest.mark.parametrize(
    "costs,supply,demand,maximize,surplus,unmet,total",
    [
        ([[7]], [5], [5], False, 0, 0, 35),
        ([[4, 6, 8], [5, 3, 7]], [30, 40], [20, 15, 10], False, 25, 0, 210),
        ([[4, 6], [5, 3]], [10, 10], [15, 10], False, 0, 5, 70),
        ([[7]], [5], [5], True, 0, 0, 35),
        ([[0]], [0], [0], False, 0, 0, 0),
    ],
)
def test_interpretation_excludes_dummy_shipments(
    costs, supply, demand, maximize, surplus, unmet, total
):
    result = solve_vogel(costs, supply, demand, maximize, context="  Mi empresa  ")
    reading = result["interpretation"]
    assert result["context"] == "Mi empresa"
    assert reading["origins"] == len(supply)
    assert reading["destinations"] == len(demand)
    assert reading["surplus"] == surplus
    assert reading["unmet"] == unmet
    assert result["total_cost"] == total
    assert sum(s["quantity"] for s in reading["shipments"]) == pytest.approx(
        min(sum(supply), sum(demand))
    )
    assert all(
        1 <= s["origin"] <= len(supply) and 1 <= s["destination"] <= len(demand)
        for s in reading["shipments"]
    )


def test_context_does_not_change_calculations_or_iterations():
    args = (
        [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
        [7, 9, 18],
        [5, 8, 7, 14],
    )
    original = solve_vogel(*args)
    contextual = solve_vogel(*args, context="Mi empresa <texto>")
    for field in ("allocation", "total_cost", "steps", "dummy"):
        assert contextual[field] == original[field]


def test_empty_context_uses_original_default():
    result = solve_vogel([[7]], [5], [5], context="  ")
    assert result["context"] == "Problema de transporte sin descripción."


def test_context_requires_text():
    with pytest.raises(TypeError, match="contexto"):
        solve_vogel([[7]], [5], [5], context={})


def test_original_tiebreak_regression():
    args = ([[4, 9, 8], [6, 5, 3], [9, 4, 5]], [4, 4, 6], [2, 5, 2])
    result = solve_vogel(*args)
    assert result["total_cost"] == 46


@pytest.mark.parametrize(
    "costs,supply,demand",
    [
        ([[7]], [5], [5]),
        ([[3, 2, 1]], [8], [2, 3, 3]),
        ([[3], [2], [1]], [2, 3, 3], [8]),
        ([[2, 3], [4, 1]], [10, 10], [10, 10]),
        ([[0, 0], [0, 0]], [0, 0], [0, 0]),
        ([[1, 2], [3, 4]], [0.1, 0.2], [0.15, 0.15]),
    ],
)
def test_trace_reconstructs_solution(costs, supply, demand):
    for maximize in (False, True):
        result = solve_vogel(costs, supply, demand, maximize=maximize)
        reconstructed = [[0] * len(result["demand"]) for _ in result["supply"]]
        for step in result["steps"]:
            i, j = step["cell"]
            assert i in step["active_rows"] and j in step["active_cols"]
            assert step["quantity"] >= 0
            reconstructed[i][j] += step["quantity"]
            if step["phase"] == "direct":
                assert step["max_penalty"] is None
                assert step["row_penalties"] == step["col_penalties"] == {}
        assert reconstructed == result["allocation"]
        assert [sum(row) for row in reconstructed] == pytest.approx(result["supply"])
        assert [sum(col) for col in zip(*reconstructed)] == pytest.approx(
            result["demand"]
        )
        json.dumps(result, allow_nan=False)


def test_api_context_and_error_contract():
    api = Api()
    response = api.solve_vogel(
        {"costs": [[7]], "supply": [5], "demand": [5], "context": "Empresa"}
    )
    assert response["status"] == "success"
    assert response["result"]["context"] == "Empresa"
    for problem in (None, {}, {"costs": [[-1]], "supply": [5], "demand": [5]}):
        response = api.solve_vogel(problem)
        assert response["status"] == "error"
        assert response["message"]
