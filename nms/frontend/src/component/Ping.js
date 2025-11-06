// src/components/Ping.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../assets/Ping.css';
import UserActivity from './UserActivity';

function Ping({ apiBaseUrl }) {
  const navigate = useNavigate();
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

  const [operations, setOperations] = useState(() =>
    Object.fromEntries(allOps.map((op) => [op, false]))
  );
  const [startIp, setStartIp] = useState('');
  const [results, setResults] = useState([]);
  const [emailList, setEmailList] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [snmpVersion, setSnmpVersion] = useState('2c');
  const [showAbout, setShowAbout] = useState(false);
  const [showSettingsDropdown, setShowSettingsDropdown] = useState(false);
  const [showUserActivity, setShowUserActivity] = useState(false);
  const [loading, setLoading] = useState(false);
  const [emailStatus, setEmailStatus] = useState(null);


  useEffect(() => {
    const storedIp = sessionStorage.getItem('ip_address');
    if (storedIp) setStartIp(storedIp);
  }, []);

  useEffect(() => {
    sessionStorage.setItem('ip_address', startIp);
  }, [startIp]);

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const handleLogout = async () => {
    try {
      setLoading(true);
      const csrfToken = getCookie('csrftoken');
      const response = await fetch(`${apiBaseUrl}/logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': csrfToken,
        },
      });

      const data = await response.json();
      if (data.success && data.logout_url) {
        window.location.href = data.logout_url;
        return;
      }

      if (response.ok) {
        navigate('/');
      } else {
        console.error('Logout failed:', data.message || 'Unknown error');
      }
    } catch (error) {
      console.error('Logout error:', error);
    }finally{
      setLoading(false);
    }
  };

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    if (name === 'snmp_walk') {
      setOperations((prev) => {
        if (checked) {
          return { ...Object.fromEntries(allOps.map((op) => [op, false])), snmp_walk: true };
        } else {
          return { ...prev, snmp_walk: false };
        }
      });
    } else {
      if (operations.snmp_walk) return;
      setOperations((prev) => ({
        ...prev,
        [name]: checked,
      }));
    }
  };

  const handleSelectAll = () => {
    if (operations.snmp_walk) return;
    const allMajorSelected = allOps
      .filter((op) => op !== 'snmp_walk')
      .every((op) => operations[op]);
    const newOps = {};
    allOps.forEach((op) => {
      newOps[op] = op === 'snmp_walk' ? false : !allMajorSelected;
    });
    setOperations(newOps);
  };

  const isSelectAllChecked = allOps
    .filter((op) => op !== 'snmp_walk')
    .every((op) => operations[op]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
        const formData = new FormData();
        formData.append('start_ip_address', startIp);
        Object.entries(operations).forEach(([key, value]) => {
        if (value) formData.append(key, '1');
        });
        formData.append('snmp_version', snmpVersion);

        if (operations.snmp_walk) {
        formData.append('community_strings', document.querySelector('input[name="community_string"]')?.value || 'public');
        formData.append('timeout', document.querySelector('input[name="timeout"]')?.value || '1000');

        if (snmpVersion === '3') {
            formData.append('username', document.querySelector('input[name="v3_username"]')?.value || '');
            formData.append('authentication_type', document.querySelector('input[name="auth_protocol"]')?.value || '');
            formData.append('password', document.querySelector('input[name="auth_password"]')?.value || '');
            formData.append('encryption_type', document.querySelector('input[name="priv_protocol"]')?.value || '');
            formData.append('encryption_key', document.querySelector('input[name="priv_password"]')?.value || '');
            formData.append('security_level', document.querySelector('input[name="security_level"]')?.value || '');
            formData.append('context_name', document.querySelector('input[name="context_name"]')?.value || '');
        }
        }

        const csrfToken = getCookie('csrftoken');
        const response = await fetch(`${apiBaseUrl}/dashboard/`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
        headers: {
            'X-CSRFToken': csrfToken,
        },
        });

        const data = await response.json();
        console.log(data);
        if (data.success) {
        setResults(data.results);
        } else {
        alert(data.error || 'Error processing the request.');
        }
    } catch (error) {
        console.error('Network error:', error);
    } finally {
        setLoading(false); // hide spinner
    }
    };


  const handleSendEmail = async () => {
    const emailArray = emailList
      .split(',')
      .map((e) => e.trim())
      .filter(Boolean);

    if (!emailArray.length) {
      setEmailStatus({ type: 'error', message: 'Please enter at least one email recipient.' });
      return;
    }

    let bodyText = 'Results:\n\n';
    results.forEach(({ operation, result }) => {
      bodyText += `Operation: ${operation}\nResult: ${result}\n\n`;
    });

    try {
      setEmailStatus({ type: 'info', message: 'Sending email…' });
      const res = await fetch(`${apiBaseUrl}/send-email/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email_list: emailArray, email_body: bodyText }),
      });
      const json = await res.json();
      if (json.success) {
        setEmailStatus({ type: 'success', message: 'Email sent successfully.' });
      } else {
        setEmailStatus({ type: 'error', message: json.message || 'Email sending failed.' });
      }
    } catch (error) {
      setEmailStatus({ type: 'error', message: 'Email sending failed. Please check the configuration.' });
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
    setEmailStatus(null);
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
            <div>Community String</div>
            <input name="community_string" placeholder="public" />
            <div>Timeout (ms)</div>
            <input name="timeout" placeholder="1000" />
          </>
        )}

        {snmpVersion === '3' && (
          <>
            <div>Username</div>
            <input name="v3_username" />
            <div>Auth Protocol</div>
            <input name="auth_protocol" />
            <div>Auth Password</div>
            <input name="auth_password" type="password" />
            <div>Privacy Protocol</div>
            <input name="priv_protocol" />
            <div>Privacy Password</div>
            <input name="priv_password" type="password" />
            <div>Security Level</div>
            <input name="security_level" />
            <div>Context Name</div>
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
          <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>
          <img src="logo_left.png" alt="Left Logo" className="logo" />
        </div>
        <h2 className="title">Network Operations</h2>
        <div className="right-section">
          <img src="logo_right.png" alt="Right Logo" className="logo" />
          <div className="settings-wrapper">
            <span className="settings-icon" onClick={() => setShowSettingsDropdown((prev) => !prev)}>⚙️</span>
            {showSettingsDropdown && (
              <div className="settings-dropdown">
                <div onClick={() => {
                  navigate('/user-activity');
                  setShowSettingsDropdown(false);
                }}>👤 User</div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="main-layout">
        {loading && (
        <div className="spinner-overlay">
            <div className="spinner" />
        </div>
        )}

        {sidebarOpen && (
          <aside className="sidebar">
            <div className="operation-checkboxes">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="select_all"
                  checked={isSelectAllChecked}
                  onChange={handleSelectAll}
                  disabled={operations.snmp_walk}
                />
                Select All
              </label>

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

              <label key="snmp_walk" htmlFor={`chk_snmp_walk`} className="checkbox-label">
                <input
                  id={`chk_snmp_walk`}
                  type="checkbox"
                  name="snmp_walk"
                  checked={operations.snmp_walk}
                  onChange={handleCheckboxChange}
                />
                snmp walk
              </label>

              {renderSNMPFields()}
            </div>

            <div className="footer-icons">
              <div style={{ cursor: 'pointer' }} onClick={() => setShowAbout(true)}>ℹ️ ABOUT</div>
              <div style={{ cursor: 'pointer' }} onClick={handleLogout}>↩ LOGOUT</div>
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
                placeholder="Enter Your IP Address"
                required
              />
              <button type="submit">Submit</button>
              <button  style={{background:"red"}} type="button" onClick={clearForm}>
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
              {emailStatus && (
                <p className={`email-status email-status-${emailStatus.type}`}>{emailStatus.message}</p>
              )}

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

        {showAbout && (
          <div className="about-popup">
            <div className="popup-overlay" onClick={() => setShowAbout(false)}></div>
            <div className="popup-content">
              <button className="close-btn" onClick={() => setShowAbout(false)}>✖</button>
              <iframe
                src="/about.pdf"
                title="About PDF"
                width="100%"
                height="500px"
                frameBorder="0"
              />
            </div>
          </div>
        )}

        {showUserActivity && (
          <div className="user-activity-modal">
            <div className="popup-overlay" onClick={() => setShowUserActivity(false)}></div>
            <div className="popup-content">
              <button className="close-btn" onClick={() => setShowUserActivity(false)}>✖</button>
              <UserActivity />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Ping;
