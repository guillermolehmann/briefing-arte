#!/usr/bin/env python3
"""
Genera los episodios del día de la familia "Arte a la Mañana":
  1) El debrief diario  : guion.txt        -> docs/episodios/FECHA.mp3  + docs/feed.xml
  2) El curso (separado): guion_curso.txt  -> docs/curso/episodios/FECHA.mp3 + docs/curso/feed.xml

Desde agosto de 2026 cada programa entrega DOS episodios por día, uno en
español y otro en inglés, y los dos viajan en el MISMO feed:
  guion.txt        -> docs/episodios/FECHA.mp3
  guion_en.txt     -> docs/episodios/FECHA-en.mp3
  guion_curso.txt  -> docs/curso/episodios/FECHA.mp3
  guion_curso_en.txt -> docs/curso/episodios/FECHA-en.mp3

Cada episodio se genera SOLO si su clave está en el archivo de títulos
(FECHA para el español, FECHA-en para el inglés), así un guion viejo nunca se
publica con fecha nueva. Las dos versiones son independientes: si falla la voz
en inglés, la de español sale igual, y al revés también.

Uso: python3 generar_episodio.py
Requisitos: ffmpeg, pip install edge-tts mutagen
"""
import json, ssl, asyncio, subprocess, datetime, html, os, re, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
HOY = datetime.date.today().isoformat()

# Sufijo de la clave -> (hora de publicación, etiqueta que se antepone al título).
# El español sale 07:05 y el inglés 07:00 para que en la app la versión en
# español quede arriba y, si Virginia sigue escuchando de corrido, la que sigue
# sea la misma lección en inglés.
VARIANTES_META = {
    "":    ("07:05:00", ""),
    "-en": ("07:00:00", "(EN) "),
}


def tts(cfg, guion_path, voz_tmp):
    import edge_tts
    import edge_tts.communicate as comm
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        comm._SSL_CTX = ctx
    except Exception:
        pass

    async def run():
        text = open(guion_path).read()
        t = edge_tts.Communicate(text, voice=cfg["voz"], rate=cfg["velocidad"])
        await t.save(voz_tmp)

    asyncio.run(run())


def solo_voz(voz_tmp, salida):
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", voz_tmp,
         "-af", "aformat=sample_rates=44100:channel_layouts=stereo,"
                "adelay=400|400,apad=pad_dur=1.2,loudnorm=I=-16:TP=-1.5",
         "-b:a", "128k", salida], check=True)
    os.remove(voz_tmp)


def mezclar(cfg, voz_tmp, salida):
    from mutagen.mp3 import MP3
    cama_tmp = salida + ".cama.wav"
    dur = MP3(voz_tmp).info.length
    entrada_voz = 5.5
    fin_voz = entrada_voz + dur
    sube = fin_voz - 2
    total = fin_voz + 12
    fade = total - 6
    vol_cama = cfg.get("volumen_cama", 0.15)
    vol_expr = (
        f"if(lt(t,4.5),0.95, if(lt(t,6.5), 0.95-{0.95 - vol_cama}*(t-4.5)/2, "
        f"if(lt(t,{sube:.1f}),{vol_cama}, if(lt(t,{sube + 2:.1f}),"
        f"{vol_cama}+0.65*(t-{sube:.1f})/2, 0.8))))"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1",
         "-t", f"{total:.1f}", "-i", f"{BASE}/{cfg['cortina']}",
         "-af", f"volume='{vol_expr}':eval=frame,afade=t=out:st={fade:.1f}:d=6",
         cama_tmp], check=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", cama_tmp, "-i", voz_tmp,
         "-filter_complex",
         "[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];"
         "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,"
         "adelay=5500|5500[a1];"
         "[a0][a1]amix=inputs=2:duration=longest:normalize=0,"
         "loudnorm=I=-16:TP=-1.5[out]",
         "-map", "[out]", "-b:a", "128k", salida], check=True)
    os.remove(voz_tmp)
    os.remove(cama_tmp)


_URL_RE = re.compile(r'(https?://[^\s<>"\')\]]+)')


def _descripcion_html(texto):
    """Descripcion para <description>: viaja dentro de CDATA y con las URLs
    convertidas en links clickeables en la app de podcasts. Dentro de CDATA no
    se escapa nada, solo hay que cortar un cierre accidental de la seccion."""
    t = texto.replace("]]>", "]]&gt;")

    def _a(m):
        u = m.group(1)
        return '<a href="{}">{}</a>'.format(u.replace("&", "&amp;"), u)

    return _URL_RE.sub(_a, t)


def _partir_clave(clave):
    """'2026-08-10-en' -> ('2026-08-10', '-en'). '2026-08-10' -> (fecha, '')."""
    fecha, sufijo = clave[:10], clave[10:]
    return fecha, sufijo


def reconstruir_feed(cfg, titulos_path, ep_dir, feed_path, ep_url_prefix, image_url, link_url):
    from mutagen.mp3 import MP3
    titulos = json.load(open(titulos_path))
    entradas = []
    for clave in titulos:
        fecha, sufijo = _partir_clave(clave)
        if sufijo not in VARIANTES_META:
            print(f"[feed] clave desconocida, la salteo: {clave}")
            continue
        mp3 = f"{ep_dir}/{clave}.mp3"
        if not os.path.exists(mp3):
            continue
        hora, etiqueta = VARIANTES_META[sufijo]
        try:
            d = datetime.datetime.fromisoformat(f"{fecha}T{hora}-04:00")
        except ValueError:
            print(f"[feed] fecha invalida, la salteo: {clave}")
            continue
        entradas.append((d, clave, mp3, etiqueta))
    # Más nuevo primero. Con la misma fecha, el español queda arriba porque su
    # hora de publicación es posterior a la del inglés.
    entradas.sort(key=lambda e: e[0], reverse=True)

    items = []
    for d, clave, mp3, etiqueta in entradas:
        info = MP3(mp3)
        dur = int(info.info.length)
        size = os.path.getsize(mp3)
        pub = d.strftime("%a, %d %b %Y %H:%M:%S %z")
        titulo = titulos[clave]["titulo"]
        # La etiqueta la pone el generador y no el guionista: una regla escrita
        # en el PROMPT se puede desobedecer, esto no.
        if etiqueta and not titulo.startswith(etiqueta.strip()):
            titulo = etiqueta + titulo
        t = html.escape(titulo)
        desc = _descripcion_html(titulos[clave]["descripcion"])
        url = f"{ep_url_prefix}/{clave}.mp3"
        items.append(f"""    <item>
      <title>{t}</title>
      <description><![CDATA[{desc}]]></description>
      <pubDate>{pub}</pubDate>
      <enclosure url="{url}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{clave}</guid>
      <itunes:duration>{dur}</itunes:duration>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{html.escape(cfg['titulo'])}</title>
    <description>{html.escape(cfg['descripcion'])}</description>
    <language>es</language>
    <link>{link_url}</link>
    <itunes:image href="{image_url}"/>
    <itunes:author>{html.escape(cfg['autor'])}</itunes:author>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
"""
    open(feed_path, "w").write(feed)


def _audio_de_variante(nombre, cfg, guion_path, salida, intentos=3, espera=30):
    """Genera el audio de UNA variante con reintentos propios.

    Las dos variantes de un mismo programa son independientes: que falle la voz
    en ingles no puede dejar sin episodio a la version en espanol.
    """
    token = re.sub(r"[^A-Za-z0-9_-]", "_", nombre)
    for i in range(1, intentos + 1):
        try:
            voz_tmp = f"{BASE}/voz_tmp_{token}.mp3"
            tts(cfg, guion_path, voz_tmp)
            if cfg.get("cortina"):
                mezclar(cfg, voz_tmp, salida)
            else:
                solo_voz(voz_tmp, salida)
            print(f"[{nombre}] episodio listo: {salida}")
            return True
        except Exception as e:
            print(f"[{nombre}] intento {i} de {intentos} fallo: {e}")
            if i < intentos:
                time.sleep(espera)
    print(f"[{nombre}] ERROR: fallaron los {intentos} intentos")
    return False


def producir(nombre, config_file, guion_file, titulos_file, ep_subdir, feed_file, url_sub,
             config_en_file=None, guion_en_file=None):
    cfg_path = f"{BASE}/{config_file}"
    guion_path = f"{BASE}/{guion_file}"
    titulos_path = f"{BASE}/{titulos_file}"
    if not (os.path.exists(cfg_path) and os.path.exists(guion_path) and os.path.exists(titulos_path)):
        print(f"[{nombre}] faltan archivos, salteado")
        return False
    cfg = json.load(open(cfg_path))
    if cfg["base_url"].startswith("COMPLETAR"):
        sys.exit(f"[{nombre}] Editá {config_file} y poné tu base_url")
    base_url = cfg["base_url"].rstrip("/")
    titulos = json.load(open(titulos_path))
    ep_dir = f"{BASE}/docs/{ep_subdir}"
    os.makedirs(ep_dir, exist_ok=True)

    # Variante en español (siempre) y variante en inglés (si están sus archivos).
    variantes = [("", cfg, guion_path)]
    if config_en_file and guion_en_file:
        cfg_en_path = f"{BASE}/{config_en_file}"
        guion_en_path = f"{BASE}/{guion_en_file}"
        if os.path.exists(cfg_en_path) and os.path.exists(guion_en_path):
            cfg_en = dict(cfg)          # hereda titulo, base_url y demás
            cfg_en.update(json.load(open(cfg_en_path)))   # pisa voz, velocidad, cortina
            variantes.append(("-en", cfg_en, guion_en_path))
        else:
            print(f"[{nombre}] sin archivos en inglés todavía, sigo solo con español")

    todo_bien = True
    for sufijo, cfg_v, guion_v in variantes:
        clave = HOY + sufijo
        etiqueta = "en" if sufijo else "es"
        if clave not in titulos:
            print(f"[{nombre}/{etiqueta}] sin entrada de {clave} en {titulos_file}: no genero audio nuevo")
            continue
        if not _audio_de_variante(f"{nombre}/{etiqueta}", cfg_v, guion_v, f"{ep_dir}/{clave}.mp3"):
            todo_bien = False

    link_url = base_url if not url_sub else f"{base_url}/{url_sub}"
    ep_url_prefix = f"{base_url}/{ep_subdir}"
    # El nombre lleva version a proposito. Las apps de podcast guardan la
    # portada POR DIRECCION y no la revisan por dias, asi que cambiar el
    # archivo sin cambiarle el nombre no las hace bajar la nueva. Si algun dia
    # se rediseña la portada, hay que subirla con un nombre nuevo y cambiarlo
    # aca, o Apple sigue mostrando la vieja durante semanas.
    PORTADA = "portada-2026.png"
    image_url = f"{base_url}/{PORTADA}" if not url_sub else f"{base_url}/{url_sub}/{PORTADA}"
    reconstruir_feed(cfg, titulos_path, ep_dir, f"{BASE}/docs/{feed_file}",
                     ep_url_prefix, image_url, link_url)
    print(f"[{nombre}] feed reconstruido")
    return todo_bien


def producir_aislado(nombre, *args, intentos=3, espera=30, **kwargs):
    """Corre un programa con reintentos y sin que su caida arrastre al otro.

    Los dos podcasts son independientes: si la voz del debrief falla, el curso
    tiene que salir igual (y su PDF y su mail), y al reves tambien. Los
    reintentos del AUDIO ya son por variante (ver _audio_de_variante); estos
    cubren el resto del proceso, sobre todo la reconstruccion del feed. Solo
    SystemExit se propaga, porque eso es un error de configuracion que hay que
    ver si o si. Devuelve True si el programa salio bien.
    """
    for i in range(1, intentos + 1):
        try:
            # producir ya reintenta el audio por variante; lo que puede devolver
            # False es que algun episodio del dia no haya salido, y eso no se
            # arregla repitiendo todo de nuevo.
            return producir(nombre, *args, **kwargs)
        except SystemExit:
            raise
        except Exception as e:
            print(f"[{nombre}] intento {i} de {intentos} fallo: {e}")
            if i < intentos:
                time.sleep(espera)
    print(f"[{nombre}] ERROR: fallaron los {intentos} intentos")
    return False


if __name__ == "__main__":
    ok_debrief = producir_aislado(
        "debrief", "config.json", "guion.txt", "titulos.json",
        "episodios", "feed.xml", "",
        config_en_file="config_en.json", guion_en_file="guion_en.txt")
    ok_curso = producir_aislado(
        "curso", "config_curso.json", "guion_curso.txt", "titulos_curso.json",
        "curso/episodios", "curso/feed.xml", "curso",
        config_en_file="config_curso_en.json", guion_en_file="guion_curso_en.txt")

    if ok_debrief and ok_curso:
        print("Todos los episodios del dia se generaron bien")
    elif ok_debrief or ok_curso:
        # Algo quedo sin publicar, pero no todo. Salimos con 0 a proposito para
        # que el workflow siga: hay que renderizar los PDF, commitear docs/ y
        # mandar los mails de lo que SI se genero. Cual episodio falto queda
        # arriba en el log, con la linea [programa/idioma].
        flojo = "curso" if ok_debrief else "debrief"
        print(f"AVISO: al {flojo} le falto algun episodio del dia (mirar las lineas de arriba). "
              f"El resto sigue su curso normal")
    else:
        sys.exit("No se genero ningun episodio de ningun programa")
