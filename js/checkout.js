/**
 * Douéra Shop - Checkout Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const step1 = document.getElementById('step-1-content');
    const step2 = document.getElementById('step-2-content');
    const step1Ind = document.getElementById('step-1-indicator');
    const step2Ind = document.getElementById('step-2-indicator');
    const summaryList = document.getElementById('checkout-items-summary');
    const totalEl = document.getElementById('summary-total');
    const subtotalEl = document.getElementById('summary-subtotal');
    
    let selectedMethod = 'orange';

    function initCheckout() {
        const cart = Cart.getItems();
        if (cart.length === 0) {
            window.location.href = 'index.html';
            return;
        }

        // Pre-fill user data
        if (typeof AuthService !== 'undefined') {
            const user = AuthService.getCurrentUser();
            if (user) {
                if (document.getElementById('first-name')) document.getElementById('first-name').value = user.name.split(' ')[0];
                if (document.getElementById('last-name')) document.getElementById('last-name').value = user.name.split(' ').slice(1).join(' ');
                if (document.getElementById('delivery-phone') && user.phone) document.getElementById('delivery-phone').value = user.phone;
                if (document.getElementById('address') && user.address) document.getElementById('address').value = user.address;
                
                // Show save default option if logged in
                const saveDefaultContainer = document.getElementById('save-default-container');
                if (saveDefaultContainer) saveDefaultContainer.style.display = 'flex';
            }
        }

        // Render Summary
        if (summaryList) {
            summaryList.innerHTML = '';
            cart.forEach(item => {
                const row = document.createElement('div');
                row.style.cssText = 'display: flex; gap: 1rem; align-items: center;';
                row.innerHTML = `
                    <div style="position: relative;">
                        <img src="${item.image}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover; background: #EEE; border: 1px solid var(--color-border);">
                        <span style="position: absolute; top: -8px; right: -8px; background: var(--color-muted); color: white; width: 20px; height: 20px; border-radius: 50%; font-size: 0.7rem; display: flex; align-items: center; justify-content: center;">${item.quantity}</span>
                    </div>
                    <div style="flex: 1; font-size: 0.85rem;">
                        <div style="font-weight: 600;">${item.name}</div>
                    </div>
                    <div style="font-weight: 700;">${(item.price * item.quantity).toLocaleString()} XOF</div>
                `;
                summaryList.appendChild(row);
            });
        }

        const total = Cart.getTotal();
        if (totalEl) totalEl.textContent = `${total.toLocaleString()} XOF`;
        if (subtotalEl) subtotalEl.textContent = `${total.toLocaleString()} XOF`;
        
        if (window.lucide) lucide.createIcons();
    }

    // Step Transitions
    document.getElementById('btn-to-step-2').onclick = () => {
        // Basic validation
        const phone = document.getElementById('delivery-phone').value;
        const firstName = document.getElementById('first-name').value;
        const address = document.getElementById('address').value;

        if (!firstName || !address || !phone) {
            UI.showToast("Veuillez remplir tous les champs de livraison.", "error");
            return;
        }
        
        step1.style.display = 'none';
        step2.style.display = 'block';
        
        // Update Indicators
        step1Ind.querySelector('.step-number').style.background = 'var(--color-success)';
        step1Ind.querySelector('.step-number').innerHTML = '<i data-lucide="check" style="width: 16px;"></i>';
        step2Ind.querySelector('.step-number').style.background = 'var(--color-primary)';
        step2Ind.classList.add('active');
        
        if (window.lucide) lucide.createIcons();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    document.getElementById('btn-back-to-step-1').onclick = () => {
        step1.style.display = 'block';
        step2.style.display = 'none';
        step2Ind.classList.remove('active');
        step2Ind.querySelector('.step-number').style.background = 'var(--color-border)';
        step1Ind.querySelector('.step-number').style.background = 'var(--color-primary)';
        step1Ind.querySelector('.step-number').textContent = '1';
    };

    // Payment Selection
    const methodBtns = document.querySelectorAll('.pay-method-btn');
    const forms = {
        orange: document.getElementById('form-mm'),
        wave: document.getElementById('form-mm'),
        card: document.getElementById('form-card'),
        cash: document.getElementById('form-cash')
    };

    methodBtns.forEach(btn => {
        btn.onclick = () => {
            methodBtns.forEach(b => {
                b.classList.remove('active');
                b.style.borderColor = 'var(--color-border)';
                b.style.background = 'white';
            });
            btn.classList.add('active');
            btn.style.borderColor = 'var(--color-primary)';
            btn.style.background = 'var(--color-primary-light)';
            
            selectedMethod = btn.dataset.method;

            // Hide all forms
            Object.values(forms).forEach(f => { if(f) f.style.display = 'none'; });
            // Show selected
            if (forms[selectedMethod]) forms[selectedMethod].style.display = 'block';
        };
    });

    // Final Processing
    const confirmBtn = document.getElementById('btn-confirm-payment');
    if (confirmBtn) {
        confirmBtn.onclick = async (e) => {
            const btn = e.currentTarget;
            UI.setLoading(btn, true, "Traitement...");

            try {
                const cart = Cart.getItems();
                if (cart.length === 0) throw new Error("Votre panier est vide.");

                let trxRef = null;

                if (selectedMethod === 'orange' || selectedMethod === 'wave') {
                    const phone = document.getElementById('mm-phone').value;
                    if (!phone) throw new Error("Veuillez entrer votre numéro de téléphone pour le paiement.");
                    trxRef = await Payment.processMobileMoney(selectedMethod, phone);
                } else if (selectedMethod === 'card') {
                    const details = {
                        number: document.getElementById('card-number').value,
                        name: document.getElementById('card-name').value,
                        expiry: document.getElementById('card-expiry').value,
                        cvc: document.getElementById('card-cvc').value
                    };
                    if (!details.number || !details.name) throw new Error("Veuillez remplir les informations de carte.");
                    trxRef = await Payment.processCard(details);
                } else {
                    // Cash
                    trxRef = Payment.generateTransactionRef();
                    await Payment.delay(1500);
                }

                // Success! Save Order
                const total = Cart.getTotal();
                await saveOrderToBackend(trxRef, cart, total);

                // Save as Default if checked
                const saveDefault = document.getElementById('save-default-address');
                const user = typeof AuthService !== 'undefined' ? AuthService.getCurrentUser() : null;
                if (saveDefault && saveDefault.checked && user) {
                    const address = document.getElementById('address').value;
                    const phone = document.getElementById('delivery-phone').value;
                    const API_URL = API_BASE_URL;
                    
                    await fetch(`${API_URL}/users/${user.userId}/profile`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ address, phone })
                    });

                    // Update local session to reflect change
                    user.address = address;
                    user.phone = phone;
                    localStorage.setItem('douera_client_session', JSON.stringify(user));
                }
                
                // Clear Cart AFTER successful order save
                Cart.clear();
                
                UI.showToast("Commande confirmée ! Merci de votre confiance.", "success");
                setTimeout(() => {
                    window.location.href = `success.html?ref=${trxRef}`;
                }, 1200);

            } catch (err) {
                UI.showToast(err.message, "error");
                UI.setLoading(btn, false, "Confirmer et Payer");
            }
        };
    }

    async function saveOrderToBackend(ref, items, total) {
        const user = typeof AuthService !== 'undefined' ? AuthService.getCurrentUser() : null;
        
        const payload = {
            id: ref,
            userId: user ? user.userId : 'guest',
            userName: user ? user.name : 'Client invité',
            date: new Date().toISOString(),
            items: items,
            total: total,
            method: selectedMethod,
            customer_firstname: document.getElementById('first-name').value,
            customer_lastname: document.getElementById('last-name').value,
            customer_address: document.getElementById('address').value,
            customer_phone: document.getElementById('delivery-phone').value
        };
        
        const API_URL = API_BASE_URL;
        await fetch(`${API_URL}/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    }

    initCheckout();
});
