# Jobalytics MVP

Resume and job matching platform using semantic analysis with SentenceTransformers.

## Features

- **Resume Upload**: Upload PDF resumes for analysis
- **Job Ingestion**: Add jobs via API or Chrome extension
- **Semantic Matching**: AI-powered matching using sentence embeddings
- **Chrome Extension**: Extract job descriptions from any webpage

## Tech Stack

- **Backend**: FastAPI + SentenceTransformers (all-MiniLM-L6-v2)
- **Frontend**: React
- **Database**: PostgreSQL
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Chrome browser (for extension)

### Run the Application

```bash
docker-compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. Navigate to any job posting page
6. Click the extension icon, fill in title/company, and click "Extract & Send Job"

## API Endpoints

### POST /api/resume/upload
Upload a PDF resume
- Body: multipart/form-data with `file` field
- Returns: `{id, filename, text_length}`

### POST /api/jobs
Add a job description
- Body: `{title, company, description, url?}`
- Returns: `{id, title}`

### GET /api/matches/{resume_id}
Get top job matches for a resume
- Query: `limit` (default: 10)
- Returns: Array of matches with scores

### GET /api/resumes
List all uploaded resumes

### GET /api/jobs
List all jobs in database

## How It Works

1. **Upload Resume**: PDF is parsed and converted to text
2. **Generate Embeddings**: Text is encoded using SentenceTransformers
3. **Store in DB**: Resume/job text and embeddings saved to PostgreSQL
4. **Match**: Cosine similarity computed between resume and job embeddings
5. **Rank**: Jobs sorted by similarity score

## Development

### Backend Only
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Only
```bash
cd frontend
npm install
npm start
```

## Notes

- First run downloads the ML model (~80MB)
- Extension requires backend running on localhost:8000
- PDF parsing extracts text only (no formatting)
- Embeddings are 384-dimensional vectors
