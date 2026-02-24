/* ══════════════════════════════════════════════════
   PinDrop Eats — API Helper + Shared Utilities
   ══════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:8000';

// ── Auth Helpers ────────────────────────────────────
function getToken() {
    return localStorage.getItem('pde_token');
}

function getUser() {
    const u = localStorage.getItem('pde_user');
    return u ? JSON.parse(u) : null;
}

function saveAuth(data) {
    localStorage.setItem('pde_token', data.access_token);
    localStorage.setItem('pde_user', JSON.stringify(data.user));
}

function logout() {
    localStorage.removeItem('pde_token');
    localStorage.removeItem('pde_user');
    window.location.href = 'index.html';
}

function requireAuth(role) {
    const user = getUser();
    if (!user || !getToken()) {
        window.location.href = 'index.html';
        return null;
    }
    if (role && user.role !== role) {
        window.location.href = getDashboardUrl(user.role);
        return null;
    }
    return user;
}

function getDashboardUrl(role) {
    const map = {
        admin: 'admin.html',
        owner: 'owner.html',
        customer: 'customer.html',
        delivery: 'delivery.html',
        care: 'care.html',
    };
    return map[role] || 'index.html';
}

// ── API Fetch Helper ────────────────────────────────
async function api(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
        const resp = await fetch(url, { ...options, headers });
        const data = await resp.json();
        if (!resp.ok) {
            throw new Error(data.detail || `HTTP ${resp.status}`);
        }
        return data;
    } catch (err) {
        if (err.message === 'Invalid or expired token') {
            logout();
        }
        throw err;
    }
}

async function apiGet(endpoint) {
    return api(endpoint, { method: 'GET' });
}

async function apiPost(endpoint, body) {
    return api(endpoint, { method: 'POST', body: JSON.stringify(body) });
}

async function apiPut(endpoint, body) {
    return api(endpoint, { method: 'PUT', body: body ? JSON.stringify(body) : undefined });
}

async function apiDelete(endpoint) {
    return api(endpoint, { method: 'DELETE' });
}

// ── Toast Notification ──────────────────────────────
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ── Tab System ──────────────────────────────────────
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabGroup = btn.closest('.tabs');
            const contentContainer = tabGroup.nextElementSibling?.classList.contains('tab-panels')
                ? tabGroup.nextElementSibling
                : tabGroup.parentElement;

            tabGroup.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const target = btn.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(tc => {
                tc.classList.toggle('active', tc.id === target);
            });

            // Trigger load for the target tab
            if (window.tabCallbacks && window.tabCallbacks[target]) {
                window.tabCallbacks[target]();
            }
        });
    });
}

// ── Status Badge Helper ─────────────────────────────
function statusBadge(status) {
    const cls = status.toLowerCase().replace(/\s+/g, '-');
    return `<span class="badge-status badge-${cls}">${status}</span>`;
}

// ── Order Timeline Helper ───────────────────────────
function renderTimeline(currentStatus) {
    const steps = ['Placed', 'Accepted', 'Preparing', 'Out for Delivery', 'Delivered'];
    const cancelled = currentStatus === 'Cancelled' || currentStatus === 'Rejected';
    const currentIdx = steps.indexOf(currentStatus);

    let html = '<div class="timeline">';
    steps.forEach((step, i) => {
        let cls = '';
        if (cancelled) {
            cls = i === 0 ? 'completed' : '';
        } else if (i < currentIdx) {
            cls = 'completed';
        } else if (i === currentIdx) {
            cls = 'active';
        }
        html += `
            <div class="timeline-step ${cls}">
                <div class="timeline-dot">${cls === 'completed' ? '✓' : i + 1}</div>
                <div class="timeline-label">${step}</div>
            </div>`;
    });
    html += '</div>';

    if (cancelled) {
        html += `<div class="text-center mt-1"><span class="badge-status badge-cancelled">${currentStatus}</span></div>`;
    }

    return html;
}

// ── Format Date ─────────────────────────────────────
function formatDate(dtStr) {
    const d = new Date(dtStr);
    return d.toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

// ── Format Currency ─────────────────────────────────
function formatPrice(n) {
    return `₹${Number(n).toFixed(2)}`;
}

// ── Navbar + Notifications ──────────────────────────
function renderNavbar(user) {
    return `
    <nav class="navbar">
        <div class="navbar-brand">🍽️ PinDrop<span>Eats</span></div>
        <div class="navbar-right">
            <div class="notification-bell" onclick="toggleNotifications()">
                🔔 <span class="badge" id="notif-count" style="display:none">0</span>
                <div class="notification-dropdown" id="notif-dropdown"></div>
            </div>
            <div class="navbar-user">
                <strong>${user.name}</strong> | ${user.role.toUpperCase()} | PIN: ${user.pin_code}
            </div>
            <button class="btn btn-sm btn-outline" onclick="logout()">Logout</button>
        </div>
    </nav>`;
}

async function loadNotifications() {
    try {
        const notifs = await apiGet('/api/notifications');
        const unread = notifs.filter(n => !n.is_read).length;
        const badge = document.getElementById('notif-count');
        if (badge) {
            badge.textContent = unread;
            badge.style.display = unread > 0 ? 'inline' : 'none';
        }
        const dropdown = document.getElementById('notif-dropdown');
        if (dropdown) {
            if (notifs.length === 0) {
                dropdown.innerHTML = '<div class="notif-item text-muted">No notifications</div>';
            } else {
                dropdown.innerHTML = notifs.map(n => `
                    <div class="notif-item ${n.is_read ? '' : 'unread'}">
                        <div>${n.message}</div>
                        <div class="notif-time">${formatDate(n.created_at)}</div>
                    </div>
                `).join('');
            }
        }
    } catch (e) {}
}

async function toggleNotifications() {
    const dd = document.getElementById('notif-dropdown');
    if (dd.classList.contains('show')) {
        dd.classList.remove('show');
    } else {
        dd.classList.add('show');
        await apiPut('/api/notifications/read');
        const badge = document.getElementById('notif-count');
        if (badge) { badge.style.display = 'none'; badge.textContent = '0'; }
    }
}

// Close notification dropdown on outside click
document.addEventListener('click', (e) => {
    if (!e.target.closest('.notification-bell')) {
        const dd = document.getElementById('notif-dropdown');
        if (dd) dd.classList.remove('show');
    }
});

// Auto-refresh notifications every 15 seconds
setInterval(loadNotifications, 15000);
