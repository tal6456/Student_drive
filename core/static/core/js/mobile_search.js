document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('navbarSearchInput');
    const mobileSearchToggle = document.getElementById('mobileSearchToggleBtn');
    const mobileSearchClose = document.getElementById('mobileSearchCloseBtn');
    const mobileOverlay = document.getElementById('mobileSearchOverlay');
    const mobileSearchInput = document.getElementById('mobileSearchInput');
    const backdrop = document.getElementById('search-focus-backdrop');

    const showBackdrop = () => {
        if (!backdrop) return;
        backdrop.style.display = 'block';
        setTimeout(() => backdrop.style.opacity = '1', 10);
    };

    const hideBackdrop = () => {
        if (!backdrop) return;
        backdrop.style.opacity = '0';
        setTimeout(() => {
            if (!mobileOverlay?.classList.contains('active') && document.activeElement !== searchInput) {
                backdrop.style.display = 'none';
            }
        }, 300);
    };

    const openMobileSearch = () => {
        if (!mobileOverlay) return;
        mobileOverlay.classList.add('active');
        mobileOverlay.setAttribute('aria-hidden', 'false');
        document.body.classList.add('search-overlay-open');
        showBackdrop();
        setTimeout(() => mobileSearchInput?.focus(), 150);
    };

    const closeMobileSearch = () => {
        if (!mobileOverlay) return;
        mobileOverlay.classList.remove('active');
        mobileOverlay.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('search-overlay-open');
        if (document.activeElement === mobileSearchInput) {
            mobileSearchInput.blur();
        }
        if (!searchInput || document.activeElement !== searchInput) {
            hideBackdrop();
        }
    };

    if (searchInput && backdrop) {
        searchInput.addEventListener('focus', showBackdrop);
        searchInput.addEventListener('blur', hideBackdrop);
    }

    if (mobileSearchToggle) {
        mobileSearchToggle.addEventListener('click', openMobileSearch);
    }

    if (mobileSearchClose) {
        mobileSearchClose.addEventListener('click', closeMobileSearch);
    }

    if (backdrop) {
        backdrop.addEventListener('click', function() {
            if (mobileOverlay?.classList.contains('active')) {
                closeMobileSearch();
            }
        });
    }

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && mobileOverlay?.classList.contains('active')) {
            closeMobileSearch();
        }
    });
});
