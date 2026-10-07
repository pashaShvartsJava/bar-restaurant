const CACHE_NAME="marani-v1";
const STATIC_ASSETS=[
    "/",
    "/bar_name",
    "/manifest.json"
];

self.addEventListener("install",event=>{
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache=>cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener("activate",event=>{
    event.waitUntil(
        caches.keys().then(keys=>Promise.all(
            keys.filter(key=>key!==CACHE_NAME).map(key=>caches.delete(key))
        ))
    );
    self.clients.claim();
});

self.addEventListener("fetch",event=>{
    if(event.request.method!=="GET")return;
    const url=new URL(event.request.url);
    if(url.origin!==self.location.origin)return;
    if(url.pathname.startsWith("/api/")||url.pathname.startsWith("/orders")||url.pathname.startsWith("/payment")||url.pathname.startsWith("/ws/"))return;
    event.respondWith(
        fetch(event.request).catch(()=>caches.match(event.request))
    );
});
