#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada único del sistema de minería.

Ejemplos:
  # Trabajo 1 — enriquecer emails (prueba, no escribe):
  python scripts/run.py enriquecer --config config/jumpbox.yaml

  # Trabajo 1 — aplicar de verdad al Sheet:
  python scripts/run.py enriquecer --config config/jumpbox.yaml --aplicar \
      --credencial credenciales/jumpbox.json

  # Trabajo 1 — sólo un lote de prueba de 15 leads:
  python scripts/run.py enriquecer --config config/jumpbox.yaml --limite 15

  # Trabajo 2 — scrapear leads nuevos (prueba):
  python scripts/run.py scrapear --config config/jumpbox.yaml \
      --rubro ortopedia --ciudad Cordoba --maps-key TU_API_KEY

  # Modo CSV (sin credenciales), plan B:
  python scripts/run.py enriquecer --config config/jumpbox.yaml \
      --csv-in crm.csv --csv-out crm_enriquecido.csv --aplicar
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src import enriquecer as t1
from src import scrapear_maps as t2


def _crm(cfg, args):
    """Abre el CRM: Google Sheet (con credencial) o CSV (plan B)."""
    if args.csv_in:
        from src.sheets import CRMCsv
        return CRMCsv(args.csv_in, cfg.columnas), "csv"
    from src.sheets import CRM
    if args.aplicar and not args.credencial:
        sys.exit("ERROR: para --aplicar en el Sheet necesitás --credencial <archivo.json>. "
                 "Ver docs/SETUP_CREDENCIAL.md (o usá --csv-in para modo CSV).")
    cred = args.credencial or _cred_por_defecto(args.config)
    return CRM.abrir(cfg, cred), "sheet"


def _cred_por_defecto(ruta_config):
    nombre = Path(ruta_config).stem
    return f"credenciales/{nombre}.json"


def cmd_enriquecer(args):
    cfg = Config.cargar(args.config)
    crm, modo = _crm(cfg, args)

    print(f">> TRABAJO 1 — Enriquecer emails | cliente: {cfg.cliente['nombre']} | modo: {modo}")
    print(f">> {'APLICAR (escribe)' if args.aplicar else 'PRUEBA (no escribe)'}\n")

    def prog(i, total, reg, email, estado):
        marca = email if email else f"(—) {estado}"
        print(f"  [{i:>3}/{total}] {str(reg.get('id')):5} {str(reg.get('empresa'))[:30]:30} -> {marca}", flush=True)

    r = t1.enriquecer(crm, cfg, aplicar=args.aplicar, limite=args.limite, on_progress=prog)

    if modo == "csv" and args.aplicar:
        crm.guardar(args.csv_out or args.csv_in)

    print("\n" + "=" * 60)
    print(f"  Leads procesados : {r['total_pendientes']}")
    print(f"  Mails encontrados: {r['mails_encontrados']}")
    print(f"  Para WhatsApp    : {r['para_whatsapp']}")
    print(f"  {'CAMBIOS APLICADOS al CRM.' if r['aplicado'] else 'PRUEBA: nada se escribió. Corré con --aplicar para guardar.'}")
    print("=" * 60)


def cmd_scrapear(args):
    cfg = Config.cargar(args.config)
    crm, modo = _crm(cfg, args)
    if not args.maps_key:
        sys.exit("ERROR: el Trabajo 2 necesita --maps-key (API key de Google Places).")

    rubros = [args.rubro] if args.rubro else None
    ciudades = [args.ciudad] if args.ciudad else None
    print(f">> TRABAJO 2 — Scrapear Maps | cliente: {cfg.cliente['nombre']} | modo: {modo}")
    print(f">> {'APLICAR (escribe)' if args.aplicar else 'PRUEBA (no escribe)'}\n")

    r = t2.scrapear(crm, cfg, args.maps_key, aplicar=args.aplicar,
                    rubros=rubros, ciudades=ciudades)
    for f in r["filas"][:50]:
        print(f"  {f['id']} {f['empresa'][:32]:32} {f['ciudad']:16} {f.get('telefono','')}")
    print("\n" + "=" * 60)
    print(f"  Nuevos únicos      : {r['encontrados_unicos']}")
    print(f"  Duplicados salteados: {r['duplicados_salteados']}")
    print(f"  Batch              : {r['batch']}")
    print(f"  {'FILAS AGREGADAS al CRM.' if r['aplicado'] else 'PRUEBA: nada se agregó. Corré con --aplicar para guardar.'}")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(description="Motor de minería mayorista parametrizable.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--config", required=True, help="Ruta al YAML del cliente.")
    comun.add_argument("--aplicar", action="store_true", help="Escribe de verdad (default: prueba).")
    comun.add_argument("--credencial", help="Ruta al JSON de la cuenta de servicio de Google.")
    comun.add_argument("--csv-in", help="Modo CSV: leer de este archivo en vez del Sheet.")
    comun.add_argument("--csv-out", help="Modo CSV: guardar el resultado en este archivo.")

    pe = sub.add_parser("enriquecer", parents=[comun], help="Trabajo 1: completar emails.")
    pe.add_argument("--limite", type=int, help="Procesar sólo N leads (prueba).")
    pe.set_defaults(func=cmd_enriquecer)

    ps = sub.add_parser("scrapear", parents=[comun], help="Trabajo 2: leads nuevos de Maps.")
    ps.add_argument("--rubro", help="Un rubro puntual (si no, usa los del YAML).")
    ps.add_argument("--ciudad", help="Una ciudad puntual (si no, usa las del YAML).")
    ps.add_argument("--maps-key", help="API key de Google Places.")
    ps.set_defaults(func=cmd_scrapear)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
