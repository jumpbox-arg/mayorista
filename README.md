# Motor de Minería Mayorista — sistema parametrizable

Sistema para **llenar y expandir un CRM de leads B2B** (Google Sheet) de forma
automática, replicable en cualquier ecommerce cambiando **un solo archivo de
configuración**. Nació para JumpBox (plantillas de fibra de carbono) y sirve
para cualquier marca que haga outreach mayorista.

Hace dos trabajos:

| Trabajo | Qué hace | Necesita |
|---------|----------|----------|
| **1 · Enriquecer emails** | Recorre los leads con web pero sin mail, entra al sitio y completa la columna EMAIL | Credencial de Google |
| **2 · Scrapear leads nuevos** | Busca negocios en Google Maps por `rubro × ciudad`, deduplica y agrega filas | Credencial + API Key de Places |

---

## 🧩 Cómo funciona (en una imagen)

```
config/<cliente>.yaml   →   define TODO (sheet, columnas, rubros, ciudades)
        │
        ▼
scripts/run.py          →   un solo comando para los dos trabajos
        │
        ├── src/email_finder.py   motor robusto de búsqueda de emails
        ├── src/sheets.py         lee/escribe el Google Sheet (seguro)
        ├── src/enriquecer.py     Trabajo 1
        └── src/scrapear_maps.py  Trabajo 2
```

El **código no se toca nunca**. Todo el comportamiento vive en el YAML del cliente.

---

## 🚀 Puesta en marcha

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Generar la credencial de Google (una sola vez)
#    → seguí docs/SETUP_CREDENCIAL.md

# 3. Prueba (NO escribe nada, solo muestra qué haría)
python scripts/run.py enriquecer --config config/jumpbox.yaml --limite 10

# 4. Aplicar de verdad al Sheet
python scripts/run.py enriquecer --config config/jumpbox.yaml \
    --aplicar --credencial credenciales/jumpbox.json
```

---

## ♻️ Replicar en otro ecommerce

1. Copiá la plantilla:
   ```bash
   cp config/_plantilla.yaml config/miclientenuevo.yaml
   ```
2. Editá `config/miclientenuevo.yaml` (ID del Sheet, columnas, rubros, ciudades).
3. Generá su credencial → `credenciales/miclientenuevo.json`.
4. Corré:
   ```bash
   python scripts/run.py enriquecer --config config/miclientenuevo.yaml --aplicar \
       --credencial credenciales/miclientenuevo.json
   ```

Listo. Mismo motor, cliente distinto.

---

## 🛟 Modo seguro (siempre activo)

- **Por defecto no escribe**: mostrás la vista previa y recién con `--aplicar` toca el CRM.
- **Nunca borra** filas ni columnas.
- Trabajo 1 sólo completa **EMAIL** y **NOTAS**. Trabajo 2 sólo **agrega filas al final**.
- **Dedupe** obligatorio en el Trabajo 2 (por nombre normalizado + teléfono).
- Los leads sin mail no se pierden: se marcan para **WhatsApp** (tienen teléfono).

## 🔌 Plan B — modo CSV (sin credenciales)

```bash
python scripts/run.py enriquecer --config config/jumpbox.yaml \
    --csv-in crm.csv --csv-out crm_enriquecido.csv --aplicar
```

## 🔒 Seguridad

Las credenciales (`credenciales/*.json`) **nunca** se suben a GitHub — están
bloqueadas en `.gitignore`. Son secretas.
