import pytest

from optilab.graphic_method import solve_graphical
from optilab.graphic_method.api import GraphicMethodApi


def test_maximization_finds_optimal_vertex():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 3, "c2": 2},
            "constraints": [
                {"a1": 2, "a2": 1, "op": "<=", "b": 18},
                {"a1": 2, "a2": 3, "op": "<=", "b": 42},
                {"a1": 3, "a2": 1, "op": "<=", "b": 24},
            ],
        }
    )

    assert result["ok"] is True
    assert result["status"] == "optimal"
    assert result["optimal"]["label"] == "P5"
    assert result["optimal"]["x1"] == pytest.approx(3)
    assert result["optimal"]["x2"] == pytest.approx(12)
    assert result["optimal"]["z"] == pytest.approx(33)
    assert result["region"]["type"] == "area"
    assert result["region"]["bounded"] is True
    assert [3, 12] in result["region"]["polygon"]
    assert result["objective_line"]["z"] == pytest.approx(33)


def test_table_contains_all_intersections_and_marks_optimum():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 3, "c2": 2},
            "constraints": [
                {"a1": 2, "a2": 1, "op": "<=", "b": 18},
                {"a1": 2, "a2": 3, "op": "<=", "b": 42},
                {"a1": 3, "a2": 1, "op": "<=", "b": 24},
            ],
        }
    )

    points = result["points"]
    assert len(points) == 10
    assert any(not point["feasible"] for point in points)
    assert any(point["feasible"] for point in points)
    assert sum(1 for point in points if point["optimal"]) == 1
    for point in points:
        expected = 3 * point["x1"] + 2 * point["x2"]
        assert point["z"] == pytest.approx(expected, abs=1e-6)


def test_intercepts_show_the_axis_calculations():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [{"a1": 2, "a2": 3, "op": "<=", "b": 12}],
        }
    )

    intercept = result["intercepts"][0]
    assert intercept["x_intercept"] == pytest.approx(6)
    assert intercept["y_intercept"] == pytest.approx(4)
    assert "x₂ = 0" in intercept["x_calc"]
    assert "x₁ = 6" in intercept["x_calc"]
    assert "x₁ = 0" in intercept["y_calc"]
    assert "x₂ = 4" in intercept["y_calc"]


def test_minimization_with_greater_equal_constraints():
    result = solve_graphical(
        {
            "sense": "min",
            "objective": {"c1": 2, "c2": 3},
            "constraints": [
                {"a1": 1, "a2": 1, "op": ">=", "b": 4},
                {"a1": 1, "a2": 3, "op": ">=", "b": 6},
            ],
        }
    )

    assert result["status"] == "optimal"
    assert result["region"]["bounded"] is False
    assert result["optimal"]["x1"] == pytest.approx(3)
    assert result["optimal"]["x2"] == pytest.approx(1)
    assert result["optimal"]["z"] == pytest.approx(9)


def test_equality_can_produce_multiple_optimal_solutions():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [
                {"a1": 1, "a2": 1, "op": "=", "b": 4},
                {"a1": 1, "a2": 0, "op": "<=", "b": 3},
                {"a1": 0, "a2": 1, "op": "<=", "b": 3},
            ],
        }
    )

    assert result["status"] == "optimal"
    assert result["region"]["type"] == "segment"
    assert len(result["optimal_points"]) == 2
    assert {(point["x1"], point["x2"]) for point in result["optimal_points"]} == {
        (1.0, 3.0),
        (3.0, 1.0),
    }
    assert all(
        point["optimal"]
        for point in result["points"]
        if (point["x1"], point["x2"]) in {(1.0, 3.0), (3.0, 1.0)}
    )


def test_infeasible_problem():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [
                {"a1": 1, "a2": 1, "op": "<=", "b": 1},
                {"a1": 1, "a2": 0, "op": ">=", "b": 2},
            ],
        }
    )

    assert result["status"] == "infeasible"
    assert result["optimal"] is None
    assert result["region"]["type"] == "empty"
    assert not any(point["feasible"] for point in result["points"])
    assert result["steps"][-1]["title"] == "Conclusión"


def test_unbounded_problem():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [{"a1": 1, "a2": -1, "op": "<=", "b": 1}],
        }
    )

    assert result["status"] == "unbounded"
    assert result["optimal"] is None
    assert result["unbounded_direction"] is not None
    assert result["region"]["bounded"] is False


def test_unbounded_region_can_still_have_a_finite_optimum():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 0},
            "constraints": [{"a1": 1, "a2": 0, "op": "<=", "b": 5}],
        }
    )

    assert result["status"] == "optimal"
    assert result["region"]["bounded"] is False
    assert result["optimal"]["x1"] == pytest.approx(5)
    assert result["optimal"]["x2"] == pytest.approx(0)


def test_single_feasible_point_is_reported_as_a_point_region():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [{"a1": 1, "a2": 1, "op": "<=", "b": 0}],
        }
    )

    assert result["status"] == "optimal"
    assert result["region"]["type"] == "point"
    assert result["region"]["point"] == [0.0, 0.0]
    assert result["optimal"]["z"] == pytest.approx(0)


def test_redundant_constraint_with_negative_rhs_keeps_first_quadrant_feasible():
    result = solve_graphical(
        {
            "sense": "min",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [{"a1": 1, "a2": 1, "op": ">=", "b": -5}],
        }
    )

    assert result["status"] == "optimal"
    assert result["region"]["type"] == "area"
    assert result["optimal"]["x1"] == pytest.approx(0)
    assert result["optimal"]["x2"] == pytest.approx(0)


def test_vertical_and_horizontal_constraints():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [
                {"a1": 1, "a2": 0, "op": "<=", "b": 5},
                {"a1": 0, "a2": 1, "op": "<=", "b": 4},
                {"a1": 1, "a2": 0, "op": ">=", "b": 1},
                {"a1": 0, "a2": 1, "op": ">=", "b": 1},
            ],
        }
    )

    assert result["status"] == "optimal"
    assert result["region"]["bounded"] is True
    assert result["optimal"]["x1"] == pytest.approx(5)
    assert result["optimal"]["x2"] == pytest.approx(4)
    assert result["optimal"]["z"] == pytest.approx(9)


def test_parallel_and_duplicate_constraints_do_not_break_the_solver():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": 1, "c2": 1},
            "constraints": [
                {"a1": 1, "a2": 0, "op": "<=", "b": 5},
                {"a1": 2, "a2": 0, "op": "<=", "b": 10},
                {"a1": 0, "a2": 1, "op": "<=", "b": 4},
            ],
        }
    )

    assert result["status"] == "optimal"
    assert result["optimal"]["x1"] == pytest.approx(5)
    assert result["optimal"]["x2"] == pytest.approx(4)


def test_negative_objective_coefficient():
    result = solve_graphical(
        {
            "sense": "max",
            "objective": {"c1": -1, "c2": 2},
            "constraints": [
                {"a1": 1, "a2": 1, "op": "<=", "b": 4},
                {"a1": 1, "a2": 0, "op": ">=", "b": 1},
            ],
        }
    )

    assert result["status"] == "optimal"
    assert result["optimal"]["x1"] == pytest.approx(1)
    assert result["optimal"]["x2"] == pytest.approx(3)
    assert result["optimal"]["z"] == pytest.approx(5)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "sense": "max",
                "objective": {"c1": 0, "c2": 0},
                "constraints": [{"a1": 1, "a2": 0, "op": "<=", "b": 1}],
            },
            "ambos coeficientes",
        ),
        (
            {"sense": "max", "objective": {"c1": 1, "c2": 1}, "constraints": []},
            "al menos una restricción",
        ),
        (
            {
                "sense": "max",
                "objective": {"c1": 1, "c2": 1},
                "constraints": [{"a1": 1, "a2": 0, "op": "!=", "b": 1}],
            },
            "relación",
        ),
        (
            {
                "sense": "max",
                "objective": {"c1": 1, "c2": 1},
                "constraints": [{"a1": 0, "a2": 0, "op": "<=", "b": 1}],
            },
            "al menos un coeficiente",
        ),
    ],
)
def test_validation_errors(payload, message):
    with pytest.raises(ValueError, match=message):
        solve_graphical(payload)


def test_api_returns_a_readable_error():
    response = GraphicMethodApi().solve_graphical({})

    assert response["ok"] is False
    assert "error" in response
