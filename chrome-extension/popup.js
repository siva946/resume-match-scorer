const API_URL =  'http://localhost:8000';

let resumes = [];
let jobs = [];

async function loadData() {
  try {
    const [resumesRes, jobsRes] = await Promise.all([
      fetch(`${API_URL}/api/resumes`),
      fetch(`${API_URL}/api/jobs`)
    ]);

    if (!resumesRes.ok || !jobsRes.ok) {
      showStatus('Backend error - check if server is running', 'error');
      return;
    }

    resumes = await resumesRes.json();
    jobs = await jobsRes.json();

    document.getElementById('resumeCount').textContent = resumes.length;
    document.getElementById('jobCount').textContent = jobs.length;

    const select = document.getElementById('resumeSelect');
    if (resumes.length === 0) {
      select.innerHTML = '<option value="">No resumes uploaded</option>';
    } else {
      select.innerHTML = resumes.map(r => 
        `<option value="${r.id}">${r.filename}</option>`
      ).join('');
    }
  } catch (error) {
    showStatus('Backend not running on localhost:8000', 'error');
    console.error('Connection error:', error);
  }
}

document.getElementById('showMatch').addEventListener('click', async () => {
  const resumeId = document.getElementById('resumeSelect').value;
  
  if (!resumeId) {
    showStatus('Please upload a resume first', 'error');
    return;
  }

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: extractJobDescription
    });

    const description = results[0].result;

    const response = await fetch(`${API_URL}/api/match-job`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resume_id: parseInt(resumeId),
        job_description: description
      })
    });

    const result = await response.json();
    const score = Math.round(result.score);
    
    showStatus(`Match Score: ${score}% - ${getScoreLabel(score)}`, 'success');
  } catch (error) {
    showStatus('Error: ' + error.message, 'error');
  }
});

document.getElementById('saveJob').addEventListener('click', async () => {
  const title = document.getElementById('title').value;
  const company = document.getElementById('company').value;

  if (!title || !company) {
    showStatus('Please fill in title and company', 'error');
    return;
  }

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: extractJobDescription
    });

    const description = results[0].result;

    const response = await fetch(`${API_URL}/api/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        company,
        description,
        url: tab.url
      })
    });

    if (response.ok) {
      showStatus('Job saved successfully!', 'success');
      document.getElementById('title').value = '';
      document.getElementById('company').value = '';
      await loadData();
    } else {
      showStatus('Failed to save job', 'error');
    }
  } catch (error) {
    showStatus('Error: ' + error.message, 'error');
  }
});

function extractJobDescription() {
  // Naukri.com specific extraction
  if (window.location.hostname.includes('naukri.com')) {
    const jobDesc = document.querySelector('.job-description, .jd-description, [class*="description"], .styles_JDC__dang-inner-html__h0K4t');
    if (jobDesc) return jobDesc.innerText.substring(0, 5000);
  }
  
  // Indeed.com specific extraction
  if (window.location.hostname.includes('indeed.com')) {
    const jobDesc = document.querySelector('#jobDescriptionText, .jobsearch-jobDescriptionText');
    if (jobDesc) return jobDesc.innerText.substring(0, 5000);
  }
  
  // LinkedIn specific extraction
  if (window.location.hostname.includes('linkedin.com')) {
    const jobDesc = document.querySelector('.jobs-description, .jobs-box__html-content');
    if (jobDesc) return jobDesc.innerText.substring(0, 5000);
  }
  
  // Fallback to body text
  const bodyText = document.body.innerText;
  return bodyText.substring(0, 5000);
}

function getScoreLabel(score) {
  if (score >= 80) return 'Excellent Match';
  if (score >= 60) return 'Good Match';
  if (score >= 40) return 'Fair Match';
  return 'Low Match';
}

function showStatus(message, type) {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = message;
  statusDiv.className = type;
  statusDiv.style.display = 'block';
  setTimeout(() => {
    statusDiv.style.display = 'none';
  }, 4000);
}

loadData();
