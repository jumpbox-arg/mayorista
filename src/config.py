# -*- coding: utf-8 -*-
"""Carga y valida el archivo de configuración YAML de un cliente."""
import yaml


class Config:
    def __init__(self, data: dict):
        self._d = data

    @classmethod
    def cargar(cls, ruta: str) -> "Config":
        with open(ruta, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        cfg = cls(data)
        cfg._validar()
        return cfg

    def _validar(self):
        for clave in ("cliente", "sheet", "columnas", "ids", "enriquecimiento"):
            if clave not in self._d:
                raise ValueError(f"Falta la sección '{clave}' en la config.")
        if not self._d["sheet"].get("id") or "PEGA_ACA" in str(self._d["sheet"]["id"]):
            raise ValueError("Configurá el ID real del Sheet en la sección 'sheet.id'.")

    # accesos cómodos
    @property
    def cliente(self): return self._d["cliente"]
    @property
    def sheet(self): return self._d["sheet"]
    @property
    def columnas(self): return self._d["columnas"]
    @property
    def ids(self): return self._d["ids"]
    @property
    def enriquecimiento(self): return self._d["enriquecimiento"]
    @property
    def mapas(self): return self._d.get("mapas", {})
