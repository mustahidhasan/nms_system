// src/component/Login.js
import { useNavigate } from 'react-router-dom';
import '../assets/Login.css';
import React, { useState } from 'react';

function Login({ apiBaseUrl }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  

  const handleSSOLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/azure-login/`);
      const data = await response.json();
      if (data.login_url) {
        window.location.href = data.login_url;
      } else if (data.success) {
        navigate('/dashboard');
      } else {
        alert('Login failed or no login URL provided.');
      }
    } catch (error) {
      console.error('Login error:', error);
    }finally{
      setLoading(true);
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
        <button onClick={handleSSOLogin}>LOGIN VIA SSO</button>
      </div>
    </div>
  );
}

export default Login;
