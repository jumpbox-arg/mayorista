# -*- coding: utf-8 -*-
"""
TRABAJO 2 — Scrapear leads nuevos de Google Maps (Places API).

Busca negocios por (rubro x ciudad), hace DEDUPE contra el CRM (por nombre
normalizado o teléfono) y prepara las filas nuevas respetando las columnas.

MODO SEGURO: por defecto sólo muestra lo que agregaría (no escribe). Se aplica
al Sheet con aplicar=True. Necesita una API key con Places API habilitada.
"""
import re
import unicodedata
from datetime import date

import requests

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"


def _norm(txt: str) -> str:
    txt = (txt or "").strip().lower()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt)
                  if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", txt)


def _digitos(tel: str) -> str:
    return re.sub(r"\D", "", tel or "")


def _wa(tel: str) -> str:
    """Deriva un WhatsApp del teléfono si parece celular argentino (link wa.me)."""
    d = _digitos(tel)
    if not d:
        return ""
    # normalizar a formato internacional AR (54) con 9 para celular
    if d.startswith("0"):
        d = d[1:]
    if "15" in (tel or "") or len(d) >= 10:
        if not d.startswith("54"):
            d = "54" + d
        return f"https://wa.me/{d}"
    return ""


def es_duplicado(negocio, existentes) -> bool:
    nom = _norm(negocio.get("empresa"))
    tel = _digitos(negocio.get("telefono"))
    for e in existentes:
        if nom and nom == _norm(e.get("empresa")):
            return True
        if tel and len(tel) >= 8 and tel == _digitos(e.get("telefono")):
            return True
    return False


def _siguiente_id(existentes, prefijo):
    nums = []
    for e in existentes:
        v = str(e.get("id", ""))
        if v.startswith(prefijo):
            d = re.sub(r"\D", "", v)
            if d:
                nums.append(int(d))
    n = (max(nums) + 1) if nums else 1
    return lambda i: f"{prefijo}{n + i:03d}"


def _siguiente_batch(existentes, prefijo):
    nums = []
    for e in existentes:
        v = str(e.get("batch", ""))
        if v.startswith(prefijo):
            d = re.sub(r"\D", "", v)
            if d:
                nums.append(int(d))
    n = (max(nums) + 1) if nums else 1
    return f"{prefijo}{n:03d}"


def buscar_places(rubro, ciudad, api_key, pais, maximo=60):
    """Consulta Places Text Search y devuelve negocios mapeados al CRM."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": ("places.displayName,places.formattedAddress,"
                             "places.nationalPhoneNumber,places.websiteUri,"
                             "places.primaryTypeDisplayName"),
    }
    resultados, token = [], None
    while len(resultados) < maximo:
        cuerpo = {"textQuery": f"{rubro} en {ciudad}, {pais}"}
        if token:
            cuerpo["pageToken"] = token
        r = requests.post(PLACES_URL, headers=headers, json=cuerpo, timeout=20)
        r.raise_for_status()
        data = r.json()
        for p in data.get("places", []):
            resultados.append({
                "empresa": (p.get("displayName") or {}).get("text", ""),
                "tipo": (p.get("primaryTypeDisplayName") or {}).get("text", rubro),
                "ciudad": ciudad,
                "telefono": p.get("nationalPhoneNumber", ""),
                "web": p.get("websiteUri", ""),
                "instagram": "",
            })
        token = data.get("nextPageToken")
        if not token:
            break
    return resultados[:maximo]


def scrapear(crm, cfg, api_key, aplicar=False, rubros=None, ciudades=None):
    m = cfg.mapas
    rubros = rubros or m.get("rubros", [])
    ciudades = ciudades or m.get("ciudades", [])
    provincia_def = m.get("provincia_por_defecto", "")
    maximo = m.get("max_por_busqueda", 60)
    pais = cfg.cliente.get("pais", "Argentina")

    existentes = crm.leer_filas()
    gen_id = _siguiente_id(existentes, cfg.ids["prefijo_id"])
    batch = _siguiente_batch(existentes, cfg.ids["prefijo_batch"])
    hoy = date.today().strftime("%d/%m/%Y")

    nuevos, duplicados = [], 0
    todos_existentes = list(existentes)
    for rubro in rubros:
        for ciudad in ciudades:
            for neg in buscar_places(rubro, ciudad, api_key, pais, maximo):
                if not neg.get("empresa"):
                    continue
                if es_duplicado(neg, todos_existentes):
                    duplicados += 1
                    continue
                neg["provincia"] = provincia_def
                nuevos.append(neg)
                todos_existentes.append(neg)  # evita duplicar dentro del mismo run

    filas_nuevas = []
    for i, neg in enumerate(nuevos):
        filas_nuevas.append({
            "id": gen_id(i), "fecha_carga": hoy, "empresa": neg["empresa"],
            "tipo": neg["tipo"], "ciudad": neg["ciudad"], "provincia": neg["provincia"],
            "email": "sin email", "telefono": neg["telefono"],
            "whatsapp": _wa(neg["telefono"]),
            "instagram": neg["instagram"], "web": neg["web"],
            "fuente": cfg.enriquecimiento["fuente"],
            "estado": cfg.enriquecimiento["estado_nuevo"], "batch": batch,
        })

    if aplicar and filas_nuevas:
        crm.agregar_filas(filas_nuevas)

    return {
        "encontrados_unicos": len(nuevos),
        "duplicados_salteados": duplicados,
        "batch": batch,
        "filas": filas_nuevas,
        "aplicado": aplicar,
    }
