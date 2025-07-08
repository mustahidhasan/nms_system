// src/components/Ping.js
import React, { useState, useEffect } from 'react';
import '../assets/Ping.css';

function Ping() {
  const [startIp, setStartIp] = useState('');
  const [operations, setOperations] = useState({});
  const [results, setResults] = useState([]);
  const [emailList, setEmailList] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const storedIp = sessionStorage.getItem('ip_address');
    if (storedIp) setStartIp(storedIp);
  }, []);

  useEffect(() => {
    sessionStorage.setItem('ip_address', startIp);
  }, [startIp]);

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setOperations((prev) => ({ ...prev, [name]: checked }));
  };

  const handleSelectAll = () => {
    const isAllSelected = Object.keys(operations).length === 7 && Object.values(operations).every(Boolean);
    const newOps = {
      enable_ping: !isAllSelected,
      verbose_ping: !isAllSelected,
      traceroute: !isAllSelected,
      dns_lookup: !isAllSelected,
      verbos_dns_lookup: !isAllSelected,
      simple_snmp_walk: !isAllSelected,
      mtr: !isAllSelected,
    };
    setOperations((prev) => ({
      ...newOps,
      snmp_walk: prev.snmp_walk || false, // exclude snmp_walk
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('start_ip_address', startIp);
    Object.entries(operations).forEach(([key, value]) => {
      if (value) formData.append(key, '1');
    });

    try {
      const response = await fetch('http://localhost:8000/ping-operation/', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      const data = await response.json();
      if (data.success) {
        setResults(data.results);
      } else {
        alert(data.error || 'Error processing the request.');
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const handleSendEmail = async () => {
    const emailArray = emailList
      .split(',')
      .map((e) => e.trim())
      .filter(Boolean);
    if (!emailArray.length) return;

    let bodyText = 'Results:\n\n';
    results.forEach(({ operation, result }) => {
      bodyText += `Operation: ${operation}\nResult: ${result}\n\n`;
    });

    try {
      await fetch('http://localhost:8000/send-email/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_list: emailArray, email_body: bodyText }),
      });
    } catch (error) {
      console.error('Email sending failed:', error);
    }
  };

  const downloadCSV = () => {
    let csv = 'Operation,Result\n';
    results.forEach(({ operation, result }) => {
      const cleanResult = result.replace(/\n/g, ' ').replace(/,/g, '');
      csv += `"${operation}","${cleanResult}"\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'network_operations.csv';
    link.click();
  };

  const clearForm = () => {
    setStartIp('');
    setOperations({});
    setResults([]);
    setEmailList('');
    sessionStorage.removeItem('ip_address');
  };

  return (
    <div className="ping-container full-screen">
      <div className="topbar">
        <div className="left-section">
          <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
          <img src="logo_left.png" alt="Left Logo" className="logo" />
        </div>
        <h2 className="title">Network Operations</h2>
        <div className="right-section">
          <img src="logo_right.png" alt="Right Logo" className="logo" />
        </div>
      </div>

      <div className="main-layout">
        {sidebarOpen && (
          <aside className="sidebar">
            <div className="operation-checkboxes">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={
                    ['enable_ping', 'verbose_ping', 'traceroute', 'dns_lookup', 'verbos_dns_lookup', 'simple_snmp_walk', 'mtr']
                      .every(op => operations[op])
                  }
                  onChange={handleSelectAll}
                />
                Select All
              </label>
              {[
                'enable_ping',
                'verbose_ping',
                'traceroute',
                'dns_lookup',
                'verbos_dns_lookup',
                'simple_snmp_walk',
                'mtr',
                'snmp_walk',
              ].map((op) => (
                <label key={op} className="checkbox-label">
                  <input
                    type="checkbox"
                    name={op}
                    checked={!!operations[op]}
                    onChange={handleCheckboxChange}
                  />
                  {op.replace(/_/g, ' ')}
                </label>
              ))}
            </div>

            <div className="footer-icons">
              <div>ℹ️ ABOUT</div>
              <div>↩ LOGOUT</div>
            </div>
          </aside>
        )}

        <main className="main-content">
          <form onSubmit={handleSubmit}>
            <div className="input-section">
              <input
                type="text"
                value={startIp}
                onChange={(e) => setStartIp(e.target.value)}
                placeholder="Start IP Address"
                required
              />
              <button type="submit">Submit</button>
              <button type="button" onClick={clearForm}>Clear</button>
            </div>
          </form>

          {results.length > 0 && (
            <section className="results-section">
              <h3>Results</h3>
              <div className="email-actions">
                <input
                  type="text"
                  placeholder="Email addresses (comma separated)"
                  value={emailList}
                  onChange={(e) => setEmailList(e.target.value)}
                />
                <button onClick={handleSendEmail}>Send Email</button>
                <button onClick={downloadCSV}>Download CSV</button>
              </div>

              <table className="result-table">
                <thead>
                  <tr>
                    <th>Operation</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map(({ operation, result }, i) => (
                    <tr key={i}>
                      <td>{operation}</td>
                      <td>
                        <pre>{result}</pre>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

export default Ping;
