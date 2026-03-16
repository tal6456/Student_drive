/* =====================================================================
   MAIN JAVASCRIPT ENGINE - Student Drive
   ===================================================================== */

// 1. Loading Bar & Toasts & A11y Menu
window.addEventListener('beforeunload', () => {
    const loader = document.getElementById('loading-bar');
    if (loader) loader.style.width = '100%';
});

document.addEventListener('DOMContentLoaded', function() {
    // אתחול Toast של Bootstrap
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    const toastList = toastElList.map(function(toastEl) { return new bootstrap.Toast(toastEl); });
    toastList.forEach(toast => toast.show());

    // תפריט נגישות
    const a11yToggle = document.getElementById('a11y-toggle');
    const a11yMenu = document.getElementById('a11y-menu');
    const a11yClose = document.getElementById('a11y-close');

    if (a11yToggle && a11yMenu) {
        a11yToggle.addEventListener('click', () => {
            a11yMenu.classList.toggle('d-none');
        });
    }
    if (a11yClose && a11yMenu) {
        a11yClose.addEventListener('click', () => {
            a11yMenu.classList.add('d-none');
        });
    }
});

function toggleA11y(className) {
    document.body.classList.toggle(className);
    localStorage.setItem(className, document.body.classList.contains(className));
}

window.addEventListener('load', function() {
    ['a11y-large-text', 'a11y-high-contrast', 'a11y-highlight-links', 'a11y-readable-font'].forEach(cls => {
        if(localStorage.getItem(cls) === 'true') document.body.classList.add(cls);
    });
});

// 2. CSRF Token Helper
function getCookie(name) {
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

// 3. Document Like Toggle
function toggleLike(event, buttonElement) {
    event.preventDefault();
    const url = buttonElement.getAttribute('data-url');
    const csrftoken = getCookie('csrftoken');

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error(data.error);
            return;
        }

        const countSpan = buttonElement.querySelector('.like-count');
        if(countSpan) countSpan.textContent = data.total_likes;

        if (data.liked) {
            buttonElement.classList.remove('btn-outline-primary');
            buttonElement.classList.add('btn-primary', 'text-white');
        } else {
            buttonElement.classList.remove('btn-primary', 'text-white');
            buttonElement.classList.add('btn-outline-primary');
        }
    })
    .catch(error => console.error('Error:', error));
}

// 4. Google Translate Engine
function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'he',
        autoDisplay: false
    }, 'google_translate_element');
}

function doGTranslate(lang_pair) {
    const lang = lang_pair.split('|')[1];
    const teCombo = document.querySelector('.goog-te-combo');

    const domain = window.location.hostname;
    document.cookie = "googtrans=/he/" + lang + "; path=/";
    document.cookie = "googtrans=/he/" + lang + "; domain=" + domain + "; path=/";

    if (teCombo) {
        teCombo.value = lang;
        teCombo.dispatchEvent(new Event('change', { bubbles: true }));
    }

    if (lang === 'he') {
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        location.reload();
    }
}

(function() {
    const checkInterval = setInterval(() => {
        const teCombo = document.querySelector('.goog-te-combo');
        const cookieValue = document.cookie.split('; ').find(row => row.startsWith('googtrans='));

        if (teCombo && cookieValue) {
            const savedLang = cookieValue.split('/')[2];
            if (teCombo.value !== savedLang) {
                teCombo.value = savedLang;
                teCombo.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }, 1000);
})();

setInterval(function() {
    const frame = document.querySelector('.goog-te-banner-frame');
    if (frame) frame.remove();
    document.body.style.top = "0px";
}, 500);