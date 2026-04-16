/* =====================================================================
   CORE JAVASCRIPT ENGINE - Student Drive (Upgraded)
   ===================================================================== */

// --- 1. PWA & Service Worker Registration ---
let deferredPrompt; // Store the browser's install event for later use

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => {
                console.log('✅ Service Worker רשום בהצלחה!', reg);
            })
            .catch(err => {
                console.error('❌ רישום ה-SW נכשל:', err);
            });
    });
}

// Listen for the event fired when the browser decides the site is installable
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the browser from showing the built-in install banner immediately
    e.preventDefault();
    deferredPrompt = e;
    console.log('🚀 האתר מוכן להתקנה כ-PWA!');
});

// --- 2. Loading Bar & Page Transitions ---
window.addEventListener('load', () => {
    const loader = document.getElementById('loading-bar');
    if (loader) {
        loader.style.width = '100%';
        setTimeout(() => { loader.style.opacity = '0'; }, 300);
    }
});

// Start the loading bar when navigating through regular links
document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && link.href && !link.target && !link.href.includes('#') && !link.href.startsWith('javascript:')) {
        const loader = document.getElementById('loading-bar');
        if (loader) {
            loader.style.opacity = '1';
            loader.style.width = '30%';
        }
    }
});

// --- 3. Advanced Theme Management ---
function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme_preference', theme);
}

// Keep the theme in sync with the OS when the preference is `auto`
const themeQuery = window.matchMedia('(prefers-color-scheme: dark)');
function handleThemeChange(e) {
    if (localStorage.getItem('theme_preference') === 'auto') {
        setTheme('auto');
    }
}
themeQuery.addListener(handleThemeChange);

// --- 4. Accessibility & UI Init ---
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap toasts
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.map(toastEl => new bootstrap.Toast(toastEl).show());

    // Accessibility menu controls
    const a11yToggle = document.getElementById('a11y-toggle');
    const a11yMenu = document.getElementById('a11y-menu');
    const a11yClose = document.getElementById('a11y-close');

    if (a11yToggle && a11yMenu) {
        a11yToggle.addEventListener('click', () => a11yMenu.classList.toggle('d-none'));
    }
    if (a11yClose && a11yMenu) {
        a11yClose.addEventListener('click', () => a11yMenu.classList.add('d-none'));
    }

    // Load saved accessibility preferences
    ['a11y-large-text', 'a11y-high-contrast', 'a11y-highlight-links', 'a11y-readable-font'].forEach(cls => {
        if(localStorage.getItem(cls) === 'true') document.body.classList.add(cls);
    });
});

function toggleA11y(className) {
    document.body.classList.toggle(className);
    localStorage.setItem(className, document.body.classList.contains(className));
}

// --- 5. Security & AJAX Helpers ---
function getCookie(name) {
    if (name === 'csrftoken') {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) return tokenElement.value;
    }
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function secureFetch(url, options = {}) {
    options.headers = {
        ...options.headers,
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
    };
    return fetch(url, options);
}

// --- 6. Interaction Logic (Likes, Comments, Folders) ---

// Toggle a like on a document
function toggleLike(event, buttonElement) {
    event.preventDefault();
    const url = buttonElement.getAttribute('data-url');

    secureFetch(url, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.error) return;
        const countSpan = buttonElement.querySelector('.like-count');
        if(countSpan) countSpan.textContent = data.total_likes;
        buttonElement.classList.toggle('btn-primary', data.liked);
        buttonElement.classList.toggle('text-white', data.liked);
        buttonElement.classList.toggle('btn-outline-primary', !data.liked);
    });
}

// Toggle a like on a community post
function handlePostLike(postId, btn) {
    secureFetch(`/post/${postId}/like/`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        const countSpan = btn.querySelector('.like-count');
        const icon = btn.querySelector('i');
        countSpan.innerText = data.total_likes;
        btn.classList.toggle('text-primary', data.liked);
        btn.classList.toggle('fw-bold', data.liked);
        icon.className = data.liked ? 'fas fa-thumbs-up fs-5' : 'far fa-thumbs-up fs-5';
    });
}

// Comment interactions
function toggleComments(postId) {
    const section = document.getElementById(`comments-section-${postId}`);
    if (section) {
        section.classList.toggle('d-none');
        const list = document.getElementById(`comments-list-${postId}`);
        list.scrollTop = list.scrollHeight;
    }
}

function submitComment(postId) {
    const input = document.getElementById(`comment-input-${postId}`);
    const text = input.value.trim();
    if (!text) return;

    const btn = input.nextElementSibling;
    btn.disabled = true;

    const formData = new FormData();
    formData.append('text', text);

    secureFetch(`/post/${postId}/comment/`, { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const list = document.getElementById(`comments-list-${postId}`);
            const html = `
                <div class="d-flex gap-2 mb-2 animate__animated animate__fadeInUp">
                    <div class="flex-shrink-0">
                        ${data.user_img ? `<img src="${data.user_img}" class="rounded-circle" style="width:32px; height:32px; object-fit:cover;">` : `<div class="rounded-circle bg-light d-flex align-items-center justify-content-center border" style="width:32px; height:32px;"><i class="fas fa-user text-muted small"></i></div>`}
                    </div>
                    <div class="p-2 rounded-4 px-3 flex-grow-1" style="background-color: var(--gd-bg); border: 1px solid var(--gd-border);">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-bold small text-primary">${data.username}</span>
                            <span class="text-muted" style="font-size:0.65rem;">${data.created_at}</span>
                        </div>
                        <p class="small mb-0">${data.text}</p>
                    </div>
                </div>`;
            list.insertAdjacentHTML('beforeend', html);
            list.scrollTop = list.scrollHeight;
            input.value = '';
            const countLabel = document.getElementById(`comment-count-${postId}`);
            countLabel.innerText = parseInt(countLabel.innerText) + 1;
        }
    }).finally(() => btn.disabled = false);
}

// --- 7. AI Summary (Integrated with Wallet) ---
function generateAISummary(docId, btn) {
    const container = document.getElementById(`ai-summary-container-${docId}`);
    const textDiv = container.querySelector('.summary-text');
    const originalHtml = btn.innerHTML;

    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> חושב...';
    btn.disabled = true;

    secureFetch(`/document/${docId}/ai-summary/`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            textDiv.innerText = data.summary;
            new bootstrap.Collapse(container, { toggle: false }).show();
            // Update the navbar wallet immediately if the server returns a new coin balance
            const walletSpan = document.querySelector('.fa-coins + span');
            if (walletSpan && data.new_coins !== undefined) {
                walletSpan.innerText = data.new_coins;
            }
        } else {
            alert("שגיאה: " + data.error);
        }
    })
    .catch(() => alert("שגיאה בתקשורת מול השרת."))
    .finally(() => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
    });
}

// --- 8. Google Translate & Cleanup ---
function googleTranslateElementInit() {
    new google.translate.TranslateElement({ pageLanguage: 'he', autoDisplay: false }, 'google_translate_element');
}

function doGTranslate(lang_pair) {
    const lang = lang_pair.split('|')[1];
    document.cookie = `googtrans=/he/${lang}; path=/; domain=${window.location.hostname}`;
    if (lang === 'he') {
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        location.reload();
    } else {
        location.reload();
    }
}
