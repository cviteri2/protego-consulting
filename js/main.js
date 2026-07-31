// PROTEGO CONSULTING — interacciones del sitio
document.addEventListener('DOMContentLoaded', function () {

  /* Menú móvil */
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? '✕' : '☰';
    });
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        links.classList.remove('open');
        toggle.textContent = '☰';
      });
    });
  }

  /* Resaltar enlace activo por página actual */
  var current = (window.location.pathname.split('/').pop() || 'index.html');
  document.querySelectorAll('.nav-links a').forEach(function (a) {
    var href = a.getAttribute('href');
    if (href === current || (current === '' && href === 'index.html')) {
      a.classList.add('active');
    }
  });

  /* Carrusel de testimonios */
  var slides = document.querySelectorAll('.tslide');
  var dotsWrap = document.querySelector('.tdots');
  if (slides.length) {
    var idx = 0;
    slides.forEach(function (s, i) {
      if (dotsWrap) {
        var b = document.createElement('button');
        b.setAttribute('aria-label', 'Ver testimonio ' + (i + 1));
        if (i === 0) b.classList.add('active');
        b.addEventListener('click', function () { show(i); });
        dotsWrap.appendChild(b);
      }
    });
    function show(i) {
      idx = i;
      slides.forEach(function (s, j) { s.classList.toggle('active', j === i); });
      if (dotsWrap) {
        dotsWrap.querySelectorAll('button').forEach(function (b, j) {
          b.classList.toggle('active', j === i);
        });
      }
    }
    show(0);
    setInterval(function () { show((idx + 1) % slides.length); }, 6000);
  }

  /* Contadores animados de estadísticas */
  var stats = document.querySelectorAll('[data-count]');
  if (stats.length && 'IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    stats.forEach(function (el) { obs.observe(el); });
  }
  function animateCount(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var suffix = el.getAttribute('data-suffix') || '';
    var duration = 1200, start = null;
    function step(ts) {
      if (!start) start = ts;
      var progress = Math.min((ts - start) / duration, 1);
      var value = Math.round(target * progress);
      el.textContent = value + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* Año dinámico en footer */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  /* Banner de consentimiento de cookies */
  var cookieBanner = document.querySelector('.cookie-banner');
  if (cookieBanner) {
    var consent = null;
    try { consent = localStorage.getItem('protego_cookie_consent'); } catch (e) {}
    if (!consent) {
      setTimeout(function () { cookieBanner.classList.add('visible'); }, 600);
    }
    function resolveCookieBanner(choice) {
      try {
        localStorage.setItem('protego_cookie_consent', choice);
        localStorage.setItem('protego_cookie_consent_date', new Date().toISOString());
      } catch (e) {}
      cookieBanner.classList.remove('visible');
    }
    var acceptBtn = cookieBanner.querySelector('[data-cookie-accept]');
    var rejectBtn = cookieBanner.querySelector('[data-cookie-reject]');
    if (acceptBtn) acceptBtn.addEventListener('click', function () { resolveCookieBanner('accepted'); });
    if (rejectBtn) rejectBtn.addEventListener('click', function () { resolveCookieBanner('essential_only'); });
  }
});
