// שינינו ל-v2 כדי שהדפדפן יזהה שהקובץ הזה (ה-Service Worker) השתנה ויתחיל את תהליך העדכון
const CACHE_NAME = 'student-drive-v2';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.json'
];

// --- קסם 1: התקנה ודילוג על תור ההמתנה ---
self.addEventListener('install', event => {
  self.skipWaiting(); // מכריח את האפליקציה באייפד להתעדכן מיד, בלי לחכות שהמשתמש יסגור אותה לחלוטין!
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

// --- קסם 2: הפעלה וניקוי זבל ישן ---
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          // אם מצאנו קאש ישן (כמו v1) - אנחנו מוחקים אותו
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim(); // לוקח פיקוד על המסך הפתוח מיד
});

// --- קסם 3: עדכון אוטומטי ואילם ברקע (Network First + Cache Update) ---
self.addEventListener('fetch', event => {
  // בקשות POST (לייק, מחיקה, התחברות) הולכות ישר לשרת
  if (event.request.method !== 'GET') {
      return;
  }

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // אם יש אינטרנט והשרת החזיר תשובה טובה (כמו קובץ CSS חדש),
        // אנחנו גם מציגים אותה למשתמש וגם שומרים אותה מיד בקאש לעתיד (לאופליין)!
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone));
        return response;
      })
      .catch(() => {
        // אם אין אינטרנט או שהשרת נפל, נשלוף את מה ששמרנו בקאש (אופליין מוד)
        return caches.match(event.request);
      })
  );
});