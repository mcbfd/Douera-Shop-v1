/**
 * Douéra Shop - Payment Simulation Engine
 */
const Payment = {
    delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

    generateTransactionRef: () => {
        return 'TRX-' + Math.random().toString(36).substr(2, 9).toUpperCase();
    },

    processMobileMoney: async (method, phone) => {
        const providerName = method === 'orange' ? 'Orange Money' : 'Wave';
        UI.showToast(`Initialisation du paiement ${providerName}...`, "info");
        
        await Payment.delay(1500);

        if (method === 'wave') {
            UI.showToast("Redirection vers votre application Wave Sénégal...", "success");
            // Simulation d'ouverture d'app (Deep Link)
            await Payment.delay(2000);
        } else {
            UI.showToast("Veuillez composer le #144#77# pour recevoir votre code de validation Orange Money.", "info");
            await Payment.delay(4000);
        }

        return Payment.generateTransactionRef();
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
