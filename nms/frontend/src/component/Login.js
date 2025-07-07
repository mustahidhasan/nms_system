// src/component/Login.js
import React from 'react';
import '../assets/Login.css'; // Import the CSS file

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
    <div className="login-container">
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
