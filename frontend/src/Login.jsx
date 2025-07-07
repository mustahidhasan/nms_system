import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getAzureLoginUrl, azureCallback } from './api';
import './Login.css'; // We'll create this for custom styles

export default function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const code = searchParams.get('code');
    if (code) {
      (async () => {
        try {
          const data = await azureCallback(code);
          localStorage.setItem('user', JSON.stringify(data.user));
          navigate('/dashboard');
        } catch (e) {
          alert('Login failed: ' + e.message);
        }
      })();
    }
  }, [searchParams, navigate]);

  async function handleLoginClick() {
    try {
      const url = await getAzureLoginUrl();
      window.location.href = url;
    } catch (e) {
      alert('Failed to get login URL');
    }
  }

  return (
    <div className="login-container d-flex align-items-center justify-content-center vh-100">
      <div className="login-box text-center position-relative p-5 bg-white rounded shadow">
        <img src="/logo1.png" alt="Logo Left" className="logo-left" />
        <img src="/logo2.png" alt="Logo Right" className="logo-right" />

        <h2 className="mb-4 text-success fw-bold">Log In</h2>
        <button className="btn btn-success btn-lg rounded-pill px-5" onClick={handleLoginClick}>
          LOGIN VIA SSO
        </button>
      </div>
    </div>
  );
}
