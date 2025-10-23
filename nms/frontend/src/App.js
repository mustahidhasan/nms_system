import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './component/Login';
import Ping from './component/Ping'; // Dashboard component
import UserActivity from './component/UserActivity'

function App() {
  const API_BASE_URL =
    process.env.REACT_APP_API_BASE_URL ||
    (window.location.hostname === "localhost" ? "http://localhost:8000" : `${window.location.protocol}//${window.location.hostname}/api`);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login apiBaseUrl={API_BASE_URL} />} />
        <Route path="/dashboard" element={<Ping apiBaseUrl={API_BASE_URL} />} />
        <Route path="/user-activity" element={<UserActivity apiBaseUrl={API_BASE_URL} />} />
      </Routes>
    </Router>
  );
}

export default App;