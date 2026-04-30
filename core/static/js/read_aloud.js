/**
 * Read-Aloud Feature — Play · Pause/Resume · Stop
 * ================================================
 * Both Hebrew and English audio are generated server-side:
 *   Hebrew  → gTTS (Google TTS, MP3, ?lang=he)
 *   English → pyttsx3 (WAV, no lang param)
 *
 * Language preference is stored in localStorage per document.
 */

// ── state ────────────────────────────────────────────────────────────────

const _tts = {
    audio: null,   // HTMLAudioElement
    docId: null,
};

// ── language preference ──────────────────────────────────────────────────

function raGetLang(docId) {
    return localStorage.getItem(`ra_lang_${docId}`) || 'he';
}

function raSetLang(docId, lang) {
    localStorage.setItem(`ra_lang_${docId}`, lang);
    const btn = document.getElementById(`ra-lang-${docId}`);
    if (btn) btn.innerHTML = lang === 'he'
        ? '<i class="fas fa-globe me-1"></i>עברית'
        : '<i class="fas fa-globe me-1"></i>English';
}

function raToggleLang(docId) {
    if (_tts.docId === docId) _stopCurrent();
    raSetLang(docId, raGetLang(docId) === 'he' ? 'en' : 'he');
}

// ── UI helpers ───────────────────────────────────────────────────────────

function _getBtns(docId) {
    return {
        play:   document.getElementById(`ra-play-${docId}`),
        pause:  document.getElementById(`ra-pause-${docId}`),
        stop:   document.getElementById(`ra-stop-${docId}`),
        status: document.querySelector(`.read-aloud-status-${docId}`),
    };
}

function _setUIState(docId, state) {
    const { play, pause, stop, status } = _getBtns(docId);
    if (!play) return;
    const lang = raGetLang(docId);
    switch (state) {
        case 'idle':
            play.classList.remove('d-none'); play.disabled = false;
            pause.classList.add('d-none');
            stop.classList.add('d-none');
            status.textContent = lang === 'he' ? 'קרא' : 'Read';
            break;
        case 'loading':
            play.classList.add('d-none'); play.disabled = true;
            pause.classList.add('d-none');
            stop.classList.add('d-none');
            status.textContent = '⏳';
            break;
        case 'generating':
            status.textContent = '🎙️ יוצר...';
            break;
        case 'playing':
            play.classList.add('d-none'); play.disabled = false;
            pause.classList.remove('d-none');
            stop.classList.remove('d-none');
            status.textContent = '▶ מנגן';
            break;
        case 'paused':
            play.classList.remove('d-none'); play.disabled = false;
            pause.classList.add('d-none');
            stop.classList.remove('d-none');
            status.textContent = '⏸ מושהה';
            break;
        case 'error':
            play.classList.remove('d-none'); play.disabled = false;
            pause.classList.add('d-none');
            stop.classList.add('d-none');
            status.textContent = '❌ שגיאה';
            break;
    }
}

// ── playback ─────────────────────────────────────────────────────────────

function _stopCurrent() {
    if (_tts.audio) {
        _tts.audio.pause();
        _tts.audio.currentTime = 0;
        _tts.audio = null;
    }
    if (_tts.docId) _setUIState(_tts.docId, 'idle');
    _tts.docId = null;
}

async function raPlay(docId) {
    // Resume if paused on the same doc
    if (_tts.docId === docId && _tts.audio?.paused && _tts.audio.currentTime > 0) {
        _tts.audio.play();
        return;
    }

    _stopCurrent();
    _setUIState(docId, 'loading');

    const lang = raGetLang(docId);
    const url  = lang === 'he'
        ? `/document/${docId}/audio/?lang=he`
        : `/document/${docId}/audio/`;

    try {
        const res  = await fetch(url);
        const data = await res.json();

        if (data.success && data.audio_url) {
            _startAudio(data.audio_url, docId);
        } else if (data.status === 'generating') {
            _setUIState(docId, 'generating');
            _pollUntilReady(docId, lang);
        } else {
            _setUIState(docId, 'error');
        }
    } catch (e) {
        console.error(e);
        _setUIState(docId, 'error');
    }
}

function raPause(docId) {
    if (_tts.docId === docId && _tts.audio && !_tts.audio.paused) {
        _tts.audio.pause();
    }
}

function raStop(docId) {
    if (_tts.docId === docId) _stopCurrent();
}

function _startAudio(audioUrl, docId) {
    const audio = new Audio(audioUrl);
    _tts.audio  = audio;
    _tts.docId  = docId;
    audio.addEventListener('playing', () => _setUIState(docId, 'playing'));
    audio.addEventListener('pause',   () => { if (audio.currentTime > 0 && !audio.ended) _setUIState(docId, 'paused'); });
    audio.addEventListener('ended',   () => _stopCurrent());
    audio.addEventListener('error',   () => { _setUIState(docId, 'error'); _tts.audio = null; _tts.docId = null; });
    audio.play().catch(e => { console.error(e); _setUIState(docId, 'error'); });
}

async function _pollUntilReady(docId, lang, attempts = 0) {
    if (attempts >= 60) { _setUIState(docId, 'error'); return; }
    const statusUrl = lang === 'he'
        ? `/document/${docId}/audio-status/?lang=he`
        : `/document/${docId}/audio-status/`;
    try {
        const res  = await fetch(statusUrl);
        const data = await res.json();
        if (data.success && data.audio_url) {
            _startAudio(data.audio_url, docId);
        } else {
            setTimeout(() => _pollUntilReady(docId, lang, attempts + 1), 2000);
        }
    } catch {
        setTimeout(() => _pollUntilReady(docId, lang, attempts + 1), 2000);
    }
}

// ── boot ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[id^="ra-lang-"]').forEach(btn => {
        const docId = btn.id.replace('ra-lang-', '');
        raSetLang(docId, raGetLang(docId));
    });

    const style = document.createElement('style');
    style.textContent = `
        .ra-btn   { transition: all .2s ease; }
        .ra-pause { background: rgba(40,167,69,.13) !important; color: #28a745; border-color: rgba(40,167,69,.4) !important; }
        .ra-stop  { background: rgba(220,53,69,.10) !important; color: #dc3545; border-color: rgba(220,53,69,.4) !important; }
        .ra-lang  { font-size: .7rem; opacity: .8; }
        .ra-lang:hover { opacity: 1; }
        .ra-status { font-size: .72rem; }
    `;
    document.head.appendChild(style);
});
