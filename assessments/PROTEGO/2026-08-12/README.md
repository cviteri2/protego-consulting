# Assessment PROTEGO — 2026-08-12

## Estado: escaneo NO ejecutado (bloqueado por política de red del entorno)

Se solicitó ejecutar `scripts/scan.sh` contra `https://protego-consulting.com` y resumir
los hallazgos de nmap, httpx, testssl, nuclei, gobuster y ZAP. No fue posible completar
esta tarea desde esta sesión por dos motivos:

1. **`scripts/scan.sh` no existe en este repositorio.** El repo contiene únicamente el
   sitio estático de protego-consulting.com (HTML/CSS/JS para GitHub Pages); no hay
   directorio `scripts/` ni historial de que ese archivo haya existido en ningún commit
   o rama.

2. **La política de egress de esta sesión bloquea el dominio de forma explícita.**
   Cualquier intento de conexión saliente hacia `protego-consulting.com` (probado con
   `httpx`, `curl` y verificado contra el estado del proxy en
   `$HTTPS_PROXY/__agentproxy/status`) devuelve `403` con motivo
   `connect_rejected — policy denial`. La documentación del proxy del entorno
   (`/root/.ccr/README.md`) indica expresamente: *"Do not retry or route around it —
   report the blocked host."* Por lo tanto no se reintentó ni se buscó una vía
   alternativa (IP directa, otro puerto, otra herramienta, etc.).

Herramientas disponibles en el entorno al momento del intento: `nmap`, `httpx`, `nuclei`,
`gobuster`, `openssl`, `curl`. **No disponibles:** `testssl.sh`, OWASP ZAP.

## Nota sobre alcance e infraestructura

`protego-consulting.com` resuelve a IPs compartidas de GitHub Pages
(185.199.108–111.153) y no a infraestructura dedicada del cliente. Cualquier escaneo
activo futuro (nmap de puertos, gobuster de fuerza bruta, nuclei/ZAP activos) debe
considerar que esas IPs son infraestructura compartida de GitHub, no exclusiva de
Protego Consulting, lo cual limita legítimamente el alcance de un pentest de "caja
negra" tradicional a nivel de red/puertos.

## Próximos pasos propuestos

- Ejecutar el escaneo desde un entorno sin esta restricción de egress (máquina local,
  runner dedicado) y aportar los archivos de salida (nmap/httpx/testssl/nuclei/gobuster/zap)
  para que se resuman aquí por severidad.
- Alternativamente, solicitar a un administrador que autorice `protego-consulting.com`
  en la política de egress de esta sesión si este flujo va a repetirse.
- Cuando existan resultados de TLS/SSL reales, recordar la salvedad pactada: si el
  escaneo se ejecuta detrás de un proxy corporativo que intercepta TLS de forma
  transparente, los hallazgos sobre cadena de certificados, emisor, expiración y
  OCSP/CRL no son fiables y no deben marcarse como Critical/High sin validación externa
  (ej. desde una red sin interceptación TLS).
