import React, { useEffect } from 'react';

export default function Dashboard() {
  useEffect(() => {
    window.location.href = 'http://localhost:8000/dashboard/';
  }, []);

  return <div>Redirecting to dashboard...</div>;
}
