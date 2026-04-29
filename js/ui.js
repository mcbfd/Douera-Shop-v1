/**
 * Douéra Shop - UI Pro Max Utilities
 */
const UI = {
    /**
     * Shows a premium toast notification
     * @param {string} message 
     * @param {'success'|'error'|'info'} type 
     */
    showToast: (message, type = 'success') => {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type} animate-fade-in`;
        
        let iconName = 'check-circle-2';
        if (type === 'error') iconName = 'alert-circle';
        if (type === 'info') iconName = 'info';

        toast.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 24px;
            background: white;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            border-left: 6px solid ${type === 'success' ? 'var(--color-success)' : type === 'error' ? 'var(--color-error)' : 'var(--color-primary)'};
            font-weight: 700;
            color: var(--color-foreground);
            min-width: 320px;
            pointer-events: auto;
            margin-bottom: 12px;
        `;

        toast.innerHTML = `
            <i data-lucide="${iconName}" style="color: ${type === 'success' ? 'var(--color-success)' : type === 'error' ? 'var(--color-error)' : 'var(--color-primary)'}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        if (window.lucide) lucide.createIcons();

        // Dismiss animation
        setTimeout(() => {
            toast.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(40px)';
            setTimeout(() => toast.remove(), 400);
        }, 3200);
    },

    /**
     * Shows a premium confirmation modal
     * @param {string} title
     * @param {string} message
     * @returns {Promise<boolean>}
     */
    showConfirm: (title, message) => {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(8px);
                display: flex; align-items: center; justify-content: center;
                z-index: 10000; animation: fadeIn 0.3s ease;
            `;

            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white; padding: 40px; border-radius: 24px;
                max-width: 440px; width: 90%; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.2);
                animation: scaleUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            `;

            modal.innerHTML = `
                <div style="width: 60px; height: 60px; background: #FEE2E2; color: #EF4444; border-radius: 20px; display: flex; align-items: center; justify-content: center; margin-bottom: 24px;">
                    <i data-lucide="alert-triangle" style="width: 30px; height: 30px;"></i>
                </div>
                <h3 style="margin-bottom: 12px; font-size: 1.5rem;">${title}</h3>
                <p style="color: var(--color-muted); margin-bottom: 32px; line-height: 1.6;">${message}</p>
                <div style="display: flex; gap: 16px;">
                    <button id="confirm-cancel" class="btn btn-outline" style="flex: 1; padding: 14px;">Annuler</button>
                    <button id="confirm-ok" class="btn" style="flex: 1; padding: 14px; background: #EF4444; color: white; border: none; font-weight: 800; border-radius: var(--radius-md); cursor: pointer;">Confirmer</button>
                </div>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            if (window.lucide) lucide.createIcons();

            document.getElementById('confirm-cancel').onclick = () => {
                overlay.remove();
                resolve(false);
            };
            document.getElementById('confirm-ok').onclick = () => {
                overlay.remove();
                resolve(true);
            };
        });
    },
    /**
     * Toggles a loading state on a button
     * @param {HTMLElement} btn 
     * @param {boolean} isLoading 
     * @param {string} [loadingText]
     */
    setLoading: (btn, isLoading, loadingText = '') => {
        if (!btn) return;
        
        if (isLoading) {
            btn.dataset.originalContent = btn.innerHTML;
            btn.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                    <div class="spinner"></div>
                    ${loadingText ? `<span>${loadingText}</span>` : ''}
                </div>
            `;
            btn.disabled = true;
            btn.style.opacity = '0.8';
            btn.style.cursor = 'not-allowed';
        } else {
            btn.innerHTML = btn.dataset.originalContent;
            btn.disabled = false;
            btn.style.opacity = '';
            btn.style.cursor = '';
        }
    }
};

// Add keyframes if not present
if (!document.getElementById('ui-animations')) {
    const style = document.createElement('style');
    style.id = 'ui-animations';
    style.textContent = `
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes scaleUp { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        .spinner { width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(style);
}
