# Sitio web de Protego Consulting

Sitio estático (HTML + CSS + JS, sin dependencias de build) listo para publicarse en **GitHub Pages** con el dominio `protego-consulting.com`.

## Estructura

```
protego-site/
├── index.html          Inicio
├── servicios.html       ISO 27001 / DPOaaS / Continuidad / Riesgos
├── nosotros.html        Misión, visión, valores, perfil de César Viteri
├── contacto.html        Formulario + información de contacto
├── blog.html            Estado inicial del blog (posts "próximamente")
├── privacidad.html       Política de privacidad (plantilla LOPDP)
├── terminos.html         Términos y condiciones (plantilla)
├── cookies.html          Aviso de cookies (plantilla)
├── css/style.css        Sistema de diseño (colores, tipografía, componentes)
├── js/main.js            Menú móvil, carrusel de testimonios, contadores
├── assets/logos/         Logos oficiales (color, negativo, isotipo, favicon)
├── CNAME                 Dominio personalizado para GitHub Pages
├── robots.txt / sitemap.xml
```

## 1. Publicar en GitHub Pages

1. Crea un repositorio nuevo en GitHub (puede ser público o privado con GitHub Pro/Team).
2. Sube todo el contenido de esta carpeta a la raíz del repositorio (rama `main`).
3. En **Settings → Pages**, selecciona la rama `main` y la carpeta `/ (root)`.
4. En **Settings → Pages → Custom domain**, escribe `protego-consulting.com` (el archivo `CNAME` ya está incluido, así que GitHub debería detectarlo automáticamente).

## 2. Configurar el DNS en GoDaddy

Como el dominio está en GoDaddy, agrega estos registros en su panel de DNS:

| Tipo  | Nombre | Valor |
|-------|--------|-------|
| A     | @      | 185.199.108.153 |
| A     | @      | 185.199.109.153 |
| A     | @      | 185.199.110.153 |
| A     | @      | 185.199.111.153 |
| CNAME | www    | tu-usuario.github.io |

La propagación puede tardar entre unos minutos y 24 horas. Luego, en GitHub Pages activa **"Enforce HTTPS"** una vez el dominio verifique correctamente.

## 3. Conectar el formulario de contacto

El formulario en `contacto.html` viene con un ejemplo funcional apuntando a **Formspree**. Para usar **CognitoForms** en su lugar:

1. Crea tu formulario en [cognitoforms.com](https://www.cognitoforms.com).
2. Copia el script de embed que te entrega Cognito.
3. En `contacto.html`, reemplaza todo el contenido dentro de `<div id="cognito-embed">...</div>` por ese script.

Si prefieres seguir con Formspree: crea una cuenta gratuita en [formspree.io](https://formspree.io), copia tu endpoint (`https://formspree.io/f/xxxxxxx`) y reemplázalo en el atributo `action` del `<form>`.

## 4. Activar Google Analytics

En **cada archivo HTML**, dentro del `<head>`, descomenta (quita `<!--` y `-->`) el bloque de Google Analytics y reemplaza `G-XXXXXXXXXX` por tu ID de medición de GA4. (Ya está incluido, comentado, en `index.html` — puedes copiar el mismo bloque a las demás páginas).

## 5. Qué reemplazar antes de publicar

- [ ] **Testimonios** en `index.html` — son ejemplos ilustrativos, reemplázalos por testimonios reales de clientes (con su autorización).
- [ ] **Enlaces de redes sociales** (`#` en LinkedIn, Instagram, YouTube, TikTok) en el footer de cada página — coloca tus URLs reales.
- [ ] **ID de Google Analytics**.
- [ ] **Formulario de contacto** (CognitoForms o Formspree, ver punto 3).
- [ ] Revisar las páginas legales (`privacidad.html`, `terminos.html`, `cookies.html`) — son plantillas base y conviene que las revises con tu criterio profesional antes de publicarlas.
- [ ] Reemplazar el avatar con iniciales "CV" en `nosotros.html` e `index.html` por una fotografía real cuando la tengas lista.

## 6. Editar contenido

No hay CMS ni build step: cada página es un archivo `.html` independiente que puedes editar directamente (con Claude Code, con un editor de texto, o subiendo cambios directo en GitHub). Los estilos compartidos están en `css/style.css` y el comportamiento interactivo en `js/main.js`.
