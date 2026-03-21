const CACHE_NAME = 'student-drive-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// --- כאן השינוי המרכזי ---
self.addEventListener('fetch', event => {
  // אם זו בקשת POST (כמו מחיקה או לייק), אל תנסה לטפל בה בקאש - שלח אותה ישר לשרת
  if (event.request.method !== 'GET') {
      return;
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});