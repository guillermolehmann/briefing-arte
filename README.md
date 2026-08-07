# Arte a la Mañana — podcast privado

Pipeline que genera un episodio diario de audio y lo publica como feed RSS
suscribible desde Apple Podcasts / Overcast / Pocket Casts.

## Puesta en marcha (una sola vez)
1. Subí todo el contenido de esta carpeta a un repo de GitHub.
2. En el repo: Settings → Pages → Source: "Deploy from a branch" →
   Branch: main, carpeta /docs → Save. Anotá la URL que te da
   (https://TU-USUARIO.github.io/NOMBRE-DEL-REPO).
3. Editá config.json y pegá esa URL en "base_url".
4. En claude.ai/code/scheduled creá una tarea diaria (ej. 6:30 AM, hora de NY)
   apuntando a este repo, con el contenido de PROMPT.md como prompt.
5. Tras la primera corrida, el feed queda en BASE_URL/feed.xml.
   Ese es el link que se suscribe en la app de podcasts.

## Estructura
- generar_episodio.py — guion → voz → mezcla con cortina → mp3 + feed
- config.json — título, voz, velocidad, volumen de cama, base_url
- PROMPT.md — prompt maestro de la tarea programada
- memoria/programa.md — memoria entre episodios (continuidad del programa)
- titulos.json — título y descripción por episodio (alimenta el feed)
- musica/cortina.mp3 — cortina ("Airport Lounge", Kevin MacLeod, CC-BY, incompetech.com)
- docs/ — lo que publica GitHub Pages: feed.xml, portada.png, episodios/
