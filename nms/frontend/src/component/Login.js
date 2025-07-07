// src/component/Login.js
import React from 'react';

function Login() {
  const handleSSOLogin = async () => {
    try {
      const response = await fetch('http://localhost:8000/azure-login/');
      const data = await response.json();
      if (data.login_url) {
        window.location.href = data.login_url;
      } else {
        alert('No login URL received.');
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  return (
    <div className="login-page">
      <h2>Login</h2>
      <button onClick={handleSSOLogin}>Login with Azure SSO</button>
    </div>
  );
}

export default Login;
