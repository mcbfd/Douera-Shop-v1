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

    window.getLocation = function() {
        if (!navigator.geolocation) {
            UI.showToast("La géolocalisation n'est pas supportée par votre navigateur.", "error");
            return;
        }

        UI.showToast("Récupération de votre position...", "info");
        
        navigator.geolocation.getCurrentPosition(async (position) => {
            const { latitude, longitude } = position.coords;
            try {
                const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
                const data = await response.json();
                if (data && data.display_name) {
                    const addrInput = document.getElementById('address');
                    if (addrInput) {
                        addrInput.value = data.display_name;
                        addrInput.style.borderColor = 'var(--color-success)';
                        UI.showToast("Position récupérée avec succès !", "success");
                    }
                }
            } catch (error) {
                UI.showToast("Erreur lors de la récupération de l'adresse.", "error");
            }
        }, () => {
            UI.showToast("Accès à la position refusé.", "error");
        });
    };

    window.removeItemFromCheckout = function(id) {
        Cart.remove(id);
        initCheckout();
        // Sync with main page if needed (cart updated event)
        window.dispatchEvent(new CustomEvent('cartUpdated'));
    };

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
                const firstNameInput = document.getElementById('first-name');
                const lastNameInput = document.getElementById('last-name');
                const phoneInput = document.getElementById('delivery-phone');
                const addressInput = document.getElementById('address');

                if (firstNameInput && !firstNameInput.value) firstNameInput.value = user.name.split(' ')[0];
                if (lastNameInput && !lastNameInput.value) lastNameInput.value = user.name.split(' ').slice(1).join(' ');
                if (phoneInput && !phoneInput.value && user.phone) phoneInput.value = user.phone;
                if (addressInput && !addressInput.value && user.address) addressInput.value = user.address;
                
                const saveDefaultContainer = document.getElementById('save-default-container');
                if (saveDefaultContainer) saveDefaultContainer.style.display = 'flex';
            }
        }

        // Render Summary
        if (summaryList) {
            summaryList.innerHTML = '';
            cart.forEach(item => {
                const row = document.createElement('div');
                row.style.cssText = 'display: flex; gap: 1rem; align-items: center; padding: 12px; border-radius: 12px; transition: background 0.3s;';
                row.onmouseover = () => row.style.background = '#F8FAFC';
                row.onmouseout = () => row.style.background = 'transparent';
                
                row.innerHTML = `
                    <div style="position: relative; flex-shrink: 0;">
                        <img src="${item.image}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover; background: #EEE; border: 1px solid var(--color-border);">
                        <span style="position: absolute; top: -8px; right: -8px; background: var(--color-primary); color: white; width: 20px; height: 20px; border-radius: 50%; font-size: 0.7rem; display: flex; align-items: center; justify-content: center; font-weight: 800; border: 2px solid white;">${item.quantity}</span>
                    </div>
                    <div style="flex: 1; font-size: 0.85rem;">
                        <div style="font-weight: 700; color: var(--color-primary-dark);">${item.name}</div>
                        <div style="font-weight: 800; color: var(--color-primary); margin-top: 2px;">${(item.price * item.quantity).toLocaleString()} XOF</div>
                    </div>
                    <button onclick="removeItemFromCheckout('${item.id}')" style="background: none; border: none; color: var(--color-error); cursor: pointer; padding: 8px; opacity: 0.4; transition: opacity 0.3s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.4'">
                        <i data-lucide="trash-2" style="width: 18px;"></i>
                    </button>
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
    function goToStep2() {
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
    }

    const btnStep2 = document.getElementById('btn-to-step-2');
    if (btnStep2) btnStep2.onclick = goToStep2;
    
    const mobileBtnStep2 = document.getElementById('mobile-btn-to-step-2');
    if (mobileBtnStep2) mobileBtnStep2.onclick = goToStep2;

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

                // DEEP UPDATE: Pre-payment stock verification
                const serverProducts = await (await fetch(`${API_BASE_URL}/products`)).json();
                for (const item of cart) {
                    const serverProd = serverProducts.find(p => p.id === item.id);
                    if (!serverProd || serverProd.stock < item.quantity) {
                        throw new Error(`Désolé, le stock pour "${item.name}" n'est plus suffisant (${serverProd ? serverProd.stock : 0} restant).`);
                    }
                }

                let trxRef = null;
                const orderId = Payment.generateTransactionRef();
                const total = Cart.getTotal();

                if (selectedMethod === 'wave') {
                    // Pour Wave, on enregistre d'abord la commande puis on redirige
                    await saveOrderToBackend(orderId, cart, total);
                    
                    const phone = document.getElementById('mm-phone').value;
                    const paymentResult = await Payment.processMobileMoney('wave', phone, { id: orderId, total: total });
                    
                    if (paymentResult.type === 'redirect') {
                        UI.showToast("Redirection vers Wave...", "success");
                        Cart.clear();
                        setTimeout(() => {
                            window.location.href = paymentResult.url;
                        }, 1000);
                        return; // Stop ici car on redirige
                    }
                } else if (selectedMethod === 'orange') {
                    // Pour Orange, on enregistre d'abord la commande puis on redirige
                    await saveOrderToBackend(orderId, cart, total);
                    
                    const phone = document.getElementById('mm-phone').value;
                    const paymentResult = await Payment.processMobileMoney('orange', phone, { id: orderId, total: total });
                    
                    if (paymentResult.type === 'redirect') {
                        UI.showToast("Redirection vers Orange Money...", "success");
                        Cart.clear();
                        setTimeout(() => {
                            window.location.href = paymentResult.url;
                        }, 1000);
                        return; // Stop ici car on redirige
                    }
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
                    trxRef = orderId;
                    await Payment.delay(1500);
                }

                // Success for non-wave methods
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
