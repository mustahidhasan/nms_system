// src/Login.jsx
import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getAzureLoginUrl, azureCallback } from './api';

export default function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // If redirected back with code, call callback API
  useEffect(() => {
    const code = searchParams.get('code');
    if (code) {
      (async () => {
        try {
          const data = await azureCallback(code);
          localStorage.setItem('user', JSON.stringify(data.user));
          navigate('/dashboard'); // Redirect after login success
        } catch (e) {
          alert('Login failed: ' + e.message);
        }
      })();
    }
  }, [searchParams, navigate]);

  // On button click, fetch login url and redirect browser
  async function handleLoginClick() {
    try {
      const url = await getAzureLoginUrl();
      window.location.href = url;
    } catch (e) {
      alert('Failed to get login URL');
    }
  }

  return (
    <div className="container mt-5 text-center">
      <h1>Login with Microsoft Azure SSO</h1>
      <button className="btn btn-success mt-3" onClick={handleLoginClick}>
        Login via SSO
      </button>
    </div>
  );
}
