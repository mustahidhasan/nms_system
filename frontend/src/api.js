// src/api.js

const API_BASE = 'http://localhost:8000'; // Adjust if needed

export async function getAzureLoginUrl() {
  const res = await fetch(`${API_BASE}/api/auth/login_url/`);
  if (!res.ok) throw new Error('Failed to get login URL');

  const data = await res.json();
  console.log("Backend login_url response:", data); // ✅ Add this
  return data.login_url;
}


export async function azureCallback(code) {
  const res = await fetch(`${API_BASE}/api/auth/callback/?code=${encodeURIComponent(code)}`, {
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Login callback failed');
  }
  return await res.json();
}

export async function logout() {
  const res = await fetch(`${API_BASE}/api/auth/logout/`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Logout failed');
  return await res.json();
}

export async function fetchActiveUsers() {
  const res = await fetch(`${API_BASE}/api/active-users/`, {
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to fetch active users');
  return await res.json();
}
