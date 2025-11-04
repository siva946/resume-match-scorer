import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [resumes, setResumes] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [matches, setMatches] = useState([]);
  const [selectedResume, setSelectedResume] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadResumes();
    loadJobs();
  }, []);

  const loadResumes = async () => {
    const res = await axios.get(`${API_URL}/api/resumes`);
    setResumes(res.data);
  };

  const loadJobs = async () => {
    const res = await axios.get(`${API_URL}/api/jobs`);
    setJobs(res.data);
  };

  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_URL}/api/resume/upload`, formData);
      await loadResumes();
      setMatches([]);
      alert('Resume uploaded successfully! Old resume replaced.');
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    }
    setUploading(false);
    e.target.value = '';
  };

  const handleGetMatches = async (resumeId) => {
    setSelectedResume(resumeId);
    const res = await axios.get(`${API_URL}/api/matches/${resumeId}`);
    setMatches(res.data);
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Delete this job permanently?')) return;
    
    try {
      await axios.delete(`${API_URL}/api/jobs/${jobId}`);
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
      await axios.delete(`${API_URL}/api/resumes/${resumeId}`);
      await loadResumes();
      setMatches([]);
      setSelectedResume(null);
    } catch (err) {
      alert('Failed to delete resume');
    }
  };

  return (
    <div className="App">
      <header>
        <h1>Jobalytics</h1>
        <p>Resume & Job Matching Platform</p>
      </header>

      <div className="container">
        <section className="upload-section">
          <h2>Upload Resume</h2>
          <input 
            type="file" 
            accept=".pdf" 
            onChange={handleResumeUpload}
            disabled={uploading}
          />
          {uploading && <p>Uploading...</p>}
        </section>

        <section className="resumes-section">
          <h2>Your Resume ({resumes.length})</h2>
          <div className="list">
            {resumes.map(resume => (
              <div key={resume.id} className="item">
                <span>{resume.filename}</span>
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
        </section>

        <section className="jobs-section">
          <h2>Jobs in Database ({jobs.length})</h2>
          <div className="list">
            {jobs.map(job => (
              <div key={job.id} className="item">
                <div>
                  <strong>{job.title}</strong> at {job.company}
                </div>
                <button onClick={() => handleDeleteJob(job.id)} className="delete-btn">
                  Delete
                </button>
              </div>
            ))}
          </div>
        </section>

        {matches.length > 0 && (
          <section className="matches-section">
            <h2>Top Matches</h2>
            <div className="matches">
              {matches.map(match => (
                <div key={match.job_id} className="match-card">
                  <div className="match-header">
                    <h3>{match.title}</h3>
                    <span className="score">{(match.score * 100).toFixed(1)}%</span>
                  </div>
                  <p className="company">{match.company}</p>
                  <p className="description">{match.description}...</p>
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
