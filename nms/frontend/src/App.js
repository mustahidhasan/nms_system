// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './component/Login';
import Ping from './component/Ping'; // This is the dashboard component

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Ping />} /> {/* dashboard route */}
      </Routes>
    </Router>
  );
}

export default App;
