import numpy as np
import pytest

from optilab.modi_method import Opciones, ProblemaTransporte, reporte, resolver
from optilab.modi_method.analisis import comparar_metodos, sensibilidad, titulo_estado

CLASICO = {
    "costos": [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
    "oferta": [7, 9, 18],
    "demanda": [5, 8, 7, 14],
}


def _con_costo(p, i, j, valor):
    costos = p.costos.copy()
    costos[i, j] = valor
    return ProblemaTransporte(costos, p.oferta, p.demanda, p.origenes, p.destinos)


def _puntos_internos(f, holgura=25.0):
    """Extremos del rango (los infinitos se acotan) y el punto medio."""
    lo = f.minimo if np.isfinite(f.minimo) else f.costo - holgura
    hi = f.maximo if np.isfinite(f.maximo) else f.costo + holgura
    return [lo, (lo + hi) / 2, hi]


@pytest.mark.parametrize("modo", ["minimizar", "maximizar"])
def test_sensibilidad_la_solucion_sigue_siendo_optima_dentro_del_rango(modo):
    """Con el costo en cualquier punto de su rango, la asignación original sigue siendo óptima."""
    rng = np.random.default_rng(11)
    for _ in range(15):
        m, n = rng.integers(2, 5, size=2)
        p = ProblemaTransporte(
            rng.integers(1, 30, size=(m, n)),
            rng.integers(1, 20, size=m),
            rng.integers(1, 20, size=n),
        )
        r = resolver(p, Opciones(modo=modo))
        x = r.asignacion[: p.m, : p.n]
        for f in sensibilidad(r):
            i, j = p.origenes.index(f.origen), p.destinos.index(f.destino)
            for valor in _puntos_internos(f):
                q = _con_costo(p, i, j, valor)
                esperado = resolver(q, Opciones(modo=modo)).costo
                assert float((q.costos * x).sum()) == pytest.approx(
                    esperado, abs=1e-6
                ), (f, valor)


def test_sensibilidad_fuera_del_rango_la_solucion_mejora():
    """Pasado el límite finito de una ruta no básica, ya conviene usarla (el óptimo baja)."""
    p = ProblemaTransporte(**CLASICO)
    r = resolver(p)
    x = r.asignacion
    for f in sensibilidad(r):
        if f.basica or not np.isfinite(f.minimo):
            continue
        i, j = p.origenes.index(f.origen), p.destinos.index(f.destino)
        q = _con_costo(p, i, j, f.minimo - 1)
        assert resolver(q).costo < float((q.costos * x).sum()) - 1e-9


def test_sensibilidad_valores_conocidos():
    r = resolver(ProblemaTransporte(**CLASICO))
    por_ruta = {(f.origen, f.destino): f for f in sensibilidad(r)}
    f = por_ruta[("O1", "D2")]  # no básica con Δ = 32 y costo 30
    assert not f.basica and f.minimo == pytest.approx(-2) and f.maximo == np.inf
    assert all(f.minimo <= f.costo <= f.maximo for f in por_ruta.values())


def test_sensibilidad_requiere_optimo():
    r = resolver(
        ProblemaTransporte(**CLASICO),
        Opciones(metodo_inicial="noroeste", max_iteraciones=1),
    )
    with pytest.raises(ValueError):
        sensibilidad(r)


def test_sensibilidad_no_reporta_ficticios():
    p = ProblemaTransporte([[4, 6], [5, 3]], [20, 30], [10, 25])
    assert len(sensibilidad(resolver(p))) == 4


def test_comparar_metodos():
    filas = comparar_metodos(ProblemaTransporte(**CLASICO))
    assert [f.metodo for f in filas] == ["noroeste", "costo_minimo", "vogel"]
    assert all(f.optimo and f.costo_final == pytest.approx(743) for f in filas)
    assert [f.costo_inicial for f in filas] == [1015, 814, 779]
    assert filas[2].iteraciones <= filas[0].iteraciones


def test_bloques_de_texto():
    r = resolver(
        ProblemaTransporte(**CLASICO),
        Opciones(mostrar_sensibilidad=True, mostrar_procedimiento=False),
    )
    t = reporte.formatear(r)
    assert "ANÁLISIS DE SENSIBILIDAD" in t and "RESULTADO FINAL" in t
    assert "SENSIBILIDAD" not in reporte.formatear(
        resolver(ProblemaTransporte(**CLASICO))
    )
    assert "mismo óptimo (743)" in reporte.bloque_comparacion(
        comparar_metodos(ProblemaTransporte(**CLASICO))
    )


def test_titulos_de_estado():
    r = resolver(ProblemaTransporte(**CLASICO), Opciones(metodo_inicial="noroeste"))
    titulos = [titulo_estado(r, k) for k in range(len(r.historial))]
    assert "solución inicial" in titulos[0] and "óptima" in titulos[-1]
