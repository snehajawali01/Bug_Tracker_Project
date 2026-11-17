
import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const EMPTY_FORM = {
  title: '',
  description: '',
  priority: 'medium',
}

function formatStatus(value) {
  return {
    open: 'Open',
    in_progress: 'In Progress',
    resolved: 'Resolved',
    closed: 'Closed',
  }[value] || value
}

function formatPriority(value) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function formatBug(bug) {
  return {
    ...bug,
    displayId: `BUG-${bug.id}`,
    displayStatus: formatStatus(bug.status),
    displayPriority: formatPriority(bug.priority),
    date: new Date(bug.created_at).toLocaleDateString(),
    assignee: bug.assignee_id ? `User #${bug.assignee_id}` : 'Unassigned',
  }
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('bug_tracker_token'))
  const [user, setUser] = useState(null)
  const [bugs, setBugs] = useState([])
  const [loading, setLoading] = useState(false)
  const [authChecking, setAuthChecking] = useState(Boolean(localStorage.getItem('bug_tracker_token')))
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [activePage, setActivePage] = useState('Dashboard')
  const [showForm, setShowForm] = useState(false)
  const [editingBug, setEditingBug] = useState(null)
  const [loginForm, setLoginForm] = useState({
    username_or_email: '',
    password: '',
  })
  const [form, setForm] = useState(EMPTY_FORM)

  const apiRequest = useCallback(async (path, options = {}, accessToken = token) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...options.headers,
      },
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      const detail = data.detail
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg).join(', ')
        : detail || data.message || `Request failed (${response.status})`

      if (response.status === 401) {
        logout()
      }

      throw new Error(message)
    }

    return data
  }, [token])

  function logout() {
    localStorage.removeItem('bug_tracker_token')
    setToken(null)
    setUser(null)
    setBugs([])
    setError('')
    setAuthChecking(false)
    setEditingBug(null)
    setShowForm(false)
  }

  async function loadBugs(accessToken = token) {
    const data = await apiRequest('/api/bugs/', {}, accessToken)
    setBugs(data.map(formatBug))
  }

  useEffect(() => {
    if (!token) {
      return
    }

    let cancelled = false

    async function restoreSession() {
      setAuthChecking(true)
      setError('')

      try {
        const currentUser = await apiRequest('/api/auth/me', {}, token)

        if (cancelled) return

        setUser(currentUser)

        const bugData = await apiRequest('/api/bugs/', {}, token)

        if (!cancelled) {
          setBugs(bugData.map(formatBug))
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
          setAuthChecking(false)
        }
      }
    }

    restoreSession()

    return () => {
      cancelled = true
    }
  }, [token, apiRequest])

  async function handleLogin(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await apiRequest('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      }, null)

      localStorage.setItem('bug_tracker_token', result.access_token)
      setToken(result.access_token)
      setLoginForm({
        username_or_email: '',
        password: '',
      })
    } catch (loginError) {
      setError(loginError.message)
    } finally {
      setLoading(false)
    }
  }

  function openCreateForm() {
    setError('')
    setEditingBug(null)
    setForm(EMPTY_FORM)
    setShowForm(true)
  }

  function startEditingBug(bug) {
    setError('')
    setEditingBug(bug)
    setForm({
      title: bug.title,
      description: bug.description || '',
      priority: bug.priority,
    })
    setShowForm(true)
  }

  function closeBugForm() {
    if (loading) return

    setShowForm(false)
    setEditingBug(null)
    setForm(EMPTY_FORM)
  }

  async function saveBug(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const requestBody = {
        title: form.title.trim(),
        description: form.description.trim(),
        priority: form.priority,
      }

      if (editingBug) {
        await apiRequest(`/api/bugs/${editingBug.id}`, {
          method: 'PUT',
          body: JSON.stringify(requestBody),
        })
      } else {
        await apiRequest('/api/bugs/', {
          method: 'POST',
          body: JSON.stringify(requestBody),
        })
      }

      await loadBugs()

      setForm(EMPTY_FORM)
      setEditingBug(null)
      setShowForm(false)
      setActivePage('Bugs')
      setStatusFilter('All')
      setSearch('')
    } catch (saveError) {
      setError(saveError.message)
    } finally {
      setLoading(false)
    }
  }

  async function deleteBug(bug) {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${bug.displayId} - ${bug.title}? This action cannot be undone.`
    )

    if (!confirmed) return

    setError('')
    setLoading(true)

    try {
      await apiRequest(`/api/bugs/${bug.id}`, {
        method: 'DELETE',
      })

      await loadBugs()
      setActivePage('Bugs')
    } catch (deleteError) {
      setError(deleteError.message)
    } finally {
      setLoading(false)
    }
  }
  const filteredBugs = useMemo(() => bugs.filter((bug) => {
    const matchesSearch = `${bug.displayId} ${bug.title} ${bug.assignee}`
      .toLowerCase()
      .includes(search.toLowerCase())

    const matchesStatus =
      statusFilter === 'All' || bug.displayStatus === statusFilter

    return matchesSearch && matchesStatus
  }), [bugs, search, statusFilter])

  const openCount = bugs.filter((bug) => bug.status === 'open').length
  const progressCount = bugs.filter((bug) => bug.status === 'in_progress').length
  const resolvedCount = bugs.filter((bug) => bug.status === 'resolved').length

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((part) => part[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'U'

  if (authChecking) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <div className="brand-mark">B</div>
          <h2>Checking your session...</h2>
          <p>Please wait while we connect to BugTrack.</p>
        </div>
      </div>
    )
  }

  if (!token || !user) {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <div className="auth-brand">
            <div className="brand-mark">B</div>
            <div>
              <strong>BugTrack</strong>
              <span>ISSUE MANAGEMENT</span>
            </div>
          </div>

          <p className="eyebrow">WELCOME BACK</p>
          <h1>Sign in to your workspace</h1>
          <p className="auth-description">
            Enter your account details to manage and track bugs.
          </p>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleLogin}>
            <label>
              Username or email
              <input
                required
                autoComplete="username"
                value={loginForm.username_or_email}
                onChange={(event) =>
                  setLoginForm({
                    ...loginForm,
                    username_or_email: event.target.value,
                  })
                }
                placeholder="Enter your username or email"
              />
            </label>

            <label>
              Password
              <input
                required
                type="password"
                autoComplete="current-password"
                value={loginForm.password}
                onChange={(event) =>
                  setLoginForm({
                    ...loginForm,
                    password: event.target.value,
                  })
                }
                placeholder="Enter your password"
              />
            </label>

            <button
              className="primary-button auth-submit"
              type="submit"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="auth-footer">
            Secure access to your BugTrack workspace
          </p>
        </div>
      </div>
    )
  }

  const navigation = [
    {
      section: 'WORKSPACE',
      items: [
        { name: 'Dashboard', icon: '⌂' },
        { name: 'Bugs', icon: '▣', count: bugs.length },
      ],
    },
  ]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">B</div>
          <div>
            <strong>BugTrack</strong>
            <span>ISSUE MANAGEMENT</span>
          </div>
        </div>

        <div className="workspace-switch">
          <div className="workspace-avatar">W</div>
          <div className="workspace-name">
            <strong>Workspace</strong>
            <span>Development Team</span>
          </div>
          <span className="switch-arrow">⌄</span>
        </div>

        <nav className="side-navigation">
          {navigation.map((group) => (
            <div className="nav-group" key={group.section}>
              <p className="nav-heading">{group.section}</p>

              {group.items.map((item) => (
                <button
                  key={item.name}
                  className={`nav-link ${activePage === item.name ? 'active' : ''}`}
                  onClick={() => setActivePage(item.name)}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.name}</span>
                  {item.count !== undefined && (
                    <span className="nav-count">{item.count}</span>
                  )}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="help-card">
            <strong>Need some help?</strong>
            <p>Report issues and track their progress with BugTrack.</p>
          </div>

          <div className="profile">
            <div className="profile-avatar">{initials}</div>
            <div className="profile-details">
              <strong>{user.full_name}</strong>
              <span>{user.role}</span>
            </div>
            <button
              className="profile-menu"
              onClick={logout}
              aria-label="Log out"
              title="Log out"
            >
              ↪
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-slash">/</span>
            <strong>{activePage}</strong>
          </div>

          <div className="topbar-actions">
            <div className="system-status">
              <span className="status-dot"></span>
              API connected
            </div>
            <div className="top-avatar">{initials}</div>
          </div>
        </header>

        <div className="page-content">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">
                {new Date().toLocaleDateString(undefined, {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                }).toUpperCase()}
              </p>

              <h1>
                {activePage === 'Dashboard'
                  ? `Good day, ${user.full_name.split(' ')[0]}!`
                  : activePage}
              </h1>

              <p className="page-subtitle">
                {activePage === 'Dashboard'
                  ? "Here's what's happening with your bugs today."
                  : 'Manage and track reported issues in one place.'}
              </p>
            </div>

            <button className="primary-button" onClick={openCreateForm}>
              <span>+</span> Create Bug
            </button>
          </section>

          {error && (
            <div className="error-message dashboard-error">
              {error}
              <button onClick={() => setError('')}>×</button>
            </div>
          )}

          <section className="stats-grid">
            <div className="stat-card">
              <div className="stat-top">
                <span>Total Bugs</span>
                <span className="stat-icon purple">▣</span>
              </div>
              <div className="stat-value">
                {bugs.length.toString().padStart(2, '0')}
              </div>
              <div className="stat-foot">
                <span className="trend positive">Live</span>
                <span> tracked issues</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-top">
                <span>Open Bugs</span>
                <span className="stat-icon orange">!</span>
              </div>
              <div className="stat-value">
                {openCount.toString().padStart(2, '0')}
              </div>
              <div className="stat-foot">
                <span className="status-dot open-dot"></span>
                <span> Need attention</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-top">
                <span>In Progress</span>
                <span className="stat-icon blue">↻</span>
              </div>
              <div className="stat-value">
                {progressCount.toString().padStart(2, '0')}
              </div>
              <div className="stat-foot">
                <span className="status-dot progress-dot"></span>
                <span> Currently being fixed</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-top">
                <span>Resolved Bugs</span>
                <span className="stat-icon green">✓</span>
              </div>
              <div className="stat-value">
                {resolvedCount.toString().padStart(2, '0')}
              </div>
              <div className="stat-foot">
                <span className="status-dot resolved-dot"></span>
                <span> Successfully resolved</span>
              </div>
            </div>
          </section>

          <section className="content-grid">
            <div className="panel bugs-panel">
              <div className="panel-header">
                <div>
                  <h2>
                    {activePage === 'Dashboard' ? 'Recent Bugs' : 'All Bugs'}
                  </h2>
                  <p>Live issues retrieved from the backend</p>
                </div>

                <button
                  className="text-button"
                  onClick={() => {
                    setActivePage('Bugs')
                    setStatusFilter('All')
                  }}
                >
                  View all →
                </button>
              </div>

              <div className="table-toolbar">
                <div className="search-box">
                  <span>⌕</span>
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search bugs..."
                  />
                </div>

                <select
                  className="filter-select"
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                >
                  <option value="All">All statuses</option>
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Closed">Closed</option>
                </select>

                <button
                  className="text-button"
                  onClick={() =>
                    loadBugs().catch((loadError) => setError(loadError.message))
                  }
                >
                  Refresh
                </button>
              </div>

              <div className="table-wrap">
                <table className="bugs-table">
                  <thead>
                    <tr>
                      <th>BUG / ISSUE</th>
                      <th>PRIORITY</th>
                      <th>STATUS</th>
                      <th>ASSIGNEE</th>
                      <th>CREATED</th>
                      <th>ACTION</th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredBugs
                      .slice(0, activePage === 'Dashboard' ? 5 : undefined)
                      .map((bug) => (
                        <tr key={bug.id}>
                          <td>
                            <div className="bug-title">{bug.title}</div>
                            <div className="bug-meta">
                              {bug.displayId} <span>·</span> Reporter #{bug.reporter_id}
                            </div>
                          </td>

                          <td>
                            <span className={`priority-badge ${bug.displayPriority.toLowerCase()}`}>
                              <i></i>
                              {bug.displayPriority}
                            </span>
                          </td>

                          <td>
                            <span className={`status-badge ${bug.displayStatus.toLowerCase().replace(' ', '-')}`}>
                              {bug.displayStatus}
                            </span>
                          </td>

                          <td>
                            <span className="assignee">
                              <span className="assignee-avatar">
                                {bug.assignee === 'Unassigned'
                                  ? '?'
                                  : bug.assignee.replace('User #', 'U')}
                              </span>
                              {bug.assignee}
                            </span>
                          </td>

                          <td className="date-cell">{bug.date}</td>

                          <td>
                            <button
                              type="button"
                              className="text-button"
                              onClick={() => startEditingBug(bug)}
                              disabled={loading}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="text-button"
                              onClick={() => deleteBug(bug)}
                              disabled={loading}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}

                    {loading && (
                      <tr>
                        <td colSpan="6" className="empty-state">
                          Loading bugs...
                        </td>
                      </tr>
                    )}

                    {!loading && filteredBugs.length === 0 && (
                      <tr>
                        <td colSpan="6" className="empty-state">
                          No bugs found. Try changing your search or filter.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="table-footer">
                <span>
                  Showing {filteredBugs.length === 0 ? 0 : 1}–
                  {Math.min(
                    filteredBugs.length,
                    activePage === 'Dashboard' ? 5 : filteredBugs.length,
                  )}{' '}
                  of {filteredBugs.length} bugs
                </span>

                <button
                  onClick={() => {
                    setActivePage('Bugs')
                    setStatusFilter('All')
                  }}
                >
                  See all bugs →
                </button>
              </div>
            </div>

            <aside className="right-column">
              <div className="panel activity-panel">
                <div className="panel-header">
                  <div>
                    <h2>Recent Bugs</h2>
                    <p>Latest reported issues</p>
                  </div>
                </div>

                <div className="activity-list">
                  {bugs.slice(0, 3).map((bug) => (
                    <div className="activity-item" key={bug.id}>
                      <div className="activity-avatar purple-bg">B</div>
                      <div>
                        <p>
                          <strong>{bug.displayId}</strong> · {bug.displayStatus}
                        </p>
                        <span>{bug.title}</span>
                        <small>{bug.date}</small>
                      </div>
                    </div>
                  ))}

                  {bugs.length === 0 && (
                    <p className="empty-state">No reported bugs yet.</p>
                  )}
                </div>
              </div>

              <div className="tip-card">
                <div className="tip-symbol">✓</div>
                <div>
                  <strong>Stay on top of bugs</strong>
                  <p>
                    Create clear bug reports with a description and priority
                    to help your team investigate issues.
                  </p>
                </div>
              </div>
            </aside>
          </section>

          <footer className="page-footer">
            <span>© 2026 BugTrack. Built for better teamwork.</span>
            <span>Version 1.0.0</span>
          </footer>
        </div>
      </main>

      {showForm && (
        <div
          className="modal-backdrop"
          onClick={closeBugForm}
        >
          <div
            className="bug-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-heading">
              <div>
                <h2>{editingBug ? 'Edit bug' : 'Create a new bug'}</h2>
                <p>
                  {editingBug
                    ? 'Update the details of this reported issue.'
                    : 'Describe the issue you want your team to fix.'}
                </p>
              </div>

              <button
                onClick={closeBugForm}
                aria-label="Close"
                disabled={loading}
              >
                ×
              </button>
            </div>

            <form onSubmit={saveBug}>
              <label>
                Bug title
                <input
                  required
                  minLength="3"
                  maxLength="200"
                  placeholder="e.g. Login page is not responding"
                  value={form.title}
                  onChange={(event) =>
                    setForm({ ...form, title: event.target.value })
                  }
                />
              </label>

              <label>
                Priority
                <select
                  value={form.priority}
                  onChange={(event) =>
                    setForm({ ...form, priority: event.target.value })
                  }
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </label>

              <label>
                Description
                <textarea
                  required
                  minLength="5"
                  rows="4"
                  placeholder="Add details about the issue..."
                  value={form.description}
                  onChange={(event) =>
                    setForm({ ...form, description: event.target.value })
                  }
                />
              </label>

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={closeBugForm}
                  disabled={loading}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={loading}
                >
                  {loading
                    ? 'Saving...'
                    : editingBug
                      ? 'Save Changes'
                      : 'Create Bug'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default App

