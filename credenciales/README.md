# Carpeta de credenciales

Acá va el archivo JSON de la cuenta de servicio de Google, **uno por cliente**:

```
credenciales/
├── jumpbox.json          ← credencial de JumpBox (NO se sube a GitHub)
└── otrocliente.json      ← credencial de otro ecommerce
```

🔒 **Estos archivos nunca se suben al repositorio** — están bloqueados en
`.gitignore`. Son secretos, como una contraseña. Cada persona/máquina que corra
el sistema tiene su copia local.

Para generarlos, seguí la guía en [`../docs/SETUP_CREDENCIAL.md`](../docs/SETUP_CREDENCIAL.md).
