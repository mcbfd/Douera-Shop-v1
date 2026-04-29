/**
 * Douéra Shop - Cart Page Controller v4.1 (Sync with ID-based Cart)
 */

document.addEventListener('DOMContentLoaded', () => {
    const itemsList = document.getElementById('cart-items-list');
    const emptyMsg = document.getElementById('empty-cart-msg');
    const itemsWrapper = document.getElementById('cart-items-wrapper');
    const subtotalEl = document.getElementById('cart-subtotal');
    const totalEl = document.getElementById('cart-total');

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
                    <h4>${item.name}</h4>
                    <p>${item.price.toLocaleString()} XOF</p>
                </div>
                <div class="cart-item-qty-wrapper">
                    <button class="qty-btn" data-id="${item.id}" data-delta="-1">-</button>
                    <span>${item.quantity}</span>
                    <button class="qty-btn" data-id="${item.id}" data-delta="1">+</button>
                </div>
                <div class="cart-item-price-total">
                    ${(item.price * item.quantity).toLocaleString()} XOF
                </div>
                <button class="remove-btn" data-id="${item.id}">
                    <i data-lucide="trash-2"></i>
                </button>
            `;
            
            if (itemsList) itemsList.appendChild(itemElement);
        });

        // Update Totals
        const total = Cart.getTotal();
        if (subtotalEl) subtotalEl.textContent = `${total.toLocaleString()} XOF`;
        if (totalEl) totalEl.textContent = `${total.toLocaleString()} XOF`;

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
                message += `• ${item.name} (x${item.quantity}) - ${item.price.toLocaleString()} XOF\n`;
            });
            message += `\n*Total : ${Cart.getTotal().toLocaleString()} XOF*`;
            message += "\n\nMerci de me recontacter pour la livraison !";

            const waUrl = `https://wa.me/221781607468?text=${encodeURIComponent(message)}`;
            window.open(waUrl, '_blank');
        };
    }

    // Initial Render
    renderCartPage();
});
