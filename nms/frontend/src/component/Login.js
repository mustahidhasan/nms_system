import { useNavigate } from 'react-router-dom';
import '../assets/Login.css';
import React, { useState, useEffect, useRef } from 'react';

function Login({ apiBaseUrl }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const pollingRef = useRef(null);

  const startPollingLoginStatus = () => {
    let attempts = 0;
    const maxAttempts = 20;
    pollingRef.current = setInterval(async () => {
      attempts++;
      try {
        const res = await fetch(`${apiBaseUrl}/azure-login/status/`, {
          credentials: 'include',
        });

        if (res.headers.get('content-type')?.includes('application/json')) {
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
        } else {
          // received HTML (likely redirect) → stop polling
          clearInterval(pollingRef.current);
          setLoading(false);
          window.location.href = `${apiBaseUrl}/azure-login/`;
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
      const response = await fetch(`${apiBaseUrl}/azure-login/`, {
        credentials: 'include',
      });

      if (response.headers.get('content-type')?.includes('application/json')) {
        const data = await response.json();
        if (data.login_url) {
          window.location.href = data.login_url;
        } else if (data.success) {
          setLoading(false);
          navigate('/dashboard');
        } else {
          startPollingLoginStatus();
        }
      } else {
        // Redirect directly
        window.location.href = `${apiBaseUrl}/azure-login/`;
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
      alert('Login failed.');
    }
  };

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

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
