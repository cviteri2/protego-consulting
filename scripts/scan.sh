#!/usr/bin/env bash
#
# scan.sh — Recon/vuln scan orchestrator for authorized security assessments.
#
# Usage: scripts/scan.sh <URL> <CLIENT_CODE>
# Example: scripts/scan.sh https://nuevomundo.edu.ec/ NM
#
# Runs nmap, httpx, testssl.sh, nuclei, gobuster and (if available) OWASP ZAP
# baseline against the target, saving raw output under:
#   assessments/<CLIENT_CODE>/<YYYY-MM-DD>/raw/
#
# Each tool is best-effort: a failure or blocked connection in one tool does
# not stop the others. Check raw/*.log for stderr from any tool that failed.

set -uo pipefail

if [[ $# -ne 2 ]]; then
  echo "Uso: $0 <URL> <CODIGO_CLIENTE>" >&2
  exit 1
fi

TARGET_URL="$1"
CLIENT_CODE="$2"
HOST="$(echo "$TARGET_URL" | sed -E 's#^[a-zA-Z]+://##; s#/.*$##; s#:.*$##')"

DATE="$(date +%Y-%m-%d)"
OUT_DIR="assessments/${CLIENT_CODE}/${DATE}/raw"
mkdir -p "$OUT_DIR"

echo "== scan.sh =="
echo "Target : $TARGET_URL"
echo "Host   : $HOST"
echo "Cliente: $CLIENT_CODE"
echo "Salida : $OUT_DIR"
echo

run_step() {
  local name="$1"; shift
  echo "--> $name"
  if ! "$@"; then
    echo "    [!] $name terminó con error (ver ${name}.log)"
  fi
}

# --- nmap: port/service scan ---------------------------------------------
nmap_scan() {
  nmap -Pn -sV -T4 --top-ports 1000 \
    -oN "$OUT_DIR/nmap.txt" \
    "$HOST" > "$OUT_DIR/nmap.log" 2>&1
}

# --- httpx: HTTP probing ---------------------------------------------------
httpx_scan() {
  echo "$TARGET_URL" | httpx -silent -sc -title -tech-detect -location \
    -json -o "$OUT_DIR/httpx.json" > "$OUT_DIR/httpx.log" 2>&1
}

# --- testssl.sh: TLS/SSL configuration ------------------------------------
testssl_scan() {
  local bin="testssl.sh"
  command -v testssl.sh >/dev/null 2>&1 || bin="/opt/testssl.sh/testssl.sh"
  "$bin" --quiet --color 0 \
    --logfile "$OUT_DIR/testssl.log" \
    -oN "$OUT_DIR/testssl.txt" \
    "$TARGET_URL" > "$OUT_DIR/testssl.stdout.log" 2>&1
}

# --- nuclei: vulnerability templates ---------------------------------------
nuclei_scan() {
  echo "$TARGET_URL" | nuclei -silent -severity low,medium,high,critical \
    -o "$OUT_DIR/nuclei.txt" > "$OUT_DIR/nuclei.log" 2>&1
}

# --- gobuster: directory/file enumeration ----------------------------------
gobuster_scan() {
  local wordlist="/usr/share/wordlists/dirb/common.txt"
  [[ -f "$wordlist" ]] || wordlist="/usr/share/seclists/Discovery/Web-Content/common.txt"
  if [[ ! -f "$wordlist" ]]; then
    echo "    [!] No se encontró wordlist para gobuster" | tee "$OUT_DIR/gobuster.log"
    return 1
  fi
  gobuster dir -u "$TARGET_URL" -w "$wordlist" -q -o "$OUT_DIR/gobuster.txt" \
    > "$OUT_DIR/gobuster.log" 2>&1
}

# --- OWASP ZAP baseline scan (best-effort, requires docker) ---------------
zap_scan() {
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "    [!] Docker no disponible: se omite ZAP baseline scan" | tee "$OUT_DIR/zap-report.log"
    return 1
  fi
  docker run --rm -v "$(pwd)/$OUT_DIR:/zap/wrk/:rw" \
    ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
    -t "$TARGET_URL" -J zap-report.json -r zap-report.html \
    > "$OUT_DIR/zap-report.log" 2>&1
}

run_step nmap     nmap_scan
run_step httpx    httpx_scan
run_step testssl  testssl_scan
run_step nuclei   nuclei_scan
run_step gobuster gobuster_scan
run_step zap      zap_scan

echo
echo "Listo. Resultados crudos en: $OUT_DIR"
