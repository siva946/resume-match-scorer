const API_URL = typeof CONFIG !== 'undefined' ? CONFIG.API_URL : 'http://localhost:8000';

function getAuthToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['token'], (result) => {
      resolve(result.token || '');
    });
  });
}

let matchScoreWidget = null;

async function checkBackendAvailable() {
  try {
    const response = await fetch(`${API_URL}/api/resumes`, { signal: AbortSignal.timeout(2000) });
    return response.ok;
  } catch {
    return false;
  }
}

async function getActiveResume() {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_URL}/api/resumes`, {
      signal: AbortSignal.timeout(3000),
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });
    if (!response.ok) throw new Error('Backend unavailable');
    const resumes = await response.json();
    return resumes.length > 0 ? resumes[0] : null;
  } catch {
    return null;
  }
}

function calculateDemoScore(jobDescription) {
  const keywords = ['python', 'javascript', 'react', 'node', 'api', 'database', 'sql', 'aws', 'docker', 'git'];
  const text = jobDescription.toLowerCase();
  const matches = keywords.filter(k => text.includes(k)).length;
  return Math.min(95, 45 + (matches * 5) + Math.random() * 10);
}

async function calculateMatchScore(jobDescription) {
  try {
    const resume = await getActiveResume();
    if (!resume) {
      return { score: calculateDemoScore(jobDescription) / 100, demo: true };
    }

    const token = await getAuthToken();
    const response = await fetch(`${API_URL}/api/match-job`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify({
        resume_id: resume.id,
        job_description: jobDescription
      }),
      signal: AbortSignal.timeout(5000)
    });

    if (!response.ok) throw new Error('API error');

    const result = await response.json();
    return { score: result.score, demo: false };
  } catch {
    return { score: calculateDemoScore(jobDescription) / 100, demo: true };
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

function createMatchWidget(score, isDemo) {
  if (matchScoreWidget) {
    matchScoreWidget.remove();
  }

  matchScoreWidget = document.createElement('div');
  matchScoreWidget.id = 'jobalytics-widget';
  const demoLabel = isDemo ? '<div style="font-size: 11px; color: #856404; margin-top: 8px; font-weight: 500;">Demo Mode - Connect backend for real scores</div>' : '';
  // amazonq-ignore-next-line
  matchScoreWidget.innerHTML = `
    <div class="jobalytics-header" id="jobalytics-drag-handle">
      <span>Jobalytics Match</span>
      <button id="jobalytics-close">×</button>
    </div>
    <div class="jobalytics-score" id="jobalytics-score-handle">
      <div class="score-circle" style="background: conic-gradient(#2c3e50 ${score * 3.6}deg, #e9ecef 0deg)">
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
  
  makeDraggable(matchScoreWidget);
}

function makeDraggable(element) {
  let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
  const header = element.querySelector('#jobalytics-drag-handle');
  const scorer=element.querySelector('#jobalytics-score-handle')
  header.onmousedown = dragMouseDown;
  scorer.onmousedown=dragMouseDown;
  function dragMouseDown(e) {
    e.preventDefault();
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    document.onmousemove = elementDrag;
  }

  function elementDrag(e) {
    e.preventDefault();
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    element.style.top = (element.offsetTop - pos2) + 'px';
    element.style.left = (element.offsetLeft - pos1) + 'px';
    element.style.right = 'auto';
  }

  function closeDragElement() {
    document.onmouseup = null;
    document.onmousemove = null;
  }
}

function getScoreLabel(score) {
  if (score >= 80) return 'Excellent Match';
  if (score >= 60) return 'Good Match';
  if (score >= 40) return 'Fair Match';
  return 'Low Match';
}

async function saveCurrentJob() {
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
    console.log('Saving job:', { title, company, descLength: jobDescription.length });
    const token = await getAuthToken();
    const response = await fetch(`${API_URL}/api/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify({
        title: title,
        company: company,
        description: jobDescription,
        url: window.location.href
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Save failed:', response.status, errorText);
      throw new Error(`Save failed: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Job saved:', result);
    // amazonq-ignore-next-line
    alert('Job saved successfully!');
  } catch (error) {
    console.error('Error saving job:', error);
    // amazonq-ignore-next-line
    alert(`Failed to save job: ${error.message}`);
  }
}

async function showMatchScore() {
  try {
    const jobDescription = extractJobDescription();
    const result = await calculateMatchScore(jobDescription);

    createMatchWidget(result.score * 100, result.demo);
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
