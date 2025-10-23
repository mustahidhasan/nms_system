import { useNavigate } from 'react-router-dom';
import '../assets/Login.css';
import React, { useState, useEffect, useRef } from 'react';

function Login({ apiBaseUrl }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const pollingRef = useRef(null);

  // Poll backend login status
  const startPollingLoginStatus = () => {
    let attempts = 0;
    const maxAttempts = 20; // poll ~20 seconds

    pollingRef.current = setInterval(async () => {
      attempts++;
      try {
        const res = await fetch(`${apiBaseUrl}/azure-login/status/`, {
          credentials: 'include',
        });

        const contentType = res.headers.get('content-type');
        if (contentType?.includes('application/json')) {
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
          // Received HTML instead of JSON → probably a redirect
          clearInterval(pollingRef.current);
          setLoading(false);
          window.location.href = `${apiBaseUrl}/azure-login/`;
        }
      } catch (err) {
        clearInterval(pollingRef.current);
        setLoading(false);
        console.error('Polling error:', err);
        alert('Error checking login status.');
      }
    }, 1000);
  };

  // Handle initial SSO login
  const handleSSOLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/azure-login/`, {
        credentials: 'include',
      });

      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const data = await response.json();
        if (data.login_url) {
          // Redirect to Azure login page
          window.location.href = data.login_url;
        } else if (data.success) {
          // Already logged in
          setLoading(false);
          navigate('/dashboard');
        } else {
          // Start polling if login not immediate
          startPollingLoginStatus();
        }
      } else {
        // Backend returned HTML → redirect
        window.location.href = `${apiBaseUrl}/azure-login/`;
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
      alert('Login failed.');
    }
  };

  // Cleanup polling on unmount
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
