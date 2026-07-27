# -*- coding: utf-8 -*-
"""
Motor de búsqueda de emails en sitios web — robusto y reutilizable.

Diseñado para NO traer basura. Los falsos positivos típicos (archivos de
fuentes .woff, imágenes, placeholders tipo 'ejemplo@mail.com', mails de
plataformas como Tiendanube) quedan filtrados por varias capas:

  1. Extracción priorizada de enlaces mailto: (la señal más confiable).
  2. Regex sobre el texto visible, con desofuscación ('info (at) dominio').
  3. Rechazo por extensión de asset en el dominio (.woff, .png, .css, ...).
  4. Validación de TLD real.
  5. Preferencia por el mail cuyo dominio COINCIDE con el del sitio.
  6. Preferencia por prefijo comercial (ventas, compras, mayorista, info...).

No depende de ninguna config global: se le pasan los parámetros.
"""
import re
import html
import time
from urllib.parse import urljoin, urlparse

import requests

try:
    from bs4 import BeautifulSoup
    _HAY_BS4 = True
except ImportError:  # el sistema sigue funcionando sin bs4, con menos precisión
    _HAY_BS4 = False

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
MAILTO_RE = re.compile(r'mailto:([^"\'>?\s]+)', re.I)

# Extensiones de archivos: si aparecen en el "dominio", NO es un email real.
ASSET_EXT = (
    "woff", "woff2", "ttf", "eot", "otf",           # fuentes tipográficas
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp",  # imágenes
    "css", "js", "map", "json", "xml",              # código/estilos
    "mp4", "webm", "mp3", "wav", "pdf", "zip",      # media/archivos
)

# Fragmentos que marcan un mail como placeholder / de terceros / basura.
BLOCK = (
    "sentry", "wixpress", "@wix", "cloudflare", "godaddy",
    "example", "ejemplo", "@dominio", "@mail.com", "@email.com",
    "tumail", "tucorreo", "youremail", "your@", "test@", "sample@",
    "usuario@", "nombre@", "name@", "user@", "abc@", "xxx@",
    "no-reply", "noreply", "@sentry", "soporte@tiendanube",
    "@sentry.io", "u003e", "u0040",
)

# Plataformas de ecommerce: un mail con ESE dominio no es del negocio.
PLATAFORMA = ("tiendanube.com", "mitiendanube.com", "mercadoshops.com",
              "mercadolibre.com", "empretienda.com", "wix.com")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121 Safari/537.36")


def _dominio_raiz(url_o_dominio: str) -> str:
    """'https://www.solodeportes.com.ar/x' -> 'solodeportes' (parte registrable)."""
    s = re.sub(r"^https?://", "", (url_o_dominio or "").strip().lower())
    s = s.split("/")[0]
    s = re.sub(r"^www\.", "", s)
    partes = s.split(".")
    if not partes or not partes[0]:
        return ""
    # para .com.ar / .com.mx el nombre registrable es el primer label
    return partes[0]


def _es_asset(mail: str) -> bool:
    dominio = mail.split("@")[-1]
    tld = dominio.rsplit(".", 1)[-1].lower()
    return tld in ASSET_EXT


def _tld_valido(mail: str) -> bool:
    dominio = mail.split("@")[-1]
    if "." not in dominio:
        return False
    tld = dominio.rsplit(".", 1)[-1].lower()
    return tld.isalpha() and 2 <= len(tld) <= 24 and tld not in ASSET_EXT


def _desofuscar(texto: str) -> str:
    t = html.unescape(texto)
    t = re.sub(r"\s*\(?\s*(?:at|arroba)\s*\)?\s*", "@", t, flags=re.I)
    t = re.sub(r"\s*\(?\s*(?:dot|punto)\s*\)?\s*", ".", t, flags=re.I)
    return t


def _limpiar_candidato(mail: str) -> str:
    return mail.strip().strip(".,;:()<>[]\"' ").lower()


def _validos_en(texto: str):
    """Devuelve emails plausibles en un HTML, priorizando mailto:."""
    salida = []
    # 1) mailto: primero (más confiable)
    candidatos = MAILTO_RE.findall(texto)
    # 2) texto visible / crudo con desofuscación
    candidatos += EMAIL_RE.findall(_desofuscar(texto))
    for c in candidatos:
        m = _limpiar_candidato(c)
        if not m or m in salida:
            continue
        if any(b in m for b in BLOCK):
            continue
        if _es_asset(m) or not _tld_valido(m):
            continue
        salida.append(m)
    return salida


def _variantes(web: str):
    """Prueba https/http y con/sin www hasta que una responda."""
    w = (web or "").strip().rstrip("/")
    if not w:
        return []
    dom = re.sub(r"^https?://", "", w)
    outs = []
    for scheme in ("https://", "http://"):
        hosts = [dom]
        if not dom.startswith("www."):
            hosts.append("www." + dom)
        for host in hosts:
            u = scheme + host
            if u not in outs:
                outs.append(u)
    return outs


def buscar_email(web: str, paths, prioridad, timeout=15, pausa=0.25):
    """
    Entra al sitio y devuelve (email, estado).
    estado: 'ok' | 'sin web' | 'no responde' | 'no encontrado' | '<Error>'
    """
    bases = _variantes(web)
    if not bases:
        return "", "sin web"

    headers = {"User-Agent": UA}
    encontrados, err, base_ok = [], "", None

    # 1) encontrar una variante de dominio que responda, leer la home
    for base in bases:
        try:
            r = requests.get(base, headers=headers, timeout=timeout, allow_redirects=True)
            if r.status_code < 400:
                base_ok = r.url.rstrip("/")
                encontrados += _validos_en(r.text)
                break
        except requests.RequestException as e:
            err = type(e).__name__
            continue
    if not base_ok:
        return "", (err or "no responde")

    # 2) recorrer las páginas de contacto
    for path in [p for p in paths if p]:
        try:
            r = requests.get(urljoin(base_ok + "/", path), headers=headers,
                             timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                for e in _validos_en(r.text):
                    if e not in encontrados:
                        encontrados.append(e)
        except requests.RequestException:
            continue
        time.sleep(pausa)

    if not encontrados:
        return "", "no encontrado"

    return _elegir(encontrados, base_ok, prioridad), "ok"


def _elegir(mails, base_ok, prioridad):
    """Elige el mejor email: dominio propio > prefijo comercial > el primero."""
    raiz = _dominio_raiz(base_ok)

    # descartar mails de plataformas de ecommerce (no son del negocio)
    propios = [m for m in mails if not any(p in m for p in PLATAFORMA)]
    pool = propios or mails

    # preferir los del mismo dominio que el sitio
    del_dominio = [m for m in pool if raiz and raiz in m.split("@")[-1]]
    candidatos = del_dominio or pool

    # entre esos, preferir prefijo comercial (ventas@, compras@, info@, ...)
    for pref in prioridad:
        for m in candidatos:
            if m.split("@")[0].startswith(pref):
                return m
        for m in candidatos:
            if pref in m.split("@")[0]:
                return m
    return candidatos[0]
