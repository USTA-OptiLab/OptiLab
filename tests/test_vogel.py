import pytest

from optilab.vogel import balance, main, penalty, solve_vogel


def assert_respects_totals(allocation, supply, demand):
    row_sums = [sum(x or 0 for x in row) for row in allocation]
    col_sums = [sum(x or 0 for x in col) for col in zip(*allocation)]
    assert row_sums == pytest.approx(supply)
    assert col_sums == pytest.approx(demand)


def test_penalty():
    assert penalty([4, 9, 6]) == 2
    assert penalty([5]) == 5
    assert penalty([]) == 0


def test_balance_adds_dummy_column(capsys):
    costs, _, demand = balance([[4, 6, 8], [5, 3, 7]], [30, 40], [20, 15, 10])
    assert costs == [[4, 6, 8, 0], [5, 3, 7, 0]]
    assert demand == [20, 15, 10, 25]
    assert "DESTINO ficticio" in capsys.readouterr().out


def test_balance_adds_dummy_row(capsys):
    costs, supply, _ = balance([[4, 6], [5, 3]], [10, 10], [15, 10])
    assert costs == [[4, 6], [5, 3], [0, 0]]
    assert supply == [10, 10, 5]
    assert "ORIGEN ficticio" in capsys.readouterr().out


def test_balanced_classic_example():
    costs = [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]]
    *_, allocation, total_cost = solve_vogel(costs, [7, 9, 18], [5, 8, 7, 14], False)
    assert total_cost == 779
    assert_respects_totals(allocation, [7, 9, 18], [5, 8, 7, 14])


def test_excess_supply():
    _, supply, demand, allocation, total_cost = solve_vogel(
        [[4, 6, 8], [5, 3, 7]], [30, 40], [20, 15, 10], False
    )
    assert total_cost == 210
    assert_respects_totals(allocation, supply, demand)


def test_excess_demand():
    _, supply, demand, allocation, total_cost = solve_vogel(
        [[4, 6], [5, 3]], [10, 10], [15, 10], False
    )
    assert len(allocation) == 3
    assert total_cost == 70
    assert_respects_totals(allocation, supply, demand)


def test_degenerate_keeps_basic_cell_count():
    *_, allocation, total_cost = solve_vogel(
        [[2, 3], [4, 1]], [10, 10], [10, 10], False
    )
    assert total_cost == 30
    assert sum(1 for row in allocation for x in row if x is not None) == 2 + 2 - 1


def test_single_cell():
    *_, allocation, total_cost = solve_vogel([[7]], [5], [5], False)
    assert allocation == [[5]]
    assert total_cost == 35


def test_main_example(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _="": "1")
    main()
    out = capsys.readouterr().out
    assert "ITERACIÓN 1" in out
    assert "Costo total Z = 779" in out


def run_main(monkeypatch, answers):
    answers = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _="": next(answers))
    main()


def test_main_user_input_with_context(monkeypatch, capsys):
    run_main(
        monkeypatch,
        ["2", "Mi empresa", "2", "3", "4 6 8", "5 3 7", "30 40", "20 15 10"],
    )
    out = capsys.readouterr().out
    assert "Problema: Mi empresa" in out
    assert "DESTINO ficticio" in out
    assert "Costo total Z = 210" in out
    assert "El costo total de transporte de esta solución inicial es 210" in out
    assert "Sobra oferta: 25 unidades" in out


def test_main_empty_context_uses_default(monkeypatch, capsys):
    run_main(monkeypatch, ["2", "", "1", "1", "7", "5", "5"])
    out = capsys.readouterr().out
    assert "Problema de transporte sin descripción" in out
    assert "El origen O1 envía 5 unidades al destino D1" in out


def test_main_retries_invalid_input(monkeypatch, capsys):
    run_main(
        monkeypatch,
        [
            "2",
            "",
            "abc",
            "0",
            "2",
            "3",
            "4 6",
            "4 6 x",
            "4 6 8",
            "5 -3 7",
            "5 3 7",
            "nan 40",
            "30 40",
            "20 15",
            "20 15 10",
        ],
    )
    out = capsys.readouterr().out
    assert "ingrese un número entero" in out
    assert "mayor o igual a 1" in out
    assert "Debe ingresar 3 valores y ingresó 2" in out
    assert "números finitos mayores o iguales a 0" in out
    assert "Costo total Z = 210" in out


def test_main_excess_demand_interpretation(monkeypatch, capsys):
    run_main(monkeypatch, ["2", "", "2", "2", "4 6", "5 3", "10 10", "15 10"])
    out = capsys.readouterr().out
    assert "Falta oferta: 5 unidades" in out


def test_main_exits_cleanly_on_eof(monkeypatch, capsys):
    answers = iter(["2", "", "2"])

    def fake_input(_=""):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)
    main()
    assert "Entrada cancelada" in capsys.readouterr().out
