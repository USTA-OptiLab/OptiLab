"""Definición del problema de transporte y su balanceo."""

import json
from pathlib import Path

import numpy as np

ETIQUETA_FICTICIO = "Ficticio"


class ProblemaTransporte:
    def __init__(self, costos, oferta, demanda, origenes=None, destinos=None):
        self.costos = np.array(costos, dtype=float)
        self.oferta = np.array(oferta, dtype=float)
        self.demanda = np.array(demanda, dtype=float)

        if self.costos.ndim != 2 or self.costos.size == 0:
            raise ValueError("costos debe ser una matriz no vacía")
        m, n = self.costos.shape
        if self.oferta.shape != (m,):
            raise ValueError(f"oferta debe tener {m} elementos (uno por origen)")
        if self.demanda.shape != (n,):
            raise ValueError(f"demanda debe tener {n} elementos (uno por destino)")
        if (self.oferta < 0).any() or (self.demanda < 0).any():
            raise ValueError("oferta y demanda no pueden ser negativas")

        self.origenes = list(origenes) if origenes else [f"O{i + 1}" for i in range(m)]
        self.destinos = list(destinos) if destinos else [f"D{j + 1}" for j in range(n)]
        if len(self.origenes) != m or len(self.destinos) != n:
            raise ValueError("la cantidad de nombres no coincide con las dimensiones")

        # Índice de la fila/columna agregada por `balancear()`, si la hay.
        self.fila_ficticia: int | None = None
        self.columna_ficticia: int | None = None

    @property
    def m(self) -> int:
        return self.costos.shape[0]

    @property
    def n(self) -> int:
        return self.costos.shape[1]

    def esta_balanceado(self, tol: float = 1e-9) -> bool:
        return abs(self.oferta.sum() - self.demanda.sum()) <= tol

    def balancear(self) -> "ProblemaTransporte":
        """Devuelve un problema balanceado; agrega fila o columna ficticia (costo 0) si hace falta."""
        if self.esta_balanceado():
            return self
        dif = self.oferta.sum() - self.demanda.sum()
        if dif > 0:  # sobra oferta: destino ficticio
            costos = np.hstack([self.costos, np.zeros((self.m, 1))])
            nuevo = ProblemaTransporte(
                costos,
                self.oferta,
                np.append(self.demanda, dif),
                self.origenes,
                self.destinos + [ETIQUETA_FICTICIO],
            )
            nuevo.columna_ficticia = self.n
        else:  # sobra demanda: origen ficticio
            costos = np.vstack([self.costos, np.zeros((1, self.n))])
            nuevo = ProblemaTransporte(
                costos,
                np.append(self.oferta, -dif),
                self.demanda,
                self.origenes + [ETIQUETA_FICTICIO],
                self.destinos,
            )
            nuevo.fila_ficticia = self.m
        return nuevo

    def a_dict(self) -> dict:
        return {
            "costos": self.costos.tolist(),
            "oferta": self.oferta.tolist(),
            "demanda": self.demanda.tolist(),
            "origenes": self.origenes,
            "destinos": self.destinos,
        }

    @classmethod
    def desde_dict(cls, datos: dict) -> "ProblemaTransporte":
        try:
            return cls(
                datos["costos"],
                datos["oferta"],
                datos["demanda"],
                datos.get("origenes"),
                datos.get("destinos"),
            )
        except KeyError as e:
            raise ValueError(f"falta el campo {e} en el problema") from None

    @classmethod
    def desde_json(cls, ruta) -> "ProblemaTransporte":
        return cls.desde_dict(json.loads(Path(ruta).read_text(encoding="utf-8")))

    def guardar_json(self, ruta) -> None:
        Path(ruta).write_text(
            json.dumps(self.a_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
