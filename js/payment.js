/**
 * Douéra Shop - Payment Simulation Engine
 */
const Payment = {
    delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

    generateTransactionRef: () => {
        return 'TRX-' + Math.random().toString(36).substr(2, 9).toUpperCase();
    },

    processMobileMoney: async (method, phone, orderDetails = null) => {
        const providerName = method === 'orange' ? 'Orange Money' : 'Wave';
        UI.showToast(`Initialisation du paiement ${providerName}...`, "info");
        
        await Payment.delay(1000);

        if (method === 'wave') {
            if (!orderDetails) throw new Error("Détails de commande manquants pour Wave.");
            
            UI.showToast("Ouverture de la session Wave sécurisée...", "info");
            
            // Appel au backend pour créer la session Wave
            const response = await fetch(`${API_BASE_URL}/payments/wave/session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: orderDetails.total,
                    order_id: orderDetails.id
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Erreur lors de la création de la session Wave.");

            return {
                type: 'redirect',
                url: data.wave_launch_url,
                id: data.id 
            };
        } else if (method === 'orange') {
            if (!orderDetails) throw new Error("Détails de commande manquants pour Orange Money.");
            
            UI.showToast("Initialisation de la transaction Orange Money...", "info");
            
            // Appel au backend pour créer la session Orange
            const response = await fetch(`${API_BASE_URL}/payments/orange/session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: orderDetails.total,
                    order_id: orderDetails.id
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Erreur lors de la création de la session Orange Money.");

            return {
                type: 'redirect',
                url: data.payment_url,
                token: data.pay_token
            };
        } else {
            UI.showToast("Veuillez composer le #144#77# pour recevoir votre code de validation Orange Money.", "info");
            await Payment.delay(4000);
            return { type: 'ref', value: Payment.generateTransactionRef() };
        }
    },

    processCard: async (cardDetails) => {
        UI.showToast("Communication sécurisée avec la banque (Visa/Mastercard)...", "info");
        
        if (cardDetails.number.replace(/\s/g, '').length < 16) {
            throw new Error("Numéro de carte invalide. Veuillez vérifier les 16 chiffres.");
        }

        await Payment.delay(4000); // Bank 3D Secure
        return Payment.generateTransactionRef();
    }
};
