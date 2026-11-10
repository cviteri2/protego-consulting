#!/usr/bin/env bash
# Comprueba que cada artículo de content/blog/ esté en línea en el sitio
# y aparezca en blog.html y feed.xml.
#
# Uso: scripts/verificar_publicacion.sh [espera_maxima_en_segundos]
# Sale con 0 si todo está publicado; con 1 si algo falta al vencer la espera.
set -uo pipefail

SITE="${SITE:-https://protego-consulting.com}"
MAX_WAIT="${1:-900}"
INTERVAL="${INTERVAL:-30}"
cd "$(dirname "$0")/.."

slugs=()
for f in content/blog/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md; do
  [ -e "$f" ] || continue
  name="$(basename "$f" .md)"
  slugs+=("${name:11}")
done
if [ ${#slugs[@]} -eq 0 ]; then
  echo "No hay artículos en content/blog/."
  exit 0
fi

# El parámetro ?v= evita la caché del CDN de GitHub Pages.
fetch() { curl -sS -L --max-time 20 "$SITE/$1?v=$(date +%s)" 2>/dev/null || true; }
status() { curl -sS -L -o /dev/null --max-time 20 -w '%{http_code}' "$SITE/$1?v=$(date +%s)" 2>/dev/null || echo 000; }

check() {
  missing=()
  local index feed
  index="$(fetch blog.html)"
  feed="$(fetch feed.xml)"
  for s in "${slugs[@]}"; do
    code="$(status "blog/$s.html")"
    [ "$code" = 200 ] || { missing+=("blog/$s.html (HTTP $code)"); continue; }
    grep -q "blog/$s.html" <<<"$index" || missing+=("blog/$s.html (no aparece en blog.html)")
    grep -q "/blog/$s.html" <<<"$feed" || missing+=("blog/$s.html (no aparece en feed.xml)")
  done
  [ ${#missing[@]} -eq 0 ]
}

deadline=$(( $(date +%s) + MAX_WAIT ))
while true; do
  if check; then
    echo "Publicado: ${#slugs[@]} artículo(s) en línea en $SITE."
    exit 0
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "::error::Sin publicar en $SITE tras ${MAX_WAIT}s:"
    printf '  - %s\n' "${missing[@]}"
    exit 1
  fi
  echo "Aún no publicado (${#missing[@]} pendiente(s)); reintento en ${INTERVAL}s..."
  sleep "$INTERVAL"
done
