import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

function App() {
  const [resumes, setResumes] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [matches, setMatches] = useState([]);
  const [selectedResume, setSelectedResume] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLogin, setShowLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
      loadResumes();
      loadJobs();
    }
  }, [isAuthenticated]);

  const handleAuth = async (isLogin) => {
    if (!email || !password) {
      alert('Please enter email and password');
      return;
    }
    
    setAuthLoading(true);
    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const res = await api.post(endpoint, { email, password });
      localStorage.setItem('token', res.data.access_token);
      setIsAuthenticated(true);
      setEmail('');
      setPassword('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Authentication failed');
    }
    setAuthLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setResumes([]);
    setJobs([]);
    setMatches([]);
  };

  const loadResumes = async () => {
    try {
      const res = await api.get('/api/resumes');
      setResumes(res.data);
    } catch (err) {
      console.error('Failed to load resumes:', err);
    }
  };

  const loadJobs = async () => {
    try {
      const res = await api.get('/api/jobs');
      setJobs(res.data);
    } catch (err) {
      console.error('Failed to load jobs:', err);
    }
  };

  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      alert('File too large. Maximum size: 10MB');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/api/resume/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await loadResumes();
      setMatches([]);
      alert('Resume uploaded successfully!');
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    }
    setUploading(false);
    e.target.value = '';
  };

  const handleGetMatches = async (resumeId) => {
    setSelectedResume(resumeId);
    try {
      const res = await api.get(`/api/matches/${resumeId}`);
      setMatches(res.data);
    } catch (err) {
      alert('Failed to get matches: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Delete this job permanently?')) return;
    
    try {
      await api.delete(`/api/jobs/${jobId}`);
      await loadJobs();
      if (matches.length > 0) {
        setMatches(matches.filter(m => m.job_id !== jobId));
      }
    } catch (err) {
      alert('Failed to delete job');
    }
  };

  const handleDeleteResume = async (resumeId) => {
    if (!window.confirm('Delete this resume permanently?')) return;
    
    try {
      await api.delete(`/api/resumes/${resumeId}`);
      await loadResumes();
      setMatches([]);
      setSelectedResume(null);
    } catch (err) {
      alert('Failed to delete resume');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="App">
        <header>
          <h1>ResumSync</h1>
          <p>Resume & Job Matching Platform</p>
        </header>
        <div className="container">
          <section className="auth-section">
            <h2>{showLogin ? 'Login' : 'Register'}</h2>
            <div className="auth-form">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
              />
              <input
                type="password"
                placeholder="Password (min 8 characters)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
              />
              <button
                onClick={() => handleAuth(showLogin)}
                disabled={authLoading}
                className="auth-button"
              >
                {authLoading ? 'Loading...' : (showLogin ? 'Login' : 'Register')}
              </button>
              <button
                onClick={() => setShowLogin(!showLogin)}
                className="toggle-auth"
              >
                {showLogin ? 'Need an account? Register' : 'Have an account? Login'}
              </button>
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header>
        <div>
          <h1>ResumSync</h1>
          <p>Resume & Job Matching Platform</p>
        </div>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      <div className="container">
        <div className="dashboard-grid">
          <div className="stat-card">
            <div className="stat-number">{resumes.length}</div>
            <div className="stat-label">Resumes</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{jobs.length}</div>
            <div className="stat-label">Jobs</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{matches.length}</div>
            <div className="stat-label">Matches</div>
          </div>
        </div>

        <section className="upload-section">
          <h2>Upload Resume</h2>
          <label className="upload-area" htmlFor="resume-upload">
            <input 
              id="resume-upload"
              type="file" 
              accept=".pdf" 
              onChange={handleResumeUpload}
              disabled={uploading}
            />
            <div className="upload-text">
              {uploading ? 'Uploading...' : 'Click to upload PDF resume'}
            </div>
            <div className="upload-hint">PDF files only</div>
          </label>
        </section>

        <section className="resumes-section">
          <h2>Your Resumes</h2>
          {resumes.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-text">No resumes uploaded yet</div>
            </div>
          ) : (
            <div className="list">
              {resumes.map(resume => (
                <div key={resume.id} className="item">
                  <div className="item-content">
                    <div className="item-title">{resume.filename}</div>
                    <div className="item-subtitle">ID: {resume.id}</div>
                  </div>
                  <div>
                    <button onClick={() => handleGetMatches(resume.id)}>
                      Find Matches
                    </button>
                    <button onClick={() => handleDeleteResume(resume.id)} className="delete-btn">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="jobs-section">
          <h2>Jobs Database</h2>
          {jobs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-text">No jobs saved yet. Use the Chrome extension to add jobs.</div>
            </div>
          ) : (
            <div className="list">
              {jobs.map(job => (
                <div key={job.id} className="item">
                  <div className="item-content">
                    <div className="item-title">{job.title}</div>
                    <div className="item-subtitle">{job.company}</div>
                  </div>
                  <button onClick={() => handleDeleteJob(job.id)} className="delete-btn">
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {matches.length > 0 && (
          <section className="matches-section">
            <h2>Top Matches</h2>
            <div className="matches">
              {matches.map(match => (
                <div key={match.job_id} className="match-card">
                  <div className="match-header">
                    <h3>{match.title}</h3>
                    <span className="score">{(match.score*100).toFixed(1)}%</span>
                  </div>
                  <p className="company">{match.company}</p>
                  <p className="description">{match.description.substring(0, 150)}...</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
