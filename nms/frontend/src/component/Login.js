import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../assets/Login.css';

function Login({ legacyBaseUrl }) {
  const navigate = useNavigate();
  const pollingRef = useRef(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const startPollingLoginStatus = () => {
    let attempts = 0;
    const maxAttempts = 20;
    pollingRef.current = setInterval(async () => {
      attempts += 1;
      try {
        const res = await fetch(`${legacyBaseUrl}/azure-login/status/`, {
          credentials: 'include',
        });
        const data = await res.json();
        if (data.success) {
          clearInterval(pollingRef.current);
          setLoading(false);
          navigate('/dashboard');
        } else if (attempts >= maxAttempts) {
          clearInterval(pollingRef.current);
          setLoading(false);
          alert('Login timed out. Please try again.');
        }
      } catch (err) {
        clearInterval(pollingRef.current);
        setLoading(false);
        alert('Error checking login status.');
      }
    }, 1000);
  };

  const handleSSOLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${legacyBaseUrl}/azure-login/`);
      const data = await response.json();

      if (data.login_url) {
        window.location.href = data.login_url;
      } else if (data.success) {
        setLoading(false);
        navigate('/dashboard');
      } else {
        startPollingLoginStatus();
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
      alert('Login failed.');
    }
  };

  return (
    <div className="login-container">
      {loading && (
        <div className="spinner-overlay">
          <div className="spinner" />
        </div>
      )}
      <div className="login-box">
        <img src="logo_left.png" className="logo-left" alt="LOGO1" />
        <img src="logo_right.png" className="logo-right" alt="LOGO2" />
        <h1>Log In</h1>
        <button onClick={handleSSOLogin} disabled={loading}>
          {loading ? 'Loading...' : 'LOGIN VIA SSO'}
        </button>
      </div>
    </div>
  );
}

export default Login;
