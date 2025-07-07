import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getAzureLoginUrl, azureCallback } from './api';
import './Login.css'; // Import the CSS file

export default function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Handle Azure callback with ?code=
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

  const handleLoginClick = async () => {
    try {
      const data = await getAzureLoginUrl();
      window.location.href = data.login_url;
    } catch (e) {
      alert('Failed to get login URL');
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <img src="/logo1.png" alt="LOGO1" className="logo-left" />
        <img src="/logo2.png" alt="LOGO2" className="logo-right" />
        <h1>Log In</h1>
        <button onClick={handleLoginClick}>LOGIN VIA SSO</button>
      </div>
    </div>
  );
}
