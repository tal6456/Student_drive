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
// 2. Universal CSRF & Cookie Helper
function getCookie(name) {
    let cookieValue = null;

    // קסם ה-CSRF: שאיבה ישירה מה-HTML!
    if (name === 'csrftoken') {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            return tokenElement.value;
        }
    }

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
// 2.5 Global Secure Fetch (Auto-injects CSRF token)
function secureFetch(url, options = {}) {
    const csrfToken = getCookie('csrftoken');

    options.headers = {
        ...options.headers,
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
    };

    return fetch(url, options);
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


// הצגה/הסתרה של אזור התגובות
function toggleComments(postId) {
    const section = document.getElementById(`comments-section-${postId}`);
    if (section) {
        section.classList.toggle('d-none');
        // גלילה לסוף התגובות באופן אוטומטי כשפותחים
        const list = document.getElementById(`comments-list-${postId}`);
        list.scrollTop = list.scrollHeight;
    }
}

/* =====================================================================
   COMMUNITY AJAX - Likes & Comments (Using secureFetch)
   ===================================================================== */

// פונקציית הלייק לפוסטים בקהילה
function handlePostLike(postId, btn) {
    secureFetch(`/post/${postId}/like/`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) throw new Error("Server error or CSRF failed.");
        return response.json();
    })
    .then(data => {
        if (data.total_likes !== undefined) {
            const countSpan = btn.querySelector('.like-count');
            const icon = btn.querySelector('i');
            countSpan.innerText = data.total_likes;

            if (data.liked) {
                btn.classList.add('text-primary', 'fw-bold');
                btn.classList.remove('text-muted');
                icon.className = 'fas fa-thumbs-up fs-5';
            } else {
                btn.classList.remove('text-primary', 'fw-bold');
                btn.classList.add('text-muted');
                icon.className = 'far fa-thumbs-up fs-5';
            }
        }
    })
    .catch(err => console.error("Error liking post:", err));
}

// שליחת תגובה ב-AJAX
function submitComment(postId) {
    const input = document.getElementById(`comment-input-${postId}`);
    const text = input.value.trim();
    if (!text) return;

    const btn = input.nextElementSibling;
    btn.disabled = true;

    const formData = new FormData();
    formData.append('text', text);

    secureFetch(`/post/${postId}/comment/`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Server error or CSRF failed.");
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const list = document.getElementById(`comments-list-${postId}`);
            const commentHTML = `
                <div class="d-flex gap-2 mb-2 animate__animated animate__fadeInUp">
                    <div class="flex-shrink-0">
                        ${data.user_img ? `<img src="${data.user_img}" class="rounded-circle shadow-sm" style="width:32px; height:32px; object-fit:cover;">` : 
                        `<div class="rounded-circle bg-light d-flex align-items-center justify-content-center border shadow-sm" style="width:32px; height:32px;"><i class="fas fa-user text-muted small"></i></div>`}
                    </div>
                    <div class="p-2 rounded-4 px-3 flex-grow-1 shadow-sm" style="background-color: var(--gd-bg); border: 1px solid var(--gd-border);">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-bold small text-primary">${data.username}</span>
                            <span class="text-muted" style="font-size:0.65rem;">${data.created_at}</span>
                        </div>
                        <p class="small mb-0" style="color:var(--gd-text);">${data.text}</p>
                    </div>
                </div>`;
            list.insertAdjacentHTML('beforeend', commentHTML);
            list.scrollTop = list.scrollHeight;
            input.value = '';
            const countLabel = document.getElementById(`comment-count-${postId}`);
            countLabel.innerText = parseInt(countLabel.innerText) + 1;
        }
    })
    .catch(err => console.error("Error submitting comment:", err))
    .finally(() => btn.disabled = false);
}
//
// /* =====================================================================
//    AI FEATURES - Document Summarization
//    ===================================================================== */
//
// function generateAISummary(docId, btn) {
//     // 1. מציאת אלמנטים במסך
//     const container = document.getElementById(`ai-summary-container-${docId}`);
//     const textDiv = container.querySelector('.summary-text');
//
//     // 2. שמירת המצב המקורי של הכפתור ושינוי למצב "טעינה"
//     const originalHtml = btn.innerHTML;
//     btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> חושב...';
//     btn.disabled = true;
//
//     // 3. קריאה לשרת עם הנתיב המדויק מתוך urls.py שלך!
//     secureFetch(`/document/${docId}/ai-summary/`, {
//         method: 'POST'
//     })
//     .then(response => {
//         if (!response.ok) throw new Error("Server error");
//         return response.json();
//     })
//     .then(data => {
//         if (data.success) {
//             // הכל עבד! נציג את הסיכום
//             textDiv.innerText = data.summary;
//
//             // פתיחת חלונית הסיכום
//             const bsCollapse = new bootstrap.Collapse(container, {
//                 toggle: false
//             });
//             bsCollapse.show();
//
//         } else {
//             // השרת החזיר שגיאה (למשל: אין מספיק מטבעות)
//             alert("שגיאה: " + data.error);
//         }
//     })
//     .catch(err => {
//         console.error("Error generating AI summary:", err);
//         alert("אירעה שגיאה בתקשורת מול השרת. אנא נסה שוב.");
//     })
//     .finally(() => {
//         // 4. החזרת הכפתור למצב הרגיל
//         btn.innerHTML = originalHtml;
//         btn.disabled = false;
//     });
// }