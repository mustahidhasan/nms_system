// src/Login.js
import React from 'react';

function Login() {
  return (
    <div className="Login">
      <h2>Login Page</h2>
      <form>
        <input type="text" placeholder="Email" /><br />
        <input type="password" placeholder="Password" /><br />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;
