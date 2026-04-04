import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppFooter from './AppFooter';
import '../assets/Login.css';

function Login({ apiBaseUrl, auth, setAuth }) {
  const navigate = useNavigate();
  const insightsRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [mode, setMode] = useState('home');
  const [errorText, setErrorText] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });

  useEffect(() => {
    const hasSession = auth || localStorage.getItem('nmsAuth');
    if (hasSession) {
      navigate('/dashboard');
    }
  }, [auth, navigate]);

  const handleSSOLogin = async () => {
    setErrorText('');
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/azure-login/`, {
        credentials: 'include',
      });
      const data = await response.json();

      if (data.login_url) {
        window.location.href = data.login_url;
      } else {
        throw new Error('SSO login URL is missing.');
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
      setErrorText('SSO login failed. Please try again.');
    }
  };

  const storeAuthAndRedirect = (data) => {
    localStorage.setItem('nmsAuth', JSON.stringify(data));
    if (typeof setAuth === 'function') {
      setAuth(data);
    }
    navigate('/dashboard');
  };

  const handleLocalLogin = async (event) => {
    event.preventDefault();
    setErrorText('');
    setLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl}/local-login/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginForm),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Login failed.');
      }
      storeAuthAndRedirect(data);
    } catch (error) {
      setErrorText(error.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  const onLoginFieldChange = (event) => {
    const { name, value } = event.target;
    setLoginForm((prev) => ({ ...prev, [name]: value }));
  };

  const toggleInsights = () => setShowInsights((prev) => !prev);

  useEffect(() => {
    if (!showInsights) return undefined;
    const handleClickOutside = (event) => {
      if (
        insightsRef.current &&
        !insightsRef.current.contains(event.target) &&
        !event.target.closest('.insights-trigger')
      ) {
        setShowInsights(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showInsights]);

  return (
    <div className="login-container">
      {loading && (
        <div className="spinner-overlay">
          <div className="spinner" />
        </div>
      )}
      <div className="login-frame">
        <header className="login-header">
          <img src="logo_left.png" className="logo-left" alt="Network logo" />
          <div className="login-title">Network Management Operations</div>
          <img src="logo_right.png" className="logo-right" alt="Operations logo" />
          <button
            type="button"
            className={`insights-trigger ${showInsights ? 'active' : ''}`}
            aria-expanded={showInsights}
            aria-controls="login-insights"
            onClick={toggleInsights}
          >
            ?
          </button>
          {showInsights && (
            <div className="insights-popover" id="login-insights" role="dialog" ref={insightsRef}>
              <button
                type="button"
                className="close-insights"
                onClick={() => setShowInsights(false)}
                aria-label="Close operational insights"
              >
                ✖
              </button>
              <p className="insights-title">Operational insights</p>
              <ul>
                <li>Run diagnostics for ping, traceroute, DNS, SNMP, and MTR from one workspace.</li>
                <li>Export or email results after each operation.</li>
                <li>Track operator activity through the shared NMS login flow.</li>
              </ul>
            </div>
          )}
        </header>
        <main className="login-box">
          <h1>Welcome back</h1>
          <p className="login-subtitle">Securely access diagnostics, ping tools, and operator workflows.</p>
          {mode === 'home' && (
            <div className="auth-mode-switch">
              <button
                type="button"
                className="auth-mode-btn active"
                onClick={() => {
                  setMode('login');
                  setErrorText('');
                }}
                disabled={loading}
              >
                Login with Username
              </button>
              <button type="button" className="auth-mode-btn active" onClick={handleSSOLogin} disabled={loading}>
                Login via SSO
              </button>
            </div>
          )}

          {mode === 'login' && (
            <form className="auth-form" onSubmit={handleLocalLogin}>
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                name="email"
                type="email"
                autoComplete="email"
                value={loginForm.email}
                onChange={onLoginFieldChange}
                required
              />
              <label htmlFor="login-password">Password</label>
              <div className="password-input-wrap">
                <input
                  id="login-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={loginForm.password}
                  onChange={onLoginFieldChange}
                  required
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  👁
                </button>
              </div>
              <button type="submit" disabled={loading}>
                {loading ? 'Signing you in…' : 'Login as User'}
              </button>
              <button
                type="button"
                className="auth-mode-btn"
                onClick={() => {
                  setMode('home');
                  setErrorText('');
                }}
                disabled={loading}
              >
                Back
              </button>
            </form>
          )}
          {/* <small className="login-hint">Default user: admin@gmail.com | password: admin@gmail.com</small> */}
          {errorText && <p className="auth-error">{errorText}</p>}
        </main>
      </div>
      <AppFooter apiBaseUrl={apiBaseUrl} />
    </div>
  );
}

export default Login;
