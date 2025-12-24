// src/components/UserActivity.js
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom'; // import useNavigate
import AppFooter from './AppFooter';
import '../assets/UserActivity.css';

const formatDateTimeIST = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata',
  }).format(date);
};

function UserActivity({ apiBaseUrl, auth, setAuth }) {
  const navigate = useNavigate(); // initialize navigate
  const [loading, setLoading] = useState(true);
  const [activeUsers, setActiveUsers] = useState([]);
  const [activityLogs, setActivityLogs] = useState([]);
  const [activeUserCount, setActiveUserCount] = useState(0);
  const [error, setError] = useState(null);
  const storedAuth = useMemo(() => {
    try {
      const raw = localStorage.getItem('nmsAuth');
      return raw ? JSON.parse(raw) : null;
    } catch (err) {
      return null;
    }
  }, []);
  const effectiveAuth = auth || storedAuth;
  const accessToken = effectiveAuth?.access;

  useEffect(() => {
    const loadActivity = async () => {
      try {
        setLoading(true);
        setError(null);
        const headers = {};
        if (accessToken) {
          headers.Authorization = `Bearer ${accessToken}`;
        }
        const res = await fetch(`${apiBaseUrl}/active-users/`, {
          credentials: 'include',
          headers,
        });
        if (res.status === 401) {
          localStorage.removeItem('nmsAuth');
          if (typeof setAuth === 'function') {
            setAuth(null);
          }
          navigate('/dashboard');
          return;
        }
        let data = null;
        try {
          data = await res.json();
        } catch (err) {
          // ignore parse errors for empty responses
        }
        if (!res.ok) {
          throw new Error(data?.detail || 'Failed to fetch user activity');
        }
        setActiveUsers(data?.active_users || []);
        setActivityLogs(data?.user_activities || []);
        setActiveUserCount(data?.active_user_count || 0);
      } catch (err) {
        console.error(err);
        setError(err.message || 'Error loading activity');
      } finally {
        setLoading(false);
      }
    };
    loadActivity();
  }, [apiBaseUrl, accessToken, navigate, setAuth]);

  if (loading) return <div className="activity-loader">Loading...</div>;
  if (error) return <div className="activity-error">Error: {error}</div>;

  return (
    <div className="user-activity-container">
      <button
        className="back-to-home-btn"
        onClick={() => navigate('/dashboard')}
        style={{ marginBottom: '20px', padding: '8px 16px', cursor: 'pointer' }}
      >
        ← Back to Home
      </button>

      <h3>Active Users ({activeUserCount})</h3>
      <ul className="active-user-list">
        {activeUsers.map((user) => (
          <li key={user.id}>
            <strong>{user.name || 'N/A'}</strong> ({user.email})
          </li>
        ))}
      </ul>

      <h4>Recent Activity Logs</h4>
      <table className="activity-table">
        <thead>
          <tr>
            <th>User ID</th>
            <th>Email</th>
            <th>Activity Type</th>
            <th>Timestamp</th>
            <th>Duration</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {activityLogs.map((log, index) => (
            <tr key={index}>
              <td>{log.user_id}</td>
              <td>{log.email}</td>
              <td>{log.activity_type}</td>
              <td>{formatDateTimeIST(log.timestamp)}</td>
              <td>{log.duration}</td>
              <td>{log.session_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <AppFooter apiBaseUrl={apiBaseUrl} />
    </div>
  );
}

export default UserActivity;
