from fractions import Fraction

import pytest

from optilab.app import Api
from optilab.primal_dual import Problem, build_dual, solve, solve_request


def lp(sense, c, cons, signs=None):
    return Problem(sense, c, cons, signs or [">=0"] * len(c))


def z_of(out):
    return out["result"]["z"]


def test_dual_of_max_is_min():
    p = lp("max", [4, 3], [([2, 1], "<=", 10), ([1, 2], "<=", 8)])
    d = build_dual(p)
    assert d.sense == "min"
    assert d.c == [10, 8]
    assert d.signs == [">=0", ">=0"]
    assert [t for _, t, _ in d.cons] == [">=", ">="]


def test_ej1_produccion():
    p = lp("max", [3, 5], [([1, 0], "<=", 4), ([0, 2], "<=", 12), ([3, 2], "<=", 18)])
    out = solve(p, verify=True)
    assert out["result"]["status"] == "optimal"
    assert z_of(out) == 36
    assert out["primal_result"]["z"] == 36
    assert out["primal_result"]["x"] == [2, 6]


def test_ej2_dieta():
    p = lp("min", [2, 3], [([1, 1], ">=", 4), ([1, 3], ">=", 6)])
    assert z_of(solve(p)) == 9


def test_ej9_dual_values():
    p = lp("max", [4, 3], [([2, 1], "<=", 10), ([1, 2], "<=", 8)])
    out = solve(p)
    assert z_of(out) == 22
    assert out["result"]["x"] == [Fraction(5, 3), Fraction(2, 3)]


def test_ej8_fractions():
    p = lp("min", [6, 8, 5], [([2, 1, 1], ">=", 10), ([1, 3, 1], ">=", 12), ([1, 1, 2], ">=", 8)])
    out = solve(p, verify=True)
    assert z_of(out) == Fraction(316, 7)
    assert out["primal_result"]["x"] == [Fraction(22, 7), Fraction(18, 7), Fraction(8, 7)]


def test_ej4_equality_free_dual():
    p = lp("min", [2, 3], [([1, 1], "=", 10), ([1, 0], ">=", 2)])
    d = build_dual(p)
    assert d.signs == ["libre", ">=0"]
    assert z_of(solve(p)) == 20


def test_ej5_free_variable():
    p = lp("max", [1, 1], [([1, 1], "<=", 6), ([1, -1], "<=", 2)], [">=0", "libre"])
    assert z_of(solve(p)) == 6


def test_infeasible_primal_gives_unbounded_dual():
    p = lp("max", [1, 1], [([1, 1], "<=", 2), ([1, 1], ">=", 5)])
    out = solve(p, verify=True)
    assert out["primal_result"]["status"] == "infeasible"
    assert out["result"]["status"] != "optimal"


def test_unbounded_primal_gives_infeasible_dual():
    p = lp("max", [1, 1], [([1, -1], "<=", 2)])
    out = solve(p, verify=True)
    assert out["primal_result"]["status"] == "unbounded"
    assert out["result"]["status"] == "infeasible"


@pytest.mark.parametrize("bad", [{"sense": "x"}, {}])
def test_request_invalid(bad):
    with pytest.raises(ValueError):
        solve_request(bad)


def payload(**kw):
    base = {
        "sense": "max",
        "c": ["4", "3"],
        "cons": [{"a": ["2", "1"], "type": "<=", "b": "10"}, {"a": ["1", "2"], "type": "<=", "b": "8"}],
        "signs": [">=0", ">=0"],
    }
    return {**base, **kw}


def test_api_ok_and_formats():
    r = Api().solve_primal_dual(payload(verify=True))
    assert r["status"] == "ok"
    assert r["primal"]["objective"] == "max Z = 4x1 + 3x2"
    assert r["dual"]["objective"] == "min Z = 10y1 + 8y2"
    assert r["result"]["z"]["frac"] == "22"
    assert [v["frac"] for v in r["result"]["vars"]] == ["5/3", "2/3"]
    assert r["primal_result"]["z"]["frac"] == "22"


def test_api_accepts_decimals_commas_fractions():
    r = Api().solve_primal_dual(payload(c=["2,5", "1/2"]))
    assert r["status"] == "ok"
    assert r["primal"]["objective"] == "max Z = 5/2x1 + 1/2x2"


@pytest.mark.parametrize(
    "bad",
    [
        payload(c=["a", "3"]),
        payload(c=["1/0", "3"]),
        payload(c=["", "3"]),
        payload(sense="foo"),
        {"sense": "max"},
    ],
)
def test_api_errors_do_not_raise(bad):
    r = Api().solve_primal_dual(bad)
    assert r["status"] == "error"
    assert r["message"]
