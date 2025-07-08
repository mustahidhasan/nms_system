// src/component/Ping.js
import React, { useState } from 'react';
import '../assets/Ping.css';

function Ping() {
  const [startIp, setStartIp] = useState('');
  const [operations, setOperations] = useState({});
  const [results, setResults] = useState([]);
  const [emailList, setEmailList] = useState('');

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setOperations((prev) => ({ ...prev, [name]: checked }));
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
    const emailArray = emailList.split(',').map((e) => e.trim()).filter(Boolean);
    if (!emailArray.length) return;

    let bodyText = 'Results:\n\n';
    results.forEach(({ operation, result }) => {
      bodyText += `Operation: ${operation}\nResult: ${result}\n\n`;
    });

    try {
      await fetch('http://localhost:8000/send-email/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_list: emailArray, email_body: bodyText })
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

  return (
    <div className="ping-container">
      <h2>Dashboard</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={startIp}
          onChange={(e) => setStartIp(e.target.value)}
          placeholder="Start IP Address"
          required
        />
        <div className="checkbox-group">
          {['enable_ping', 'verbose_ping', 'traceroute', 'dns_lookup', 'verbos_dns_lookup', 'snmp_walk', 'simple_snmp_walk', 'mtr'].map((op) => (
            <label key={op}>
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
        <button type="submit">Submit</button>
      </form>

      {results.length > 0 && (
        <div className="results-section">
          <h3>Results</h3>
          <div>
            <input
              type="text"
              placeholder="Email addresses (comma separated)"
              value={emailList}
              onChange={(e) => setEmailList(e.target.value)}
            />
            <button onClick={handleSendEmail}>Send Email</button>
            <button onClick={downloadCSV}>Download CSV</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Operation</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {results.map((res, i) => (
                <tr key={i}>
                  <td>{res.operation}</td>
                  <td><pre>{res.result}</pre></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Ping;
