import dataclasses
import os
from pathlib import Path

import numpy as np
import webview
from scipy import stats

from optilab.modi_method import analisis, modi, reporte
from optilab.modi_method.opciones import Opciones
from optilab.modi_method.problema import ProblemaTransporte

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
DIST_INDEX = FRONTEND_DIR / "dist" / "index.html"
DEV_SERVER_URL = "http://localhost:5173"
EJEMPLO = Path(__file__).resolve().parents[2] / "ejemplos" / "ejemplo1.json"


def _ventana():
    return webview.windows[0]


def _primera_ruta(resultado):
    """`create_file_dialog` devuelve una tupla de rutas (o, en algunas versiones, un str)."""
    if not resultado:
        return None
    return resultado if isinstance(resultado, str) else resultado[0]


def _limite(x):
    return None if np.isinf(x) else x


def _rango_a_dict(f):
    return {
        "origen": f.origen,
        "destino": f.destino,
        "basica": f.basica,
        "costo": f.costo,
        "minimo": _limite(f.minimo),
        "maximo": _limite(f.maximo),
    }


def _iteracion_a_dict(it):
    return {
        "numero": it.numero,
        "asignacion": it.asignacion.tolist(),
        "basicas": [list(c) for c in sorted(it.basicas)],
        "u": it.u.tolist(),
        "v": it.v.tolist(),
        "delta": [
            [None if np.isnan(d) else d for d in fila] for fila in it.delta.tolist()
        ],
        "costo": it.costo,
        "entrante": list(it.entrante) if it.entrante else None,
        "ciclo": [list(c) for c in it.ciclo],
        "theta": it.theta,
        "sale": list(it.sale) if it.sale else None,
    }


def _resultado_a_dict(r):
    return {
        "problema": r.problema.a_dict(),
        "historial": [_iteracion_a_dict(it) for it in r.historial],
        "titulos": [analisis.titulo_estado(r, k) for k in range(len(r.historial))],
        "costo_inicial": r.costo_inicial,
        "costo": r.costo,
        "optimo": r.optimo,
        "optimos_alternativos": r.optimos_alternativos,
        "columna_ficticia": r.problema.columna_ficticia,
        "fila_ficticia": r.problema.fila_ficticia,
        "mejoras": sum(1 for it in r.historial if it.entrante is not None),
        "bloques": reporte.secciones(r),
    }


class Api:
    def describe(self, values):
        data = np.asarray(values, dtype=float)
        return {
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "zscores": stats.zscore(data).tolist(),
        }

    def ejemplo(self):
        try:
            return {"problema": ProblemaTransporte.desde_json(EJEMPLO).a_dict()}
        except (OSError, ValueError) as e:
            return {"error": str(e)}

    def resolver(self, problema, opciones):
        try:
            p = ProblemaTransporte.desde_dict(problema)
            o = Opciones(**opciones)
            r = modi.resolver(p, o)
        except (ValueError, RuntimeError) as e:
            return {"error": str(e)}
        return _resultado_a_dict(r)

    def sensibilidad(self, problema, opciones):
        try:
            p = ProblemaTransporte.desde_dict(problema)
            o = Opciones(**opciones)
            r = modi.resolver(p, o)
            if not r.optimo:
                return {
                    "error": "la sensibilidad solo se calcula sobre una solución óptima"
                }
            filas = analisis.sensibilidad(r)
        except (ValueError, RuntimeError) as e:
            return {"error": str(e)}
        return {"filas": [_rango_a_dict(f) for f in filas]}

    def comparar(self, problema, opciones):
        try:
            p = ProblemaTransporte.desde_dict(problema)
            o = Opciones(**opciones)
            filas = analisis.comparar_metodos(p, o)
        except (ValueError, RuntimeError) as e:
            return {"error": str(e)}
        return {"filas": [dataclasses.asdict(f) for f in filas]}

    def abrir_problema(self):
        ruta = _primera_ruta(
            _ventana().create_file_dialog(
                webview.OPEN_DIALOG,
                file_types=("Problema JSON (*.json)", "Todos los archivos (*.*)"),
            )
        )
        if not ruta:
            return None
        try:
            return {
                "problema": ProblemaTransporte.desde_json(ruta).a_dict(),
                "ruta": ruta,
            }
        except (OSError, ValueError) as e:
            return {"error": str(e)}

    def guardar_problema(self, problema):
        ruta = _primera_ruta(
            _ventana().create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename="problema.json",
                file_types=("Problema JSON (*.json)",),
            )
        )
        if not ruta:
            return None
        try:
            ProblemaTransporte.desde_dict(problema).guardar_json(ruta)
        except (OSError, ValueError) as e:
            return {"error": str(e)}
        return {"ruta": ruta}

    def exportar_procedimiento(self, problema, opciones):
        ruta = _primera_ruta(
            _ventana().create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename="procedimiento.txt",
                file_types=("Texto (*.txt)", "JSON (*.json)"),
            )
        )
        if not ruta:
            return None
        try:
            p = ProblemaTransporte.desde_dict(problema)
            o = Opciones(**opciones)
            r = modi.resolver(p, o)
            reporte.exportar(r, ruta)
        except (ValueError, RuntimeError, OSError) as e:
            return {"error": str(e)}
        return {"ruta": ruta}


def main():
    url = (
        DEV_SERVER_URL
        if os.environ.get("OPTILAB_DEV") or not DIST_INDEX.exists()
        else str(DIST_INDEX)
    )
    webview.create_window(
        "OptiLab", url, js_api=Api(), width=1280, height=800, min_size=(640, 480)
    )
    # pywebview forces the Qt backend on any KDE session regardless of what's
    # installed; we only have GTK/WebKit bindings, so pin the GTK backend.
    webview.start(gui="gtk")


if __name__ == "__main__":
    main()
