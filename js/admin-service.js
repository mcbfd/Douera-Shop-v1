/**
 * Douéra Shop - Admin Service Layer (REST API Integration)
 */

const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') 
    ? 'http://127.0.0.1:5001/api' 
    : '/api';

const AdminService = {
    KEYS: {
        SESSION: 'douera_admin_session'
    },

    init: async () => {
        // Backend DB initializes itself
    },

    // 2. Authentication
    login: async (email, password) => {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Erreur de connexion.");
        }

        const session = await response.json();
        localStorage.setItem(AdminService.KEYS.SESSION, JSON.stringify(session));
        return session;
    },

    logout: () => {
        localStorage.removeItem(AdminService.KEYS.SESSION);
        window.location.href = 'login.html';
    },

    checkAuth: () => {
        const session = JSON.parse(localStorage.getItem(AdminService.KEYS.SESSION));
        if (!session || Date.now() > session.expires) {
            window.location.href = 'login.html';
            return null;
        }
        return session;
    },

    // 3. Products CRUD
    getProducts: async () => {
        const res = await fetch(`${API_BASE_URL}/products`);
        return await res.json();
    },
    
    saveProduct: async (product) => {
        const res = await fetch(`${API_BASE_URL}/products`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(product)
        });
        await res.json();
        window.dispatchEvent(new CustomEvent('dataSynced', { detail: { type: 'products' } }));
    },

    deleteProduct: async (id) => {
        await fetch(`${API_BASE_URL}/products/${id}`, { method: 'DELETE' });
    },

    // 4. Orders CRUD
    getOrders: async () => {
        const res = await fetch(`${API_BASE_URL}/orders`);
        return await res.json();
    },
    
    updateOrderStatus: async (orderId, status) => {
        await fetch(`${API_BASE_URL}/orders/${orderId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
    },

    deleteOrder: async (id) => {
        await fetch(`${API_BASE_URL}/orders/${id}`, { method: 'DELETE' });
    },

    // 5. Users Management
    getUsers: async () => {
        const res = await fetch(`${API_BASE_URL}/users`);
        return await res.json();
    },
    
    saveUser: async (user) => {
        await fetch(`${API_BASE_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(user)
        });
    },

    deleteUser: async (id) => {
        await fetch(`${API_BASE_URL}/users/${id}`, { method: 'DELETE' });
    },

    // 6. Stats Dashboard
    getStats: async () => {
        const orders = await AdminService.getOrders();
        const products = await AdminService.getProducts();
        const users = await AdminService.getUsers();

        const totalVentes = orders.reduce((acc, o) => acc + (o.total || 0), 0);
        const nbClients = users.filter(u => u.role === 'client').length;
        const nbRupture = products.filter(p => (p.stock || 0) <= 0).length;
        // Top Products Logic
        const productSales = {};
        orders.forEach(o => {
            o.items.forEach(item => {
                productSales[item.id] = (productSales[item.id] || 0) + (item.quantity || 1);
            });
        });

        const popularProducts = Object.entries(productSales)
            .map(([id, sales]) => {
                const p = products.find(prod => prod.id === id);
                return p ? { ...p, sales } : null;
            })
            .filter(p => p !== null)
            .sort((a, b) => b.sales - a.sales)
            .slice(0, 3);
        
        return {
            totalVentes,
            nbCommandes: orders.length,
            nbClients,
            nbProduits: products.length,
            nbRupture,
            recentOrders: orders.slice(0, 5),
            popularProducts 
        };
    }
};

// Auto-Init
AdminService.init();
