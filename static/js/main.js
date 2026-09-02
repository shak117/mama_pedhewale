// Mama Pedhewale - Main Client Script

const CART_STORAGE_KEY = 'mama_pedhewale_cart';
const FREE_SHIPPING_THRESHOLD = 799;

// ==================== CART MANAGEMENT ====================

function getCart() {
    try {
        const data = localStorage.getItem(CART_STORAGE_KEY);
        return data ? JSON.parse(data) : [];
    } catch (e) {
        console.error('Failed to parse cart data:', e);
        return [];
    }
}

function saveCart(cart) {
    try {
        localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
        updateCartBadge();
        renderCartDrawer();
    } catch (e) {
        console.error('Failed to save cart:', e);
    }
}

function addToCart(product) {
    const cart = getCart();
    
    // Check if same item with same weight exists (custom boxes are always unique or match contents)
    const existingIndex = cart.findIndex(item => 
        item.id === product.id && 
        item.weight === product.weight && 
        !item.is_custom_box
    );

    if (existingIndex > -1) {
        cart[existingIndex].quantity += (product.quantity || 1);
    } else {
        cart.push({
            id: product.id,
            name: product.name,
            name_mr: product.name_mr || '',
            price: parseInt(product.price),
            weight: product.weight || '500g',
            quantity: product.quantity || 1,
            image_url: product.image_url,
            is_custom_box: product.is_custom_box || false,
            box_contents: product.box_contents || null
        });
    }

    saveCart(cart);
    showToast('Added to Mithai Box!', `${product.name} (${product.weight || '500g'}) added to your order.`);
    openCartDrawer();
}

function updateCartQuantity(index, delta) {
    const cart = getCart();
    if (cart[index]) {
        cart[index].quantity += delta;
        if (cart[index].quantity <= 0) {
            cart.splice(index, 1);
            showToast('Item Removed', 'Sweet removed from your basket.');
        }
        saveCart(cart);
    }
}

function removeFromCart(index) {
    const cart = getCart();
    if (cart[index]) {
        const item = cart[index];
        cart.splice(index, 1);
        saveCart(cart);
        showToast('Item Removed', `${item.name} removed from your basket.`);
    }
}

function clearCart() {
    localStorage.removeItem(CART_STORAGE_KEY);
    updateCartBadge();
    renderCartDrawer();
}

function getCartSubtotal() {
    const cart = getCart();
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

function updateCartBadge() {
    const cart = getCart();
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    const badge = document.getElementById('cart-badge-count');
    const totalCountEl = document.getElementById('cart-items-total-count');
    if (badge) badge.innerText = count;
    if (totalCountEl) totalCountEl.innerText = count;
}

function renderCartDrawer() {
    const cart = getCart();
    const container = document.getElementById('cart-items-container');
    const emptyState = document.getElementById('cart-empty-state');
    const cartFooter = document.getElementById('cart-footer');
    const subtotalEl = document.getElementById('cart-subtotal-val');
    const totalEl = document.getElementById('cart-total-val');
    const freeDeliveryMsg = document.getElementById('free-delivery-msg');
    const freeDeliveryLeft = document.getElementById('free-delivery-amount-left');
    const freeDeliveryProgress = document.getElementById('free-delivery-progress');

    if (!container) return;

    const subtotal = getCartSubtotal();

    // Free delivery calculation
    if (subtotal >= FREE_SHIPPING_THRESHOLD) {
        if (freeDeliveryMsg) {
            freeDeliveryMsg.innerHTML = `<span class="text-green-800 font-semibold flex items-center gap-1.5"><i data-lucide="sparkles" class="w-4 h-4 text-brand-gold"></i> Congratulations! You've unlocked <strong>FREE Express Shipping</strong>!</span>`;
        }
        if (freeDeliveryProgress) {
            freeDeliveryProgress.style.width = '100%';
            freeDeliveryProgress.classList.add('bg-green-600');
        }
    } else {
        const needed = FREE_SHIPPING_THRESHOLD - subtotal;
        if (freeDeliveryLeft) freeDeliveryLeft.innerText = needed;
        if (freeDeliveryMsg) {
            freeDeliveryMsg.innerHTML = `<span>Add ₹<strong>${needed}</strong> more for <strong>FREE Express Shipping</strong>!</span><i data-lucide="truck" class="w-4 h-4 text-brand-maroon"></i>`;
        }
        if (freeDeliveryProgress) {
            const pct = Math.min(100, Math.round((subtotal / FREE_SHIPPING_THRESHOLD) * 100));
            freeDeliveryProgress.style.width = `${pct}%`;
            freeDeliveryProgress.classList.remove('bg-green-600');
        }
    }

    if (subtotalEl) subtotalEl.innerText = subtotal;
    if (totalEl) totalEl.innerText = subtotal;

    if (cart.length === 0) {
        if (container) container.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
        if (cartFooter) cartFooter.classList.add('opacity-50', 'pointer-events-none');
        return;
    }

    if (container) container.classList.remove('hidden');
    if (emptyState) emptyState.classList.add('hidden');
    if (cartFooter) cartFooter.classList.remove('opacity-50', 'pointer-events-none');

    // Build Cart HTML
    let html = '';
    cart.forEach((item, idx) => {
        let customBoxBadge = '';
        if (item.is_custom_box && item.box_contents) {
            const contentsText = Object.values(item.box_contents).map(s => s.name).join(', ');
            customBoxBadge = `
                <div class="mt-1 text-[11px] bg-amber-50 text-amber-900 px-2 py-0.5 rounded border border-amber-200">
                    <span class="font-bold">Contents:</span> ${contentsText}
                </div>
            `;
        }

        html += `
            <div class="flex gap-3 pt-3 first:pt-0">
                <img src="${item.image_url || '/static/images/satara_kandi_pedha.jpg'}" alt="${item.name}" class="w-16 h-16 object-cover rounded-xl border border-amber-100 shrink-0">
                <div class="flex-grow flex flex-col justify-between">
                    <div>
                        <div class="flex items-start justify-between">
                            <h4 class="font-semibold text-sm text-gray-800 line-clamp-1">${item.name}</h4>
                            <button onclick="removeFromCart(${idx})" class="text-gray-400 hover:text-red-600 p-1 transition" title="Remove">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                        <div class="flex items-center gap-2 mt-0.5">
                            <span class="text-xs text-brand-maroon font-medium bg-amber-50 px-1.5 py-0.5 rounded">${item.weight}</span>
                            <span class="text-xs text-gray-500">₹${item.price} each</span>
                        </div>
                        ${customBoxBadge}
                    </div>
                    
                    <div class="flex items-center justify-between mt-2">
                        <div class="flex items-center border border-gray-200 rounded-lg bg-white overflow-hidden">
                            <button onclick="updateCartQuantity(${idx}, -1)" class="px-2 py-0.5 text-gray-500 hover:bg-gray-100 transition">-</button>
                            <span class="px-2.5 py-0.5 text-xs font-semibold text-gray-800">${item.quantity}</span>
                            <button onclick="updateCartQuantity(${idx}, 1)" class="px-2 py-0.5 text-gray-500 hover:bg-gray-100 transition">+</button>
                        </div>
                        <span class="font-bold text-sm text-brand-maroon">₹${item.price * item.quantity}</span>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    if (window.lucide) {
        lucide.createIcons();
    }
}

// ==================== DRAWER TOGGLES ====================

function openCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-drawer-overlay');
    if (drawer && overlay) {
        drawer.classList.remove('translate-x-full');
        overlay.classList.remove('opacity-0', 'pointer-events-none');
        document.body.classList.add('overflow-hidden');
    }
}

function closeCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-drawer-overlay');
    if (drawer && overlay) {
        drawer.classList.add('translate-x-full');
        overlay.classList.add('opacity-0', 'pointer-events-none');
        document.body.classList.remove('overflow-hidden');
    }
}

// ==================== TOAST SYSTEM ====================

function showToast(title, message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `pointer-events-auto flex items-start gap-3 p-4 bg-white rounded-xl shadow-xl border border-amber-200 transform translate-y-4 opacity-0 transition-all duration-300 max-w-sm`;

    const icon = type === 'success' 
        ? `<div class="p-1 bg-green-100 text-green-700 rounded-full"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg></div>`
        : `<div class="p-1 bg-amber-100 text-amber-700 rounded-full"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div>`;

    toast.innerHTML = `
        ${icon}
        <div class="flex-grow">
            <h5 class="text-xs font-bold text-gray-900">${title}</h5>
            <p class="text-xs text-gray-600 mt-0.5">${message}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="text-gray-400 hover:text-gray-600">✕</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('translate-y-4', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-4');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ==================== WHATSAPP ORDER ====================

function orderOnWhatsApp() {
    const cart = getCart();
    if (cart.length === 0) {
        showToast('Cart is Empty', 'Please add some sweets before ordering via WhatsApp.', 'info');
        return;
    }

    const subtotal = getCartSubtotal();
    let msg = `*Namaskar Mama Pedhewale!*%0A%0AI would like to order the following fresh sweets:%0A`;

    cart.forEach((item, i) => {
        msg += `%0A${i + 1}. *${encodeURIComponent(item.name)}* - ${item.weight} x ${item.quantity} = Rs. ${item.price * item.quantity}`;
        if (item.is_custom_box && item.box_contents) {
            const contents = Object.values(item.box_contents).map(s => s.name).join(', ');
            msg += ` (Custom Box: ${encodeURIComponent(contents)})`;
        }
    });

    msg += `%0A%0A*Total Amount:* Rs. ${subtotal}`;
    msg += `%0A*Delivery Request:* Please deliver fresh batch to my address.`;

    const waUrl = `https://wa.me/919822012345?text=${msg}`;
    window.open(waUrl, '_blank');
}

// ==================== SEARCH MODAL ====================

function openSearchModal() {
    const modal = document.getElementById('search-modal');
    const input = document.getElementById('search-modal-input');
    if (modal) {
        modal.classList.remove('hidden');
        if (input) {
            input.focus();
            input.value = '';
            fetchSearchResults('');
        }
    }
}

function closeSearchModal() {
    const modal = document.getElementById('search-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function quickSearchTag(tag) {
    const input = document.getElementById('search-modal-input');
    if (input) {
        input.value = tag;
        fetchSearchResults(tag);
    }
}

let searchDebounceTimeout = null;
function fetchSearchResults(query) {
    clearTimeout(searchDebounceTimeout);
    searchDebounceTimeout = setTimeout(() => {
        fetch(`/api/products?search=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(products => {
                const container = document.getElementById('search-items-target');
                if (!container) return;

                if (products.length === 0) {
                    container.innerHTML = `<p class="text-xs text-gray-500 text-center py-4">No sweets found matching "${query}". Try searching for Pedha, Laddu, or Barfi.</p>`;
                    return;
                }

                container.innerHTML = products.map(p => `
                    <a href="/product/${p.id}" class="flex items-center gap-3 p-2 hover:bg-amber-50 rounded-xl transition group">
                        <img src="${p.image_url}" alt="${p.name}" class="w-12 h-12 rounded-lg object-cover border border-amber-100">
                        <div class="flex-grow">
                            <h5 class="text-sm font-semibold text-gray-800 group-hover:text-brand-maroon">${p.name}</h5>
                            <span class="text-xs text-amber-700 font-devanagari">${p.name_mr}</span>
                        </div>
                        <div class="text-right">
                            <span class="text-xs text-gray-500">starts at</span>
                            <div class="font-bold text-sm text-brand-maroon">₹${p.price_250g}</div>
                        </div>
                    </a>
                `).join('');
            })
            .catch(err => console.error('Search error:', err));
    }, 200);
}

// ==================== DOM READY ATTACHMENTS ====================

document.addEventListener('DOMContentLoaded', () => {
    // Drawer buttons
    const cartBtn = document.getElementById('cart-drawer-btn');
    const closeBtn = document.getElementById('cart-close-btn');
    const overlay = document.getElementById('cart-drawer-overlay');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (cartBtn) cartBtn.addEventListener('click', openCartDrawer);
    if (closeBtn) closeBtn.addEventListener('click', closeCartDrawer);
    if (overlay) overlay.addEventListener('click', closeCartDrawer);

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Keyboard shortcut for search (Ctrl+K or Cmd+K)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearchModal();
        } else if (e.key === 'Escape') {
            closeSearchModal();
            closeCartDrawer();
        }
    });

    const searchInput = document.getElementById('search-modal-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => fetchSearchResults(e.target.value));
    }

    // Initialize cart count & contents
    updateCartBadge();
    renderCartDrawer();
});
