# 🔑 Cómo generar la credencial de Google (una sola vez)

Esto es lo que le da permiso al sistema para **escribir solo** en tu Google
Sheet (Opción 2 — escritura automática). Se hace una vez por cuenta de Google
y sirve para todos tus ecommerces. No hace falta saber programar: es todo
clickear y copiar/pegar.

> ⏱️ Tiempo: ~10 minutos. Costo: $0 (todo dentro del plan gratis de Google).

---

## Paso 1 — Crear un proyecto en Google Cloud

1. Entrá a <https://console.cloud.google.com/>.
2. Arriba a la izquierda, en el selector de proyectos, **"Proyecto nuevo"**.
3. Nombre: `mineria-mayorista` (o el que quieras). Crear.

## Paso 2 — Activar las APIs necesarias

1. Buscador de arriba: escribí **"Google Sheets API"** → Entrar → **Habilitar**.
2. (Solo si vas a usar el Trabajo 2) Buscá **"Places API (New)"** → **Habilitar**.

## Paso 3 — Crear la cuenta de servicio

1. Menú ☰ → **API y servicios** → **Credenciales**.
2. **+ Crear credenciales** → **Cuenta de servicio**.
3. Nombre: `escritor-crm`. Crear y continuar. En roles podés dejar vacío → Listo.

## Paso 4 — Bajar la llave JSON

1. En la lista de **Cuentas de servicio**, clic sobre la que creaste.
2. Pestaña **Claves** → **Agregar clave** → **Crear clave nueva** → tipo **JSON** → Crear.
3. Se descarga un archivo `.json`. **Ese es tu credencial.**
4. Copiá el **email** de la cuenta de servicio (algo como
   `escritor-crm@mineria-mayorista.iam.gserviceaccount.com`). Lo necesitás en el paso 5.

## Paso 5 — Compartir el Sheet con la cuenta de servicio

1. Abrí tu Google Sheet (el CRM).
2. Botón **Compartir**.
3. Pegá el email de la cuenta de servicio del paso 4.
4. Dale permiso de **Editor** → Enviar.

> Sin este paso, la cuenta de servicio no ve tu Sheet. Es el más olvidado.

## Paso 6 — Guardar la credencial en el proyecto

Poné el archivo JSON en la carpeta `credenciales/` con el nombre del cliente:

```
credenciales/jumpbox.json
```

⚠️ **Ese archivo NUNCA se sube a GitHub** (ya está protegido en `.gitignore`).
Es como la llave de tu casa: se queda en tu compu.

---

## Listo — probar

```bash
# Prueba (no escribe nada, solo muestra):
python scripts/run.py enriquecer --config config/jumpbox.yaml --limite 10

# Aplicar de verdad al Sheet:
python scripts/run.py enriquecer --config config/jumpbox.yaml \
    --aplicar --credencial credenciales/jumpbox.json
```

Si algo falla, copiá el error y pedímelo: lo leo y lo arreglo.
