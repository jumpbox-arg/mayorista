# -*- coding: utf-8 -*-
"""
Capa de acceso al CRM (Google Sheet) — lectura y escritura seguras.

Autenticación por CUENTA DE SERVICIO de Google (credencial JSON). Ver la guía
en docs/SETUP_CREDENCIAL.md para generarla una sola vez.

REGLAS DE SEGURIDAD (no negociables, están en el código a propósito):
  - Nunca borra filas ni columnas.
  - En el enriquecimiento sólo escribe las columnas EMAIL y NOTAS.
  - En el scraping sólo AGREGA filas nuevas al final.
  - Toda escritura pasa por métodos explícitos; el modo lectura es el default.

Incluye además un modo CSV (sin credenciales) como plan B.
"""
import csv
from pathlib import Path


class CRM:
    """Envuelve un worksheet de gspread y mapea columnas lógicas <-> reales."""

    def __init__(self, worksheet, columnas: dict, fila_encabezado: int = 1):
        self.ws = worksheet
        self.columnas = columnas                    # logico -> nombre real
        self.fila_encabezado = fila_encabezado
        self._encabezados = worksheet.row_values(fila_encabezado)
        # nombre real de columna -> índice de columna (1-based) en el Sheet
        self._col_idx = {h: i + 1 for i, h in enumerate(self._encabezados)}

    # ---- factory ----------------------------------------------------------
    @classmethod
    def abrir(cls, cfg, ruta_credencial: str) -> "CRM":
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(ruta_credencial, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(cfg.sheet["id"])
        ws = sh.worksheet(cfg.sheet.get("hoja")) if cfg.sheet.get("hoja") else sh.sheet1
        return cls(ws, cfg.columnas, cfg.sheet.get("fila_encabezado", 1))

    # ---- lectura ----------------------------------------------------------
    def leer_filas(self):
        """Devuelve lista de dicts {campo_logico: valor} con nº de fila real."""
        valores = self.ws.get_all_values()
        cabecera = valores[self.fila_encabezado - 1]
        inv = {v: k for k, v in self.columnas.items()}  # real -> logico
        filas = []
        for n, fila in enumerate(valores[self.fila_encabezado:], start=self.fila_encabezado + 1):
            registro = {"_fila": n}
            for i, celda in enumerate(fila):
                real = cabecera[i] if i < len(cabecera) else None
                if real in inv:
                    registro[inv[real]] = celda
            filas.append(registro)
        return filas

    # ---- escritura (Trabajo 1) -------------------------------------------
    def escribir_email(self, fila_real: int, email: str = None, nota: str = None):
        """Escribe SOLO las celdas EMAIL y/o NOTAS de una fila. Nada más."""
        peticiones = []
        if email is not None:
            col = self._col_idx[self.columnas["email"]]
            peticiones.append({"range": _a1(fila_real, col), "values": [[email]]})
        if nota is not None:
            col = self._col_idx[self.columnas["notas"]]
            peticiones.append({"range": _a1(fila_real, col), "values": [[nota]]})
        # batch_update tiene firma estable en gspread 5.x y 6.x (a diferencia de
        # worksheet.update, que cambió el orden de argumentos entre versiones).
        if peticiones:
            self.ws.batch_update(peticiones, value_input_option="USER_ENTERED")

    # ---- escritura (Trabajo 2) -------------------------------------------
    def agregar_filas(self, filas_dict: list):
        """Agrega filas nuevas AL FINAL, respetando el orden de columnas real."""
        matriz = []
        for reg in filas_dict:
            fila = []
            for real in self._encabezados:
                logico = {v: k for k, v in self.columnas.items()}.get(real)
                fila.append(reg.get(logico, "") if logico else "")
            matriz.append(fila)
        if matriz:
            self.ws.append_rows(matriz, value_input_option="USER_ENTERED")


def _a1(fila: int, col: int) -> str:
    """(fila, col) 1-based -> notación A1 (ej. 8, 8 -> 'H8')."""
    letras = ""
    while col:
        col, r = divmod(col - 1, 26)
        letras = chr(65 + r) + letras
    return f"{letras}{fila}"


# --------------------------------------------------------------------------
# Modo CSV (plan B, sin credenciales): trabaja sobre un archivo local.
# --------------------------------------------------------------------------
class CRMCsv:
    def __init__(self, ruta: str, columnas: dict):
        self.ruta = Path(ruta)
        self.columnas = columnas
        with self.ruta.open(encoding="utf-8") as f:
            self._filas = list(csv.DictReader(f))
        self._campos = list(self._filas[0].keys()) if self._filas else []

    def leer_filas(self):
        inv = {v: k for k, v in self.columnas.items()}
        out = []
        for n, fila in enumerate(self._filas, start=2):
            reg = {"_fila": n}
            for real, val in fila.items():
                if real in inv:
                    reg[inv[real]] = val
            out.append(reg)
        return out

    def escribir_email(self, fila_real, email=None, nota=None):
        idx = fila_real - 2
        if email is not None:
            self._filas[idx][self.columnas["email"]] = email
        if nota is not None:
            self._filas[idx][self.columnas["notas"]] = nota

    def guardar(self, ruta_salida=None):
        destino = Path(ruta_salida or self.ruta)
        with destino.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self._campos)
            w.writeheader()
            w.writerows(self._filas)
