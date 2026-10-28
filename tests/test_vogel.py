import pytest

from optilab.vogel import solve_vogel


def assert_respects_totals(result, supply, demand, dummy_supply=0, dummy_demand=0):
    allocation = result["allocation"]
    row_sums = [sum(row) for row in allocation]
    col_sums = [sum(col) for col in zip(*allocation)]
    assert row_sums == pytest.approx(
        list(supply) + [dummy_supply] * (len(row_sums) - len(supply))
    )
    assert col_sums == pytest.approx(
        list(demand) + [dummy_demand] * (len(col_sums) - len(demand))
    )


def test_balanced_classic_example():
    costs = [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]]
    result = solve_vogel(costs, [7, 9, 18], [5, 8, 7, 14])
    assert result["total_cost"] == 779
    assert result["dummy"] is None
    assert result["allocation"] == [
        [5, 0, 0, 2],
        [0, 0, 7, 2],
        [0, 8, 0, 10],
    ]
    assert result["steps"][0]["cell"] == [2, 1]
    assert_respects_totals(result, [7, 9, 18], [5, 8, 7, 14])


def test_excess_supply_adds_dummy_column():
    result = solve_vogel([[4, 6, 8], [5, 3, 7]], [30, 40], [20, 15, 10])
    assert result["dummy"] == "column"
    assert len(result["allocation"][0]) == 4
    assert result["total_cost"] == 210
    assert_respects_totals(result, [30, 40], [20, 15, 10], dummy_demand=25)


def test_excess_demand_adds_dummy_row():
    result = solve_vogel([[4, 6], [5, 3]], [10, 10], [15, 10])
    assert result["dummy"] == "row"
    assert len(result["allocation"]) == 3
    assert result["total_cost"] == 70
    assert_respects_totals(result, [10, 10], [15, 10], dummy_supply=5)


def test_degenerate_keeps_basic_cell_count():
    result = solve_vogel([[2, 3], [4, 1]], [10, 10], [10, 10])
    assert result["total_cost"] == 30
    assert len(result["steps"]) == 2 + 2 - 1


def test_single_cell():
    result = solve_vogel([[7]], [5], [5])
    assert result["allocation"] == [[5]]
    assert result["total_cost"] == 35


@pytest.mark.parametrize(
    "costs, supply, demand",
    [
        ([], [], []),
        ([[1, 2]], [5], [3]),
        ([[1, 2], [3, 4]], [5], [3, 2]),
        ([[1, -2]], [5], [2, 3]),
        ([[1, 2]], [-5], [2, 3]),
    ],
)
def test_invalid_input_raises(costs, supply, demand):
    with pytest.raises(ValueError):
        solve_vogel(costs, supply, demand)
