#!/usr/bin/env python3
"""
Genera los episodios del día de la familia "Arte a la Mañana":
  1) El debrief diario  : guion.txt        -> docs/episodios/FECHA.mp3  + docs/feed.xml
  2) El curso (separado): guion_curso.txt  -> docs/curso/episodios/FECHA.mp3 + docs/curso/feed.xml

Cada programa se genera SOLO si su archivo de títulos tiene entrada para HOY
(así un guion viejo nunca se publica con fecha nueva).

Uso: python3 generar_episodio.py
Requisitos: ffmpeg, pip install edge-tts mutagen
"""
import json, ssl, asyncio, subprocess, datetime, html, os, re, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
HOY = datetime.date.today().isoformat()


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


def reconstruir_feed(cfg, titulos_path, ep_dir, feed_path, ep_url_prefix, image_url, link_url):
    from mutagen.mp3 import MP3
    titulos = json.load(open(titulos_path))
    items = []
    for fecha in sorted(titulos.keys(), reverse=True):
        mp3 = f"{ep_dir}/{fecha}.mp3"
        if not os.path.exists(mp3):
            continue
        info = MP3(mp3)
        dur = int(info.info.length)
        size = os.path.getsize(mp3)
        d = datetime.datetime.fromisoformat(fecha + "T07:00:00-04:00")
        pub = d.strftime("%a, %d %b %Y %H:%M:%S %z")
        t = html.escape(titulos[fecha]["titulo"])
        desc = _descripcion_html(titulos[fecha]["descripcion"])
        url = f"{ep_url_prefix}/{fecha}.mp3"
        items.append(f"""    <item>
      <title>{t}</title>
      <description><![CDATA[{desc}]]></description>
      <pubDate>{pub}</pubDate>
      <enclosure url="{url}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{fecha}</guid>
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


def producir(nombre, config_file, guion_file, titulos_file, ep_subdir, feed_file, url_sub):
    cfg_path = f"{BASE}/{config_file}"
    guion_path = f"{BASE}/{guion_file}"
    titulos_path = f"{BASE}/{titulos_file}"
    if not (os.path.exists(cfg_path) and os.path.exists(guion_path) and os.path.exists(titulos_path)):
        print(f"[{nombre}] faltan archivos, salteado")
        return
    cfg = json.load(open(cfg_path))
    if cfg["base_url"].startswith("COMPLETAR"):
        sys.exit(f"[{nombre}] Editá {config_file} y poné tu base_url")
    base_url = cfg["base_url"].rstrip("/")
    titulos = json.load(open(titulos_path))
    ep_dir = f"{BASE}/docs/{ep_subdir}"
    os.makedirs(ep_dir, exist_ok=True)
    salida = f"{ep_dir}/{HOY}.mp3"
    if HOY in titulos:
        voz_tmp = f"{BASE}/voz_tmp_{nombre}.mp3"
        tts(cfg, guion_path, voz_tmp)
        if cfg.get("cortina"):
            mezclar(cfg, voz_tmp, salida)
        else:
            solo_voz(voz_tmp, salida)
        print(f"[{nombre}] episodio listo: {salida}")
    else:
        print(f"[{nombre}] sin entrada de HOY ({HOY}) en {titulos_file}: no genero audio nuevo")
    link_url = base_url if not url_sub else f"{base_url}/{url_sub}"
    ep_url_prefix = f"{base_url}/{ep_subdir}"
    image_url = f"{base_url}/portada.png" if not url_sub else f"{base_url}/{url_sub}/portada.png"
    reconstruir_feed(cfg, titulos_path, ep_dir, f"{BASE}/docs/{feed_file}",
                     ep_url_prefix, image_url, link_url)
    print(f"[{nombre}] feed reconstruido")


def producir_aislado(nombre, *args, intentos=3, espera=30):
    """Corre un programa con reintentos y sin que su caida arrastre al otro.

    Los dos podcasts son independientes: si la voz del debrief falla, el curso
    tiene que salir igual (y su PDF y su mail), y al reves tambien. Los
    reintentos son POR PROGRAMA, para que una falla pasajera de la voz no
    obligue a regenerar el que ya habia salido bien. Solo SystemExit se
    propaga, porque eso es un error de configuracion que hay que ver si o si.
    Devuelve True si el programa salio bien.
    """
    for i in range(1, intentos + 1):
        try:
            producir(nombre, *args)
            return True
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
        "episodios", "feed.xml", "")
    ok_curso = producir_aislado(
        "curso", "config_curso.json", "guion_curso.txt", "titulos_curso.json",
        "curso/episodios", "curso/feed.xml", "curso")

    if ok_debrief and ok_curso:
        print("Los dos programas se generaron bien")
    elif ok_debrief or ok_curso:
        # Uno de los dos quedo publicado. Salimos con 0 a proposito para que el
        # workflow siga: hay que renderizar el PDF, commitear docs/ y mandar el
        # mail de lo que SI se genero. El fallo queda visible en el log.
        caido = "curso" if ok_debrief else "debrief"
        print(f"AVISO: fallo el {caido}, el otro programa sigue su curso normal")
    else:
        sys.exit("Fallaron los dos programas")
