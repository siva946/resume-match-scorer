const API_URL = 'http://localhost:8000';

let matchScoreWidget = null;

async function getActiveResume() {
  const response = await fetch(`${API_URL}/api/resumes`);
  const resumes = await response.json();
  return resumes.length > 0 ? resumes[0] : null;
}

async function calculateMatchScore(jobDescription) {
  const resume = await getActiveResume();
  if (!resume) {
    return { error: 'No resume uploaded', score: null };
  }

  const response = await fetch(`${API_URL}/api/match-job`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume_id: resume.id,
      job_description: jobDescription
    })
  });

  if (!response.ok) {
    return { error: 'Match calculation failed', score: null };
  }

  const result = await response.json();
  return { score: result.score, error: null };
}

function extractJobDescription() {
  const bodyText = document.body.innerText;
  return bodyText.substring(0, 5000);
}

function createMatchWidget(score) {
  if (matchScoreWidget) {
    matchScoreWidget.remove();
  }

  matchScoreWidget = document.createElement('div');
  matchScoreWidget.id = 'jobalytics-widget';
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
  const jobDescription = extractJobDescription();
  const title = document.title.split('|')[0].trim();
  
  try {
    await fetch(`${API_URL}/api/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        company: 'Unknown',
        description: jobDescription,
        url: window.location.href
      })
    });
    alert('Job saved successfully!');
  } catch (error) {
    alert('Failed to save job');
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
      (window.location.hostname.includes('naukri.com') && currentUrl.includes('/job-listings/')) ||
      (window.location.hostname.includes('indeed.com') && (currentUrl.includes('/?vjk=') || currentUrl.includes('/jobs?'))) ||
      (window.location.hostname.includes('linkedin.com') && currentUrl.includes('/jobs/search/?currentJobId='));
    
    if (isJobPage) {
      if (matchScoreWidget) {
        matchScoreWidget.remove();
        matchScoreWidget = null;
      }
      setTimeout(showMatchScore, 2000);
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
