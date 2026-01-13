// Authentication helpers
function getToken() {
    return localStorage.getItem('access_token');
}

function isAuthenticated() {
    return !!getToken();
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');
    showAlert('Logged out successfully', 'success');
    setTimeout(() => {
        window.location.href = '/login';
    }, 1000);
}

// Theme management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

// Initialize theme and toggle button
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
});

// Update navigation based on auth state
function updateNavigation() {
    const navAuthLinks = document.getElementById('nav-auth-links');
    const navUser = document.getElementById('nav-user');
    const navCreate = document.getElementById('nav-create');
    const navMyPosts = document.getElementById('nav-my-posts');
    const userEmailSpan = document.getElementById('user-email');
    
    if (isAuthenticated()) {
        navAuthLinks.classList.add('hidden');
        navUser.classList.remove('hidden');
        navCreate.classList.remove('hidden');
        navMyPosts.classList.remove('hidden');
        
        // Try to get user info from localStorage
        const userEmail = localStorage.getItem('user_email');
        const userId = localStorage.getItem('user_id');
        
        if (userEmail && userId) {
             if (userEmailSpan) userEmailSpan.textContent = userEmail;
        } else {
            // Try to extract from token
            fetchUserInfo();
        }
    } else {
        navAuthLinks.classList.remove('hidden');
        navUser.classList.add('hidden');
        navCreate.classList.add('hidden');
        navMyPosts.classList.add('hidden');
    }
}

// Fetch user info from API
async function fetchUserInfo() {
    const token = getToken();
    if (!token) return;
    
    try {
        // Decode JWT to get email and id
        const payload = JSON.parse(atob(token.split('.')[1]));
        const email = payload.sub;
        const userId = payload.id;
        
        if (email) {
            localStorage.setItem('user_email', email);
            const emailSpan = document.getElementById('user-email');
            if (emailSpan) emailSpan.textContent = email;
        }
        
        if (userId) {
             localStorage.setItem('user_id', userId);
        }
    } catch (error) {
        console.error('Failed to decode token:', error);
    }
}

// Alert/notification system - Toast notifications
function showAlert(message, type = 'success') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = document.createElement('span');
    icon.className = 'toast-icon';
    icon.textContent = type === 'success' ? '✓' : '✕';
    
    const messageEl = document.createElement('span');
    messageEl.className = 'toast-message';
    messageEl.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => removeToast(toast);
    
    toast.appendChild(icon);
    toast.appendChild(messageEl);
    toast.appendChild(closeBtn);
    container.appendChild(toast);
    
    // Auto remove after 4 seconds
    setTimeout(() => removeToast(toast), 4000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function removeToast(toast) {
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 300);
}

// API request helper with auth
async function apiRequest(url, options = {}) {
    const token = getToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            showAlert('Session expired. Please login again.', 'error');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
            throw new Error('Unauthorized');
        }
        
        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
}

// Debounce helper for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// HTML escape helper
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

// Loading state helper
function setLoading(elementId, isLoading) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (isLoading) {
        element.innerHTML = '<div class="loading">Loading...</div>';
    }
}

// Error handler
function handleError(error, defaultMessage = 'An error occurred') {
    console.error('Error:', error);
    
    if (error.message === 'Unauthorized') {
        return; // Already handled in apiRequest
    }
    
    showAlert(error.message || defaultMessage, 'error');
}

// --- Shared State & Logic ---
window.userVotes = new Map();
let currentPostActionId = null;

// Post HTML Generator
function createPostHTML(post, currentVote, isOwnPost) {
    // Check if post object structure is nested (Post.X) or flat
    // The API /posts returns [{Post: {...}, votes: 5}, ...]
    // But /posts/me might return slightly different? Let's check my_posts.html code: "post.Post.id"
    // So both seem to be List[Row] where Row has Post model.
    
    const postData = post.Post || post; // Handle both structures if needed
    const votes = post.votes || 0;
    const email = postData.owner ? postData.owner.email : 'Unknown';
    const initial = email.charAt(0).toUpperCase();
    
    // Add visibility badge
    const visibilityBadge = !postData.published ? 
        `<span style="
            background: #f3f4f6; 
            color: #6b7280; 
            padding: 2px 8px; 
            border-radius: 9999px; 
            font-size: 0.75rem; 
            font-weight: 500;
            margin-left: 0.5rem;
            border: 1px solid #e5e7eb;
        ">Hidden</span>` : '';

    return `
        <div class="post" data-post-id="${postData.id}">
            <div class="post-header">
                <div class="post-avatar">${initial}</div>
                <div class="post-user">
                    <div style="display: flex; align-items: center;">
                        <span class="post-username">${escapeHtml(email)}</span>
                        ${visibilityBadge}
                    </div>
                    <div class="post-time">${formatDate(postData.created_at)}</div>
                </div>
                ${isOwnPost ? `
                    <div style="margin-left: auto; display: flex; gap: 10px;">
                        <button class="btn-icon" onclick="window.location.href='/edit?id=${postData.id}'" title="Edit" style="font-size: 1.1rem;">✏️</button>
                        <button class="btn-icon" onclick="handleDeleteDirect(${postData.id})" title="Delete" style="font-size: 1.1rem; color: var(--danger-color);">🗑️</button>
                    </div>
                ` : ''}
            </div>
            
            <div class="post-content">
                <div class="post-title">${escapeHtml(postData.title)}</div>
                <div class="post-body">${escapeHtml(postData.content)}</div>
            </div>
            
            <div class="post-actions">
                <div class="vote-section">
                    <button class="vote-btn ${currentVote === 1 ? 'active' : ''}" onclick="handleVoteClick(${postData.id}, 1)" title="Upvote">
                        ${currentVote === 1 ? '❤️' : '🤍'}
                    </button>
                    <span class="vote-count" id="vote-count-${postData.id}">${votes}</span>
                    <button class="vote-btn ${currentVote === 2 ? 'active' : ''}" onclick="handleVoteClick(${postData.id}, 2)" title="Downvote">
                        👎
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Render Function
function renderPosts(posts, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (posts.length === 0) {
        container.innerHTML = '';
        const emptyState = document.getElementById('empty-state');
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    }

    const emptyState = document.getElementById('empty-state');
    if (emptyState) emptyState.classList.add('hidden');

    const currentUserId = localStorage.getItem('user_id');
    
    container.innerHTML = posts.map(post => {
        const postData = post.Post || post;
        const currentVote = window.userVotes.get(postData.id);
        const isOwnPost = currentUserId && parseInt(currentUserId) === postData.owner_id;
        return createPostHTML(post, currentVote, isOwnPost);
    }).join('');
}

// Vote Logic
async function handleVoteClick(postId, voteType) {
    if (!isAuthenticated()) {
        showAlert('Please login to vote', 'error');
        return;
    }

    const currentVote = window.userVotes.get(postId);
    let action = voteType;
    if (currentVote === voteType) {
        action = 0; // Remove vote
    }
    
    try {
        const response = await apiRequest('/vote', {
            method: 'POST',
            body: JSON.stringify({ post_id: postId, action: action })
        });
        
        if (response.ok) {
            // Update local state
            if (action === 0) {
                window.userVotes.delete(postId);
            } else {
                window.userVotes.set(postId, action);
            }
            // Trigger reload or update UI
            // Ideally we re-fetch to get accurate counts, or we manually update DOM
            // Dispatch event for page to decide
            document.dispatchEvent(new CustomEvent('voteCompleted', { detail: { postId } }));
        }
    } catch (error) {
        // Handled by apiRequest
    }
}

// Modal Actions
function showPostMenu(postId) {
    currentPostActionId = postId;
    const modal = document.getElementById('post-options-modal');
    if (modal) modal.classList.add('active');
}

function closePostMenu(event, force) {
    if (force || (event && event.target === event.currentTarget)) {
        const modal = document.getElementById('post-options-modal');
        if (modal) modal.classList.remove('active');
    }
}

function handleEdit() {
    if (currentPostActionId) {
        window.location.href = `/edit?id=${currentPostActionId}`;
    }
}

function handleDeleteDirect(postId) {
    if (confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
        executeDelete(postId);
    }
}

async function executeDelete(postId) {
    try {
        const response = await apiRequest(`/posts/${postId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('Post deleted successfully!', 'success');
            document.dispatchEvent(new CustomEvent('postDeleted', { detail: { postId } }));
        }
    } catch (error) {
        // Handled
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    updateNavigation();
});

