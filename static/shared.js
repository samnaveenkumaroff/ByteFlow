// shared.js — ByteFlow Mart JS utilities
const API = 'http://localhost:8000';

// ── Auth ──────────────────────────────────────────────
function getUser() {
  const u = localStorage.getItem('bf_user');
  return u ? JSON.parse(u) : null;
}
function requireAuth(role) {
  const u = getUser();
  if (!u) { window.location.href = '/'; return null; }
  if (role && u.role !== role) { window.location.href = '/'; return null; }
  return u;
}
function logout() {
  localStorage.removeItem('bf_user');
  window.location.href = '/';
}

// ── API helper ────────────────────────────────────────
async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API error');
  }
  return res.json();
}

// ── Toast ─────────────────────────────────────────────
function toast(msg, type = 'info', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', warn: '⚠️', info: 'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${msg}</span>`;
  container.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'toastOut .3s ease forwards';
    setTimeout(() => t.remove(), 300);
  }, duration);
}

// ── Loader ────────────────────────────────────────────
function showLoader(text = 'Loading...') {
  let el = document.getElementById('global-loader');
  if (!el) {
    el = document.createElement('div');
    el.id = 'global-loader';
    el.className = 'loader-overlay';
    el.innerHTML = `<div class="loader-ring"></div><div class="loader-text">${text}</div>`;
    document.body.appendChild(el);
  } else {
    el.querySelector('.loader-text').textContent = text;
    el.style.display = 'flex';
  }
}
function hideLoader() {
  const el = document.getElementById('global-loader');
  if (el) el.style.display = 'none';
}

// ── Modal ─────────────────────────────────────────────
function openModal(titleText, bodyHTML, footerHTML = '') {
  closeModal();
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'active-modal';
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div class="modal-title">${titleText}</div>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>
      <div class="modal-body">${bodyHTML}</div>
      ${footerHTML ? `<div class="modal-footer" style="margin-top:1.2rem;display:flex;gap:.6rem;justify-content:flex-end;">${footerHTML}</div>` : ''}
    </div>`;
  overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  document.body.appendChild(overlay);
}
function closeModal() {
  const m = document.getElementById('active-modal');
  if (m) m.remove();
}

// ── Ripple ────────────────────────────────────────────
function initRipple(selector = '.btn') {
  document.querySelectorAll(selector).forEach(btn => {
    if (btn.dataset.rpl) return;
    btn.dataset.rpl = '1';
    btn.addEventListener('click', function(e) {
      const r = document.createElement('span');
      r.className = 'ripple';
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX-rect.left-size/2}px;top:${e.clientY-rect.top-size/2}px;`;
      this.appendChild(r);
      setTimeout(() => r.remove(), 600);
    });
  });
}

// ── Animated counter ──────────────────────────────────
function animateCounters() {
  document.querySelectorAll('.metric-val[data-target]').forEach(el => {
    if (el.dataset.animated) return;
    el.dataset.animated = '1';
    const target   = parseFloat(el.dataset.target);
    const prefix   = el.dataset.prefix || '';
    const suffix   = el.dataset.suffix || '';
    const isFloat  = el.dataset.float === '1';
    const start    = performance.now();
    const duration = 900;
    function step(now) {
      const p = Math.min((now - start) / duration, 1);
      const e = 1 - Math.pow(1 - p, 3);
      const v = isFloat ? (e * target).toFixed(1) : Math.round(e * target).toLocaleString('en-IN');
      el.textContent = prefix + v + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
}

// ── Card tilt ─────────────────────────────────────────
function initTilt(selector = '.product-card') {
  document.querySelectorAll(selector).forEach(card => {
    if (card.dataset.tilt) return;
    card.dataset.tilt = '1';
    card.addEventListener('mousemove', e => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top)  / r.height - 0.5;
      card.style.transform = `translateY(-4px) rotateX(${-y*5}deg) rotateY(${x*5}deg)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
}

// ── Nav active ────────────────────────────────────────
function setActiveNav(pageId) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === pageId);
  });
}

// ── Tab switching ─────────────────────────────────────
function initTabs(containerSelector) {
  document.querySelectorAll(`${containerSelector} .tab`).forEach(tab => {
    tab.addEventListener('click', () => {
      const parent = tab.closest(containerSelector) || document;
      parent.querySelectorAll('.tab,.tab-content').forEach(el => el.classList.remove('active'));
      tab.classList.add('active');
      const content = parent.querySelector(`#${tab.dataset.tab}`);
      if (content) content.classList.add('active');
    });
  });
}

// ── Render helpers ────────────────────────────────────
function renderCompetitorRow(comp, ourPrice) {
  const diff      = ourPrice - comp.price;
  const diffColor = diff > 0 ? 'var(--red)' : 'var(--green)';
  const diffTxt   = diff > 0 ? `▲ ₹${Math.abs(diff).toLocaleString('en-IN')} above`
                              : `▼ ₹${Math.abs(diff).toLocaleString('en-IN')} below`;
  return `
  <div class="comp-row">
    <div>
      <div class="comp-platform">🌐 ${comp.platform.charAt(0).toUpperCase()+comp.platform.slice(1)}</div>
      <div class="comp-meta">⭐ ${comp.rating} &nbsp;·&nbsp; 🚚 ${comp.delivery_days}d</div>
    </div>
    <div style="text-align:right;">
      <div class="comp-price">₹${comp.price.toLocaleString('en-IN')}</div>
      <div class="comp-disc">${comp.discount}% off</div>
      <div class="comp-diff" style="color:${diffColor};">${diffTxt}</div>
    </div>
  </div>`;
}

function renderBundleCard(item) {
  return `
  <div class="bundle-card">
    <div style="flex:1;min-width:0;">
      <div style="font-weight:600;font-size:.84rem;color:var(--text-1);
                  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
        ${item.name}
      </div>
      <span class="badge badge-blue" style="margin-top:.2rem;display:inline-block;">
        ${item.category}
      </span>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:.75rem;">
      <div style="font-weight:800;color:var(--gold);font-size:.95rem;">
        ₹${item.price.toLocaleString('en-IN')}
      </div>
      <div style="font-size:.72rem;color:var(--green);font-weight:600;">${item.discount}% off</div>
    </div>
  </div>`;
}

function renderAlert(msg, type = 'error') {
  return `<div class="alert alert-${type}">${msg}</div>`;
}

function renderStepBar(steps, current) {
  let html = '<div class="step-bar">';
  steps.forEach((label, i) => {
    const n = i + 1;
    const state = n < current ? 'done' : n === current ? 'active' : 'idle';
    const icon  = n < current ? '✓' : String(n);
    html += `
    <div class="step-item">
      <div class="step-circle ${state}">${icon}</div>
      <div class="step-lbl ${state}">${label}</div>
    </div>`;
    if (i < steps.length - 1) {
      html += `<div class="step-line ${n < current ? 'done' : ''}"></div>`;
    }
  });
  html += '</div>';
  return html;
}

function renderOrderTracker(status) {
  const steps  = ['Confirmed','Processing','Shipped','Out for Delivery','Delivered'];
  const icons  = ['✓','⚙','📦','🚚','🏠'];
  const colors = {Confirmed:'#3498db',Processing:'#9b59b6',Shipped:'#e67e22','Out for Delivery':'#f39c12',Delivered:'#27ae60'};
  const idx    = steps.indexOf(status);
  const color  = colors[status] || '#3498db';

  let html = '<div class="order-track">';
  steps.forEach((step, i) => {
    const done   = i < idx;
    const active = i === idx;
    const state  = done ? 'done' : active ? 'active' : 'idle';
    const dotStyle = active ? `style="background:${color};box-shadow:0 0 8px ${color}66;"` : '';
    html += `
    <div class="track-node">
      <div class="track-dot ${state}" ${dotStyle}>${done ? '✓' : icons[i]}</div>
      <div class="track-lbl ${state}">${step}</div>
    </div>`;
    if (i < steps.length - 1) {
      html += `<div class="track-line ${done ? 'done' : 'idle'}"></div>`;
    }
  });
  html += '</div>';
  return html;
}

function stockBadge(stock) {
  if (stock > 20) return `<span class="badge badge-green">✓ In Stock (${stock})</span>`;
  if (stock > 0)  return `<span class="badge badge-gold badge-pulse">⚡ Low (${stock})</span>`;
  return `<span class="badge badge-red">✗ Out of Stock</span>`;
}

// ── Sidebar user info ─────────────────────────────────
function renderSidebarUser(user) {
  const el = document.getElementById('sidebar-user');
  if (!el || !user) return;
  el.innerHTML = `
    <div class="user-pill">
      <div class="user-pill-name">${user.name}</div>
      <div class="user-pill-email">${user.email}</div>
    </div>
    <button class="btn btn-outline btn-sm btn-full" onclick="logout()">Sign Out</button>`;
}

// ── Init all interactive elements ─────────────────────
function initUI() {
  initRipple();
  initTabs('.tabs-wrap');
  animateCounters();
  initTilt();
}

// Auto-init on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initRipple();
  animateCounters();
  // Re-init after dynamic renders
  const mo = new MutationObserver(() => {
    initRipple();
    animateCounters();
    initTilt();
  });
  mo.observe(document.body, { childList: true, subtree: true });
});
