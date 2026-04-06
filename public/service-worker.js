// 1. UPDATE THIS VERSION NUMBER every time you make a big change!
const STATIC_CACHE_VERSION = 'v1.5'; 
const DYNAMIC_CACHE_VERSION = 'v1.5';
const STATIC_CACHE_NAME = `maai-static-${STATIC_CACHE_VERSION}`;
const DYNAMIC_CACHE_NAME = `maai-dynamic-${DYNAMIC_CACHE_VERSION}`;

const STATIC_ASSETS = [
    '/offline.html',
];

// These will ALWAYS be fetched from the internet, never from cache
const NETWORK_FIRST_EXTENSIONS = ['.html', '.js', '.css'];

// --- Install: Cache static images only ---
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting()) // FORCE the new worker to take over immediately
    );
});

// --- Activate: WIPE OLD CACHES IMMEDIATELY ---
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== STATIC_CACHE_NAME && key !== DYNAMIC_CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim()) // Take control of all open tabs immediately
    );
});

// --- Fetch Logic ---
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // UPGRADE A: NEVER cache API calls or Auth requests
    if (url.pathname.startsWith('/api/') || request.headers.has('Authorization')) {
        return event.respondWith(fetch(request));
    }

    const isNetworkFirst = NETWORK_FIRST_EXTENSIONS.some(ext => url.pathname.endsWith(ext)) || url.pathname === '/';

    if (isNetworkFirst) {
        // Network-first for HTML/JS/CSS — always try to get the freshest version
        event.respondWith(
            fetch(request)
                .then(networkResponse => {
                    // Only cache successful responses
                    if (networkResponse && networkResponse.status === 200) {
                        const clone = networkResponse.clone();
                        caches.open(DYNAMIC_CACHE_NAME).then(cache => cache.put(request, clone));
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    // BUG FIX: caches.match() returns a Promise — must await before ||
                    // Old code: caches.match(request) || caches.match('/offline.html')
                    // That always resolved to the FIRST promise regardless of result.
                    const cached = await caches.match(request);
                    if (cached) return cached;
                    // For navigation requests (page loads), show offline page
                    if (request.mode === 'navigate') {
                        return caches.match('/offline.html');
                    }
                    // For other requests (JS/CSS), just fail gracefully
                    return new Response('', { status: 408, statusText: 'Network timeout' });
                })
        );
    } else {
        // Cache-First for images/logos to keep things fast
        event.respondWith(
            caches.match(request).then(cached => cached || fetch(request).catch(() => new Response('', { status: 408 })))
        );
    }
});