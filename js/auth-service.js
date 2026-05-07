/**
 * Douéra Shop - Client Auth Service (REST API)
 */

const AuthService = {
    KEYS: {
        SESSION: 'douera_client_session'
    },

    // 1. Core Auth
    login: async (email, password) => {
        const baseUrl = window.API_CONFIG ? window.API_CONFIG.BASE_URL : '/api';
        const response = await fetch(`${baseUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Email ou mot de passe incorrect.");
        }

        const session = await response.json();
        
        // Normalisation: s'assurer que userId est présent (copie de id si besoin)
        if (session.id && !session.userId) {
            session.userId = session.id;
        }
        
        localStorage.setItem(AuthService.KEYS.SESSION, JSON.stringify(session));
        return session;
    },

    register: async (userData) => {
        const response = await fetch(`${API_BASE_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: userData.name,
                email: userData.email,
                password: userData.password,
                address: userData.address,
                phone: userData.phone,
                gender: userData.gender,
                country: userData.country,
                region: userData.region,
                city: userData.city,
                role: 'client',
                status: 'active'
            })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Erreur lors de l'inscription.");
        }

        // Auto-login after register
        return await AuthService.login(userData.email, userData.password);
    },

    logout: () => {
        localStorage.removeItem(AuthService.KEYS.SESSION);
        // Détecter si on est dans un sous-dossier (comme account/)
        const isSubfolder = window.location.pathname.includes('/account/') || window.location.pathname.includes('/admin/');
        window.location.href = isSubfolder ? '../index.html' : 'index.html';
    },

    // 2. Session Management
    getCurrentUser: () => {
        const session = JSON.parse(localStorage.getItem(AuthService.KEYS.SESSION));
        if (!session || Date.now() > session.expires) {
            localStorage.removeItem(AuthService.KEYS.SESSION);
            return null;
        }
        return session;
    },

    isAuthenticated: () => {
        return AuthService.getCurrentUser() !== null;
    },

    // 3. Navigation Guard
    guard: (redirectUrl = '../account/login.html') => {
        if (!AuthService.isAuthenticated()) {
            const currentPath = window.location.pathname;
            localStorage.setItem('auth_redirect', currentPath);
            window.location.href = redirectUrl;
            return false;
        }
        return true;
    }
};
