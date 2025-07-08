// src/components/Ping.js
import React, { useState, useEffect } from 'react';
import '../assets/Ping.css';

function Ping() {
  const allOps = [
    'enable_ping',
    'verbose_ping',
    'traceroute',
    'dns_lookup',
    'verbos_dns_lookup',
    'simple_snmp_walk',
    'mtr',
    'snmp_walk',
  ];

  // Initial state: all major options false, including snmp_walk
  const [operations, setOperations] = useState(() =>
    Object.fromEntries(allOps.map((op) => [op, false]))
  );
  const [startIp, setStartIp] = useState('');
  const [results, setResults] = useState([]);
  const [emailList, setEmailList] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [snmpVersion, setSnmpVersion] = useState('2c');

  useEffect(() => {
    const storedIp = sessionStorage.getItem('ip_address');
    if (storedIp) setStartIp(storedIp);
  }, []);

  useEffect(() => {
    sessionStorage.setItem('ip_address', startIp);
  }, [startIp]);

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    console.log(`Checkbox changed — name: ${name}, checked: ${checked}`);

    if (name === 'snmp_walk') {
      // When snmp_walk toggled:
      // If checked, uncheck all other ops.
      // If unchecked, no effect on others.
      setOperations((prev) => {
        if (checked) {
          return { ...Object.fromEntries(allOps.map((op) => [op, false])), snmp_walk: true };
        } else {
          return { ...prev, snmp_walk: false };
        }
      });
    } else {
      // If snmp_walk is checked, ignore other checkboxes (hidden anyway)
      if (operations.snmp_walk) {
        return;
      }
      setOperations((prev) => ({
        ...prev,
        [name]: checked,
      }));
    }
  };

  const handleSelectAll = () => {
    // Select all except snmp_walk only if snmp_walk is not selected
    if (operations.snmp_walk) {
      // ignore select all when snmp_walk selected
      return;
    }
    const allMajorSelected = allOps
      .filter((op) => op !== 'snmp_walk')
      .every((op) => operations[op]);
    const newOps = {};
    allOps.forEach((op) => {
      if (op === 'snmp_walk') {
        newOps[op] = false;
      } else {
        newOps[op] = !allMajorSelected;
      }
    });
    setOperations(newOps);
  };

  // Select All checkbox status: true if all major (non-snmp_walk) are selected
  const isSelectAllChecked = allOps
    .filter((op) => op !== 'snmp_walk')
    .every((op) => operations[op]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('start_ip_address', startIp);

    Object.entries(operations).forEach(([key, value]) => {
      if (value) formData.append(key, '1');
    });

    formData.append('snmp_version', snmpVersion);

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
      console.log('Email sent successfully');
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
    setOperations(Object.fromEntries(allOps.map((op) => [op, false])));
    setResults([]);
    setEmailList('');
    sessionStorage.removeItem('ip_address');
  };

  const renderSNMPFields = () => {
    if (!operations['snmp_walk']) return null;

    return (
      <div id="snmp_fields" className="snmp-fields">
        <label htmlFor="snmp_version">SNMP Version</label>
        <select
          name="snmp_version"
          id="snmp_version"
          value={snmpVersion}
          onChange={(e) => setSnmpVersion(e.target.value)}
        >
          <option value="1">v1</option>
          <option value="2c">v2c</option>
          <option value="3">v3</option>
        </select>

        {(snmpVersion === '2c' || snmpVersion === '3') && (
          <>
            <div> Community String</div>
            <input name="community_string" placeholder="public" />
            <div> Timeout (ms)</div>
            <input name="timeout" placeholder="1000" />
          </>
        )}

        {snmpVersion === '3' && (
          <>
            <div> Username</div>
            <input name="v3_username" />
            <div> Auth Protocol</div>
            <input name="auth_protocol" />
            <div> Auth Password</div>
            <input name="auth_password" type="password" />
            <div> Privacy Protocol</div>
            <input name="priv_protocol" />
            <div> Privacy Password</div>
            <input name="priv_password" type="password" />
            <div> Security Level</div>
            <input name="security_level" />
            <div> Context Name</div>
            <input name="context_name" />
          </>
        )}
      </div>
    );
  };

  return (
    <div className="ping-container full-screen">
      <div className="topbar">
        <div className="left-section">
          <button
            className="menu-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
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
                  name="select_all"
                  checked={isSelectAllChecked}
                  onChange={handleSelectAll}
                  disabled={operations.snmp_walk} // disable select all if snmp_walk is selected
                />
                Select All
              </label>

              {/* Show all major options except snmp_walk if snmp_walk unchecked */}
              {!operations.snmp_walk &&
                allOps
                  .filter((op) => op !== 'snmp_walk')
                  .map((op) => (
                    <label key={op} htmlFor={`chk_${op}`} className="checkbox-label">
                      <input
                        id={`chk_${op}`}
                        type="checkbox"
                        name={op}
                        checked={operations[op]}
                        onChange={handleCheckboxChange}
                      />
                      {op.replace(/_/g, ' ')}
                    </label>
                  ))}

              {/* Show snmp_walk option checkbox always */}
              <label
                key="snmp_walk"
                htmlFor={`chk_snmp_walk`}
                className="checkbox-label"
              >
                <input
                  id={`chk_snmp_walk`}
                  type="checkbox"
                  name="snmp_walk"
                  checked={operations.snmp_walk}
                  onChange={handleCheckboxChange}
                />
                snmp walk
              </label>

              {/* Show SNMP fields only if snmp_walk selected */}
              {renderSNMPFields()}
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
                name="start_ip"
                type="text"
                value={startIp}
                onChange={(e) => setStartIp(e.target.value)}
                placeholder="Start IP Address"
                required
              />
              <button type="submit">Submit</button>
              <button type="button" onClick={clearForm}>
                Clear
              </button>
            </div>
          </form>

          {results.length > 0 && (
            <section className="results-section">
              <h3>Results</h3>
              <div className="email-actions">
                <input
                  type="text"
                  name="email_list"
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
