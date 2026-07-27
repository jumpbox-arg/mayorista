# -*- coding: utf-8 -*-
"""
TRABAJO 1 — Enriquecer emails del CRM.

Para cada lead que tiene WEB pero no EMAIL, entra al sitio, busca el mail y
completa la columna EMAIL. Si no encuentra, deja la nota para ir por WhatsApp.

MODO SEGURO: por defecto sólo muestra la vista previa (no escribe). Se aplica
al Sheet real únicamente con aplicar=True.
"""
from . import email_finder


def _necesita_email(reg) -> bool:
    email = (reg.get("email") or "").strip().lower()
    web = (reg.get("web") or "").strip()
    return web != "" and email in ("", "sin email", "sin mail")


def enriquecer(crm, cfg, aplicar=False, limite=None, on_progress=None):
    """
    crm: instancia de CRM o CRMCsv (ya abierta).
    Devuelve un resumen con la lista de cambios.
    """
    paths = cfg.enriquecimiento["paths"]
    prioridad = cfg.enriquecimiento["prioridad"]
    nota_sin = cfg.enriquecimiento["nota_sin_email"]

    filas = crm.leer_filas()
    pendientes = [r for r in filas if _necesita_email(r)]
    if limite:
        pendientes = pendientes[:limite]

    cambios, para_wa = [], []
    for i, reg in enumerate(pendientes, 1):
        email, estado = email_finder.buscar_email(reg["web"], paths, prioridad)
        if email:
            cambios.append({"fila": reg["_fila"], "id": reg.get("id"),
                            "empresa": reg.get("empresa"), "web": reg["web"],
                            "email": email})
            if aplicar:
                crm.escribir_email(reg["_fila"], email=email)
        else:
            para_wa.append({"fila": reg["_fila"], "id": reg.get("id"),
                            "empresa": reg.get("empresa"), "web": reg["web"],
                            "motivo": estado})
            if aplicar:
                crm.escribir_email(reg["_fila"], nota=nota_sin)
        if on_progress:
            on_progress(i, len(pendientes), reg, email, estado)

    return {
        "total_pendientes": len(pendientes),
        "mails_encontrados": len(cambios),
        "para_whatsapp": len(para_wa),
        "cambios": cambios,
        "wa": para_wa,
        "aplicado": aplicar,
    }
