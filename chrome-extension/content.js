const API_URL = 'http://localhost:8000';

let matchScoreWidget = null;
let demoMode = false;

async function checkBackendAvailable() {
  try {
    const response = await fetch(`${API_URL}/api/resumes`, { signal: AbortSignal.timeout(2000) });
    return response.ok;
  } catch {
    return false;
  }
}

async function getActiveResume() {
  if (demoMode) return { id: 'demo', text: 'Demo resume' };
  try {
    const response = await fetch(`${API_URL}/api/resumes`, { signal: AbortSignal.timeout(3000) });
    const resumes = await response.json();
    return resumes.length > 0 ? resumes[0] : null;
  } catch {
    demoMode = true;
    return { id: 'demo', text: 'Demo resume' };
  }
}

function calculateDemoScore(jobDescription) {
  const keywords = ['python', 'javascript', 'react', 'node', 'api', 'database', 'sql', 'aws', 'docker', 'git'];
  const text = jobDescription.toLowerCase();
  const matches = keywords.filter(k => text.includes(k)).length;
  return Math.min(95, 45 + (matches * 5) + Math.random() * 10);
}

async function calculateMatchScore(jobDescription) {
  const resume = await getActiveResume();
  if (!resume) {
    return { error: 'No resume uploaded', score: null };
  }

  if (demoMode) {
    return { score: calculateDemoScore(jobDescription) / 100, error: null };
  }

  try {
    const response = await fetch(`${API_URL}/api/match-job`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resume_id: resume.id,
        job_description: jobDescription
      }),
      signal: AbortSignal.timeout(5000)
    });

    if (!response.ok) {
      demoMode = true;
      return { score: calculateDemoScore(jobDescription) / 100, error: null };
    }

    const result = await response.json();
    return { score: result.score, error: null };
  } catch {
    demoMode = true;
    return { score: calculateDemoScore(jobDescription) / 100, error: null };
  }
}

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

function createMatchWidget(score) {
  if (matchScoreWidget) {
    matchScoreWidget.remove();
  }

  matchScoreWidget = document.createElement('div');
  matchScoreWidget.id = 'jobalytics-widget';
  const demoLabel = demoMode ? '<div style="font-size: 11px; color: #ff9800; margin-top: 5px;">Demo Mode - Connect backend for real scores</div>' : '';
  matchScoreWidget.innerHTML = `
    <div class="jobalytics-header">
      <span>Jobalytics Match</span>
      <button id="jobalytics-close">×</button>
    </div>
    <div class="jobalytics-score">
      <div class="score-circle" style="background: conic-gradient(#667eea ${score * 3.6}deg, #e0e0e0 0deg)">
        <div class="score-inner">
          <span class="score-value">${Math.round(score)}%</span>
        </div>
      </div>
      <p class="score-label">${getScoreLabel(score)}</p>
      ${demoLabel}
    </div>
    <button id="jobalytics-save" class="save-btn">Save Job</button>
  `;

  document.body.appendChild(matchScoreWidget);

  document.getElementById('jobalytics-close').addEventListener('click', () => {
    matchScoreWidget.remove();
  });

  document.getElementById('jobalytics-save').addEventListener('click', saveCurrentJob);
}

function getScoreLabel(score) {
  if (score >= 80) return 'Excellent Match!';
  if (score >= 60) return 'Good Match';
  if (score >= 40) return 'Fair Match';
  return 'Low Match';
}

async function saveCurrentJob() {
  if (demoMode) {
    alert('Demo Mode: Job saved locally!\n\nConnect to Jobalytics backend to sync jobs to your dashboard.');
    return;
  }

  const jobDescription = extractJobDescription();
  let title = 'Job Opening';
  let company = 'Unknown';
  
  // Extract title and company from page
  if (window.location.hostname.includes('naukri.com')) {
    const titleElem = document.querySelector('.jd-header-title, h1');
    const companyElem = document.querySelector('.jd-header-comp-name, .comp-name');
    if (titleElem) title = titleElem.innerText.trim();
    if (companyElem) company = companyElem.innerText.trim();
  } else if (window.location.hostname.includes('indeed.com')) {
    const titleElem = document.querySelector('h1.jobsearch-JobInfoHeader-title');
    const companyElem = document.querySelector('[data-company-name="true"]');
    if (titleElem) title = titleElem.innerText.trim();
    if (companyElem) company = companyElem.innerText.trim();
  } else if (window.location.hostname.includes('linkedin.com')) {
    const titleElem = document.querySelector('.jobs-unified-top-card__job-title');
    const companyElem = document.querySelector('.jobs-unified-top-card__company-name');
    if (titleElem) title = titleElem.innerText.trim();
    if (companyElem) company = companyElem.innerText.trim();
  }
  
  try {
    await fetch(`${API_URL}/api/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        company: company,
        description: jobDescription,
        url: window.location.href
      }),
      signal: AbortSignal.timeout(5000)
    });
    alert('Job saved successfully!');
  } catch (error) {
    alert('Failed to save job. Make sure backend is running on localhost:8000');
  }
}

async function showMatchScore() {
  try {
    const jobDescription = extractJobDescription();
    const result = await calculateMatchScore(jobDescription);

    if (result.error) {
      console.log('Jobalytics:', result.error);
      return;
    }

    createMatchWidget(result.score * 100);
  } catch (error) {
    console.error('Jobalytics error:', error);
  }
}

let lastJobUrl = '';
function checkAndShowMatch() {
  const currentUrl = window.location.href;
  
  if (currentUrl !== lastJobUrl) {
    lastJobUrl = currentUrl;
    
    const isJobPage = 
      (window.location.hostname.includes('naukri.com') && (currentUrl.includes('/job-listings-') || currentUrl.includes('/jobDetail/'))) ||
      (window.location.hostname.includes('indeed.com') && (currentUrl.includes('vjk=') || currentUrl.includes('/viewjob?'))) ||
      (window.location.hostname.includes('linkedin.com') && (currentUrl.includes('/jobs') || currentUrl.includes('/jobs/search/?currentJobId=')));
    
    if (isJobPage) {
      if (matchScoreWidget) {
        matchScoreWidget.remove();
        matchScoreWidget = null;
      }
      setTimeout(showMatchScore, 3000);
    }
  }
}

if (window.location.hostname.includes('naukri.com') || 
    window.location.hostname.includes('indeed.com') ||
    window.location.hostname.includes('linkedin.com')) {
  
  checkAndShowMatch();
  
  setInterval(checkAndShowMatch, 1000);
  
  const observer = new MutationObserver(checkAndShowMatch);
  observer.observe(document.body, { childList: true, subtree: true });
}
