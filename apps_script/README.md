# 📝 Enriquecer emails desde adentro del Sheet (sin instalar nada)

Esta es la forma **más simple** de llenar la columna EMAIL de tu CRM cuando tu
organización bloquea las cuentas de servicio. El script corre **dentro de tu
Google Sheet**, como si lo ejecutaras vos. No usa cuenta de servicio, no toca
ninguna política, y no hay que instalar Python ni nada en tu compu.

> ⏱️ Configurarlo: 3 minutos. Después es un clic.

---

## Pasos (una sola vez)

1. Abrí tu Google Sheet (el CRM).
2. Menú **Extensiones** → **Apps Script**. Se abre un editor en otra pestaña.
3. Borrá lo que haya en el editor y **pegá TODO el contenido** de
   [`enriquecer.gs`](enriquecer.gs).
4. Clic en el ícono de **guardar** (💾).
5. Volvé a la pestaña de tu Sheet y **recargá la página** (F5).
6. Aparece un menú nuevo arriba: **JumpBox**.

## Usarlo

1. Menú **JumpBox** → **Enriquecer emails (lote)**.
2. La **primera vez** Google te pide autorizar el script:
   - Clic en **Revisar permisos** → elegí tu cuenta.
   - Si dice *"Google no verificó esta app"*: **Configuración avanzada** →
     **Ir a (nombre del proyecto) (no seguro)** → **Permitir**.
     (Es tu propio script, sobre tu propia planilla: es seguro.)
3. Corre sobre un lote de ~40 negocios (por el límite de tiempo de Google) y te
   avisa cuántos mails encontró y cuántos quedan.
4. **Volvé a hacer clic** en *Enriquecer emails (lote)* hasta que diga
   "¡Terminaste todo el CRM!". Cada corrida saltea lo ya hecho.

---

## Qué hace exactamente (y qué NO)

- ✅ Sólo completa **EMAIL** (mail encontrado) o **NOTAS** ("sin mail — ir por
  WhatsApp") en las filas con WEB y sin mail.
- ✅ Filtra basura: archivos de fuentes (`.woff`), imágenes, placeholders
  (`ejemplo@mail.com`), TLDs falsos (`.loc`) y mails de plataformas (Tiendanube).
- ✅ Prioriza el mail del dominio propio y los prefijos comerciales
  (ventas@, compras@, info@…).
- 🚫 **Nunca** borra ni modifica otras columnas. Es re-ejecutable sin miedo.

## Ajustes

Si tu Sheet usa otros nombres de columna, cambialos arriba del script
(`COL_WEB`, `COL_EMAIL`, `COL_NOTAS`). `LOTE = 40` controla cuántos procesa por
corrida; podés bajarlo si algún lote se corta por tiempo.
