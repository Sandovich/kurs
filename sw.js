// Курс — офлайн-кэш. Оболочка: из кэша. Карта OSM/OpenSeaMap: что смотрели — сохраняется (по правилам OSM кэшировать просмотренное можно, массово скачивать нельзя).
// Яндекс не кэшируем: условия API это не разрешают явно. Погода: сначала сеть, без сети — последний ответ.
const V='kurs-v0.4.0', SHELL=['./','./index.html','./manifest.webmanifest','./icon.svg',
 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css','https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js','https://unpkg.com/protomaps-leaflet@5.1.0/dist/protomaps-leaflet.js'];
const TILES='kurs-tiles', WX='kurs-wx', MAPC='kurs-map', MAX_TILES=6000;
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('kurs-v')&&k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
async function trim(){const c=await caches.open(TILES),k=await c.keys();if(k.length>MAX_TILES)for(const r of k.slice(0,k.length-MAX_TILES))await c.delete(r)}
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);if(e.request.method!=='GET')return;
  if(/tile\.openstreetmap\.org|tiles\.openseamap\.org|tile\.opentopomap\.org/.test(u.host)){
    e.respondWith(caches.open(TILES).then(async c=>{const hit=await c.match(e.request);if(hit)return hit;
      try{const r=await fetch(e.request);if(r.ok){c.put(e.request,r.clone());trim()}return r}catch(err){return new Response('',{status:504})}}));return}
  if(/open-meteo\.com$/.test(u.host)){
    e.respondWith(fetch(e.request).then(r=>{if(r.ok){const cl=r.clone();caches.open(WX).then(c=>c.put(e.request,cl))}return r}).catch(()=>caches.open(WX).then(c=>c.match(e.request)).then(r=>r||Response.error())));return}
  if(u.origin===location.origin&&u.pathname.includes('/map/')){
    e.respondWith(caches.open(MAPC).then(async c=>{const hit=await c.match(e.request);if(hit)return hit;
      try{const r=await fetch(e.request);if(r.ok)c.put(e.request,r.clone());return r}catch(err){return new Response('',{status:504})}}));return}
  if(u.origin===location.origin||u.host==='cdnjs.cloudflare.com'||u.host==='unpkg.com'){
    e.respondWith(caches.match(e.request).then(hit=>{const net=fetch(e.request).then(r=>{if(r.ok&&u.origin===location.origin){const cl=r.clone();caches.open(V).then(c=>c.put(e.request,cl))}return r}).catch(()=>hit);return hit||net}))}
});
