// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './component/Login';
import Ping from './component/Ping'; // This is the dashboard component

function App() {
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login apiBaseUrl={API_BASE_URL} />} />
        <Route path="/dashboard" element={<Ping apiBaseUrl={API_BASE_URL} />} />
      </Routes>
    </Router>
  );
}

export default App;
