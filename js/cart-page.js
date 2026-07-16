/**
 * Douéra Shop - Cart Page Controller v4.2
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Theme & Currency Utilities ---
    window.formatPrice = function(priceXOF) {
        const currency = localStorage.getItem('douera_currency') || 'XOF';
        if (currency === 'EUR') {
            const price = Math.round(priceXOF / 655);
            return price + ' €';
        } else if (currency === 'USD') {
            const price = Math.round(priceXOF / 600);
            return price + ' $';
        }
        return new Intl.NumberFormat('fr-FR').format(priceXOF) + ' XOF';
    };

    function initTheme() {
        const theme = localStorage.getItem('douera_theme') || 'light';
        document.body.classList.toggle('dark-mode', theme === 'dark');
        const themeBtn = document.getElementById('theme-toggle-btn');
        if (themeBtn) {
            themeBtn.innerHTML = theme === 'dark' ? '<i data-lucide="sun"></i>' : '<i data-lucide="moon"></i>';
            if (window.lucide) lucide.createIcons();
        }
    }

    function initCurrency() {
        const currency = localStorage.getItem('douera_currency') || 'XOF';
        const currencySelect = document.getElementById('currency-select');
        if (currencySelect) {
            currencySelect.value = currency;
            currencySelect.onchange = (e) => {
                localStorage.setItem('douera_currency', e.target.value);
                window.dispatchEvent(new Event('currencychange'));
                renderCartPage();
            };
        }
    }

    initTheme();
    initCurrency();

    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
        themeBtn.onclick = () => {
            const isDark = document.body.classList.contains('dark-mode');
            const newTheme = isDark ? 'light' : 'dark';
            localStorage.setItem('douera_theme', newTheme);
            document.body.classList.toggle('dark-mode', newTheme === 'dark');
            themeBtn.innerHTML = newTheme === 'dark' ? '<i data-lucide="sun"></i>' : '<i data-lucide="moon"></i>';
            if (window.lucide) lucide.createIcons();
        };
    }

    // --- ELEMENTS ---
    const itemsList = document.getElementById('cart-items-list');
    const emptyMsg = document.getElementById('empty-cart-msg');
    const itemsWrapper = document.getElementById('cart-items-wrapper');
    const subtotalEl = document.getElementById('cart-subtotal');
    const totalEl = document.getElementById('cart-total');

    // Promo elements
    const promoInput = document.getElementById('promo-code-input');
    const promoBtn = document.getElementById('promo-code-apply');
    const promoMsg = document.getElementById('promo-message');
    const discountRow = document.getElementById('discount-row');
    const discountEl = document.getElementById('cart-discount');

    let discountPct = parseFloat(sessionStorage.getItem('douera_discount_pct') || '0');
    let discountCode = sessionStorage.getItem('douera_discount_code') || '';

    function showPromoMsg(text, type) {
        if (!promoMsg) return;
        promoMsg.textContent = text;
        promoMsg.style.color = type === 'success' ? 'var(--color-success)' : 'var(--color-error)';
        promoMsg.style.display = 'block';
    }

    if (promoBtn) {
        promoBtn.onclick = () => {
            const code = promoInput.value.trim().toUpperCase();
            if (code === 'WELCOME10') {
                discountPct = 10;
                discountCode = 'WELCOME10';
                showPromoMsg("Code WELCOME10 appliqué ! -10% sur la commande.", "success");
            } else if (code === 'DOUERA20') {
                discountPct = 20;
                discountCode = 'DOUERA20';
                showPromoMsg("Code DOUERA20 appliqué ! -20% sur la commande.", "success");
            } else if (code === '') {
                discountPct = 0;
                discountCode = '';
                promoMsg.style.display = 'none';
            } else {
                discountPct = 0;
                discountCode = '';
                showPromoMsg("Code promo inconnu.", "error");
            }
            sessionStorage.setItem('douera_discount_pct', discountPct.toString());
            sessionStorage.setItem('douera_discount_code', discountCode);
            renderCartPage();
        };
    }

    // Pre-fill promo if active
    if (discountCode && promoInput) {
        promoInput.value = discountCode;
        showPromoMsg(`Code ${discountCode} actif (${discountPct}%)`, "success");
    }

    function renderCartPage() {
        const cart = Cart.getItems();

        if (cart.length === 0) {
            if (emptyMsg) emptyMsg.style.display = 'block';
            if (itemsWrapper) itemsWrapper.style.display = 'none';
            return;
        }

        if (emptyMsg) emptyMsg.style.display = 'none';
        if (itemsWrapper) itemsWrapper.style.display = 'block';
        if (itemsList) itemsList.innerHTML = '';

        cart.forEach((item) => {
            const itemElement = document.createElement('div');
            itemElement.className = 'cart-item-card animate-fade-in';
            
            itemElement.innerHTML = `
                <div class="cart-item-img-wrapper">
                    <img src="${item.image}" alt="${item.name}">
                </div>
                <div class="cart-item-info">
                    <h4 class="outfit-title">${item.name}</h4>
                    <p style="font-weight: 700; color: var(--color-muted);">${window.formatPrice(item.price)}</p>
                </div>
                <div class="cart-item-qty-wrapper">
                    <button class="qty-btn" data-id="${item.id}" data-delta="-1">-</button>
                    <span style="font-weight: 800; font-size: 1.1rem; min-width: 20px; text-align: center;">${item.quantity}</span>
                    <button class="qty-btn" data-id="${item.id}" data-delta="1">+</button>
                </div>
                <div class="cart-item-price-total" style="font-weight: 800; color: var(--color-primary);">
                    ${window.formatPrice(item.price * item.quantity)}
                </div>
                <button class="remove-btn" data-id="${item.id}" style="background: none; border: none; color: var(--color-error); cursor: pointer; opacity: 0.7;">
                    <i data-lucide="trash-2"></i>
                </button>
            `;
            
            if (itemsList) itemsList.appendChild(itemElement);
        });

        // Update Totals
        const total = Cart.getTotal();
        const discountAmount = Math.round(total * (discountPct / 100));
        const finalTotal = total - discountAmount;

        if (subtotalEl) subtotalEl.textContent = window.formatPrice(total);

        if (discountAmount > 0) {
            if (discountRow) discountRow.style.display = 'flex';
            if (discountEl) discountEl.textContent = `-${window.formatPrice(discountAmount)}`;
        } else {
            if (discountRow) discountRow.style.display = 'none';
        }

        if (totalEl) totalEl.textContent = window.formatPrice(finalTotal);
        
        const mobileTotalEl = document.getElementById('mobile-cart-total');
        if (mobileTotalEl) mobileTotalEl.textContent = window.formatPrice(finalTotal);

        if (window.lucide) lucide.createIcons();
    }

    // Delegation for dynamic buttons
    if (itemsList) {
        itemsList.addEventListener('click', (e) => {
            const qtyBtn = e.target.closest('.qty-btn');
            const removeBtn = e.target.closest('.remove-btn');

            if (qtyBtn) {
                const id = qtyBtn.dataset.id;
                const delta = parseInt(qtyBtn.dataset.delta);
                Cart.updateQuantity(id, delta);
                renderCartPage();
            }

            if (removeBtn) {
                const id = removeBtn.dataset.id;
                Cart.remove(id);
                renderCartPage();
            }
        });
    }

    // Global listener for updates
    window.addEventListener('cartUpdated', renderCartPage);

    // WhatsApp Fast Checkout
    const waBtn = document.getElementById('whatsapp-fast-checkout');
    if (waBtn) {
        waBtn.onclick = () => {
            const cart = Cart.getItems();
            if (cart.length === 0) return;

            let message = "Salam Douéra Shop ! Je souhaite commander les articles suivants :\n\n";
            cart.forEach(item => {
                message += `• ${item.name} (x${item.quantity}) - ${window.formatPrice(item.price)}\n`;
            });
            
            const total = Cart.getTotal();
            const discountAmount = Math.round(total * (discountPct / 100));
            const finalTotal = total - discountAmount;

            if (discountAmount > 0) {
                message += `\nCode promo : ${discountCode} (-${discountPct}%)\n`;
                message += `Sous-total : ${window.formatPrice(total)}\n`;
                message += `*Total Réduit : ${window.formatPrice(finalTotal)}*\n`;
            } else {
                message += `\n*Total : ${window.formatPrice(total)}*\n`;
            }
            message += "\nMerci de me recontacter pour la livraison !";

            const waUrl = `https://wa.me/221781607468?text=${encodeURIComponent(message)}`;
            window.open(waUrl, '_blank');
        };
    }

    // Initial Render
    renderCartPage();
});
