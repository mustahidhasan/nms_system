import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';

const defaultIncidentForm = {
  title: '',
  summary: '',
  impact: '',
  severity: 'P3',
  template_type: 'incident',
  primary_distribution_list: '',
};

const defaultMessageForm = {
  subject: '',
  body: '',
  template_type: 'incident',
  distribution_list: '',
  extraRecipients: '',
};

const defaultListForm = {
  name: '',
  description: '',
  emails: '',
  scope: 'team',
};

const defaultCloseForm = {
  subject: '',
  body: '',
  distribution_list: '',
};

function Dashboard({ apiBaseUrl, auth, setAuth }) {
  const navigate = useNavigate();
  const token = auth?.access;
  const [teams, setTeams] = useState(() => (Array.isArray(auth?.teams) ? auth.teams : []));
  const [selectedTeam, setSelectedTeam] = useState(() => auth?.teams?.[0]?.id || null);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [messages, setMessages] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [distributionLists, setDistributionLists] = useState([]);
  const [incidentForm, setIncidentForm] = useState(defaultIncidentForm);
  const [messageForm, setMessageForm] = useState(defaultMessageForm);
  const [messageFiles, setMessageFiles] = useState([]);
  const [listForm, setListForm] = useState(defaultListForm);
  const [closeForm, setCloseForm] = useState(defaultCloseForm);
  const [summary, setSummary] = useState({ open_incident_count: 0, recent_messages: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const headers = useMemo(() => {
    if (!token) return {};
    return {
      Authorization: `Bearer ${token}`,
    };
  }, [token]);

  const apiRequest = async (path, options = {}) => {
    const opts = { ...options };
    opts.headers = {
      ...(!opts.body || !(opts.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
      ...opts.headers,
      ...headers,
    };
    if (opts.body && !(opts.body instanceof FormData)) {
      opts.body = typeof opts.body === 'string' ? opts.body : JSON.stringify(opts.body);
    }
    const response = await fetch(`${apiBaseUrl}${path}`, {
      credentials: 'include',
      ...opts,
    });
    if (!response.ok) {
      let detail = 'Request failed';
      try {
        const data = await response.json();
        detail = data.detail || JSON.stringify(data);
      } catch (e) {
        // ignore json errors
      }
      throw new Error(detail);
    }
    if (response.status === 204) {
      return null;
    }
    return response.json();
  };

  const persistAuth = (nextAuth) => {
    if (nextAuth) {
      localStorage.setItem('nmsAuth', JSON.stringify(nextAuth));
    } else {
      localStorage.removeItem('nmsAuth');
    }
    setAuth(nextAuth);
  };

  const handleLogout = () => {
    persistAuth(null);
    navigate('/');
  };

  useEffect(() => {
    if (!token) {
      navigate('/');
      return;
    }
    const bootstrap = async () => {
      try {
        setLoading(true);
        const [templateData, teamData] = await Promise.all([
          apiRequest('/templates/'),
          apiRequest('/teams/'),
        ]);
        setTemplates(Array.isArray(templateData) ? templateData : []);
        const normalizedTeams = Array.isArray(teamData) ? teamData : [];
        setTeams(normalizedTeams);
        const initialTeam = selectedTeam || normalizedTeams[0]?.id || null;
        if (!selectedTeam && initialTeam) {
          setSelectedTeam(initialTeam);
        }
        await Promise.all([loadIncidents(), loadDistributionLists(initialTeam), loadSummary()]);
        setError('');
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (selectedTeam) {
      setSelectedIncident(null);
      loadIncidents();
      loadDistributionLists();
    } else {
      loadDistributionLists(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTeam]);

  useEffect(() => {
    if (selectedIncident) {
      loadMessages(selectedIncident);
    } else {
      setMessages([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedIncident]);

  const loadSummary = async () => {
    const data = await apiRequest('/dashboard/summary/');
    setSummary(data);
  };

  const loadIncidents = async () => {
    const data = await apiRequest('/incidents/');
    setIncidents(data);
    if (selectedIncident) {
      const stillExists = data.find((incident) => incident.id === selectedIncident);
      if (!stillExists) {
        setSelectedIncident(null);
      }
    }
  };

  const loadMessages = async (incidentId) => {
    const data = await apiRequest(`/messages/?incident=${incidentId}`);
    setMessages(data);
  };

  const loadDistributionLists = async (teamId = selectedTeam) => {
    const globalPromise = apiRequest('/distribution-lists/?team=global');
    if (!teamId) {
      const globalLists = await globalPromise;
      setDistributionLists(Array.isArray(globalLists) ? globalLists : []);
      return;
    }
    const [teamLists, globalLists] = await Promise.all([
      apiRequest(`/distribution-lists/?team=${teamId}`),
      globalPromise,
    ]);
    const normalizedTeamLists = Array.isArray(teamLists) ? teamLists : [];
    const normalizedGlobalLists = Array.isArray(globalLists) ? globalLists : [];
    setDistributionLists([...normalizedTeamLists, ...normalizedGlobalLists]);
  };

  const filteredIncidents = useMemo(() => {
    const list = Array.isArray(incidents) ? incidents : [];
    if (!selectedTeam) return list;
    return list.filter((incident) => incident.team === selectedTeam);
  }, [incidents, selectedTeam]);

  const availableLists = useMemo(() => {
    const lists = Array.isArray(distributionLists) ? distributionLists : [];
    if (!selectedTeam) return lists;
    return lists.filter((list) => list.team === selectedTeam || list.scope === 'global');
  }, [distributionLists, selectedTeam]);

  const templateOptions = useMemo(() => templates || [], [templates]);

  const handleIncidentSubmit = async (event) => {
    event.preventDefault();
    if (!selectedTeam) return;
    try {
      setLoading(true);
      setError('');
      await apiRequest('/incidents/', {
        method: 'POST',
        body: {
          ...incidentForm,
          team: selectedTeam,
          primary_distribution_list: incidentForm.primary_distribution_list || null,
        },
      });
      setIncidentForm(defaultIncidentForm);
      await loadIncidents();
      await loadSummary();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMessageSubmit = async (event) => {
    event.preventDefault();
    if (!selectedIncident) return;
    try {
      setLoading(true);
      setError('');
      const payload = new FormData();
      payload.append('incident', selectedIncident);
      payload.append('subject', messageForm.subject);
      payload.append('body', messageForm.body);
      payload.append('template_type', messageForm.template_type);
      if (messageForm.distribution_list) {
        payload.append('distribution_list', messageForm.distribution_list);
      }
      if (messageForm.extraRecipients) {
        payload.append('extra_recipients', messageForm.extraRecipients);
      }
      messageFiles.forEach((file) => payload.append('attachments', file));

      await apiRequest('/messages/', {
        method: 'POST',
        body: payload,
        headers: {},
      });

      setMessageForm(defaultMessageForm);
      setMessageFiles([]);
      await loadMessages(selectedIncident);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const parseEntriesFromEmails = () => {
    return listForm.emails
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [address, entryDescription] = line.split('|').map((part) => part.trim());
        return {
          email: address,
          description: entryDescription || '',
        };
      });
  };

  const handleDistributionListSubmit = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setError('');
      const entries = parseEntriesFromEmails();
      if (listForm.scope === 'team' && !selectedTeam) {
        throw new Error('Select a team before creating a team-scoped list.');
      }
      await apiRequest('/distribution-lists/', {
        method: 'POST',
        body: {
          name: listForm.name,
          description: listForm.description,
          team: listForm.scope === 'team' ? selectedTeam : null,
          entries,
        },
      });
      setListForm(defaultListForm);
      await loadDistributionLists();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseIncident = async (event) => {
    event.preventDefault();
    if (!selectedIncident) return;
    try {
      setLoading(true);
      setError('');
      await apiRequest(`/incidents/${selectedIncident}/close/`, {
        method: 'POST',
        body: {
          final_subject: closeForm.subject,
          final_body: closeForm.body,
          distribution_list: closeForm.distribution_list || null,
        },
      });
      setCloseForm(defaultCloseForm);
      await Promise.all([loadIncidents(), loadMessages(selectedIncident), loadSummary()]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectedIncidentDetails = filteredIncidents.find(
    (incident) => incident.id === selectedIncident
  );

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Service Communications</h1>
          <p>Structured incident and announcement workflows</p>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={() => navigate('/diagnostics')}>
            Diagnostics
          </button>
          <div className="user-meta">
            <span>{auth?.user?.first_name || auth?.user?.email}</span>
            <small>{auth?.user?.email}</small>
          </div>
          <button className="secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <section className="summary-grid">
        <div className="summary-card">
          <h3>Open Incidents</h3>
          <p className="summary-value">{summary.open_incident_count}</p>
        </div>
        <div className="summary-card recent">
          <h3>Recent Messages</h3>
          <ul>
            {summary.recent_messages.map((item) => (
              <li key={item.id}>
                <strong>{item.incident_reference}</strong> — {item.subject}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <div className="panel-header">
            <h2>Teams</h2>
          </div>
          <select
            value={selectedTeam || ''}
            onChange={(e) => setSelectedTeam(Number(e.target.value))}
          >
            <option value="" disabled>
              Select a team
            </option>
            {Array.isArray(teams) &&
              teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
          </select>
          <div className="template-hints">
            <h4>Templates</h4>
            <ul>
              {templateOptions.map((template) => (
                <li key={template.id}>
                  <strong>{template.label}</strong>: {template.subject}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>New Incident</h2>
          </div>
          <form onSubmit={handleIncidentSubmit} className="form-grid">
            <input
              placeholder="Title"
              value={incidentForm.title}
              onChange={(e) => setIncidentForm({ ...incidentForm, title: e.target.value })}
              required
            />
            <textarea
              placeholder="Summary"
              value={incidentForm.summary}
              onChange={(e) => setIncidentForm({ ...incidentForm, summary: e.target.value })}
              required
            />
            <textarea
              placeholder="Impact statement"
              value={incidentForm.impact}
              onChange={(e) => setIncidentForm({ ...incidentForm, impact: e.target.value })}
            />
            <input
              placeholder="Severity (e.g., P1, P2)"
              value={incidentForm.severity}
              onChange={(e) => setIncidentForm({ ...incidentForm, severity: e.target.value })}
            />
            <select
              value={incidentForm.template_type}
              onChange={(e) => setIncidentForm({ ...incidentForm, template_type: e.target.value })}
            >
              {templateOptions.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.label}
                </option>
              ))}
            </select>
            <select
              value={incidentForm.primary_distribution_list}
              onChange={(e) =>
                setIncidentForm({ ...incidentForm, primary_distribution_list: e.target.value })
              }
            >
              <option value="">Primary distribution list</option>
              {availableLists.map((list) => (
                <option key={list.id} value={list.id}>
                  {list.name}
                </option>
              ))}
            </select>
            <button type="submit" disabled={loading}>
              Create Incident
            </button>
          </form>
        </div>
      </section>

      <section className="grid">
        <div className="panel tall">
          <div className="panel-header">
            <h2>Active Incidents</h2>
          </div>
          <ul className="incident-list">
            {filteredIncidents.map((incident) => (
              <li
                key={incident.id}
                className={incident.id === selectedIncident ? 'active' : ''}
                onClick={() => setSelectedIncident(incident.id)}
              >
                <div>
                  <strong>{incident.reference_id}</strong> — {incident.title}
                  <span className={`status-pill ${incident.status}`}>{incident.status}</span>
                </div>
                <small>{incident.summary}</small>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel tall">
          <div className="panel-header">
            <h2>Message Timeline</h2>
          </div>
          {selectedIncidentDetails ? (
            <>
              <form onSubmit={handleMessageSubmit} className="form-grid">
                <input
                  placeholder="Subject"
                  value={messageForm.subject}
                  onChange={(e) => setMessageForm({ ...messageForm, subject: e.target.value })}
                  required
                />
                <textarea
                  placeholder="Message body"
                  value={messageForm.body}
                  onChange={(e) => setMessageForm({ ...messageForm, body: e.target.value })}
                  required
                />
                <select
                  value={messageForm.template_type}
                  onChange={(e) => setMessageForm({ ...messageForm, template_type: e.target.value })}
                >
                  {templateOptions.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.label}
                    </option>
                  ))}
                </select>
                <select
                  value={messageForm.distribution_list}
                  onChange={(e) =>
                    setMessageForm({ ...messageForm, distribution_list: e.target.value })
                  }
                >
                  <option value="">Distribution list</option>
                  {availableLists.map((list) => (
                    <option key={list.id} value={list.id}>
                      {list.name}
                    </option>
                  ))}
                </select>
                <input
                  placeholder="Extra recipients (comma separated)"
                  value={messageForm.extraRecipients}
                  onChange={(e) =>
                    setMessageForm({ ...messageForm, extraRecipients: e.target.value })
                  }
                />
                <input
                  type="file"
                  multiple
                  onChange={(e) => setMessageFiles(Array.from(e.target.files))}
                />
                <button type="submit" disabled={loading}>
                  Send Message
                </button>
              </form>

              <hr />

              <form onSubmit={handleCloseIncident} className="form-grid">
                <h3>Close Incident</h3>
                <input
                  placeholder="Final subject"
                  value={closeForm.subject}
                  onChange={(e) => setCloseForm({ ...closeForm, subject: e.target.value })}
                  required
                />
                <textarea
                  placeholder="Final message body"
                  value={closeForm.body}
                  onChange={(e) => setCloseForm({ ...closeForm, body: e.target.value })}
                  required
                />
                <select
                  value={closeForm.distribution_list}
                  onChange={(e) =>
                    setCloseForm({ ...closeForm, distribution_list: e.target.value })
                  }
                >
                  <option value="">Use incident default list</option>
                  {availableLists.map((list) => (
                    <option key={list.id} value={list.id}>
                      {list.name}
                    </option>
                  ))}
                </select>
                <button type="submit" disabled={loading}>
                  Close Incident & Notify
                </button>
              </form>

              <ul className="timeline">
                {messages.map((message) => (
                  <li key={message.id}>
                    <div className="timeline-header">
                      <strong>{message.subject}</strong>
                      <span>{new Date(message.created_at).toLocaleString()}</span>
                    </div>
                    <p>{message.body}</p>
                    <small>Delivery: {message.delivery_status}</small>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p>Select an incident to view the timeline.</p>
          )}
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <div className="panel-header">
            <h2>Distribution Lists</h2>
          </div>
          <form onSubmit={handleDistributionListSubmit} className="form-grid">
            <input
              placeholder="List name"
              value={listForm.name}
              onChange={(e) => setListForm({ ...listForm, name: e.target.value })}
              required
            />
            <textarea
              placeholder="List description"
              value={listForm.description}
              onChange={(e) => setListForm({ ...listForm, description: e.target.value })}
            />
            <textarea
              placeholder="Email addresses (one per line, optional description with | )"
              value={listForm.emails}
              onChange={(e) => setListForm({ ...listForm, emails: e.target.value })}
            />
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  value="team"
                  checked={listForm.scope === 'team'}
                  onChange={(e) => setListForm({ ...listForm, scope: e.target.value })}
                />
                Team list
              </label>
              <label>
                <input
                  type="radio"
                  value="global"
                  checked={listForm.scope === 'global'}
                  onChange={(e) => setListForm({ ...listForm, scope: e.target.value })}
                />
                Global list
              </label>
            </div>
            <button type="submit" disabled={loading}>
              Save Distribution List
            </button>
          </form>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Stored Lists</h2>
          </div>
          <ul className="list-view">
            {distributionLists.map((list) => (
              <li key={list.id}>
                <strong>{list.name}</strong> ({list.scope})
                <p>{list.description}</p>
                <small>{list.entries.length} recipients</small>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {loading && <div className="backdrop">Working...</div>}
    </div>
  );
}

export default Dashboard;
