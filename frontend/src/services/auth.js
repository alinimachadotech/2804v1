const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const TOKEN_KEY = 'gerax_access_token';
const USER_KEY = 'gerax_current_user';

function saveSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

async function parseApiError(response) {
    const data = await response.json().catch(() => ({}));
    return data.detail || data.message || 'Nao foi possivel concluir a autenticacao.';
}

export async function login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
        throw new Error(await parseApiError(response));
    }

    const data = await response.json();

    if (!data.access_token || !data.user) {
        throw new Error('Resposta de autenticacao invalida.');
    }

    saveSession(data.access_token, data.user);

    return data;
}

export function logout() {
    clearSession();
}

export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function getCurrentUser() {
    const value = localStorage.getItem(USER_KEY);

    if (!value) {
        return null;
    }

    try {
        return JSON.parse(value);
    } catch {
        clearSession();
        return null;
    }
}

export function isAuthenticated() {
    return Boolean(getToken());
}

export function hasRole(role) {
    return getCurrentUser()?.role === role;
}

export function hasAnyRole(roles) {
    return Array.isArray(roles) && roles.some((role) => hasRole(role));
}

export function hasPermission(permission) {
    const permissions = getCurrentUser()?.permissions || [];
    return permissions.includes('*') || permissions.includes(permission);
}

export function hasUserType(userType) {
    return getCurrentUser()?.user_type === userType;
}

export async function fetchMe() {
    const token = getToken();

    if (!token) {
        clearSession();
        return null;
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    if (!response.ok) {
        clearSession();
        return null;
    }

    const user = await response.json();
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
}

