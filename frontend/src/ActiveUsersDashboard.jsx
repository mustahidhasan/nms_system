// src/ActiveUsersDashboard.jsx
import React, { useEffect, useState } from 'react';
import { fetchActiveUsers, logout } from './api';
import { useNavigate } from 'react-router-dom';

export default function ActiveUsersDashboard() {
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const fetched = await fetchActiveUsers();
        setData(fetched);
      } catch (e) {
        alert('Failed to load active users: ' + e.message);
      }
    })();
  }, []);

  async function handleLogout() {
    try {
      await logout();
      localStorage.removeItem('user');
      navigate('/login');
    } catch (e) {
      alert('Logout failed: ' + e.message);
    }
  }

  if (!data) return <div>Loading...</div>;

  return (
    <div className="container mt-5">
      <h1 className="mb-4 text-center">Active Users Dashboard</h1>
      <p className="lead text-center">
        Current Active Users: <strong>{data.active_user_count}</strong>
      </p>

      <button className="btn btn-danger mb-4" onClick={handleLogout}>
        Logout
      </button>

      <div className="row">
        {data.active_users.map((user, idx) => (
          <div className="col-md-4 mb-3" key={idx}>
            <div className={`card ${user.is_active ? 'border-success' : 'border-danger'}`}>
              <div className="card-body text-center">
                <h5 className="card-title">{user.first_name}</h5>
                <p className="card-text">{user.email}</p>
                <span className={`badge ${user.is_active ? 'bg-success' : 'bg-danger'}`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <h3 className="mt-5 text-center">User Activity Log</h3>
      <div style={{ maxHeight: 400, overflowY: 'auto' }}>
        <table className="table table-striped">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Username</th>
              <th>Last Activity Time</th>
              <th>Activity Type</th>
              <th>Session Duration (seconds)</th>
            </tr>
          </thead>
          <tbody>
            {data.user_activities.map((log, i) => (
              <tr key={i}>
                <td>{log.user__id}</td>
                <td>{log.user__username}</td>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.activity_type}</td>
                <td>{log.duration || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
