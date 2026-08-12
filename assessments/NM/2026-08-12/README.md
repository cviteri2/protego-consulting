# Evaluación de seguridad — nuevomundo.edu.ec (código de cliente: NM)

**Fecha:** 2026-08-12
**Objetivo:** `https://nuevomundo.edu.ec/`
**Herramientas invocadas:** `scripts/scan.sh` (nmap, httpx, testssl.sh, nuclei, gobuster, OWASP ZAP baseline)
**Resultados crudos:** `assessments/NM/2026-08-12/raw/`

## ⚠️ Resumen ejecutivo — resultados no concluyentes

Este análisis se ejecutó dentro de un entorno Claude Code Remote (contenedor
gestionado por Anthropic), no desde un workstation de pentest dedicado. El
entorno tiene una política de salida de red restrictiva que **impidió
completar la mayoría del escaneo** y pone en duda la fiabilidad de lo poco
que sí se obtuvo. En consecuencia:

- **No se reportan hallazgos Critical ni High en este documento.** No hay
  suficiente evidencia confiable para sustentarlos.
- Este análisis debe **repetirse desde un entorno de pentest sin estas
  restricciones** (workstation del equipo o un entorno CCR con política de
  red habilitada para el dominio objetivo) antes de considerarlo válido
  para un informe final de cliente.

## Qué se pudo ejecutar y qué no

| Herramienta | Estado | Detalle |
|---|---|---|
| **nmap** | ⚠️ Ejecutó, pero resultado sospechoso | Ver nota abajo — la respuesta L7 no parece provenir del backend real. |
| **httpx** | ❌ Bloqueado | El proxy de salida del entorno rechazó la conexión HTTPS a `nuevomundo.edu.ec` con un 403 de política ("policy denial"), confirmado en el log del proxy (`/root/.ccr/__agentproxy/status`). Salida vacía. |
| **nuclei** | ❌ No ejecutó | Sin templates instalados en el entorno (`no templates provided for scan`); adicionalmente habría estado sujeto al mismo bloqueo de proxy que httpx. |
| **gobuster** | ❌ No ejecutó | Sin wordlist disponible en el entorno; adicionalmente habría estado sujeto al mismo bloqueo de proxy. |
| **testssl.sh** | ❌ No ejecutó | Falta la dependencia `hexdump` en el entorno (`Fatal error: You need to install hexdump for this program to work`). No se obtuvo ningún dato TLS. |
| **OWASP ZAP** | ❌ No disponible | No hay daemon Docker corriendo en este entorno para levantar `zap-baseline.py`. |

## Hallazgos por severidad

### Critical
Ninguno reportado — sin evidencia confiable (ver limitaciones arriba).

### High
Ninguno reportado — sin evidencia confiable (ver limitaciones arriba).

### Medium
Ninguno reportado — sin evidencia confiable (ver limitaciones arriba).

### Low / Informational
- **Resolución DNS del host** (sin verificación independiente):
  `nuevomundo.edu.ec` → `66.231.64.204`, rDNS `napo.ecuahosting.net`
  (indicaría hosting compartido en Ecuahosting). *Informativo únicamente —
  no verificado desde una fuente de red confiable.*
- **Nota de integridad sobre el propio nmap:** aunque `nmap -sV` completó y
  reportó puertos 80/tcp y 443/tcp como abiertos, la huella de servicio
  (`raw/nmap.txt`) muestra respuestas HTTP idénticas y genéricas
  (`426 Upgrade Required` / `400 Bad Request`, `content-type: text/plain`)
  para sondas completamente distintas (GetRequest, HTTPOptions, RTSP,
  Kerberos, etc.) en ambos puertos. Ese patrón — la misma respuesta
  "de catálogo" sin importar el tipo de sonda — es típico de un
  **dispositivo intermedio (gateway/proxy transparente) respondiendo en
  lugar del servidor de origen real**, no de un stack de hosting típico
  (Apache/Nginx/cPanel). Por lo tanto, **estos datos de nmap tampoco deben
  tratarse como confiables** sin re-validación desde una red sin
  interceptación.

### TLS/SSL

**No hay hallazgos TLS/SSL en este documento** — `testssl.sh` no llegó a
ejecutarse por la dependencia faltante mencionada arriba.

Se deja constancia, además, para cualquier dato TLS que se obtenga en
**futuras corridas dentro de este mismo tipo de entorno**:

> Este entorno (contenedor de Claude Code / Anthropic) intercepta el
> tráfico HTTPS de forma transparente mediante un proxy corporativo que
> re-termina la conexión TLS (ver `/root/.ccr/README.md`). Cualquier
> hallazgo sobre **cadena de certificados, emisor (issuer), fechas de
> expiración, o estado OCSP/CRL** obtenido desde este entorno **refleja
> potencialmente el certificado del proxy de Anthropic, no el del servidor
> real de `nuevomundo.edu.ec`**. Estos datos **no deben clasificarse como
> Critical ni High** sin antes validarlos de forma independiente desde una
> red sin interceptación TLS (p. ej. `openssl s_client` o `testssl.sh`
> desde un workstation de pentest fuera de este entorno).

## Recomendaciones

1. **Repetir el escaneo completo** (`scripts/scan.sh https://nuevomundo.edu.ec/ NM`)
   desde un entorno con salida de red autorizada hacia el dominio objetivo
   — un workstation del equipo de Protego o un entorno CCR configurado con
   una política de red que permita este destino.
2. Antes de esa corrida, resolver las dependencias locales detectadas:
   instalar `hexdump` (para testssl.sh), descargar templates de nuclei
   (`nuclei -update-templates`), agregar una wordlist para gobuster
   (p. ej. `seclists`/`dirb`), y disponer de un daemon Docker para el
   baseline scan de ZAP.
3. Una vez con datos confiables, re-emitir este README reemplazando cada
   sección "Ninguno reportado" con los hallazgos reales y su severidad.

## Anexos — archivos crudos

Ver `assessments/NM/2026-08-12/raw/`:
`nmap.txt`, `nmap.log`, `httpx.json`, `httpx.log`, `testssl.stdout.log`,
`nuclei.log`, `gobuster.log`, `zap-report.log`.
