# 🔐 Opción A — Login con tu propio usuario (OAuth)

Este método hace que el sistema entre a Google **como vos** (tu usuario, que ya
es dueño del Sheet). **No usa cuenta de servicio**, así que **no lo frena la
política de la organización** que te bloqueó las llaves JSON. Te logueás una
sola vez desde tu Mac y queda guardado.

> ⏱️ ~8 minutos, una sola vez. Costo: $0.

---

## Paso 1 — Activar la API de Sheets (si no lo hiciste)

1. <https://console.cloud.google.com/> → proyecto `mineria-mayorista`.
2. Buscador de arriba: **"Google Sheets API"** → **Habilitar**.

## Paso 2 — Configurar la pantalla de consentimiento

1. Menú ☰ → **API y servicios** → **Pantalla de consentimiento de OAuth**.
2. Tipo de usuario: **Interno** (si tu cuenta es de Google Workspace) → Crear.
   - *Interno* = solo tu organización, sin proceso de verificación de Google.
3. Completá nombre de la app (ej. `Mineria CRM`) y tu email de soporte → Guardar
   y continuar hasta el final.

## Paso 3 — Crear el ID de cliente OAuth (tipo Escritorio)

1. Menú ☰ → **API y servicios** → **Credenciales**.
2. **+ Crear credenciales** → **ID de cliente de OAuth**.
3. Tipo de aplicación: **App de escritorio** (Desktop app).
4. Nombre: `mineria-desktop` → **Crear**.
5. Se abre un cartel con **Descargar JSON**. Bajalo.

## Paso 4 — Guardar el cliente en el proyecto

Poné ese JSON en la carpeta `credenciales/` con este nombre exacto:

```
credenciales/jumpbox_oauth.json
```

⚠️ Igual que antes, **este archivo nunca se sube a GitHub** (está en `.gitignore`).

---

## Paso 5 — Correr (la primera vez abre el navegador)

```bash
# Instalar dependencias (una vez)
pip install -r requirements.txt

# Prueba: lee el Sheet en vivo y muestra qué haría (no escribe)
python scripts/run.py enriquecer --config config/jumpbox.yaml --oauth --limite 10
```

La **primera vez** se abre el navegador y te pide iniciar sesión con tu cuenta y
autorizar. Aceptás una vez y el sistema guarda un `credenciales/jumpbox_token.json`.
De ahí en más ya no vuelve a pedir login.

```bash
# Aplicar de verdad al Sheet (escribe los mails encontrados)
python scripts/run.py enriquecer --config config/jumpbox.yaml --oauth --aplicar
```

> Si al autorizar aparece "Google no verificó esta app": es normal (tu app es
> interna/de prueba). Clic en **Configuración avanzada → Ir a Mineria CRM
> (no seguro)** → Permitir. Es tu propia app, es seguro.

---

## ¿Y si el navegador no se abre (por ejemplo, en un servidor sin pantalla)?

Este flujo necesita un navegador la primera vez, así que corré ese primer login
en tu **Mac**. Una vez generado `credenciales/jumpbox_token.json`, ese token se
puede reusar en cualquier lado sin volver a loguear.
