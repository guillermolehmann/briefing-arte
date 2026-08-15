#!/usr/bin/env python3
"""
Arma las guías de estudio en HTML del curso "Vender arte en Nueva York",
pensadas para leer en el teléfono, con la identidad Marco.

  curso/apunte/AAAA-MM-DD.md     -> docs/curso/guia/AAAA-MM-DD.html
  curso/apunte/AAAA-MM-DD-en.md  -> docs/curso/guia/AAAA-MM-DD-en.html
  curso/examen-semana-NN.json    -> docs/curso/guia/examen-semana-NN.html + practica.html
  las 7 entregas de una semana   -> docs/curso/guia/semana-NN.html   (el booklet)
  todas                          -> docs/curso/guia/index.html

Cada página es autocontenida: sin fuentes remotas, sin scripts de afuera y sin
guardar nada del lado de quien lee. Al imprimir, la misma página se convierte
en un documento carta.

La identidad Marco sale del marco recortado del arte concreto argentino. Un
solo gesto estructural, la esquina cortada de la cabecera, y un solo acento de
color. Papel claro siempre, sin modo oscuro. No agregar más colores ni repetir
la esquina cortada en otros lugares.

Uso: python3 construir_guias.py    (desde la raíz del repo)
Requisitos: pip install markdown
"""
import os, re, glob, json, datetime, html as _html

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = f"{BASE}/curso/apunte"
DST = f"{BASE}/docs/curso/guia"
BASE_URL = "https://guillermolehmann.github.io/briefing-arte"
PPM_LECTURA = 200

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
ORDINAL = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete"]

CSS = """
:root{
  --papel:#EDEAE1; --tinta:#16150F; --laca:#9C3A2A; --tenue:#6E615F;
  --filete:#C6C0B2; --control:#887E79; --caja:#E4E0D5;
  /* --tenue pasó de #8A857A a #6E615F y nació --control, porque la auditoría de
     contraste del 15/8/2026 encontró que el gris viejo daba 3,05 sobre papel
     contra los 4,5 que exige WCAG, y que los filetes de los controles daban
     1,51 contra 3,0. --filete queda solo para líneas decorativas. */
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--papel);color:var(--tinta);
  font-family:ui-sans-serif,-apple-system,"SF Pro Text","Helvetica Neue",Arial,sans-serif;
  font-size:18px;line-height:1.66;text-rendering:optimizeLegibility}
#barra{position:fixed;top:0;left:0;height:2px;width:0;background:var(--laca);z-index:99;transition:width .1s linear}

header.panel{background:var(--tinta);color:var(--papel);padding:34px 28px 74px;
  clip-path:polygon(0 0,100% 0,100% 100%,62px 100%,0 calc(100% - 62px))}
header.panel .sello{font-family:ui-serif,"New York","Iowan Old Style",Georgia,serif;
  font-size:34px;letter-spacing:.06em;line-height:1;font-weight:400}
header.panel .nom{font-size:9.5px;letter-spacing:.26em;text-transform:uppercase;
  color:#A8A296;margin:15px 0 0;line-height:2}
header.panel .nom span{display:block;white-space:nowrap}

main{padding:34px 28px 0;max-width:37em;margin:0 auto}
.rot{font-size:9.5px;letter-spacing:.3em;text-transform:uppercase;color:var(--laca);margin:0 0 15px}
h1{font-family:ui-serif,"New York","Iowan Old Style",Georgia,serif;font-size:30px;line-height:1.16;
  margin:0 0 20px;font-weight:400;letter-spacing:-.018em}
.meta{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--tenue);
  border-top:.5px solid var(--filete);padding-top:13px;margin:0 0 26px}

p,li{font-family:ui-serif,"New York","Iowan Old Style",Georgia,serif;font-size:18px;line-height:1.66}
p{margin:0 0 15px}
ul{margin:0 0 15px;padding-left:1.15em}
li{margin-bottom:10px}
h2{font-size:10px;letter-spacing:.28em;text-transform:uppercase;color:var(--tenue);font-weight:600;
  margin:38px 0 14px;padding-top:20px;border-top:.5px solid var(--filete)}
h3{font-family:ui-serif,"New York",Georgia,serif;font-size:21px;font-weight:400;margin:26px 0 6px}
a{color:inherit;text-decoration:none;border-bottom:.5px solid var(--laca);
  -webkit-tap-highlight-color:rgba(156,58,42,.12)}

.escucha{margin:0 0 28px;padding:16px 17px 14px;border:.5px solid var(--filete);background:var(--caja)}
.escucha .r{font-size:9.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--tenue);margin:0 0 11px}
.escucha audio{width:100%;height:36px;color-scheme:light}
.idioma{display:inline-block;margin-top:12px;font-size:12px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--tinta);border:1px solid var(--control);padding:10px 15px;line-height:1}

details.toc{margin:0 0 30px;border-top:.5px solid var(--filete);border-bottom:.5px solid var(--filete)}
details.toc summary{cursor:pointer;padding:14px 2px;font-size:9.5px;letter-spacing:.28em;
  text-transform:uppercase;color:var(--tenue);list-style:none}
details.toc summary::-webkit-details-marker{display:none}
details.toc summary::after{content:"+";float:right;color:var(--laca);font-size:13px;letter-spacing:0}
details.toc[open] summary::after{content:"\\2013"}
details.toc ol{margin:0;padding:0 0 16px 1.4em}
details.toc li{font-family:ui-serif,"New York",Georgia,serif;font-size:17px;margin:10px 0}
details.toc a{border:none}

button.ref{font-family:ui-serif,"New York",Georgia,serif;font-size:12px;color:var(--laca);
  background:none;border:none;padding:5px 4px;margin:-5px -1px;vertical-align:5px;
  cursor:pointer;line-height:1;font-variant-numeric:tabular-nums}
button.ref[aria-expanded="true"]{background:var(--caja)}
.nota{display:none;margin:2px 0 20px;padding:14px 0 14px 16px;border-left:1.5px solid var(--laca);
  font-family:ui-serif,"New York",Georgia,serif;font-size:16px;line-height:1.55;color:var(--tenue)}
.nota.abierta{display:block}
.nota a{border-bottom-color:var(--tenue)}
.nota .fuente{display:block;margin-top:9px;font-family:ui-sans-serif,-apple-system,Arial,sans-serif;
  font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--laca)}

.refs{margin-top:42px}
.refs ol{padding-left:1.3em}
.refs li{font-size:16px;color:var(--tenue);margin-bottom:14px}
.refs a{border-bottom-color:var(--filete)}

/* ── examen ── */
.bajada{font-family:ui-serif,"New York",Georgia,serif;font-size:17px;color:var(--tenue);margin:0 0 30px}
.preg{margin:0 0 30px;padding:0 0 4px}
.preg .n{font-size:9.5px;letter-spacing:.26em;text-transform:uppercase;color:var(--laca);margin:0 0 8px}
.preg .q{font-family:ui-serif,"New York",Georgia,serif;font-size:19px;line-height:1.42;margin:0 0 14px}
.preg label{display:block;font-family:ui-serif,"New York",Georgia,serif;font-size:17px;line-height:1.42;
  padding:12px 14px;margin:0 0 8px;border:1px solid var(--control);cursor:pointer}
.preg label:active{background:var(--caja)}
.preg input{margin-right:10px}
.preg label.bien{border-color:#2E6B4F;border-width:1.5px;background:#E6EFE7}
.preg label.mal{border-color:var(--laca);border-width:1.5px;background:#F2E5E2}
.preg .porque{display:none;margin-top:10px;padding:13px 0 0 16px;border-left:1.5px solid var(--laca);
  font-family:ui-serif,"New York",Georgia,serif;font-size:16px;line-height:1.5;color:var(--tenue)}
.preg .porque.ver{display:block}
.preg .porque a{border-bottom-color:var(--filete)}
textarea{width:100%;min-height:120px;padding:13px;border:1px solid var(--control);background:var(--caja);
  font-family:ui-serif,"New York",Georgia,serif;font-size:17px;line-height:1.5;color:var(--tinta);
  -webkit-appearance:none;border-radius:0}
.boton{display:block;width:100%;margin:8px 0 0;padding:16px;border:none;background:var(--tinta);
  color:var(--papel);font-size:12px;letter-spacing:.22em;text-transform:uppercase;cursor:pointer}
.boton.suave{background:none;color:var(--tinta);border:1px solid var(--control);margin-top:10px}
#puntaje{display:none;margin:0 0 30px;padding:20px;background:var(--tinta);color:var(--papel);text-align:center}
#puntaje.ver{display:block}
#puntaje b{display:block;font-family:ui-serif,"New York",Georgia,serif;font-size:44px;line-height:1;
  font-variant-numeric:tabular-nums}
#puntaje span{display:block;margin-top:10px;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#A8A296}

/* ── portada de la app ── */
.hoy{display:block;border:none;margin:0 0 34px;padding:22px 20px 24px;background:var(--tinta);color:var(--papel)}
.hoy .r{font-size:9.5px;letter-spacing:.3em;text-transform:uppercase;color:#C99A86;margin:0 0 12px}
.hoy .t{font-family:ui-serif,"New York",Georgia,serif;font-size:25px;line-height:1.2;display:block}
.hoy .d{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#A8A296;margin-top:14px;display:block}
.vacio{margin:0 0 34px;padding:20px;border:.5px dashed var(--filete);color:var(--tenue);font-size:15px}
.sello-ver{margin-top:34px;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--tenue)}
.sello-ver button{font:inherit;color:var(--laca);background:none;border:none;padding:0;text-decoration:underline;cursor:pointer}

/* ── índice general y portada de semana ── */
.lista{list-style:none;margin:0;padding:0}
.lista li{border-bottom:.5px solid var(--filete);margin:0}
.lista a{display:block;padding:17px 2px;border:none}
.lista .cod{display:block;font-family:ui-sans-serif,-apple-system,Arial,sans-serif;font-size:9.5px;
  letter-spacing:.26em;text-transform:uppercase;color:var(--laca);margin-bottom:5px}
.lista .tit{font-family:ui-serif,"New York",Georgia,serif;font-size:19px;line-height:1.32}
.cap{margin:0 0 30px;padding:0 0 4px}

/* ── capítulos del booklet ── */
.cap-sem{margin-top:52px;padding-top:30px;border-top:1.5px solid var(--tinta)}
.cap-sem:first-of-type{margin-top:8px;border-top:none;padding-top:0}
.cap-sem h1{font-size:26px}

footer{margin-top:46px;padding:22px 28px 52px;border-top:.5px solid var(--filete);
  color:var(--tenue);font-size:11px;letter-spacing:.14em;text-transform:uppercase;text-align:center}
footer a{border:none;color:var(--laca)}
footer .pie{display:block;margin-top:10px;letter-spacing:.04em;text-transform:none;font-size:13px}

@media (min-width:720px){
  body{font-size:19px}
  header.panel{max-width:37em;margin:0 auto;padding:44px 34px 78px}
  main,footer{padding-left:0;padding-right:0;max-width:37em;margin-left:auto;margin-right:auto}
  h1{font-size:35px}
}
@media print{
  :root{--papel:#fff;--tinta:#000;--laca:#7A2C20;--tenue:#555;--filete:#bbb;--caja:#fff}
  #barra,.escucha,details.toc{display:none}
  .nota{display:block}
  a{border-bottom:none}
  .cap-sem{break-before:page;page-break-before:always}
  .cap-sem:first-of-type{break-before:auto;page-break-before:auto}
  h2,h3{break-after:avoid} p{orphans:3;widows:3}
  @page{size:letter;margin:2cm 2.2cm}
}
"""

JS = """
document.addEventListener('click',function(e){
  var b=e.target.closest('button.ref'); if(!b) return;
  var n=document.getElementById(b.dataset.nota); if(!n) return;
  var ab=n.classList.toggle('abierta');
  b.setAttribute('aria-expanded',ab?'true':'false');
});
var barra=document.getElementById('barra');
if(barra){addEventListener('scroll',function(){
  var h=document.documentElement, alto=h.scrollHeight-h.clientHeight;
  barra.style.width=(alto>0?(h.scrollTop/alto*100):0)+'%';
},{passive:true});}
"""


SW = """/* Service worker de las guías de estudio.
   Estrategia deliberadamente conservadora: se sirve lo guardado para que abra
   al instante y sin señal, y en paralelo se pide la versión de red y se
   guarda para la próxima. El nombre de la caché lleva la version del build,
   así que cada corrida diaria crea una caché nueva y borra las viejas.
   skipWaiting y clients.claim hacen que la versión nueva tome el control
   enseguida, que es lo que evita quedarse pegado en una versión vieja. */
const VERSION = '__VERSION__';
const CACHE = 'guias-' + VERSION;
const PRECARGA = __PRECARGA__;

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.allSettled(PRECARGA.map(u => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', e => { if (e.data === 'actualizar') self.skipWaiting(); });

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;          // fuentes externas, a la red
  if (url.pathname.endsWith('.mp3')) return;           // el audio no se guarda, pesa
  // Solo lo que cuelga de la carpeta del propio service worker. Se usa su
  // scope y no una ruta escrita a mano, que se rompe si el sitio se muda.
  if (!req.url.startsWith(self.registration.scope)) return;

  e.respondWith(
    caches.match(req).then(guardado => {
      const red = fetch(req).then(resp => {
        if (resp && resp.ok) {
          const copia = resp.clone();
          caches.open(CACHE).then(c => c.put(req, copia));
        }
        return resp;
      }).catch(() => guardado);
      return guardado || red;
    })
  );
});
"""

MANIFIESTO = {
    "name": "Vender arte en Nueva York",
    "short_name": "VG",
    "start_url": "./index.html",
    "scope": "./",
    "display": "standalone",
    "background_color": "#EDEAE1",
    "theme_color": "#16150F",
    "lang": "es",
    "icons": [
        {"src": "icono-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icono-512.png", "sizes": "512x512", "type": "image/png",
         "purpose": "any maskable"},
    ],
}

ACTUALIZAR_JS = """
function actualizar(){
  if(!('serviceWorker' in navigator)){ location.reload(); return; }
  navigator.serviceWorker.getRegistrations().then(function(rs){
    return Promise.all(rs.map(function(r){ return r.update(); }));
  }).then(function(){ location.reload(true); });
}
"""


def _dominio(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else url


def _pagina(titulo, cuerpo, pie=""):
    ACT = ACTUALIZAR_JS  # noqa
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="VG">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#16150F">
<link rel="apple-touch-icon" href="icono-180.png">
<link rel="icon" href="icono-192.png">
<link rel="manifest" href="manifest.webmanifest">
<title>{_html.escape(titulo)}</title>
<style>{CSS}</style>
</head>
<body>
<div id="barra"></div>
<header class="panel">
  <div class="sello">VG</div>
  <p class="nom"><span>Virginia Guevara</span><span>Buenos Aires &middot; Nueva York</span></p>
</header>
<main>
{cuerpo}
</main>
<footer>
  <a href="./">Vender arte en Nueva York</a>
  <span class="pie">{pie or "Tocá los números en rojo para ver la fuente de cada dato."}</span>
</footer>
<script>{JS}{ACT}</script>
<script>
if('serviceWorker' in navigator){{addEventListener('load',function(){{
  navigator.serviceWorker.register('sw.js').catch(function(){{}});
}});}}
</script>
</body>
</html>"""


def leer(md_path):
    """Convierte un apunte en las piezas que necesitan las páginas."""
    import markdown
    crudo = open(md_path).read()
    clave = os.path.basename(md_path).replace(".md", "")
    fecha, ingles = clave[:10], clave.endswith("-en")

    notas = {}
    def _cazar(m):
        notas[m.group(1)] = m.group(2).strip()
        return ""
    cuerpo = re.sub(r"^\[\^(\d+)\]:\s*(.+)$", _cazar, crudo, flags=re.M)
    cuerpo = re.sub(r"\n##\s*(Referencias|References)\s*\n", "\n", cuerpo)

    m = re.search(r"^#\s+(.+)$", cuerpo, re.M)
    titulo_full = m.group(1).strip() if m else clave
    cuerpo = re.sub(r"^#\s+.+$", "", cuerpo, count=1, flags=re.M)
    codigo, _, titulo = titulo_full.partition("—")
    codigo, titulo = codigo.strip(), (titulo.strip() or titulo_full)

    palabras = len(re.sub(r"\[\^\d+\]", "", cuerpo).split())
    minutos = max(1, round(palabras / PPM_LECTURA))

    cuerpo = re.sub(r"\[\^(\d+)\]", r"@@NOTA\1@@", cuerpo)
    md = markdown.Markdown(extensions=["extra", "tables"])
    htm = md.convert(cuerpo)
    htm = re.sub(r"@@NOTA(\d+)@@",
                 lambda mm: (f'<button class="ref" data-nota="n{clave}-{mm.group(1)}" '
                             f'aria-expanded="false" aria-label="Fuente {mm.group(1)}">'
                             f'[{mm.group(1)}]</button>'), htm)

    partes, vistas = [], set()
    for bloque in re.split(r"(?=<p>|<h2|<h3|<ul>)", htm):
        partes.append(bloque)
        for n in re.findall(r'data-nota="n' + re.escape(clave) + r'-(\d+)"', bloque):
            if n in notas and n not in vistas:
                vistas.add(n)
                texto = md.reset().convert(notas[n])
                texto = re.sub(r"^<p>|</p>$", "", texto.strip())
                urls = re.findall(r'href="([^"]+)"', texto)
                sello = f'<span class="fuente">{_html.escape(_dominio(urls[0]))}</span>' if urls else ""
                partes.append(f'<div class="nota" id="n{clave}-{n}">{texto}{sello}</div>')
    htm = "".join(partes)

    sec = re.findall(r"<h2>(.*?)</h2>", htm)
    for i, s in enumerate(sec, 1):
        htm = htm.replace(f"<h2>{s}</h2>", f'<h2 id="{clave}-s{i}">{s}</h2>', 1)

    refs = "".join(
        f"<li>{re.sub(r'^<p>|</p>$', '', md.reset().convert(notas[k]).strip())}</li>"
        for k in sorted(notas, key=int))

    mm = re.match(r"S(\d+)-([A-Z])(\d*)", codigo)
    semana, tipo, num = (int(mm.group(1)), mm.group(2), mm.group(3)) if mm else (0, "?", "")
    if ingles:
        clase = {"L": f"Lesson {num}", "R": "Review", "P": "Practice"}.get(tipo, codigo)
        rotulo = f"Week {semana} &middot; {clase}"
    else:
        clase = {"L": f"Lección {ORDINAL[int(num)] if num.isdigit() and int(num) < 8 else num}",
                 "R": "Repaso", "P": "Práctica"}.get(tipo, codigo)
        rotulo = f"Semana {ORDINAL[semana] if semana < 8 else semana} &middot; {clase}"

    d = datetime.date.fromisoformat(fecha)
    fecha_larga = (f"{MONTHS[d.month-1]} {d.day}, {d.year}" if ingles
                   else f"{d.day} de {MESES[d.month-1]} de {d.year}")

    return dict(clave=clave, fecha=fecha, ingles=ingles, codigo=codigo, titulo=titulo,
                rotulo=rotulo, semana=semana, tipo=tipo, num=num, minutos=minutos,
                htm=htm, refs=refs, secciones=sec, fecha_larga=fecha_larga)


def pagina_entrega(a):
    mp3 = f"{BASE_URL}/curso/episodios/{a['fecha']}{'-en' if a['ingles'] else ''}.mp3"
    otro_mp3 = f"{BASE_URL}/curso/episodios/{a['fecha']}{'' if a['ingles'] else '-en'}.mp3"
    rot_esc = "Listen to the class" if a["ingles"] else "Escuchar la clase"
    rot_idi = "En español" if a["ingles"] else "En inglés"
    rot_min = "min read" if a["ingles"] else "min"
    rot_cont = "Contents" if a["ingles"] else "Contenido"
    rot_refs = "References" if a["ingles"] else "Referencias"
    toc = "".join(f'<li><a href="#{a["clave"]}-s{i}">{s}</a></li>'
                  for i, s in enumerate(a["secciones"], 1))
    cuerpo = f"""  <p class="rot">{a['rotulo']}</p>
  <h1>{_html.escape(a['titulo'])}</h1>
  <p class="meta">{a['fecha_larga']} &mdash; {a['minutos']} {rot_min}</p>

  <div class="escucha">
    <p class="r">{rot_esc}</p>
    <audio controls preload="none" src="{mp3}"></audio>
    <a class="idioma" href="{otro_mp3}">{rot_idi}</a>
  </div>

  <details class="toc"><summary>{rot_cont}</summary><ol>{toc}</ol></details>

  {a['htm']}

  <section class="refs">
    <h2>{rot_refs}</h2>
    <ol>{a['refs']}</ol>
  </section>"""
    return _pagina(f"{a['codigo']} — {a['titulo']}", cuerpo)


def pagina_semana(semana, entregas):
    """El booklet: las siete entregas de la semana en una sola página."""
    ini, fin = entregas[0], entregas[-1]
    d1, d2 = datetime.date.fromisoformat(ini["fecha"]), datetime.date.fromisoformat(fin["fecha"])
    rango = (f"{d1.day} de {MESES[d1.month-1]} al {d2.day} de {MESES[d2.month-1]} de {d2.year}"
             if d1.month != d2.month else
             f"{d1.day} al {d2.day} de {MESES[d2.month-1]} de {d2.year}")
    total = sum(a["minutos"] for a in entregas)
    idx = "".join(
        f'<li><a href="#{a["clave"]}"><span class="cod">{a["rotulo"]}</span>'
        f'<span class="tit">{_html.escape(a["titulo"])}</span></a></li>' for a in entregas)
    caps = ""
    for a in entregas:
        caps += f"""<section class="cap-sem" id="{a['clave']}">
  <p class="rot">{a['rotulo']}</p>
  <h1>{_html.escape(a['titulo'])}</h1>
  <p class="meta">{a['fecha_larga']} &mdash; {a['minutos']} min</p>
  {a['htm']}
  <section class="refs"><h2>Referencias</h2><ol>{a['refs']}</ol></section>
</section>"""
    cuerpo = f"""  <p class="rot">Guía de la semana {ORDINAL[semana] if semana < 8 else semana}</p>
  <h1>Las {len(entregas)} entregas de la semana</h1>
  <p class="meta">{rango} &mdash; {total} min de lectura</p>
  <ul class="lista cap">{idx}</ul>
{caps}"""
    return _pagina(f"Semana {semana} — Vender arte en Nueva York", cuerpo,
                   pie="Esta página se imprime en tamaño carta, una entrega por página.")


EXAMEN_JS = """
function corregir(){
  var qs = document.querySelectorAll('.preg[data-correcta]'), bien = 0, sin = 0;
  qs.forEach(function(q){
    var sel = q.querySelector('input:checked');
    var ok = parseInt(q.dataset.correcta, 10);
    if(!sel){ sin++; }
    q.querySelectorAll('label').forEach(function(l, i){
      l.classList.remove('bien','mal');
      if(i === ok) l.classList.add('bien');
      else if(sel && parseInt(sel.value,10) === i) l.classList.add('mal');
    });
    if(sel && parseInt(sel.value,10) === ok) bien++;
    q.querySelector('.porque').classList.add('ver');
    q.querySelectorAll('input').forEach(function(i){ i.disabled = true; });
  });
  var p = document.getElementById('puntaje');
  p.querySelector('b').textContent = bien + ' de ' + qs.length;
  p.querySelector('span').textContent = sin ? (sin + ' sin contestar') : 'respondiste todas';
  p.classList.add('ver');
  p.scrollIntoView({behavior:'smooth', block:'center'});
}
function verModelo(id){
  var m = document.getElementById(id);
  m.classList.add('ver');
  m.previousElementSibling.style.display = 'none';
}
"""


def pagina_examen(d):
    """El examen de la semana: opción múltiple que se corrige sola y preguntas
    para escribir con su respuesta modelo. No guarda nada: el puntaje vive en
    la pantalla y se va cuando cierra."""
    sem = d["semana"]
    nom = ORDINAL[sem] if sem < 8 else sem
    partes = []
    for i, q in enumerate(d["opcion_multiple"], 1):
        ops = "".join(
            f'<label><input type="radio" name="p{i}" value="{j}">{_html.escape(o)}</label>'
            for j, o in enumerate(q["opciones"]))
        fuente = (f' <a href="{q["fuente"]}.html">Volver a esa clase</a>'
                  if q.get("fuente") else "")
        partes.append(
            f'<div class="preg" data-correcta="{q["correcta"]}">'
            f'<p class="n">Pregunta {i} de {len(d["opcion_multiple"])}</p>'
            f'<p class="q">{_html.escape(q["pregunta"])}</p>{ops}'
            f'<div class="porque">{_html.escape(q["porque"])}{fuente}</div></div>')

    abiertas = []
    for i, q in enumerate(d.get("abiertas", []), 1):
        fuente = (f' <a href="{q["fuente"]}.html">Volver a esa clase</a>'
                  if q.get("fuente") else "")
        abiertas.append(
            f'<div class="preg"><p class="n">Para escribir {i} de {len(d["abiertas"])}</p>'
            f'<p class="q">{_html.escape(q["pregunta"])}</p>'
            f'<textarea placeholder="Escribí tu respuesta y después compará"></textarea>'
            f'<button class="boton suave" onclick="verModelo(\'m{i}\')">Ver la respuesta modelo</button>'
            f'<div class="porque" id="m{i}">{_html.escape(q["modelo"])}{fuente}</div></div>')

    cuerpo = f"""  <p class="rot">Examen &middot; Semana {nom}</p>
  <h1>{_html.escape(d.get("titulo", "Examen de la semana"))}</h1>
  <p class="meta">{len(d["opcion_multiple"])} de opción múltiple &mdash; {len(d.get("abiertas", []))} para escribir</p>
  <p class="bajada">{_html.escape(d.get("bajada", ""))}</p>
  <div id="puntaje"><b></b><span></span></div>
  {"".join(partes)}
  <button class="boton" onclick="corregir()">Corregir</button>
  <h2>Para escribir</h2>
  <p class="bajada">Estas no se corrigen solas. Escribí tu respuesta y después mirá la modelo.</p>
  {"".join(abiertas)}
  <p class="sello-ver">Nada de lo que escribas se guarda ni se manda a ningún lado.</p>"""
    return _pagina(f"Examen de la semana {sem}", cuerpo,
                   pie="Cada respuesta correcta indica de qué clase salió.").replace(
        "<script>", "<script>" + EXAMEN_JS, 1)

PRACTICA_CSS = """
.tapa-p{margin:0 0 30px}
.dosis{display:flex;gap:0;border-top:1px solid var(--tinta);border-bottom:.5px solid var(--filete);margin:24px 0}
.dosis div{flex:1;padding:16px 0}
.dosis b{display:block;font-family:ui-serif,"New York",Georgia,serif;font-size:27px;line-height:1;
  font-variant-numeric:tabular-nums}
.dosis span{display:block;margin-top:7px;font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--tenue)}
#pantalla{min-height:60vh}
.oculto{display:none}
.ronda{font-size:9.5px;letter-spacing:.26em;text-transform:uppercase;color:var(--laca);margin:0 0 16px}
.pregunta{font-family:ui-serif,"New York",Georgia,serif;font-size:21px;line-height:1.38;margin:0 0 8px}
.origen{font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--tenue);margin:0 0 20px}
.op{display:flex;align-items:stretch;margin:0 0 9px;border:1px solid var(--control)}
.op.fuera{opacity:.42}
.op.fuera .txt{text-decoration:line-through}
.op .txt{flex:1;padding:13px 14px;font-family:ui-serif,"New York",Georgia,serif;font-size:17px;
  line-height:1.4;cursor:pointer;background:none;border:none;text-align:left;color:var(--tinta)}
.op .x{width:46px;border:none;border-left:1px solid var(--control);background:none;color:var(--tenue);
  font-size:15px;cursor:pointer}
.op.elegida{border-width:2px;border-color:var(--tinta)}
.op.bien{border-width:2px;border-color:#2E6B4F;background:#E6EFE7}
.op.mal{border-width:2px;border-color:var(--laca);background:#F2E5E2}
.chance{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--tenue);margin:14px 0 0}
.chance b{color:var(--laca)}
.conf{margin:24px 0 0;padding-top:20px;border-top:.5px solid var(--filete)}
.conf p{font-family:ui-serif,"New York",Georgia,serif;font-size:18px;margin:0 0 14px}
.conf .par{display:flex;gap:10px}
.conf .par button{flex:1;padding:15px 8px;border:1px solid var(--control);background:none;
  color:var(--tinta);font-size:11px;letter-spacing:.16em;text-transform:uppercase;cursor:pointer}
.veredicto{margin:24px 0 0;padding:18px 0 0;border-top:1px solid var(--tinta)}
.veredicto .v{font-size:11px;letter-spacing:.22em;text-transform:uppercase;margin:0 0 12px}
.veredicto .v.si{color:#2E6B4F}
.veredicto .v.no{color:var(--laca)}
.veredicto p{font-family:ui-serif,"New York",Georgia,serif;font-size:17px;line-height:1.55;margin:0 0 12px}
.hiper{margin:0 0 14px;padding:14px 0 14px 16px;border-left:1.5px solid var(--laca);
  font-family:ui-serif,"New York",Georgia,serif;font-size:16px;line-height:1.5;color:var(--tenue)}
.pie-nav{margin:28px 0 0;padding-top:18px;border-top:.5px solid var(--filete);display:flex;
  justify-content:space-between;align-items:center}
.parar{background:none;border:none;color:var(--tenue);font-size:10px;letter-spacing:.18em;
  text-transform:uppercase;cursor:pointer;padding:8px 0}
.teclas{font-size:10px;letter-spacing:.1em;color:var(--tenue)}
.resumen b{display:block;font-family:ui-serif,"New York",Georgia,serif;font-size:52px;line-height:1;
  font-variant-numeric:tabular-nums;margin:0 0 8px}
.aviso{margin:20px 0;padding:15px 0 15px 16px;border-left:1.5px solid var(--laca);
  font-family:ui-serif,"New York",Georgia,serif;font-size:16px;line-height:1.5;color:var(--tenue)}
"""

PRACTICA_JS = """
const LLAVE='vg_practica_v1';
let S=(function(){try{return JSON.parse(localStorage.getItem(LLAVE))||{}}catch(e){return {}}})();
S.usadas=S.usadas||[]; S.fallos=S.fallos||{}; S.sesiones=S.sesiones||0;
function guardar(){try{localStorage.setItem(LLAVE,JSON.stringify(S))}catch(e){}}

const PORID={}; BANCO.forEach(q=>PORID[q.id]=q);
let cola=[], i=0, ronda='', elegida=null, seguro=null, fuera=[], nuevas=[], falladas=[], reciclado=false;

function elegirSesion(){
  // Ronda 1: lo que ya falló. Primero lo que falló estando segura, después lo más viejo.
  const rep=Object.keys(S.fallos).filter(id=>PORID[id])
    .sort((a,b)=>{const A=S.fallos[a],B=S.fallos[b];
      if(A.seguro!==B.seguro) return A.seguro?-1:1; return A.ts-B.ts;}).slice(0,6);
  // Ronda 2: preguntas que todavía no vio. Si se agotaron, se recicla.
  let pool=BANCO.filter(q=>S.usadas.indexOf(q.id)<0 && rep.indexOf(q.id)<0);
  if(pool.length<8){ reciclado=true; S.usadas=[]; pool=BANCO.filter(q=>rep.indexOf(q.id)<0); }
  // Interleaving: nunca dos seguidas de la misma clase.
  const porClase={}; pool.forEach(q=>{(porClase[q.fuente]=porClase[q.fuente]||[]).push(q)});
  const nue=[]; let ultima=null;
  while(nue.length<Math.min(8,pool.length)){
    const claves=Object.keys(porClase).filter(k=>porClase[k].length&&k!==ultima);
    const usar=claves.length?claves:Object.keys(porClase).filter(k=>porClase[k].length);
    if(!usar.length) break;
    usar.sort((a,b)=>porClase[b].length-porClase[a].length);
    nue.push(porClase[usar[0]].shift()); ultima=usar[0];
  }
  falladas=rep.map(id=>PORID[id]); nuevas=nue;
}

function empezar(){
  document.getElementById('portada').classList.add('oculto');
  document.getElementById('pantalla').classList.remove('oculto');
  if(falladas.length){ ronda='1'; cola=falladas.slice(); } else { ronda='2'; cola=nuevas.slice(); }
  i=0; pintar();
}

function pintar(){
  elegida=null; seguro=null; fuera=[];
  const q=cola[i], p=document.getElementById('pantalla');
  const rot = ronda==='1' ? 'Ronda 1 · Lo que ya te ganó' : (ronda==='2' ? 'Ronda 2 · Preguntas nuevas' : 'Ronda 3 · Segunda vuelta');
  p.innerHTML =
    '<p class="ronda">'+rot+' &middot; '+(i+1)+' de '+cola.length+'</p>'+
    '<p class="pregunta">'+q.q+'</p>'+
    '<p class="origen">'+q.rot+'</p>'+
    '<div id="ops">'+q.opts.map(function(o,j){
      return '<div class="op" data-j="'+j+'">'+
        '<button class="txt" onclick="elegir('+j+')">'+o+'</button>'+
        '<button class="x" onclick="tachar('+j+')" aria-label="Descartar esta opción">&times;</button></div>';
    }).join('')+'</div>'+
    '<p class="chance" id="chance"></p>'+
    '<div id="paso"></div>'+
    '<div class="pie-nav"><button class="parar" onclick="parar()">Parar por hoy</button>'+
    '<span class="teclas">1 a 4 elegir &middot; Enter seguir</span></div>';
  chance();
}

function chance(){
  const vivas=cola[i].opts.length-fuera.length;
  const el=document.getElementById('chance');
  if(!fuera.length){ el.innerHTML='Una en '+vivas+' &middot; '+Math.round(100/vivas)+'%'; }
  else{ el.innerHTML='Una en '+vivas+' &middot; <b>'+Math.round(100/vivas)+'%</b> &middot; descartaste '+fuera.length; }
}
function tachar(j){
  if(elegida!==null) return;
  const d=document.querySelector('.op[data-j="'+j+'"]');
  const k=fuera.indexOf(j);
  if(k<0){ if(cola[i].opts.length-fuera.length<=1) return; fuera.push(j); d.classList.add('fuera'); }
  else { fuera.splice(k,1); d.classList.remove('fuera'); }
  chance();
}
function elegir(j){
  if(elegida!==null) return;
  elegida=j;
  document.querySelector('.op[data-j="'+j+'"]').classList.add('elegida');
  document.getElementById('paso').innerHTML=
    '<div class="conf"><p>Antes de ver el resultado. ¿Estabas segura o adivinando?</p>'+
    '<div class="par"><button onclick="confianza(true)">Estaba segura</button>'+
    '<button onclick="confianza(false)">Adivinando</button></div></div>';
}
function confianza(v){
  seguro=v; const q=cola[i], ok=(elegida===q.ok);
  if(ok){ if(S.fallos[q.id]) delete S.fallos[q.id]; }
  else { S.fallos[q.id]={seguro:v, ts:Date.now()}; }
  if(S.usadas.indexOf(q.id)<0) S.usadas.push(q.id);
  guardar();
  if(ronda==='2'){ avanzar(); return; }     // la ronda 2 no da feedback hasta el final
  mostrarVeredicto(ok, q);
}
function mostrarVeredicto(ok, q){
  document.querySelectorAll('.op').forEach(function(d){
    const j=parseInt(d.dataset.j,10);
    if(j===q.ok) d.classList.add('bien'); else if(j===elegida) d.classList.add('mal');
  });
  const hiper = (!ok && seguro) ? '<div class="hiper">Fallaste esta estando segura. Es el mejor momento de aprendizaje de toda la sesión, porque un error cometido con confianza se corrige mucho mejor que uno dudado. Por eso vuelve al final.</div>' : '';
  const gano = (ok && fuera.length) ? '<p>Mirá cómo llegaste. Descartaste '+fuera.length+' antes de comprometerte. Esa es la jugada.</p>' : '';
  document.getElementById('paso').innerHTML=
    '<div class="veredicto"><p class="v '+(ok?'si':'no')+'">'+(ok?'Correcta':'Incorrecta')+'</p>'+
    hiper+gano+'<p>'+q.porque+'</p>'+
    (q.fuente?'<p><a href="'+q.fuente+'.html">Volver a esa clase</a></p>':'')+
    '<button class="boton" onclick="avanzar()">Seguir</button></div>';
}
function avanzar(){
  i++;
  if(i<cola.length){ pintar(); return; }
  if(ronda==='1'){ ronda='2'; cola=nuevas.slice(); i=0; pintar(); return; }
  if(ronda==='2'){
    const mal=nuevas.filter(q=>S.fallos[q.id]);
    if(mal.length){ ronda='3'; cola=mal; i=0; pintar(); return; }
  }
  terminar();
}
function terminar(){
  S.sesiones++; guardar();
  const bien=nuevas.filter(q=>!S.fallos[q.id]).length;
  const pend=Object.keys(S.fallos).length;
  document.getElementById('pantalla').innerHTML=
    '<div class="resumen"><p class="ronda">Sesión terminada</p>'+
    '<b>'+bien+' de '+nuevas.length+'</b>'+
    '<p class="origen">En el bloque de preguntas nuevas</p>'+
    (pend?'<p>Te quedan '+pend+' preguntas pendientes de arreglar. Mañana empiezan por ahí.</p>'
        :'<p>No te quedó ninguna pendiente. Mañana arrancás con material nuevo.</p>')+
    (reciclado?'<div class="aviso">Se dio una vuelta entera al banco de preguntas y volvió a empezar. A partir de acá se repiten, que para fijar está bien.</div>':'')+
    '<button class="boton" onclick="location.reload()">Otra sesión</button></div>';
  window.scrollTo(0,0);
}
function parar(){
  guardar();
  document.getElementById('pantalla').innerHTML=
    '<div class="resumen"><p class="ronda">Guardado</p>'+
    '<p class="pregunta">Parar es una decisión, no un abandono.</p>'+
    '<p>Lo que hiciste quedó guardado. Mañana sigue desde acá.</p></div>';
  window.scrollTo(0,0);
}
document.addEventListener('keydown',function(e){
  if(document.getElementById('portada') && !document.getElementById('portada').classList.contains('oculto')){
    if(e.key==='Enter'){ empezar(); } return; }
  if(elegida===null && /^[1-4]$/.test(e.key)){
    const j=parseInt(e.key,10)-1;
    if(j<cola[i].opts.length){ e.shiftKey ? tachar(j) : elegir(j); } return; }
  if(e.key==='Enter'||e.key==='ArrowRight'){
    const b=document.querySelector('#paso .boton'); if(b) b.click();
    const c=document.querySelector('.conf'); if(c) return;
  }
});
"""


def pagina_practica(examenes):
    """El motor de práctica: una sola página con el banco entero adentro que
    arma la sesión del día sola. Tres rondas, según lo aprendido en el proyecto
    de Guillermito: primero lo que ya falló, después preguntas nuevas sin
    feedback, y al final vuelve todo lo que erró en el bloque.

    Lo que recuerda vive en el localStorage del teléfono de ella y no sale de
    ahí: no hay servidor, no hay planilla, no se manda nada a ningún lado.
    """
    banco = []
    for sem in sorted(examenes):
        d = examenes[sem]
        nom = ORDINAL[sem] if sem < 8 else sem
        for k, q in enumerate(d["opcion_multiple"]):
            banco.append({
                "id": f"s{sem:02d}q{k:02d}",
                "q": q["pregunta"],
                "opts": q["opciones"],
                "ok": q["correcta"],
                "porque": q["porque"],
                "fuente": q.get("fuente", ""),
                "rot": f"Semana {nom}",
            })
    n = len(banco)
    cuerpo = f"""  <div id="portada">
  <p class="rot">La práctica de hoy</p>
  <h1>Ponerte a prueba</h1>
  <p class="bajada">Una sesión corta, distinta cada día. Empieza por lo que fallaste
  antes, sigue con preguntas nuevas y termina repreguntando lo que erraste en el camino.</p>
  <div class="dosis">
    <div><b>8</b><span>preguntas nuevas</span></div>
    <div><b>10</b><span>minutos</span></div>
    <div><b>{n}</b><span>en el banco</span></div>
  </div>
  <p class="bajada">Podés descartar opciones con la crucecita antes de contestar, y ver
  cómo se te mueven las chances. Nada de lo que hagas se guarda fuera de este teléfono.</p>
  <button class="boton" onclick="empezar()">Empezar</button>
  </div>
  <div id="pantalla" class="oculto"></div>"""
    doc = _pagina("Práctica — Vender arte en Nueva York", cuerpo,
                  pie="Tu progreso vive en este teléfono y no se manda a ningún lado.")
    doc = doc.replace("</style>", PRACTICA_CSS + "</style>", 1)
    banco_js = "const BANCO=" + json.dumps(banco, ensure_ascii=False) + ";"
    return doc.replace("<script>", "<script>" + banco_js + PRACTICA_JS + "elegirSesion();", 1)


def pagina_indice(apuntes, version, examenes=None):
    """La portada de la app: la clase de hoy arriba, después la semana, después todo."""
    hoy = datetime.date.today().isoformat()
    del_dia = next((a for a in apuntes if a["fecha"] == hoy), None)
    if del_dia is None:
        del_dia = apuntes[0] if apuntes else None
        rot_hoy = "La última clase"
    else:
        rot_hoy = "La clase de hoy"

    if del_dia:
        destacada = (f'<a class="hoy" href="{del_dia["clave"]}.html">'
                     f'<span class="r">{rot_hoy} &middot; {del_dia["rotulo"]}</span>'
                     f'<span class="t">{_html.escape(del_dia["titulo"])}</span>'
                     f'<span class="d">{del_dia["fecha_larga"]} &mdash; {del_dia["minutos"]} min</span></a>')
        sem_actual = del_dia["semana"]
    else:
        destacada = '<p class="vacio">Todavía no hay ninguna clase publicada.</p>'
        sem_actual = 0

    esta_sem = [a for a in apuntes if a["semana"] == sem_actual and a is not del_dia]
    esta_sem.sort(key=lambda a: a["fecha"], reverse=True)
    bloque_sem = ""
    if esta_sem:
        filas = "".join(
            f'<li><a href="{a["clave"]}.html"><span class="cod">{a["rotulo"]}</span>'
            f'<span class="tit">{_html.escape(a["titulo"])}</span></a></li>' for a in esta_sem)
        bloque_sem = (f'<h2>Esta semana</h2><ul class="lista cap">{filas}</ul>'
                      f'<ul class="lista cap"><li><a href="semana-{sem_actual:02d}.html">'
                      f'<span class="cod">Booklet</span><span class="tit">'
                      f'La semana {ORDINAL[sem_actual] if sem_actual < 8 else sem_actual} entera, '
                      f'para leer de un tirón o imprimir</span></a></li></ul>')

    otras = [a for a in apuntes if a["semana"] != sem_actual]
    filas = "".join(
        f'<li><a href="{a["clave"]}.html"><span class="cod">{a["rotulo"]}</span>'
        f'<span class="tit">{_html.escape(a["titulo"])}</span></a></li>' for a in otras)
    bloque_otras = f'<h2>Las clases anteriores</h2><ul class="lista">{filas}</ul>' if otras else ""

    examenes = examenes or {}
    practica = ('<ul class="lista cap"><li><a href="practica.html">'
                '<span class="cod">Práctica de hoy</span><span class="tit">'
                'Una sesión corta para ponerte a prueba, distinta cada día</span></a></li></ul>'
                if examenes else "")
    if sem_actual in examenes:
        bloque_sem += (f'<ul class="lista cap"><li><a href="examen-semana-{sem_actual:02d}.html">'
                       f'<span class="cod">Examen</span><span class="tit">'
                       f'Ponerte a prueba con la semana {ORDINAL[sem_actual] if sem_actual < 8 else sem_actual}'
                       f'</span></a></li></ul>')
    semanas = sorted({a["semana"] for a in otras if a["semana"]}, reverse=True)
    booklets = "".join(
        f'<li><a href="semana-{x:02d}.html"><span class="cod">Booklet</span>'
        f'<span class="tit">Semana {ORDINAL[x] if x < 8 else x}, las entregas juntas</span></a></li>'
        for x in semanas)
    booklets += "".join(
        f'<li><a href="examen-semana-{x:02d}.html"><span class="cod">Examen</span>'
        f'<span class="tit">Semana {ORDINAL[x] if x < 8 else x}, ponerte a prueba</span></a></li>'
        for x in semanas if x in examenes)
    bloque_book = f'<h2>Booklets y exámenes</h2><ul class="lista">{booklets}</ul>' if booklets else ""

    cuerpo = f"""  <p class="rot">Guías de estudio</p>
  <h1>Vender arte en Nueva York</h1>
  <p class="meta">{len(apuntes)} clases</p>
  {destacada}
  {practica}
  {bloque_sem}
  {bloque_otras}
  {bloque_book}
  <p class="sello-ver">Versión {version} &middot; <button onclick="actualizar()">Buscar novedades</button></p>"""
    return _pagina("Vender arte en Nueva York", cuerpo,
                   pie="Agregala a la pantalla de inicio y la tenés siempre a mano.")


def main():
    if not os.path.isdir(SRC):
        print("[guia] sin carpeta de apuntes, nada que hacer")
        return
    os.makedirs(DST, exist_ok=True)
    hoy = datetime.date.today().isoformat()

    apuntes, hechas = [], 0
    for md in sorted(glob.glob(f"{SRC}/*.md")):
        try:
            a = leer(md)
        except Exception as e:
            print(f"[guia] ERROR leyendo {os.path.basename(md)}: {e}")
            continue
        apuntes.append(a)
        destino = f"{DST}/{a['clave']}.html"
        if os.path.exists(destino) and not a["clave"].startswith(hoy):
            continue
        try:
            open(destino, "w").write(pagina_entrega(a))
            hechas += 1
            print(f"[guia] {a['clave']}.html listo")
        except Exception as e:
            print(f"[guia] ERROR armando {a['clave']}: {e}")

    # Exámenes de la semana, escritos por la rutina como JSON.
    examenes = {}
    for j in sorted(glob.glob(f"{BASE}/curso/examen-semana-*.json")):
        try:
            d = json.load(open(j))
            open(f"{DST}/examen-semana-{d['semana']:02d}.html", "w").write(pagina_examen(d))
            examenes[d["semana"]] = d
            print(f"[guia] examen-semana-{d['semana']:02d}.html "
                  f"({len(d['opcion_multiple'])} + {len(d.get('abiertas', []))} preguntas)")
        except Exception as e:
            print(f"[guia] ERROR con {os.path.basename(j)}: {e}")

    if examenes:
        try:
            open(f"{DST}/practica.html", "w").write(pagina_practica(examenes))
            total = sum(len(d["opcion_multiple"]) for d in examenes.values())
            print(f"[guia] practica.html con {total} preguntas de {len(examenes)} semanas")
        except Exception as e:
            print(f"[guia] ERROR con la práctica: {e}")

    # Booklets por semana, solo en español y solo con la semana completa o en curso.
    porsem = {}
    for a in apuntes:
        if not a["ingles"] and a["semana"]:
            porsem.setdefault(a["semana"], []).append(a)
    for s, lista in porsem.items():
        orden = {"L": 0, "R": 1, "P": 2}
        lista.sort(key=lambda a: (a["fecha"], orden.get(a["tipo"], 9)))
        try:
            open(f"{DST}/semana-{s:02d}.html", "w").write(pagina_semana(s, lista))
            print(f"[guia] semana-{s:02d}.html con {len(lista)} entregas")
        except Exception as e:
            print(f"[guia] ERROR armando la semana {s}: {e}")

    esp = sorted([a for a in apuntes if not a["ingles"]], key=lambda a: a["fecha"], reverse=True)

    # La version de la cache sale del contenido: ultima fecha y cantidad de
    # entregas. Cambia sola cuando hay material nuevo y no cambia cuando no.
    version = f"{esp[0]['fecha'] if esp else '0000-00-00'}-{len(apuntes)}"

    try:
        open(f"{DST}/index.html", "w").write(pagina_indice(esp, version, examenes))
        print(f"[guia] index.html con {len(esp)} entregas")
    except Exception as e:
        print(f"[guia] ERROR con el índice: {e}")

    # Manifiesto, para que se pueda agregar a la pantalla de inicio.
    try:
        open(f"{DST}/manifest.webmanifest", "w").write(json.dumps(MANIFIESTO, indent=2))
    except Exception as e:
        print(f"[guia] ERROR con el manifiesto: {e}")

    # Service worker, con la lista de lo que se guarda para leer sin señal.
    try:
        precarga = ["./", "index.html", "manifest.webmanifest", "icono-180.png", "icono-192.png"]
        precarga += sorted(os.path.basename(f) for f in glob.glob(f"{DST}/*.html")
                           if not f.endswith("index.html"))
        sw = SW.replace("__VERSION__", version).replace("__PRECARGA__", json.dumps(precarga))
        open(f"{DST}/sw.js", "w").write(sw)
        print(f"[guia] sw.js versión {version}, {len(precarga)} archivos para leer sin señal")
    except Exception as e:
        print(f"[guia] ERROR con el service worker: {e}")

    # Los íconos viven en el repo junto al script y se copian una sola vez.
    for px in (180, 192, 512):
        origen, destino = f"{BASE}/icono-{px}.png", f"{DST}/icono-{px}.png"
        if os.path.exists(origen) and not os.path.exists(destino):
            try:
                open(destino, "wb").write(open(origen, "rb").read())
                print(f"[guia] icono-{px}.png copiado")
            except Exception as e:
                print(f"[guia] ERROR copiando el ícono {px}: {e}")

    if not hechas:
        print("[guia] no había guías nuevas que armar")


if __name__ == "__main__":
    main()
