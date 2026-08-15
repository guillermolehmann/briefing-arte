#!/usr/bin/env python3
"""
Arma las guías de estudio en HTML del curso "Vender arte en Nueva York",
pensadas para leer en el teléfono, con la identidad Marco.

  curso/apunte/AAAA-MM-DD.md     -> docs/curso/guia/AAAA-MM-DD.html
  curso/apunte/AAAA-MM-DD-en.md  -> docs/curso/guia/AAAA-MM-DD-en.html
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
  --papel:#EDEAE1; --tinta:#16150F; --laca:#9C3A2A; --tenue:#8A857A;
  --filete:#C6C0B2; --caja:#E4E0D5;
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
  color:#8F8B80;margin:15px 0 0;line-height:2}
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
  color:var(--tinta);border:.5px solid var(--filete);padding:10px 15px;line-height:1}

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


def _dominio(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else url


def _pagina(titulo, cuerpo, pie=""):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="VG">
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
<script>{JS}</script>
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


def pagina_indice(apuntes):
    filas = ""
    for a in apuntes:
        filas += (f'<li><a href="{a["clave"]}.html"><span class="cod">{a["rotulo"]}</span>'
                  f'<span class="tit">{_html.escape(a["titulo"])}</span></a></li>')
    semanas = sorted({a["semana"] for a in apuntes if a["semana"]}, reverse=True)
    sem = "".join(f'<li><a href="semana-{s:02d}.html"><span class="cod">Booklet</span>'
                  f'<span class="tit">Semana {ORDINAL[s] if s < 8 else s}, las siete entregas juntas</span>'
                  f'</a></li>' for s in semanas)
    cuerpo = f"""  <p class="rot">Guías de estudio</p>
  <h1>Vender arte en Nueva York</h1>
  <p class="meta">{len(apuntes)} entregas</p>
  <ul class="lista cap">{sem}</ul>
  <h2>Todas las entregas</h2>
  <ul class="lista">{filas}</ul>"""
    return _pagina("Guías — Vender arte en Nueva York", cuerpo,
                   pie="Una guía nueva cada mañana, también por mail.")


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
    try:
        open(f"{DST}/index.html", "w").write(pagina_indice(esp))
        print(f"[guia] index.html con {len(esp)} entregas")
    except Exception as e:
        print(f"[guia] ERROR con el índice: {e}")

    if not hechas:
        print("[guia] no había guías nuevas que armar")


if __name__ == "__main__":
    main()
