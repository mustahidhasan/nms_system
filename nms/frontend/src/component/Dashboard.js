import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';
import '../assets/ServiceCommunications.css';

const REGION_OPTIONS = ['Global', 'India', 'Africa', 'Russia'];

const SUB_NAV_SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'teams', label: 'Teams & Templates' },
  { id: 'incident', label: 'Create Incident' },
  { id: 'active', label: 'Active Incidents' },
  { id: 'messaging', label: 'Messaging' },
  { id: 'lists', label: 'Distribution Lists' },
];

const PANEL_KEYS = ['teams', 'incident', 'active', 'messaging', 'lists', 'storedLists'];
const COLLAPSE_STORAGE_KEY = 'nmsCollapsedPanels';

const buildDefaultCollapsedState = () =>
  PANEL_KEYS.reduce((acc, key) => {
    acc[key] = false;
    return acc;
  }, {});

const toArray = (payload) => {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (payload && Array.isArray(payload.results)) {
    return payload.results;
  }
  if (payload && Array.isArray(payload.data)) {
    return payload.data;
  }
  return [];
};

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
  const [activeSubNav, setActiveSubNav] = useState('overview');
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [collapsedPanels, setCollapsedPanels] = useState(() => {
    const defaults = buildDefaultCollapsedState();
    if (typeof window === 'undefined') {
      return defaults;
    }
    try {
      const raw = window.localStorage.getItem(COLLAPSE_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') {
          return {
            ...defaults,
            ...parsed,
          };
        }
      }
    } catch (err) {
      // ignore storage issues and fall back to defaults
    }
    return defaults;
  });
  const refreshPromiseRef = useRef(null);
  const settingsMenuRef = useRef(null);
  const distributionListFormRef = useRef(null);
  const overviewSectionRef = useRef(null);
  const teamsPanelRef = useRef(null);
  const incidentPanelRef = useRef(null);
  const activeIncidentsRef = useRef(null);
  const messagePanelRef = useRef(null);
  const distributionListsPanelRef = useRef(null);

  const previousIncidentRef = useRef(null);

  const profileDisplayName = useMemo(() => {
    const first = (auth?.user?.first_name || '').trim();
    if (first) return first;
    const email = auth?.user?.email || '';
    if (email) {
      const [localPart] = email.split('@');
      if (localPart) return localPart;
    }
    return 'Service Comms User';
  }, [auth]);

  const userInitials = useMemo(() => {
    const first = auth?.user?.first_name || '';
    const last = auth?.user?.last_name || '';
    const initials = `${first.slice(0, 1)}${last.slice(0, 1)}`.trim();
    if (initials) return initials.toUpperCase();
    const email = auth?.user?.email || '';
    return email.slice(0, 2).toUpperCase() || 'SC';
  }, [auth]);

  const sectionRefs = useMemo(
    () => ({
      overview: overviewSectionRef,
      teams: teamsPanelRef,
      incident: incidentPanelRef,
      active: activeIncidentsRef,
      messaging: messagePanelRef,
      lists: distributionListsPanelRef,
    }),
    [
      overviewSectionRef,
      teamsPanelRef,
      incidentPanelRef,
      activeIncidentsRef,
      messagePanelRef,
      distributionListsPanelRef,
    ]
  );

  useEffect(() => {
    let ticking = false;
    const handleScroll = () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        const ranked = SUB_NAV_SECTIONS.map(({ id }) => {
          const ref = sectionRefs[id];
          if (!ref?.current) {
            return null;
          }
          const rect = ref.current.getBoundingClientRect();
          const distance = Math.abs(rect.top - 150);
          return { id, distance };
        }).filter(Boolean);
        if (ranked.length) {
          ranked.sort((a, b) => a.distance - b.distance);
          const nextSection = ranked[0].id;
          setActiveSubNav((prev) => (prev === nextSection ? prev : nextSection));
        }
        setShowScrollTop(window.scrollY > 400);
        ticking = false;
      });
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [sectionRefs]);

  const handleSectionNav = useCallback(
    (sectionId) => {
      setActiveSubNav(sectionId);
      const target = sectionRefs[sectionId]?.current;
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },
    [sectionRefs]
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(COLLAPSE_STORAGE_KEY, JSON.stringify(collapsedPanels));
    } catch (err) {
      // ignore storage persistence errors
    }
  }, [collapsedPanels]);

  const togglePanel = useCallback((panelId) => {
    setCollapsedPanels((prev) => ({
      ...prev,
      [panelId]: !prev[panelId],
    }));
  }, []);

  const isPanelCollapsed = useCallback((panelId) => !!collapsedPanels[panelId], [collapsedPanels]);

  const handlePanelHeaderKeyDown = (event, panelId) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      togglePanel(panelId);
    }
  };

  const handleScrollTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

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
            data?.detail ||
            data?.message ||
            (data && typeof data === 'object'
              ? JSON.stringify(data)
              : typeof data === 'string'
              ? data
              : 'Request failed');
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
    navigate('/');
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
        setTemplates(toArray(templateData));
        const normalizedTeams = toArray(teamData);
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
    const list = toArray(data);
    setIncidents(list);
    if (selectedIncident) {
      const stillExists = list.find((incident) => incident.id === selectedIncident);
      if (!stillExists) {
        setSelectedIncident(null);
      }
    }
  };

  const loadMessages = async (incidentId) => {
    const data = await apiRequest(`/messages/?incident=${incidentId}`);
    setMessages(toArray(data));
  };

  const loadDistributionLists = async (teamId = selectedTeam) => {
    const globalPromise = apiRequest('/distribution-lists/?team=global');
    if (!teamId) {
      const globalLists = toArray(await globalPromise);
      setDistributionLists(globalLists);
      return;
    }
    const [teamLists, globalLists] = await Promise.all([
      apiRequest(`/distribution-lists/?team=${teamId}`),
      globalPromise,
    ]);
    const normalizedTeamLists = toArray(teamLists);
    const normalizedGlobalLists = toArray(globalLists);
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

  const selectedIncidentDetails = useMemo(
    () => filteredIncidents.find((incident) => incident.id === selectedIncident),
    [filteredIncidents, selectedIncident]
  );

  useEffect(() => {
    setIncidentForm((prev) => {
      const allowedIds = availableLists.map((list) => list.id);
      const filtered = prev.distributionLists.filter((id) => allowedIds.includes(id));
      if (filtered.length) {
        const sameLength = filtered.length === prev.distributionLists.length;
        const sameOrder = sameLength && filtered.every((id, idx) => id === prev.distributionLists[idx]);
        if (sameOrder) {
          return prev;
        }
        return { ...prev, distributionLists: filtered };
      }
      if (!availableLists.length) {
        return prev.distributionLists.length ? { ...prev, distributionLists: [] } : prev;
      }
      const defaultSelection = [availableLists[0].id];
      const alreadyDefault =
        prev.distributionLists.length === 1 && prev.distributionLists[0] === defaultSelection[0];
      return alreadyDefault ? prev : { ...prev, distributionLists: defaultSelection };
    });
  }, [availableLists]);

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

  useEffect(() => {
    setMessageForm((prev) => {
      const allowedIds = availableLists.map((list) => list.id);
      const filtered = prev.distributionLists.filter((id) => allowedIds.includes(id));
      let nextLists = filtered;
      if (!filtered.length) {
        const incidentDefaults = (Array.isArray(selectedIncidentDetails?.distribution_lists)
          ? selectedIncidentDetails.distribution_lists
          : []
        ).filter((id) => allowedIds.includes(id));
        if (incidentDefaults.length) {
          nextLists = incidentDefaults;
        } else if (allowedIds.length) {
          nextLists = [allowedIds[0]];
        } else {
          nextLists = [];
        }
      }
      const unchanged =
        nextLists.length === prev.distributionLists.length &&
        nextLists.every((id, idx) => id === prev.distributionLists[idx]);
      if (unchanged) {
        return prev;
      }
      return { ...prev, distributionLists: nextLists };
    });
  }, [availableLists, selectedIncidentDetails]);

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
    if (!incidentForm.incidentType) {
      setError('Type is required.');
      return;
    }
    if (!incidentForm.workaround.trim()) {
      setError('Workaround is required.');
      return;
    }
    if (!incidentForm.affectedRegions.length) {
      setError('Select at least one affected region.');
      return;
    }
    if (!incidentForm.distributionLists.length) {
      setError('Select at least one distribution list.');
      return;
    }
    if (!incidentForm.nextCommunicationTime) {
      setError('Next communication time is required.');
      return;
    }
    try {
      setLoading(true);
      setError('');
      await apiRequest('/incidents/', {
        method: 'POST',
        body: {
          team: selectedTeam,
          inc_number: incidentForm.incNumber,
          title: incidentForm.subject,
          incident_type: incidentForm.incidentType,
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
    const allowedIds = availableLists.map((list) => list.id);
    const fallbackLists = (Array.isArray(selectedIncidentDetails?.distribution_lists)
      ? selectedIncidentDetails.distribution_lists
      : []
    ).map(Number);
    const chosenListsRaw = messageForm.distributionLists.length
      ? messageForm.distributionLists
      : fallbackLists;
    let chosenLists = chosenListsRaw.filter((id) => allowedIds.includes(id));
    if (!chosenLists.length && allowedIds.length) {
      chosenLists = [allowedIds[0]];
    }
    if (!chosenLists.length) {
      setError('Add a distribution list to this incident before sending a message.');
      return;
    }
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
      chosenLists.forEach((listId) => payload.append('distribution_lists', listId));
      if (messageForm.extraRecipients) {
        const recipients = messageForm.extraRecipients
          .split(/[\s,;]+/)
          .map((email) => email.trim())
          .filter(Boolean);
        recipients.forEach((email) => payload.append('extra_recipients', email));
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
      .split(/[\n,;]+/)
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => {
        const [address, entryDescription] = item.split('|').map((part) => part.trim());
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
      const created = await apiRequest('/distribution-lists/', {
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
      if (created?.id) {
        setIncidentForm((prev) => ({
          ...prev,
          distributionLists: Array.from(new Set([...prev.distributionLists, created.id])),
        }));
      }
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

  const scrollToDistributionListForm = () => {
    handleSectionNav('lists');
    distributionListFormRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const scrollToIncidentForm = () => {
    handleSectionNav('incident');
  };

  const scrollToActiveIncidents = () => {
    handleSectionNav('active');
  };

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
        <div className="header-actions sc-header-actions">
          <img
            src="logo_right.png"
            alt="Operations Partner"
            className="sc-logo sc-logo-compact"
          />
          <div className="sc-settings-trigger" ref={settingsMenuRef}>
            <button
              type="button"
              className={`icon-button ${showSettingsDropdown ? 'active' : ''}`}
              aria-haspopup="menu"
              aria-controls="sc-settings-menu"
              aria-expanded={showSettingsDropdown}
              onClick={() => setShowSettingsDropdown((prev) => !prev)}
            >
              ⚙️
            </button>
            {showSettingsDropdown && (
              <div className="sc-settings-dropdown" id="sc-settings-menu" role="menu">
                <div className="sc-profile-card" title={profileDisplayName}>
                  <div className="sc-avatar">{userInitials}</div>
                  <div className="sc-profile-details">
                    <span>{profileDisplayName}</span>
                  </div>
                </div>
                <button type="button" onClick={handleNavigateHome}>
                  🏠 Home
                </button>
                <button type="button" onClick={handleLogout}>
                  ↩ Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <nav className="sc-subnav">
        {SUB_NAV_SECTIONS.map((section) => (
          <button
            type="button"
            key={section.id}
            className={`subnav-item ${activeSubNav === section.id ? 'active' : ''}`}
            onClick={() => handleSectionNav(section.id)}
          >
            {section.label}
          </button>
        ))}
      </nav>

      {error && <div className="alert">{error}</div>}

      <section className="sc-overview" ref={overviewSectionRef} data-section="overview">
        <div className="summary-grid sc-overview-grid">
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
        </div>
        <div className="summary-actions">
          <button type="button" className="sc-action primary" onClick={scrollToIncidentForm}>
            Create New Incident
          </button>
          <button type="button" className="sc-action" onClick={scrollToActiveIncidents}>
            View All Active Incidents
          </button>
        </div>
      </section>

      <section className="grid">
        <div className="panel" data-section="teams" ref={teamsPanelRef}>
          <div
            className={`panel-header ${isPanelCollapsed('teams') ? 'collapsed' : ''}`}
            role="button"
            tabIndex={0}
            aria-expanded={!isPanelCollapsed('teams')}
            aria-controls="panel-teams"
            onClick={() => togglePanel('teams')}
            onKeyDown={(event) => handlePanelHeaderKeyDown(event, 'teams')}
          >
            <h2>Teams</h2>
            <span className="panel-toggle-indicator" aria-hidden="true">
              ▾
            </span>
          </div>
          <div
            id="panel-teams"
            className={`panel-body ${isPanelCollapsed('teams') ? 'collapsed' : ''}`}
          >
            <label className="form-field">
              <span>Select Team</span>
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
            </label>
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
        </div>

        <div className="panel" data-section="incident" ref={incidentPanelRef}>
          <div
            className={`panel-header ${isPanelCollapsed('incident') ? 'collapsed' : ''}`}
            role="button"
            tabIndex={0}
            aria-expanded={!isPanelCollapsed('incident')}
            aria-controls="panel-incident"
            onClick={() => togglePanel('incident')}
            onKeyDown={(event) => handlePanelHeaderKeyDown(event, 'incident')}
          >
            <h2>New Incident</h2>
            <span className="panel-toggle-indicator" aria-hidden="true">
              ▾
            </span>
          </div>
          <div
            id="panel-incident"
            className={`panel-body ${isPanelCollapsed('incident') ? 'collapsed' : ''}`}
          >
            <form onSubmit={handleIncidentSubmit} className="form-grid">
              <label className="form-field">
                <span>INC Number</span>
                <input
                  placeholder="INC123456"
                  value={incidentForm.incNumber}
                  onChange={(e) => setIncidentForm({ ...incidentForm, incNumber: e.target.value })}
                  required
                />
              </label>
              <label className="form-field">
                <span>Subject</span>
                <input
                  placeholder="Subject line for stakeholders"
                  value={incidentForm.subject}
                  onChange={(e) => setIncidentForm({ ...incidentForm, subject: e.target.value })}
                  required
                />
              </label>
              <label className="form-field">
                <span>Incident Type</span>
                <select
                  value={incidentForm.incidentType}
                  onChange={(e) => setIncidentForm({ ...incidentForm, incidentType: e.target.value })}
                  required
                >
                  <option value="major">Major</option>
                  <option value="critical">Critical</option>
                  <option value="informational">Informational</option>
                </select>
              </label>
              <label className="form-field">
                <span>Problem Description</span>
                <textarea
                  placeholder="Symptoms, scope, timeline"
                  value={incidentForm.problemDescription}
                  onChange={(e) =>
                    setIncidentForm({ ...incidentForm, problemDescription: e.target.value })
                  }
                  required
                />
              </label>
              <label className="form-field">
                <span>Workaround / Mitigations</span>
                <textarea
                  placeholder="Include known mitigations"
                  value={incidentForm.workaround}
                  onChange={(e) => setIncidentForm({ ...incidentForm, workaround: e.target.value })}
                  required
                />
              </label>
              <label className="form-field">
                <span>Impact Statement</span>
                <textarea
                  placeholder="Customers, services, regions"
                  value={incidentForm.impact}
                  onChange={(e) => setIncidentForm({ ...incidentForm, impact: e.target.value })}
                />
              </label>
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
              <label className="form-field">
                <span>Next Communication Time (UTC/local)</span>
                <input
                  type="datetime-local"
                  value={incidentForm.nextCommunicationTime}
                  onChange={(e) =>
                    setIncidentForm({ ...incidentForm, nextCommunicationTime: e.target.value })
                  }
                  required
                />
              </label>
              <label className="form-field">
                <span>Templates</span>
                <select
                  value={incidentForm.templateType}
                  onChange={(e) =>
                    setIncidentForm({ ...incidentForm, templateType: e.target.value })
                  }
                >
                  {templateOptions.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-field">
                <span>Distribution Lists</span>
                <select
                  multiple
                  value={incidentForm.distributionLists.map(String)}
                  onChange={handleIncidentDistributionChange}
                  required
                >
                  {availableLists.map((list) => (
                    <option key={list.id} value={list.id}>
                      {list.name}
                    </option>
                  ))}
                </select>
                {availableLists.length === 0 && (
                  <small className="form-hint">
                    No distribution lists yet.{' '}
                    <button
                      type="button"
                      onClick={scrollToDistributionListForm}
                      className="text-link"
                    >
                      Create one below
                    </button>
                  </small>
                )}
              </label>
              <button type="submit" disabled={loading}>
                Save Incident
              </button>
            </form>
          </div>
        </div>
      </section>

      <section className="grid">
        <div className="panel tall" data-section="active" ref={activeIncidentsRef}>
          <div
            className={`panel-header ${isPanelCollapsed('active') ? 'collapsed' : ''}`}
            role="button"
            tabIndex={0}
            aria-expanded={!isPanelCollapsed('active')}
            aria-controls="panel-active"
            onClick={() => togglePanel('active')}
            onKeyDown={(event) => handlePanelHeaderKeyDown(event, 'active')}
          >
            <h2>Active Incidents</h2>
            <span className="panel-toggle-indicator" aria-hidden="true">
              ▾
            </span>
          </div>
          <div
            id="panel-active"
            className={`panel-body ${isPanelCollapsed('active') ? 'collapsed' : ''}`}
          >
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
        </div>

        <div className="panel tall" data-section="messaging" ref={messagePanelRef}>
          <div
            className={`panel-header ${isPanelCollapsed('messaging') ? 'collapsed' : ''}`}
            role="button"
            tabIndex={0}
            aria-expanded={!isPanelCollapsed('messaging')}
            aria-controls="panel-messaging"
            onClick={() => togglePanel('messaging')}
            onKeyDown={(event) => handlePanelHeaderKeyDown(event, 'messaging')}
          >
            <h2>Message Timeline</h2>
            <span className="panel-toggle-indicator" aria-hidden="true">
              ▾
            </span>
          </div>
          <div
            id="panel-messaging"
            className={`panel-body ${isPanelCollapsed('messaging') ? 'collapsed' : ''}`}
          >
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
                  <label className="form-field">
                    <span>Subject</span>
                    <input
                      placeholder="Subject"
                      value={messageForm.subject}
                      onChange={(e) => setMessageForm({ ...messageForm, subject: e.target.value })}
                      required
                    />
                  </label>
                  <label className="form-field">
                    <span>Message Body</span>
                    <textarea
                      placeholder="Message body"
                      value={messageForm.body}
                      onChange={(e) => setMessageForm({ ...messageForm, body: e.target.value })}
                      required
                    />
                  </label>
                  <label className="form-field">
                    <span>Template</span>
                    <select
                      value={messageForm.templateType}
                      onChange={(e) =>
                        setMessageForm({ ...messageForm, templateType: e.target.value })
                      }
                    >
                      {templateOptions.map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="form-field">
                    <span>Distribution Lists</span>
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
                  <label className="form-field">
                    <span>Point of Contact</span>
                    <input
                      placeholder="Point of contact"
                      value={messageForm.pointOfContact}
                      onChange={(e) =>
                        setMessageForm({ ...messageForm, pointOfContact: e.target.value })
                      }
                    />
                  </label>
                  <label className="form-field">
                    <span>Override Problem Description</span>
                    <textarea
                      placeholder="Optional override"
                      value={messageForm.problemDescription}
                      onChange={(e) =>
                        setMessageForm({ ...messageForm, problemDescription: e.target.value })
                      }
                    />
                  </label>
                  <label className="form-field">
                    <span>Override Workaround</span>
                    <textarea
                      placeholder="Optional override"
                      value={messageForm.workaround}
                      onChange={(e) =>
                        setMessageForm({ ...messageForm, workaround: e.target.value })
                      }
                    />
                  </label>
                  <label className="form-field">
                    <span>Override Next Communication</span>
                    <input
                      type="datetime-local"
                      value={messageForm.nextCommunicationTime}
                      onChange={(e) =>
                        setMessageForm({ ...messageForm, nextCommunicationTime: e.target.value })
                      }
                    />
                  </label>
                  <label className="form-field">
                    <span>Extra Recipients</span>
                    <input
                      placeholder="Comma separated emails"
                      value={messageForm.extraRecipients}
                      onChange={(e) =>
                        setMessageForm({ ...messageForm, extraRecipients: e.target.value })
                      }
                    />
                  </label>
                  <label className="form-field">
                    <span>Attachments</span>
                    <input
                      type="file"
                      multiple
                      onChange={(e) => setMessageFiles(Array.from(e.target.files))}
                    />
                  </label>
                  <button type="submit" disabled={loading}>
                    Send Message
                  </button>
                </form>

                <hr />

                <form onSubmit={handleCloseIncident} className="form-grid">
                  <h3>Close Incident</h3>
                  <label className="form-field">
                    <span>Final Subject</span>
                    <input
                      placeholder="Final subject"
                      value={closeForm.subject}
                      onChange={(e) => setCloseForm({ ...closeForm, subject: e.target.value })}
                      required
                    />
                  </label>
                  <label className="form-field">
                    <span>Final Message Body</span>
                    <textarea
                      placeholder="Final message body"
                      value={closeForm.body}
                      onChange={(e) => setCloseForm({ ...closeForm, body: e.target.value })}
                      required
                    />
                  </label>
                  <label className="form-field">
                    <span>Distribution List</span>
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
                  </label>
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
              <p className="empty-state">Select an incident to view the timeline.</p>
            )}
          </div>
        </div>
      </section>

      <section className="grid">
        <div className="panel" data-section="lists" ref={distributionListsPanelRef}>
          <div
            className={`panel-header ${isPanelCollapsed('lists') ? 'collapsed' : ''}`}
            role="button"
            tabIndex={0}
            aria-expanded={!isPanelCollapsed('lists')}
            aria-controls="panel-lists"
            onClick={() => togglePanel('lists')}
            onKeyDown={(event) => handlePanelHeaderKeyDown(event, 'lists')}
          >
            <h2>Distribution Lists</h2>
            <span className="panel-toggle-indicator" aria-hidden="true">
              ▾
            </span>
          </div>
          <div
            id="panel-lists"
            className={`panel-body ${isPanelCollapsed('lists') ? 'collapsed' : ''}`}
          >
            <form
              onSubmit={handleDistributionListSubmit}
              className="form-grid"
              ref={distributionListFormRef}
            >
              <label className="form-field">
                <span>List Name</span>
                <input
                  placeholder="List name"
                  value={listForm.name}
                  onChange={(e) => setListForm({ ...listForm, name: e.target.value })}
                  required
                />
              </label>
              <label className="form-field">
                <span>Description</span>
                <textarea
                  placeholder="List description"
                  value={listForm.description}
                  onChange={(e) => setListForm({ ...listForm, description: e.target.value })}
                />
              </label>
              <label className="form-field">
                <span>Email Addresses</span>
                <textarea
                  placeholder="one@example.com | optional description"
                  value={listForm.emails}
                  onChange={(e) => setListForm({ ...listForm, emails: e.target.value })}
                />
              </label>
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
        </div>

        <div className="panel">
          <div
            className={`panel-header ${isPanelCollapsed('storedLists') ? 'collapsed' : ''}`}
            role="button"
            tabIndex={0}
            aria-expanded={!isPanelCollapsed('storedLists')}
            aria-controls="panel-storedLists"
            onClick={() => togglePanel('storedLists')}
            onKeyDown={(event) => handlePanelHeaderKeyDown(event, 'storedLists')}
          >
            <h2>Stored Lists</h2>
            <span className="panel-toggle-indicator" aria-hidden="true">
              ▾
            </span>
          </div>
          <div
            id="panel-storedLists"
            className={`panel-body ${isPanelCollapsed('storedLists') ? 'collapsed' : ''}`}
          >
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
        </div>
      </section>

      {showScrollTop && (
        <button type="button" className="scroll-top-btn" onClick={handleScrollTop} aria-label="Scroll to top">
          ↑
        </button>
      )}
      {loading && <div className="backdrop">Working...</div>}
    </div>
  );
}

export default Dashboard;
