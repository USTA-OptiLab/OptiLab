import numpy as np
import pytest
from scipy.optimize import linprog

from optilab.modi_method import Opciones, ProblemaTransporte, reporte, resolver
from optilab.modi_method.inicial import METODOS
from optilab.modi_method.modi import encontrar_ciclo

CLASICO = {
    "costos": [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
    "oferta": [7, 9, 18],
    "demanda": [5, 8, 7, 14],
}
METODOS_INI = list(METODOS)


def optimo_lineal(problema, maximizar=False):
    """Óptimo de referencia con programación lineal (problema balanceado)."""
    p = problema.balancear()
    a_eq, b_eq = [], []
    for i in range(p.m):
        fila = np.zeros(p.m * p.n)
        fila[i * p.n : (i + 1) * p.n] = 1
        a_eq.append(fila)
        b_eq.append(p.oferta[i])
    for j in range(p.n):
        col = np.zeros(p.m * p.n)
        col[j :: p.n] = 1
        a_eq.append(col)
        b_eq.append(p.demanda[j])
    res = linprog(
        p.costos.ravel() * (-1 if maximizar else 1),
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=(0, None),
    )
    return -res.fun if maximizar else res.fun


@pytest.mark.parametrize("metodo", METODOS_INI)
def test_clasico_llega_al_optimo(metodo):
    r = resolver(ProblemaTransporte(**CLASICO), Opciones(metodo_inicial=metodo))
    assert r.optimo
    assert r.costo == pytest.approx(743)


@pytest.mark.parametrize("metodo", METODOS_INI)
def test_inicial_es_factible_y_basica(metodo):
    p = ProblemaTransporte(**CLASICO).balancear()
    x, basicas = METODOS[metodo](p.costos, p.oferta, p.demanda)
    assert x.sum(axis=1) == pytest.approx(p.oferta)
    assert x.sum(axis=0) == pytest.approx(p.demanda)
    assert len(basicas) == p.m + p.n - 1
    assert all(
        (x[i, j] == 0) or ((i, j) in basicas) for i in range(p.m) for j in range(p.n)
    )


def test_oferta_mayor_agrega_destino_ficticio():
    p = ProblemaTransporte([[4, 6], [5, 3]], [20, 30], [10, 25])
    r = resolver(p)
    assert r.problema.columna_ficticia == 2
    assert r.costo == pytest.approx(optimo_lineal(p))
    assert r.asignacion[:, 2].sum() == pytest.approx(15)


def test_demanda_mayor_agrega_origen_ficticio():
    p = ProblemaTransporte([[4, 6], [5, 3]], [10, 15], [20, 20])
    r = resolver(p)
    assert r.problema.fila_ficticia == 2
    assert r.costo == pytest.approx(optimo_lineal(p))


@pytest.mark.parametrize("metodo", METODOS_INI)
def test_caso_degenerado(metodo):
    # oferta y demanda se agotan a la vez varias veces
    p = ProblemaTransporte(
        [[8, 6, 10], [9, 12, 13], [14, 9, 16]], [10, 10, 10], [10, 10, 10]
    )
    r = resolver(p, Opciones(metodo_inicial=metodo))
    assert r.optimo
    assert r.costo == pytest.approx(optimo_lineal(p))


@pytest.mark.parametrize("criterio", ["mas_negativo", "primero_negativo"])
@pytest.mark.parametrize("metodo", METODOS_INI)
def test_criterios_y_metodos_coinciden_con_lineal(criterio, metodo):
    rng = np.random.default_rng(7)
    for _ in range(25):
        m, n = rng.integers(2, 6, size=2)
        oferta = rng.integers(1, 30, size=m)
        demanda = rng.integers(1, 30, size=n)
        p = ProblemaTransporte(rng.integers(1, 40, size=(m, n)), oferta, demanda)
        r = resolver(p, Opciones(metodo_inicial=metodo, criterio_entrada=criterio))
        assert r.optimo
        assert r.costo == pytest.approx(optimo_lineal(p))


def test_costo_nunca_aumenta():
    p = ProblemaTransporte(**CLASICO)
    r = resolver(p, Opciones(metodo_inicial="noroeste"))
    costos = [it.costo for it in r.historial]
    assert costos == sorted(costos, reverse=True)


def test_maximizar():
    p = ProblemaTransporte(**CLASICO)
    r = resolver(p, Opciones(modo="maximizar"))
    assert r.optimo
    assert r.costo == pytest.approx(optimo_lineal(p, maximizar=True))


def test_optimos_alternativos():
    # costos iguales: cualquier reparto es óptimo, así que algún Δ vale 0
    r = resolver(ProblemaTransporte([[1, 1], [1, 1]], [5, 5], [5, 5]))
    assert r.optimos_alternativos


def test_max_iteraciones_corta():
    r = resolver(
        ProblemaTransporte(**CLASICO),
        Opciones(metodo_inicial="noroeste", max_iteraciones=1),
    )
    assert not r.optimo
    assert "NO CONVERGIÓ" in reporte.formatear(r)


def test_ciclo_balanceado():
    p = ProblemaTransporte(**CLASICO).balancear()
    _x, basicas = METODOS["noroeste"](p.costos, p.oferta, p.demanda)
    ciclo = encontrar_ciclo((2, 1), basicas, p.m, p.n)
    assert sum(s for _, _, s in ciclo) == 0
    for k in range(
        len(ciclo)
    ):  # celdas consecutivas comparten fila o columna alternadamente
        (i1, j1, _), (i2, j2, _) = ciclo[k], ciclo[(k + 1) % len(ciclo)]
        assert (i1 == i2) != (j1 == j2)


def test_datos_invalidos():
    with pytest.raises(ValueError):
        ProblemaTransporte([[1, 2]], [5, 5], [5, 5])
    with pytest.raises(ValueError):
        ProblemaTransporte([[1, 2]], [-5], [2, 3])
    with pytest.raises(ValueError):
        Opciones(metodo_inicial="otro")


def test_json_ida_y_vuelta(tmp_path):
    p = ProblemaTransporte(**CLASICO)
    ruta = tmp_path / "p.json"
    p.guardar_json(ruta)
    q = ProblemaTransporte.desde_json(ruta)
    assert (q.costos == p.costos).all() and q.origenes == p.origenes


# --- opciones de visualización ---


def _texto(**kw):
    return reporte.formatear(
        resolver(
            ProblemaTransporte(**CLASICO), Opciones(metodo_inicial="noroeste", **kw)
        )
    )


def test_sin_procedimiento_solo_resultado():
    t = _texto(mostrar_procedimiento=False)
    assert "RESULTADO FINAL" in t
    assert (
        "ITERACIÓN" not in t
        and "SOLUCIÓN INICIAL" not in t
        and "DATOS DEL PROBLEMA" not in t
    )


@pytest.mark.parametrize(
    "flag,marca",
    [
        ("mostrar_inicial", "SOLUCIÓN INICIAL"),
        ("mostrar_potenciales", "Potenciales"),
        ("mostrar_costos_reducidos", "Costos reducidos"),
        ("mostrar_ciclo", "Ciclo:"),
    ],
)
def test_granularidad(flag, marca):
    assert marca in _texto()
    assert marca not in _texto(**{flag: False})


def test_exportar(tmp_path):
    r = resolver(ProblemaTransporte(**CLASICO), Opciones(mostrar_procedimiento=False))
    reporte.exportar(r, tmp_path / "p.txt")
    reporte.exportar(r, tmp_path / "p.json")
    assert "ITERACIÓN" in (tmp_path / "p.txt").read_text(
        encoding="utf-8"
    )  # exporta completo
    assert '"costo": 743' in (tmp_path / "p.json").read_text(encoding="utf-8")
