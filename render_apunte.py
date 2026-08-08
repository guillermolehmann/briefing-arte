#!/usr/bin/env python3
"""
Convierte los apuntes académicos del curso (curso/apunte/AAAA-MM-DD.md)
en PDFs con formato universitario (docs/curso/pdf/AAAA-MM-DD.pdf).
Solo renderiza los que no tienen PDF todavía, más el de hoy si cambió.
Uso: python3 render_apunte.py   |   Requisitos: pip install markdown weasyprint
"""
import os, sys, glob, datetime, re

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = f"{BASE}/curso/apunte"
DST = f"{BASE}/docs/curso/pdf"

CSS = """
@page { size: A4; margin: 2.4cm 2.6cm 2.6cm 2.6cm;
  @bottom-center { content: "Vender arte en Nueva York — El curso de Arte a la Mañana";
                   font-size: 8pt; color: #888; }
  @bottom-right { content: counter(page); font-size: 9pt; color: #555; } }
body { font-family: "DejaVu Serif", serif; font-size: 10.5pt; line-height: 1.55;
       color: #1a1a1a; text-align: justify; hyphens: auto; }
h1 { font-size: 19pt; line-height: 1.25; margin: 0 0 4pt 0; text-align: left; }
.cabecera { border-bottom: 2.5pt solid #1F3B32; padding-bottom: 10pt; margin-bottom: 18pt; }
.cabecera p { margin: 2pt 0; font-size: 9pt; color: #555; text-align: left;
              text-transform: uppercase; letter-spacing: 1.2pt; }
h2 { font-size: 13pt; margin: 18pt 0 6pt 0; text-align: left; color: #1F3B32; }
h3 { font-size: 11pt; margin: 14pt 0 4pt 0; text-align: left; }
p { margin: 0 0 8pt 0; }
blockquote { margin: 8pt 16pt; padding-left: 10pt; border-left: 2pt solid #C9A24B;
             color: #444; font-style: italic; }
a { color: #1a56db; text-decoration: underline; }
sup { font-size: 7.5pt; }
ol, ul { margin: 4pt 0 10pt 18pt; padding: 0; }
li { margin-bottom: 4pt; }
hr { border: none; border-top: 0.8pt solid #bbb; margin: 16pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 8pt 0; }
th, td { border: 0.6pt solid #999; padding: 4pt 6pt; text-align: left; }
th { background: #EFEBE0; }
"""

URL_SUELTA = re.compile(r'(?<![\(\[<"\'=/])(https?://[^\s\)\]>"]+)')

def autolink(texto):
    """Convierte URLs sueltas (texto plano) en links de markdown clickeables.
    No toca las que ya están dentro de [texto](url) o <url>."""
    def _link(m):
        url = m.group(1).rstrip('.,;:')
        resto = m.group(1)[len(url):]
        return f'[{url}]({url}){resto}'
    return URL_SUELTA.sub(_link, texto)

def render(md_path, pdf_path):
    import markdown
    from weasyprint import HTML
    raw = autolink(open(md_path).read())
    body = markdown.markdown(raw, extensions=["extra", "tables", "footnotes", "toc"])
    fecha = os.path.basename(md_path).replace(".md", "")
    html = f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="cabecera">
<p>Vender arte en Nueva York · El curso de Arte a la Mañana · {fecha}</p>
</div>
{body}
</body></html>"""
    HTML(string=html).write_pdf(pdf_path)
    print(f"[apunte] {os.path.basename(pdf_path)} listo")

INDICE_CSS = """
body { font-family: Georgia, 'Times New Roman', serif; margin: 0; background: #F6F3EC; color: #1a1a1a; }
header { background: #1F3B32; color: #F6F3EC; padding: 28px 20px 22px; }
header h1 { margin: 0; font-size: 26px; font-weight: normal; letter-spacing: 0.5px; }
header p { margin: 6px 0 0; font-size: 13px; color: #C9A24B; text-transform: uppercase; letter-spacing: 2px; }
main { max-width: 640px; margin: 0 auto; padding: 24px 20px 48px; }
ul { list-style: none; margin: 0; padding: 0; }
li { border-bottom: 1px solid #ddd6c6; }
li a { display: block; padding: 14px 6px; color: #1F3B32; text-decoration: none; font-size: 17px; line-height: 1.4; }
li a:hover { background: #EFEBE0; }
.fecha { display: block; font-size: 12px; color: #8a8474; letter-spacing: 1px; margin-bottom: 2px; }
footer { text-align: center; font-size: 12px; color: #8a8474; padding-bottom: 32px; }
"""

def indice():
    """Genera docs/curso/pdf/index.html con la lista de todos los apuntes."""
    import json
    titulos = {}
    try:
        titulos = json.load(open(f"{BASE}/titulos_curso.json"))
    except Exception:
        pass
    filas = []
    for pdf in sorted(glob.glob(f"{DST}/*.pdf"), reverse=True):
        fecha = os.path.basename(pdf).replace(".pdf", "")
        titulo = titulos.get(fecha, {}).get("titulo", fecha)
        filas.append(
            f'<li><a href="{fecha}.pdf"><span class="fecha">{fecha}</span>{titulo}</a></li>')
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Apuntes — Vender arte en Nueva York</title><style>{INDICE_CSS}</style></head><body>
<header><h1>Vender arte en Nueva York</h1><p>Los apuntes del curso · Arte a la Mañana</p></header>
<main><ul>
{chr(10).join(filas)}
</ul></main>
<footer>Un apunte nuevo cada mañana, también por mail.</footer>
</body></html>"""
    open(f"{DST}/index.html", "w").write(html)
    print(f"[apunte] index.html con {len(filas)} apuntes")

def main():
    if not os.path.isdir(SRC):
        print("[apunte] sin carpeta de apuntes, nada que hacer"); return
    os.makedirs(DST, exist_ok=True)
    hoy = datetime.date.today().isoformat()
    hechos = 0
    for md in sorted(glob.glob(f"{SRC}/*.md")):
        fecha = os.path.basename(md).replace(".md", "")
        pdf = f"{DST}/{fecha}.pdf"
        if os.path.exists(pdf) and fecha != hoy:
            continue
        try:
            render(md, pdf)
            hechos += 1
        except Exception as e:
            print(f"[apunte] ERROR con {md}: {e}")
    if not hechos:
        print("[apunte] nada nuevo que renderizar")
    try:
        indice()
    except Exception as e:
        print(f"[apunte] ERROR con el índice: {e}")

if __name__ == "__main__":
    main()
