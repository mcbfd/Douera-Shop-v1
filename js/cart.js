/**
 * Douéra Shop - Cart Engine v4.1 (Bug Fix: ID-based operations)
 */
const Cart = {
    key: 'douera_v2_cart',

    getItems: () => JSON.parse(localStorage.getItem(Cart.key)) || [],

    save: (items) => {
        localStorage.setItem(Cart.key, JSON.stringify(items));
        window.dispatchEvent(new CustomEvent('cartUpdated'));
    },

    add: (product, qty = 1) => {
        const items = Cart.getItems();
        const existing = items.find(i => i.id === product.id);
        
        if (existing) {
            existing.quantity += qty;
        } else {
            items.push({ ...product, quantity: qty });
        }
        
        Cart.save(items);
    },

    remove: (id) => {
        let items = Cart.getItems();
        const item = items.find(i => i.id === id);
        if (!item) return;

        if (confirm(`Voulez-vous vraiment retirer "${item.name}" du panier ?`)) {
            items = items.filter(i => i.id !== id);
            Cart.save(items);
            if (window.UI) UI.showToast(`Produit retiré.`);
        }
    },

    updateQuantity: (id, delta) => {
        let items = Cart.getItems();
        const item = items.find(i => i.id === id);
        if (!item) return;

        item.quantity += delta;
        
        if (item.quantity < 1) {
            Cart.remove(id);
        } else {
            Cart.save(items);
        }
    },

    getTotal: () => {
        return Cart.getItems().reduce((sum, item) => sum + (item.price * item.quantity), 0);
    },

    clear: () => localStorage.removeItem(Cart.key)
};
