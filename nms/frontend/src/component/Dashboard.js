import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';
import '../assets/ServiceCommunications.css';

const REGION_OPTIONS = ['Global', 'India', 'Africa', 'Russia'];

const formatDateTime = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

const toLocalInputValue = (value) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const tzOffset = date.getTimezoneOffset() * 60000;
  const local = new Date(date.getTime() - tzOffset);
  return local.toISOString().slice(0, 16);
};

const normalizeDateForApi = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
};

const getDefaultPointOfContact = (auth) => {
  if (!auth?.user) return '';
  const { first_name: firstName, last_name: lastName, email } = auth.user;
  const fullName = [firstName, lastName].filter(Boolean).join(' ').trim();
  return fullName || email || '';
};

const buildDefaultIncidentForm = () => ({
  incNumber: '',
  subject: '',
  incidentType: 'major',
  templateType: 'incident',
  problemDescription: '',
  workaround: '',
  affectedRegions: [],
  nextCommunicationTime: '',
  distributionLists: [],
  impact: '',
  severity: 'P3',
});

const buildDefaultMessageForm = (auth) => ({
  subject: '',
  body: '',
  templateType: 'incident',
  distributionLists: [],
  extraRecipients: '',
  pointOfContact: getDefaultPointOfContact(auth),
  problemDescription: '',
  workaround: '',
  nextCommunicationTime: '',
});

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
  const [incidentForm, setIncidentForm] = useState(buildDefaultIncidentForm);
  const [messageForm, setMessageForm] = useState(() => buildDefaultMessageForm(auth));
  const [messageFiles, setMessageFiles] = useState([]);
  const [listForm, setListForm] = useState(defaultListForm);
  const [closeForm, setCloseForm] = useState(defaultCloseForm);
  const [summary, setSummary] = useState({ open_incident_count: 0, recent_messages: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSettingsDropdown, setShowSettingsDropdown] = useState(false);
  const refreshPromiseRef = useRef(null);
  const settingsMenuRef = useRef(null);

  const previousIncidentRef = useRef(null);

  const persistAuth = useCallback(
    (nextAuth) => {
      if (nextAuth) {
        localStorage.setItem('nmsAuth', JSON.stringify(nextAuth));
      } else {
        localStorage.removeItem('nmsAuth');
      }
      setAuth(nextAuth);
    },
    [setAuth]
  );

  const fetchWithToken = useCallback(
    (path, options = {}, forcedToken) => {
      const opts = { ...options };
      const headers = { ...(opts.headers || {}) };
      const requestToken = forcedToken || token;
      const shouldSerializeBody = opts.body && !(opts.body instanceof FormData);
      if (!opts.body || shouldSerializeBody) {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json';
      }
      if (requestToken) {
        headers.Authorization = `Bearer ${requestToken}`;
      }
      opts.headers = headers;
      if (shouldSerializeBody && typeof opts.body !== 'string') {
        opts.body = JSON.stringify(opts.body);
      }
      return fetch(`${apiBaseUrl}${path}`, {
        credentials: 'include',
        ...opts,
      });
    },
    [apiBaseUrl, token]
  );

  const refreshAccessToken = useCallback(async () => {
    if (!auth?.refresh) {
      throw new Error('Session expired. Please sign in again.');
    }
    if (!refreshPromiseRef.current) {
      refreshPromiseRef.current = (async () => {
        const response = await fetch(`${apiBaseUrl}/auth/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ refresh: auth.refresh }),
        });
        let data = null;
        try {
          data = await response.json();
        } catch (err) {
          // ignore parsing issue, handled below
        }
        if (!response.ok || !data?.access) {
          persistAuth(null);
          navigate('/dashboard');
          throw new Error(data?.detail || 'Session expired. Please sign in again.');
        }
        const nextAuth = {
          ...(auth || {}),
          access: data.access,
          refresh: data.refresh || auth.refresh,
        };
        persistAuth(nextAuth);
        return nextAuth.access;
      })().finally(() => {
        refreshPromiseRef.current = null;
      });
    }
    return refreshPromiseRef.current;
  }, [apiBaseUrl, auth, navigate, persistAuth]);

  const apiRequest = useCallback(
    async (path, options = {}, allowRefresh = true) => {
      const execute = async (overrideToken) => {
        const response = await fetchWithToken(path, options, overrideToken);
        if (response.status === 204) {
          return null;
        }
        let data = null;
        try {
          data = await response.json();
        } catch (err) {
          // ignore json parse issues for empty bodies
        }
        if (!response.ok) {
          const detail =
            data?.detail || data?.message || (typeof data === 'string' ? data : 'Request failed');
          const error = new Error(detail);
          error.status = response.status;
          error.responseData = data;
          throw error;
        }
        return data;
      };

      try {
        return await execute();
      } catch (err) {
        if (err.status === 401) {
          if (allowRefresh && auth?.refresh) {
            const newAccess = await refreshAccessToken();
            return execute(newAccess);
          }
          persistAuth(null);
          navigate('/dashboard');
        }
        throw err;
      }
    },
    [auth?.refresh, fetchWithToken, navigate, persistAuth, refreshAccessToken]
  );

  const handleNavigateHome = () => {
    setShowSettingsDropdown(false);
    navigate('/dashboard');
  };

  const handleLogout = () => {
    setShowSettingsDropdown(false);
    persistAuth(null);
    navigate('/dashboard');
  };

  useEffect(() => {
    if (!token) {
      navigate('/dashboard');
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

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (settingsMenuRef.current && !settingsMenuRef.current.contains(event.target)) {
        setShowSettingsDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

  const distributionLookup = useMemo(() => {
    const map = new Map();
    (distributionLists || []).forEach((list) => map.set(list.id, list));
    return map;
  }, [distributionLists]);

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

  useEffect(() => {
    setMessageForm((prev) => ({
      ...prev,
      pointOfContact: prev.pointOfContact || getDefaultPointOfContact(auth),
    }));
  }, [auth]);

  useEffect(() => {
    if (!selectedIncident) {
      previousIncidentRef.current = null;
      setMessageForm(buildDefaultMessageForm(auth));
      return;
    }
    const details = incidents.find((incident) => incident.id === selectedIncident);
    if (!details || previousIncidentRef.current === details.id) {
      return;
    }
    previousIncidentRef.current = details.id;
    setMessageForm((prev) => ({
      ...prev,
      pointOfContact: prev.pointOfContact || getDefaultPointOfContact(auth),
      problemDescription: details.problem_description || '',
      workaround: details.workaround || '',
      nextCommunicationTime: toLocalInputValue(details.next_communication_time),
      distributionLists: Array.isArray(details.distribution_lists)
        ? details.distribution_lists
        : [],
    }));
  }, [selectedIncident, incidents, auth]);

  const handleIncidentDistributionChange = (event) => {
    const values = Array.from(event.target.selectedOptions).map((option) => Number(option.value));
    setIncidentForm({ ...incidentForm, distributionLists: values });
  };

  const handleMessageDistributionChange = (event) => {
    const values = Array.from(event.target.selectedOptions).map((option) => Number(option.value));
    setMessageForm({ ...messageForm, distributionLists: values });
  };

  const toggleRegion = (region) => {
    setIncidentForm((prev) => {
      const exists = prev.affectedRegions.includes(region);
      const affectedRegions = exists
        ? prev.affectedRegions.filter((item) => item !== region)
        : [...prev.affectedRegions, region];
      return { ...prev, affectedRegions };
    });
  };

  const handleIncidentSubmit = async (event) => {
    event.preventDefault();
    if (!selectedTeam) return;
    try {
      setLoading(true);
      setError('');
      await apiRequest('/incidents/', {
        method: 'POST',
        body: {
          team: selectedTeam,
          inc_number: incidentForm.incNumber,
          title: incidentForm.subject,
          summary: incidentForm.problemDescription,
          impact: incidentForm.impact,
          severity: incidentForm.severity,
          template_type: incidentForm.templateType,
          problem_description: incidentForm.problemDescription,
          workaround: incidentForm.workaround,
          affected_regions: incidentForm.affectedRegions,
          next_communication_time: normalizeDateForApi(incidentForm.nextCommunicationTime),
          distribution_lists: incidentForm.distributionLists,
        },
      });
      setIncidentForm(buildDefaultIncidentForm());
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
      payload.append('template_type', messageForm.templateType);
      payload.append('point_of_contact', messageForm.pointOfContact);
      payload.append('problem_description', messageForm.problemDescription);
      payload.append('workaround', messageForm.workaround);
      const nextComms = normalizeDateForApi(messageForm.nextCommunicationTime);
      if (nextComms) {
        payload.append('next_communication_time', nextComms);
      }
      messageForm.distributionLists.forEach((listId) => payload.append('distribution_lists', listId));
      if (messageForm.extraRecipients) {
        payload.append('extra_recipients', messageForm.extraRecipients);
      }
      messageFiles.forEach((file) => payload.append('attachments', file));

      await apiRequest('/messages/', {
        method: 'POST',
        body: payload,
        headers: {},
      });

      setMessageForm(() => ({
        ...buildDefaultMessageForm(auth),
        problemDescription: selectedIncidentDetails?.problem_description || '',
        workaround: selectedIncidentDetails?.workaround || '',
        nextCommunicationTime: toLocalInputValue(selectedIncidentDetails?.next_communication_time),
        distributionLists: selectedIncidentDetails?.distribution_lists || [],
      }));
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
    <div className="app-shell service-communications">
      <header className="app-header sc-header">
        <div className="sc-branding">
          <img src="logo_left.png" alt="Network Operations" className="sc-logo" />
          <div>
            <h1>Service Communications</h1>
            <p>Structured incident and announcement workflows</p>
          </div>
        </div>
        <div className="header-actions sc-header-actions" ref={settingsMenuRef}>
          <div className="user-meta">
            <span>{auth?.user?.first_name || auth?.user?.email}</span>
            <small>{auth?.user?.email}</small>
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={() => setShowSettingsDropdown((prev) => !prev)}
          >
            ⚙️
          </button>
          {showSettingsDropdown && (
            <div className="sc-settings-dropdown">
              <button type="button" onClick={handleNavigateHome}>
                🏠 Home
              </button>
              <button type="button" onClick={handleLogout}>
                ↩ Logout
              </button>
            </div>
          )}
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
            onChange={(e) => {
              const value = e.target.value;
              setSelectedTeam(value ? Number(value) : null);
            }}
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
              placeholder="INC Number"
              value={incidentForm.incNumber}
              onChange={(e) => setIncidentForm({ ...incidentForm, incNumber: e.target.value })}
              required
            />
            <input
              placeholder="Subject Line"
              value={incidentForm.subject}
              onChange={(e) => setIncidentForm({ ...incidentForm, subject: e.target.value })}
              required
            />
            <select
              value={incidentForm.incidentType}
              onChange={(e) => setIncidentForm({ ...incidentForm, incidentType: e.target.value })}
            >
              <option value="major">Major</option>
              <option value="critical">Critical</option>
              <option value="informational">Informational</option>
            </select>
            <textarea
              placeholder="Problem Description"
              value={incidentForm.problemDescription}
              onChange={(e) =>
                setIncidentForm({ ...incidentForm, problemDescription: e.target.value })
              }
              required
            />
            <textarea
              placeholder="Workaround (optional)"
              value={incidentForm.workaround}
              onChange={(e) => setIncidentForm({ ...incidentForm, workaround: e.target.value })}
            />
            <textarea
              placeholder="Impact statement"
              value={incidentForm.impact}
              onChange={(e) => setIncidentForm({ ...incidentForm, impact: e.target.value })}
            />
            <div className="checkbox-grid">
              <label>Affected Regions</label>
              <div className="regions">
                {REGION_OPTIONS.map((region) => (
                  <label key={region}>
                    <input
                      type="checkbox"
                      checked={incidentForm.affectedRegions.includes(region)}
                      onChange={() => toggleRegion(region)}
                    />
                    {region}
                  </label>
                ))}
              </div>
            </div>
            <label>
              Next Communication Time
              <input
                type="datetime-local"
                value={incidentForm.nextCommunicationTime}
                onChange={(e) =>
                  setIncidentForm({ ...incidentForm, nextCommunicationTime: e.target.value })
                }
              />
            </label>
            <label>
              Templates
              <select
                value={incidentForm.templateType}
                onChange={(e) => setIncidentForm({ ...incidentForm, templateType: e.target.value })}
              >
                {templateOptions.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Distribution Lists
              <select
                multiple
                value={incidentForm.distributionLists.map(String)}
                onChange={handleIncidentDistributionChange}
              >
                {availableLists.map((list) => (
                  <option key={list.id} value={list.id}>
                    {list.name}
                  </option>
                ))}
              </select>
            </label>
            <button type="submit" disabled={loading}>
              Save Incident
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
                  <strong>{incident.reference_id || incident.inc_number || incident.id}</strong> —{' '}
                  {incident.title}
                  <span className={`status-pill ${incident.status}`}>{incident.status}</span>
                </div>
                <small>
                  {incident.inc_number ? `${incident.inc_number} • ` : ''}
                  {incident.incident_type?.toUpperCase()}
                </small>
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
              <div className="incident-details-card">
                <p>
                  <strong>INC:</strong> {selectedIncidentDetails.inc_number || '—'}
                </p>
                <p>
                  <strong>Type:</strong> {selectedIncidentDetails.incident_type}
                </p>
                <p>
                  <strong>Problem:</strong> {selectedIncidentDetails.problem_description || '—'}
                </p>
                <p>
                  <strong>Workaround:</strong> {selectedIncidentDetails.workaround || '—'}
                </p>
                <p>
                  <strong>Affected Regions:</strong>{' '}
                  {Array.isArray(selectedIncidentDetails.affected_regions) &&
                  selectedIncidentDetails.affected_regions.length
                    ? selectedIncidentDetails.affected_regions.join(', ')
                    : '—'}
                </p>
                <p>
                  <strong>Next Communication:</strong>{' '}
                  {formatDateTime(selectedIncidentDetails.next_communication_time)}
                </p>
              </div>

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
                  value={messageForm.templateType}
                  onChange={(e) => setMessageForm({ ...messageForm, templateType: e.target.value })}
                >
                  {templateOptions.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.label}
                    </option>
                  ))}
                </select>
                <label>
                  Distribution Lists
                  <select
                    multiple
                    value={messageForm.distributionLists.map(String)}
                    onChange={handleMessageDistributionChange}
                  >
                    {availableLists.map((list) => (
                      <option key={list.id} value={list.id}>
                        {list.name}
                      </option>
                    ))}
                  </select>
                </label>
                <input
                  placeholder="Point of Contact"
                  value={messageForm.pointOfContact}
                  onChange={(e) =>
                    setMessageForm({ ...messageForm, pointOfContact: e.target.value })
                  }
                />
                <textarea
                  placeholder="Override Problem Description (optional)"
                  value={messageForm.problemDescription}
                  onChange={(e) =>
                    setMessageForm({ ...messageForm, problemDescription: e.target.value })
                  }
                />
                <textarea
                  placeholder="Override Workaround (optional)"
                  value={messageForm.workaround}
                  onChange={(e) => setMessageForm({ ...messageForm, workaround: e.target.value })}
                />
                <label>
                  Override Next Communication Time
                  <input
                    type="datetime-local"
                    value={messageForm.nextCommunicationTime}
                    onChange={(e) =>
                      setMessageForm({ ...messageForm, nextCommunicationTime: e.target.value })
                    }
                  />
                </label>
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
                    <div className="timeline-meta">
                      <small>POC: {message.point_of_contact || '—'}</small>
                      <small>
                        Next Communication: {formatDateTime(message.next_communication_time)}
                      </small>
                    </div>
                    <p>
                      <strong>Problem:</strong> {message.problem_description || '—'}
                    </p>
                    {message.workaround && (
                      <p>
                        <strong>Workaround:</strong> {message.workaround}
                      </p>
                    )}
                    <small>
                      Distribution:{' '}
                      {(() => {
                        const listNames = [
                          ...(message.distribution_lists || []),
                        ].map((id) => distributionLookup.get(id)?.name || `List ${id}`);
                        if (!listNames.length && message.distribution_list) {
                          listNames.push(
                            distributionLookup.get(message.distribution_list)?.name ||
                              `List ${message.distribution_list}`
                          );
                        }
                        return listNames.length ? listNames.join(', ') : '—';
                      })()}
                    </small>
                    <br />
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
                <small>{Array.isArray(list.entries) ? list.entries.length : 0} recipients</small>
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
