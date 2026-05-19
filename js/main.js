/**
 * Douéra Shop - Main App Controller v4.0 (Excellence)
 */

// API_BASE_URL is defined in auth-service.js


document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ELEMENTS ---
    const productGrid = document.getElementById('productGrid');
    const authArea = document.getElementById('nav-auth-area');
    const storeSearch = document.getElementById('storeSearch');
    const storeSort = document.getElementById('storeSort');
    const filterContainer = document.getElementById('categoryFilters');
    
    // Drawer Elements
    const cartDrawer = document.getElementById('cartDrawer');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const cartToggleBtn = document.getElementById('cartToggleBtn');
    const closeDrawerBtn = document.getElementById('closeDrawerBtn');
    const cartDrawerItems = document.getElementById('cartDrawerItems');
    const drawerTotal = document.getElementById('drawerTotal');
    const cartBadge = document.querySelector('.cart-count');

    // Quick View Elements
    const qvModal = document.getElementById('quickViewModal');
    
    // State
    let allProducts = [];
    let currentCategory = 'all';
    let currentSearch = '';
    let currentSort = 'default';
    let currentMaxPrice = 5000000;
    let currentInStockOnly = false;

    // --- 1. INITIALIZATION ---

    async function init() {
        // Parallel load for speed
        const loadProductsPromise = (async () => {
            const cached = sessionStorage.getItem('douera_products_cache');
            if (cached) {
                allProducts = JSON.parse(cached);
                renderAppProducts(); // Show cached version immediately
                // Then update in background
            }
            try {
                const res = await fetch(`${API_BASE_URL}/products`);
                if (res.ok) {
                    const data = await res.json();
                    allProducts = data;
                    sessionStorage.setItem('douera_products_cache', JSON.stringify(data));
                    renderAppProducts();
                }
            } catch(e) { console.error("Update failed", e); }
        })();

        const initAuthPromise = updateAuthUI();
        
        await Promise.all([loadProductsPromise, initAuthPromise]);
        
        initHeroBackground();
        
        // Populate Categories
        const categories = [...new Set(allProducts.map(p => p.category))];
        categories.forEach(cat => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-outline filter-chip';
            btn.style.borderRadius = 'var(--radius-full)';
            btn.dataset.category = cat;
            btn.textContent = cat;
            btn.onclick = () => {
                document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentCategory = cat;
                renderAppProducts();
            };
            if (filterContainer) filterContainer.appendChild(btn);
        });

        // Setup Events with Debounce
        let searchTimeout;
        if (storeSearch) storeSearch.oninput = (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentSearch = e.target.value.toLowerCase();
                renderAppProducts();
            }, 300);
        };
        if (storeSort) storeSort.onchange = (e) => { currentSort = e.target.value; renderAppProducts(); };
        
        // Advanced Filters
        const toggleFiltersBtn = document.getElementById('toggleFiltersBtn');
        const advancedFiltersPanel = document.getElementById('advancedFiltersPanel');
        const priceRange = document.getElementById('priceRange');
        const priceValueDisplay = document.getElementById('priceValueDisplay');
        const inStockToggle = document.getElementById('inStockToggle');

        if (toggleFiltersBtn && advancedFiltersPanel) {
            toggleFiltersBtn.onclick = () => {
                const isHidden = advancedFiltersPanel.style.display === 'none';
                advancedFiltersPanel.style.display = isHidden ? 'flex' : 'none';
                toggleFiltersBtn.classList.toggle('active');
            };
        }

        if (priceRange) {
            priceRange.oninput = (e) => {
                currentMaxPrice = parseInt(e.target.value);
                if (priceValueDisplay) priceValueDisplay.textContent = currentMaxPrice.toLocaleString() + ' XOF';
            };
            priceRange.onchange = () => renderAppProducts();
        }

        if (inStockToggle) {
            inStockToggle.onchange = (e) => {
                currentInStockOnly = e.target.checked;
                renderAppProducts();
            };
        }
        
        // Drawer Controls
        if (closeDrawerBtn) closeDrawerBtn.onclick = toggleDrawer;
        if (drawerOverlay) drawerOverlay.onclick = toggleDrawer;

        // Global Sync
        window.addEventListener('cartUpdated', () => { updateBadge(); renderCartDrawer(); });
        window.addEventListener('dataSynced', async () => { 
            const API_URL = (window.location.protocol === 'file:') ? 'http://127.0.0.1:5001/api' : `http://${window.location.hostname}:5001/api`;
            try {
                const res = await fetch(`${API_BASE_URL}/products`);
                if (res.ok) allProducts = await res.json();
            } catch(e) {}
            renderAppProducts(); 
        });

        updateAuthUI();
        updateBadge();
        renderAppProducts();
        renderCartDrawer();
    }

    // --- 2. UI UTILITIES ---

    function toggleDrawer() {
        cartDrawer.classList.toggle('active');
        drawerOverlay.classList.toggle('active');
        document.body.style.overflow = cartDrawer.classList.contains('active') ? 'hidden' : '';
    }

    function updateBadge() {
        const items = Cart.getItems();
        const count = items.reduce((t, i) => t + i.quantity, 0);
        document.querySelectorAll('.cart-count').forEach(badge => {
            badge.textContent = count;
            badge.classList.remove('animate-pop');
            void badge.offsetWidth; // Trigger reflow
            badge.classList.add('animate-pop');
        });
    }

    async function updateAuthUI() {
        if (!authArea) return;
        const user = AuthService.getCurrentUser();
        const cartCount = Cart.getItems().reduce((t, i) => t + i.quantity, 0);

        // Update Bottom Nav Link dynamically
        const mobileAccountBtn = document.querySelector('.mobile-bottom-nav a:last-child');
        if (mobileAccountBtn) {
            mobileAccountBtn.href = user ? 'profile.html' : 'account/login.html';
        }

        // Optimized notification check
        let hasNewReply = false;
        if (user) {
            const lastCheck = sessionStorage.getItem('last_notif_check');
            const now = Date.now();
            if (!lastCheck || (now - lastCheck > 30000)) {
                try {
                    const res = await fetch(`${API_BASE_URL}/orders?userId=${user.userId}`);
                    if (res.ok) {
                        const orders = await res.json();
                        sessionStorage.setItem('last_notif_check', now);
                        const userOrders = orders.filter(o => String(o.userId || o.userid) === String(user.userId));
                        const seenReplies = JSON.parse(localStorage.getItem('seen_replies') || '[]');
                        hasNewReply = userOrders.some(o => o.admin_reply && !seenReplies.includes(o.review_id));
                        sessionStorage.setItem('has_new_reply_cache', hasNewReply);
                    }
                } catch (e) { console.error("Notif error", e); }
            } else {
                hasNewReply = sessionStorage.getItem('has_new_reply_cache') === 'true';
            }
        }

        // Tracking link update
        const trackNavLinks = [document.getElementById('track-nav-link'), document.getElementById('mobile-track-nav-link')];
        trackNavLinks.forEach(link => {
            if (link) {
                link.href = user ? 'orders.html' : 'track-order.html';
                if (link.id === 'track-nav-link') {
                    link.innerHTML = `
                        <i data-lucide="package" style="width: 24px; height: 24px;"></i>
                        ${hasNewReply ? '<span style="position: absolute; top: 0; right: -4px; width: 10px; height: 10px; background: #EF4444; border-radius: 50%; border: 2px solid white;"></span>' : ''}
                    `;
                } else {
                    const mobileBadge = document.getElementById('mobile-notif-badge');
                    if (mobileBadge) mobileBadge.style.display = hasNewReply ? 'block' : 'none';
                }
                if (window.lucide) lucide.createIcons({ root: link });
            }
        });

        const cartIconHtml = `
            <a href="checkout.html" class="cart-icon-wrapper" style="position: relative; color: var(--color-primary); text-decoration: none;">
                <i data-lucide="shopping-cart" style="width: 28px; height: 28px;"></i>
                <span class="cart-count nav-badge" style="top: -2px; right: -8px;">${cartCount}</span>
            </a>
        `;

        if (user) {
            authArea.innerHTML = `
                <div style="display: flex; align-items: center; gap: 12px;">
                    ${cartIconHtml}
                    <div style="display: flex; align-items: center; gap: 8px; background: var(--color-primary-light); padding: 4px 12px; border-radius: 12px; border: 1px solid var(--color-primary-light);">
                        <div style="text-align: right; line-height: 1;">
                            <span style="font-size: 0.55rem; color: var(--color-primary); font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;" class="desktop-only-badge">Client Privilège</span>
                            <p style="font-weight: 800; color: var(--color-primary-dark); font-size: 0.85rem;">${user.name.split(' ')[0]}</p>
                        </div>
                        <button id="logoutBtn" style="background: white; border: none; color: var(--color-primary); cursor: pointer; padding: 6px; border-radius: 8px; box-shadow: var(--shadow-soft);" title="Déconnexion">
                            <i data-lucide="log-out" style="width: 16px;"></i>
                        </button>
                    </div>
                </div>
            `;
            document.getElementById('logoutBtn').onclick = () => AuthService.logout();
        } else {
            authArea.innerHTML = `
                <div style="display: flex; align-items: center; gap: 16px;">
                    ${cartIconHtml}
                    <a href="account/login.html" class="btn btn-primary" style="padding: 8px 16px; font-size: 0.8rem; border-radius: 10px;">Connexion</a>
                </div>
            `;
        }
        if (window.lucide) lucide.createIcons();
    }

    // --- 3. RENDERING ---

    function renderAppProducts() {
        if (!productGrid) return;
        
        // Filtering
        let filtered = allProducts.filter(p => {
            const matchesSearch = p.name.toLowerCase().includes(currentSearch);
            const matchesCategory = currentCategory === 'all' || p.category === currentCategory;
            const matchesPrice = p.price <= currentMaxPrice;
            const matchesStock = !currentInStockOnly || p.stock > 0;
            return matchesSearch && matchesCategory && matchesPrice && matchesStock;
        });

        // Sorting
        if (currentSort === 'price-asc') filtered.sort((a,b) => a.price - b.price);
        else if (currentSort === 'price-desc') filtered.sort((a,b) => b.price - a.price);
        else if (currentSort === 'newest') filtered.reverse();

        productGrid.innerHTML = '';
        const noResults = document.getElementById('no-results');
        if (filtered.length === 0) { if (noResults) noResults.style.display = 'block'; return; }
        if (noResults) noResults.style.display = 'none';

        filtered.forEach((p, idx) => {
            const card = document.createElement('div');
            card.className = 'product-card animate-fade-in';
            card.style.animationDelay = `${idx * 0.05}s`;
            
            const price = parseInt(p.price).toLocaleString();
            const hasStock = p.stock > 0;

            card.innerHTML = `
                <div class="product-image-wrapper">
                    <img src="${p.image}" alt="${p.name}" class="product-image" loading="lazy">
                    <div class="product-overlay">
                        <button class="overlay-btn" onclick="openQuickView('${p.id}')" title="Voir les détails">
                            <i data-lucide="eye"></i>
                        </button>
                        <button class="overlay-btn" onclick="addToCart('${p.id}')" title="Ajout rapide">
                            <i data-lucide="shopping-cart"></i>
                        </button>
                    </div>
                    ${!hasStock ? '<div style="position: absolute; inset: 0; background: rgba(255,255,255,0.7); display: flex; align-items: center; justify-content: center; font-weight: 800; color: var(--color-danger); font-size: 0.8rem; text-transform: uppercase; z-index: 5;">Rupture</div>' : ''}
                    <div class="product-badge">
                        <i data-lucide="shield-check" style="width: 12px;"></i> VERIFIED
                    </div>
                </div>
                <div class="product-info">
                    <div class="product-category">${p.category}</div>
                    <h3 class="product-title" style="line-clamp: 2; -webkit-line-clamp: 2; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; height: 2.8rem;">${p.name}</h3>
                    
                    <div style="margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end;">
                        <div>
                            <div class="product-price" style="font-size: 1.25rem;">${price} <span style="font-size: 0.75rem;">XOF</span></div>
                            <div style="font-size: 0.7rem; color: var(--color-success); font-weight: 800; margin-top: 4px; display: flex; align-items: center; gap: 4px;">
                                <i data-lucide="truck" style="width: 12px;"></i> Livraison 24h
                            </div>
                        </div>
                        <button class="btn btn-primary" onclick="addToCart('${p.id}'); event.stopPropagation();" style="padding: 10px; border-radius: 12px; min-width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 16px rgba(43, 89, 162, 0.15);">
                            <i data-lucide="shopping-bag" style="width: 20px;"></i>
                        </button>
                    </div>
                </div>
            `;
            productGrid.appendChild(card);
            // Initialize icons for this card only
            if (window.lucide) lucide.createIcons({
                attrs: { "stroke-width": 2.5 },
                nameAttr: 'data-lucide',
                root: card
            });
        });
    }

    function renderCartDrawer() {
        if (!cartDrawerItems) return;
        const items = Cart.getItems();
        const total = Cart.getTotal();
        const drawerSummary = document.getElementById('cartDrawerSummary');

        if (drawerTotal) drawerTotal.textContent = total.toLocaleString() + ' XOF';
        cartDrawerItems.innerHTML = '';

        if (items.length === 0) {
            if (drawerSummary) drawerSummary.style.display = 'none';
            cartDrawerItems.innerHTML = `
                <div style="text-align: center; padding: 64px 0; color: var(--color-muted);">
                    <div style="width: 80px; height: 80px; background: var(--color-muted-light); border-radius: var(--radius-full); display: flex; align-items: center; justify-content: center; margin: 0 auto 24px;">
                        <i data-lucide="shopping-bag" style="width: 40px; height: 40px; opacity: 0.5;"></i>
                    </div>
                    <h4 style="margin-bottom: 8px;">Votre panier est vide</h4>
                    <p style="font-size: 0.9rem;">Ajoutez des articles pour commencer votre shopping.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        if (drawerSummary) drawerSummary.style.display = 'block';

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'cart-item';
            div.style.marginBottom = '24px';
            div.innerHTML = `
                <img src="${item.image}" alt="${item.name}" style="width: 70px; height: 70px;">
                <div class="cart-item-info">
                    <div class="cart-item-title" style="font-size: 0.95rem;">${item.name}</div>
                    <div class="cart-item-price" style="font-size: 1rem;">${item.price.toLocaleString()} XOF</div>
                    <div class="quantity-controls">
                        <button class="qty-btn" onclick="updateQty('${item.id}', -1)"><i data-lucide="minus" style="width: 12px;"></i></button>
                        <span style="font-weight: 800; font-size: 0.9rem;">${item.quantity}</span>
                        <button class="qty-btn" onclick="updateQty('${item.id}', 1)"><i data-lucide="plus" style="width: 12px;"></i></button>
                    </div>
                </div>
                <button onclick="removeFromCart('${item.id}')" style="background: none; border: none; color: var(--color-error); padding: 8px; cursor: pointer; opacity: 0.6;">
                    <i data-lucide="trash-2" style="width: 18px;"></i>
                </button>
            `;
            cartDrawerItems.appendChild(div);
        });
        if (window.lucide) lucide.createIcons();
    }

    // --- 4. GLOBAL ACTIONS ---

    window.addToCart = function(id, qty = 1) {
        const product = allProducts.find(p => p.id === id);
        if (product) {
            Cart.add(product, qty);
            UI.showToast(`${product.name} ajouté au panier !`, 'success');
            // NO auto-toggle drawer here for seamless pro experience
        }
    };

    window.removeFromCart = function(id) {
        Cart.remove(id);
        renderCartDrawer();
    };

    window.updateQty = function(id, delta) {
        Cart.updateQuantity(id, delta);
        renderCartDrawer();
    };

    window.resetFilters = function() {
        currentCategory = 'all';
        currentSearch = '';
        currentSort = 'default';
        currentMaxPrice = 5000000;
        currentInStockOnly = false;

        if (storeSearch) storeSearch.value = '';
        if (storeSort) storeSort.value = 'default';
        
        const priceRange = document.getElementById('priceRange');
        const priceDisplay = document.getElementById('priceValueDisplay');
        const inStockToggle = document.getElementById('inStockToggle');
        
        if (priceRange) priceRange.value = 5000000;
        if (priceDisplay) priceDisplay.textContent = 'Tout';
        if (inStockToggle) inStockToggle.checked = false;

        document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
const allBtn = document.querySelector('[data-category="all"]');
        if (allBtn) allBtn.classList.add('active');
        renderAppProducts();
    };

    // --- 5. QUICK VIEW LOGIC ---

    window.openQuickView = function(id) {
        const p = allProducts.find(x => x.id === id);
        if (!p) return;

        // --- MEDIA GALLERY LOGIC ---
        const mediaData = typeof p.media === 'string' ? JSON.parse(p.media || '[]') : (p.media || []);
        const mediaContainer = document.getElementById('qv-image-container');
        
        if (mediaData.length > 0) {
            // Support multi-media gallery
            mediaContainer.innerHTML = `
                <div class="qv-gallery-wrapper" style="width: 100%; height: 100%; position: relative;">
                    <div id="qv-media-stage" style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #F8FAFC;">
                        <!-- Current active media will be here -->
                    </div>
                    
                    <div class="qv-thumbnails" style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); display: flex; gap: 8px; z-index: 20; background: rgba(255,255,255,0.8); padding: 8px; border-radius: 12px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.3); max-width: 90%; overflow-x: auto;">
                        <div class="thumb active" onclick="setQVMedia('image', '${p.image}', this)" style="width: 40px; height: 40px; border-radius: 6px; overflow: hidden; cursor: pointer; border: 2px solid var(--color-primary); flex-shrink: 0;">
                            <img src="${p.image}" style="width:100%; height:100%; object-fit:cover;">
                        </div>
                        ${mediaData.map(m => `
                            <div class="thumb" onclick="setQVMedia('${m.type}', '${m.url}', this)" style="width: 40px; height: 40px; border-radius: 6px; overflow: hidden; cursor: pointer; border: 2px solid transparent; flex-shrink: 0; position: relative;">
                                ${m.type === 'video' ? '<div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,0.2); color:white;"><i data-lucide="play" style="width:16px;"></i></div>' : ''}
                                <img src="${m.type === 'video' ? 'assets/logo.png' : m.url}" style="width:100%; height:100%; object-fit:cover;">
                            </div>
                        `).join('')}
                    </div>

                    <div style="position: absolute; top: 20px; left: 20px; z-index: 10;">
                        <span style="background: white; padding: 6px 12px; border-radius: 8px; font-weight: 800; font-size: 0.7rem; color: var(--color-primary); box-shadow: var(--shadow-sm); display: flex; align-items: center; gap: 4px;">
                            <i data-lucide="shield-check" style="width: 12px;"></i> EXCLUSIVITÉ
                        </span>
                    </div>
                </div>
            `;
            // Set initial media
            setQVMedia('image', p.image);
        } else {
            // Legacy single image view
            mediaContainer.innerHTML = `
                <img src="${p.image}" style="width: 100%; height: 100%; object-fit: contain; transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);" id="qv-main-img">
                <div style="position: absolute; top: 20px; left: 20px; z-index: 10;">
                    <span style="background: white; padding: 6px 12px; border-radius: 8px; font-weight: 800; font-size: 0.7rem; color: var(--color-primary); box-shadow: var(--shadow-sm); display: flex; align-items: center; gap: 4px;">
                        <i data-lucide="shield-check" style="width: 12px;"></i> VERIFIED
                    </span>
                </div>
            `;
        }
        document.getElementById('qv-category').textContent = p.category;
        document.getElementById('qv-title').textContent = p.name;
        document.getElementById('qv-price').textContent = p.price.toLocaleString() + ' XOF';
        
        const infoContainer = document.getElementById('qv-info-container');
        const existingAction = infoContainer.querySelector('.sticky-action-area');
        if (existingAction) existingAction.remove();

        const actionArea = document.createElement('div');
        actionArea.className = 'sticky-action-area';
        actionArea.style.cssText = 'display: flex; gap: 12px; margin-top: 32px;';
        actionArea.innerHTML = `
            <button class="btn btn-outline" style="flex: 1; padding: 16px; border-radius: 12px;" onclick="addToCart('${p.id}'); UI.showToast('Ajouté au panier', 'success');">
                <i data-lucide="shopping-cart" style="margin-right: 8px;"></i> Panier
            </button>
            <button class="btn btn-primary" style="flex: 2; padding: 16px; border-radius: 12px;" onclick="addToCart('${p.id}'); window.location.href='checkout.html';">
                Acheter maintenant
            </button>
        `;
        infoContainer.appendChild(actionArea);

        const intro = "Un produit d'exception sélectionné par Douéra Shop pour sa qualité supérieure et son design élégant.";
        document.getElementById('qv-description').textContent = p.description ? `${intro} ${p.description}` : intro;
        
        // Technical Specs
        const specsContainer = document.getElementById('qv-specs-container');
        if (specsContainer) {
            specsContainer.innerHTML = '';
            if (p.specs) {
                const specsList = p.specs.split('|');
                specsList.forEach(spec => {
                    const badge = document.createElement('span');
                    badge.style.cssText = `background: #F1F5F9; color: var(--color-primary-dark); padding: 6px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; border: 1px solid var(--color-border);`;
                    badge.textContent = spec.trim();
                    specsContainer.appendChild(badge);
                });
            }
        }
        
        // Stock Indicator
        const stockBadge = document.getElementById('qv-stock-badge');
        if (p.stock <= 0) {
            stockBadge.innerHTML = '<span style="width: 8px; height: 8px; background: #EF4444; border-radius: 50%;"></span> Rupture de stock';
            stockBadge.style.color = '#EF4444';
        } else if (p.stock < 5) {
            stockBadge.innerHTML = '<span style="width: 8px; height: 8px; background: #F59E0B; border-radius: 50%;"></span> Plus que ' + p.stock + ' en stock';
            stockBadge.style.color = '#F59E0B';
        } else {
            stockBadge.innerHTML = '<span style="width: 8px; height: 8px; background: #10B981; border-radius: 50%;"></span> En Stock';
            stockBadge.style.color = '#10B981';
        }

        const addBtn = document.getElementById('qv-add-btn');
        const qtyInput = document.getElementById('qv-qty-input');
        if (qtyInput) qtyInput.value = 1; 

        addBtn.onclick = () => { 
            const qty = qtyInput ? parseInt(qtyInput.value) || 1 : 1;
            addToCart(p.id, qty); 
            closeQuickView(); 
        };
        
        // WhatsApp Share
        const shareBtn = document.getElementById('qv-whatsapp-share');
        if (shareBtn) {
            const shareText = encodeURIComponent(`Salam ! Regarde cette pépite sur Douéra Shop : *${p.name}* à ${p.price.toLocaleString()} XOF. C'est magnifique ! \n\nLien : ${window.location.href}`);
            shareBtn.href = `https://wa.me/?text=${shareText}`;
        }

        // Render Stars
        const starsContainer = document.getElementById('qv-stars');
        if (starsContainer) {
            starsContainer.innerHTML = '';
            for (let i = 0; i < 5; i++) {
                const star = document.createElement('i');
                star.dataset.lucide = 'star';
                star.style.cssText = `width: 18px; height: 18px; fill: #F59E0B;`;
                starsContainer.appendChild(star);
            }
        }
        document.getElementById('qv-rating-text').textContent = "4.9 (24 avis vérifiés)";

        // Render FAQ
        renderProductFAQ(p);
        
        // Render Reviews
        renderProductReviews(p);

        qvModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Render Similar Products
        renderSimilarProducts(p);
        
        if (window.lucide) lucide.createIcons();
    };

    function renderSimilarProducts(currentProduct) {
        const container = document.getElementById('qv-similar-products');
        if (!container) return;

        const similar = allProducts
            .filter(p => p.category === currentProduct.category && p.id !== currentProduct.id)
            .slice(0, 4);

        if (similar.length === 0) {
            container.parentElement.style.display = 'none';
            return;
        }

        container.parentElement.style.display = 'block';
        container.innerHTML = '';
        
        similar.forEach(p => {
            const div = document.createElement('div');
            div.style.cssText = `background: white; border-radius: 16px; overflow: hidden; border: 1px solid var(--color-border); transition: var(--transition-base); cursor: pointer;`;
            div.onclick = () => {
                document.querySelector('.modal-content').scrollTop = 0;
                openQuickView(p.id);
            };
            div.onmouseover = () => div.style.transform = 'translateY(-5px)';
            div.onmouseout = () => div.style.transform = 'translateY(0)';

            div.innerHTML = `
                <div style="height: 140px; overflow: hidden; background: #f8fafc;">
                    <img src="${p.image}" style="width: 100%; height: 100%; object-fit: contain;">
                </div>
                <div style="padding: 12px;">
                    <div style="font-weight: 800; font-size: 0.85rem; color: var(--color-primary-dark); margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;">${p.name}</div>
                    <div style="font-weight: 800; color: var(--color-primary); font-size: 0.9rem;">${p.price.toLocaleString()} XOF</div>
                </div>
            `;
            container.appendChild(div);
        });
    }

    function renderProductFAQ(product) {
        const container = document.getElementById('qv-faq-items');
        if (!container) return;

        const faqs = [
            { q: "Quelle est la durée de la livraison ?", a: "La livraison à Douéra et Dakar se fait généralement sous 24h. Pour les autres régions du Sénégal, comptez 48h à 72h." },
            { q: "Le produit est-il original ?", a: "Oui, Douéra Shop s'approvisionne directement auprès de fournisseurs agréés à l'international pour garantir l'authenticité de chaque pépite." },
            { q: "Quels sont les modes de paiement ?", a: "Nous acceptons Wave, Orange Money et le paiement en espèces à la livraison pour votre totale tranquillité d'esprit." }
        ];

        // Add category specific FAQ
        if (product.category === 'Électronique' || product.category === 'Téléphone') {
            faqs.push({ q: "Y a-t-il une garantie ?", a: "Tous nos produits électroniques bénéficient d'une garantie de 6 mois contre tout défaut de fabrication." });
        }

        container.innerHTML = '';
        faqs.forEach((faq, index) => {
            const item = document.createElement('div');
            item.style.cssText = `border: 1px solid var(--color-border); border-radius: 12px; overflow: hidden;`;
            item.innerHTML = `
                <div class="faq-trigger" style="padding: 12px 16px; background: #F8FAFC; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; font-weight: 700;">
                    <span>${faq.q}</span>
                    <i data-lucide="chevron-down" style="width: 14px; transition: 0.3s;"></i>
                </div>
                <div class="faq-content" style="padding: 0 16px; max-height: 0; overflow: hidden; transition: all 0.3s ease-out; font-size: 0.8rem; color: var(--color-muted); background: white;">
                    <div style="padding: 12px 0;">${faq.a}</div>
                </div>
            `;
            
            item.querySelector('.faq-trigger').onclick = function() {
                const content = this.nextElementSibling;
                const icon = this.querySelector('i');
                const isOpen = content.style.maxHeight !== '0px' && content.style.maxHeight !== '';
                
                // Close all others
                document.querySelectorAll('.faq-content').forEach(c => c.style.maxHeight = '0');
                document.querySelectorAll('.faq-trigger i').forEach(i => i.style.transform = 'rotate(0)');

                if (!isOpen) {
                    content.style.maxHeight = '100px';
                    icon.style.transform = 'rotate(180deg)';
                }
            };
            
            container.appendChild(item);
        });
        if (window.lucide) lucide.createIcons();
    }

    async function renderProductReviews(product) {
        const container = document.getElementById('qv-reviews-list');
        if (!container) return;

        const API_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') 
            ? 'http://127.0.0.1:5001/api' 
            : '/api';
        
        let allReviews = [];
        try {
            const res = await fetch(`${API_BASE_URL}/reviews`);
            if (res.ok) {
                const data = await res.json();
                // Filtrage robuste (gère productId et productid)
                allReviews = data.filter(r => (r.productId === product.id) || (r.productid === product.id));
            }
        } catch (e) {
            console.error("Erreur chargement avis", e);
        }

        container.innerHTML = '';
        
        if (allReviews.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; background: #F8FAFC; border-radius: 20px; border: 2px dashed #E2E8F0;">
                    <i data-lucide="message-square" style="width: 48px; height: 48px; color: #CBD5E1; margin-bottom: 16px;"></i>
                    <h3 style="color: var(--color-primary-dark); margin-bottom: 8px;">Aucun avis pour le moment</h3>
                    <p style="color: var(--color-muted); font-size: 0.9rem;">Soyez le premier à partager votre expérience après votre achat !</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        allReviews.forEach(review => {
            const date = new Date(review.date || review.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
            const uName = review.userName || review.username || 'Client Douéra';
            const rProd = parseInt(review.rating_product || review.ratingproduct || 5);

            const div = document.createElement('div');
            div.style.cssText = `padding: 24px; background: #FFF; border-radius: 20px; border: 1px solid #F1F5F9; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);`;
            
            div.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                    <div>
                        <div style="font-weight: 800; font-size: 1rem; color: var(--color-primary-dark);">${uName}</div>
                        <div style="display: flex; gap: 4px; color: #F59E0B; margin-top: 6px;">
                            ${Array(rProd).fill('<i data-lucide="star" style="width: 14px; height: 14px; fill: currentColor;"></i>').join('')}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 0.75rem; color: var(--color-muted);">${date}</span>
                        <div style="display: flex; align-items: center; gap: 4px; color: var(--color-success); font-size: 0.7rem; font-weight: 800; margin-top: 6px;">
                            <i data-lucide="check-circle-2" style="width: 14px;"></i> ACHAT VÉRIFIÉ
                        </div>
                    </div>
                </div>
                <p style="font-size: 0.95rem; color: var(--color-foreground); line-height: 1.6; font-style: italic;">"${review.comment}"</p>
                
                ${review.admin_reply ? `
                    <div style="margin-top: 20px; padding: 16px; background: rgba(43, 89, 162, 0.04); border-radius: 12px; border-left: 4px solid var(--color-primary);">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <img src="assets/logo.png" style="width: 20px; height: 20px; border-radius: 4px; object-fit: contain;">
                            <span style="font-size: 0.75rem; font-weight: 800; color: var(--color-primary); text-transform: uppercase;">Réponse de Douéra Shop</span>
                        </div>
                        <p style="font-size: 0.85rem; color: var(--color-primary-dark); line-height: 1.5;">${review.admin_reply}</p>
                    </div>
                ` : ''}
            `;
            container.appendChild(div);
        });
        if (window.lucide) lucide.createIcons();
    }

    window.changeQVQty = function(delta) {
        const input = document.getElementById('qv-qty-input');
        if (!input) return;
        let val = parseInt(input.value) + delta;
        if (val < 1) val = 1;
        input.value = val;
    };

    window.closeQuickView = function() {
        if (qvModal) qvModal.classList.remove('active');
        document.body.style.overflow = '';
    };

    function initHeroBackground() {
        // Delay background initialization to prioritize main content
        setTimeout(() => {
            const track1 = document.getElementById('hero-track-1');
            const track2 = document.getElementById('hero-track-2');
            const slider = document.getElementById('hero-bg-slider');
            
            if (!track1 || !track2 || !allProducts.length) return;

            track1.innerHTML = '';
            track2.innerHTML = '';

            const pool = [...allProducts].sort(() => 0.5 - Math.random());
            const items = pool.slice(0, 6); // Limit to 6 items for performance

            const createImg = (p) => {
                const img = document.createElement('img');
                img.src = p.image;
                img.className = 'hero-bg-img';
                img.loading = 'lazy'; // Don't block critical path
                img.alt = p.name;
                img.onerror = () => { img.src = 'assets/electronics_1.png'; };
                return img;
            };

            items.forEach(p => track1.appendChild(createImg(p)));
            items.forEach(p => track1.appendChild(createImg(p)));

            const items2 = [...items].reverse();
            items2.forEach(p => track2.appendChild(createImg(p)));
            items2.forEach(p => track2.appendChild(createImg(p)));

            if (slider) slider.style.display = 'flex';
        }, 1500); // 1.5s delay
    }

    window.setQVMedia = function(type, url, thumb = null) {
        const stage = document.getElementById('qv-media-stage');
        if (!stage) return;

        if (thumb) {
            document.querySelectorAll('.qv-thumbnails .thumb').forEach(t => t.style.borderColor = 'transparent');
            thumb.style.borderColor = 'var(--color-primary)';
        }

        if (type === 'video') {
            // Extract ID if YouTube, else use raw URL
            let videoHtml = '';
            if (url.includes('youtube.com') || url.includes('youtu.be')) {
                const id = url.includes('v=') ? url.split('v=')[1].split('&')[0] : url.split('/').pop();
                videoHtml = `<iframe width="100%" height="100%" src="https://www.youtube.com/embed/${id}?autoplay=1&mute=1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border-radius:0;"></iframe>`;
            } else {
                videoHtml = `<video src="${url}" controls autoplay muted style="width:100%; height:100%; object-fit:contain; background:black;"></video>`;
            }
            stage.innerHTML = videoHtml;
        } else {
            stage.innerHTML = `<img src="${url}" style="width: 100%; height: 100%; object-fit: contain; animation: fadeScale 0.5s ease-out;">`;
        }
        if (window.lucide) lucide.createIcons();
    };

    // --- 6. SCROLL REVEAL ANIMATIONS ---
    function initScrollReveal() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    // Optional: remove observer if we only want it to animate once
                    // observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        const revealElements = document.querySelectorAll('.reveal-up');
        revealElements.forEach(el => observer.observe(el));
    }

    // --- BOOTSTRAP ---
    init().then(() => {
        // Initializer scroll anims après le render
        setTimeout(initScrollReveal, 100);
    });
});
