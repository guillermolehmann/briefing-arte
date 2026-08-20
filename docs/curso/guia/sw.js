/* Service worker de las guías de estudio.
   Estrategia deliberadamente conservadora: se sirve lo guardado para que abra
   al instante y sin señal, y en paralelo se pide la versión de red y se
   guarda para la próxima. El nombre de la caché lleva la version del build,
   así que cada corrida diaria crea una caché nueva y borra las viejas.
   skipWaiting y clients.claim hacen que la versión nueva tome el control
   enseguida, que es lo que evita quedarse pegado en una versión vieja. */
const VERSION = '2026-08-20-771c6f81';
const CACHE = 'guias-' + VERSION;
const PRECARGA = ["./", "index.html", "manifest.webmanifest", "icono-180.png", "icono-192.png", "2026-08-08.html", "2026-08-09.html", "2026-08-10.html", "2026-08-11-en.html", "2026-08-11.html", "2026-08-12-en.html", "2026-08-12.html", "2026-08-13-en.html", "2026-08-13.html", "2026-08-14-en.html", "2026-08-14.html", "2026-08-15-en.html", "2026-08-15.html", "2026-08-16-en.html", "2026-08-16.html", "2026-08-17-en.html", "2026-08-17.html", "2026-08-18-en.html", "2026-08-18.html", "2026-08-19-en.html", "2026-08-19.html", "2026-08-20-en.html", "2026-08-20.html", "examen-semana-01.html", "examen-semana-02.html", "practica.html", "semana-01.html", "semana-02.html"];

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
