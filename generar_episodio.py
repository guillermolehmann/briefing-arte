#!/usr/bin/env python3
"""
Genera el episodio del día de "Arte a la Mañana":
guion.txt -> voz (edge-tts) -> mezcla con cortina (ffmpeg) -> docs/episodios/FECHA.mp3
y reconstruye el feed RSS completo (docs/feed.xml) a partir de titulos.json.

Uso: python3 generar_episodio.py
Requisitos: ffmpeg, pip install edge-tts mutagen
"""
import json, ssl, asyncio, subprocess, datetime, html, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{BASE}/config.json"))
HOY = datetime.date.today().isoformat()
VOZ_TMP = f"{BASE}/voz_tmp.mp3"
CAMA_TMP = f"{BASE}/cama_tmp.wav"
SALIDA = f"{BASE}/docs/episodios/{HOY}.mp3"


def tts():
    import edge_tts
    import edge_tts.communicate as comm
    try:
        # Algunos entornos interceptan TLS con certificado propio
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        comm._SSL_CTX = ctx
    except Exception:
        pass

    async def run():
        text = open(f"{BASE}/guion.txt").read()
        t = edge_tts.Communicate(text, voice=CFG["voz"], rate=CFG["velocidad"])
        await t.save(VOZ_TMP)

    asyncio.run(run())


def mezclar():
    from mutagen.mp3 import MP3
    dur = MP3(VOZ_TMP).info.length
    entrada_voz = 5.5
    fin_voz = entrada_voz + dur
    sube = fin_voz - 2
    total = fin_voz + 12
    fade = total - 6
    vol_cama = CFG.get("volumen_cama", 0.15)
    vol_expr = (
        f"if(lt(t,4.5),0.95, if(lt(t,6.5), 0.95-{0.95 - vol_cama}*(t-4.5)/2, "
        f"if(lt(t,{sube:.1f}),{vol_cama}, if(lt(t,{sube + 2:.1f}),"
        f"{vol_cama}+0.65*(t-{sube:.1f})/2, 0.8))))"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1",
         "-t", f"{total:.1f}", "-i", f"{BASE}/{CFG['cortina']}",
         "-af", f"volume='{vol_expr}':eval=frame,afade=t=out:st={fade:.1f}:d=6",
         CAMA_TMP], check=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", CAMA_TMP, "-i", VOZ_TMP,
         "-filter_complex",
         "[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];"
         "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,"
         "adelay=5500|5500[a1];"
         "[a0][a1]amix=inputs=2:duration=longest:normalize=0,"
         "loudnorm=I=-16:TP=-1.5[out]",
         "-map", "[out]", "-b:a", "128k", SALIDA], check=True)
    os.remove(VOZ_TMP)
    os.remove(CAMA_TMP)


def reconstruir_feed():
    from mutagen.mp3 import MP3
    base_url = CFG["base_url"].rstrip("/")
    titulos = json.load(open(f"{BASE}/titulos.json"))
    items = []
    for fecha in sorted(titulos.keys(), reverse=True):
        mp3 = f"{BASE}/docs/episodios/{fecha}.mp3"
        if not os.path.exists(mp3):
            continue
        info = MP3(mp3)
        dur = int(info.info.length)
        size = os.path.getsize(mp3)
        d = datetime.datetime.fromisoformat(fecha + "T07:00:00-04:00")
        pub = d.strftime("%a, %d %b %Y %H:%M:%S %z")
        t = html.escape(titulos[fecha]["titulo"])
        desc = html.escape(titulos[fecha]["descripcion"])
        url = f"{base_url}/episodios/{fecha}.mp3"
        items.append(f"""    <item>
      <title>{t}</title>
      <description>{desc}</description>
      <pubDate>{pub}</pubDate>
      <enclosure url="{url}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{fecha}</guid>
      <itunes:duration>{dur}</itunes:duration>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{html.escape(CFG['titulo'])}</title>
    <description>{html.escape(CFG['descripcion'])}</description>
    <language>es</language>
    <link>{base_url}</link>
    <itunes:image href="{base_url}/portada.png"/>
    <itunes:author>{html.escape(CFG['autor'])}</itunes:author>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
"""
    open(f"{BASE}/docs/feed.xml", "w").write(feed)


if __name__ == "__main__":
    if CFG["base_url"].startswith("COMPLETAR"):
        sys.exit("Editá config.json y poné tu base_url de GitHub Pages")
    tts()
    mezclar()
    reconstruir_feed()
    print(f"Episodio listo: {SALIDA}")
