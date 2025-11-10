# Setup Instructions (Without Docker)

## Prerequisites

1. **Python 3.8+**: Download from https://www.python.org/downloads/
2. **Node.js 16+**: Download from https://nodejs.org/
3. **Chrome Browser**: For the extension

## Setup Steps

### 1. Setup Backend

Open Command Prompt and run:

```bash
cd e:\ResumSync
setup-backend.bat
```

This will:
- Create a Python virtual environment
- Install all backend dependencies
- Download the ML model (~80MB)

### 2. Setup Frontend

Open a NEW Command Prompt and run:

```bash
cd e:\ResumSync
setup-frontend.bat
```

This will install all React dependencies.

### 3. Run Backend

```bash
cd e:\ResumSync
run-backend.bat
```

Backend will start at http://localhost:8000

### 4. Run Frontend

Open a NEW Command Prompt and run:

```bash
cd e:\ResumSync
run-frontend.bat
```

Frontend will start at http://localhost:3000

### 5. Install Chrome Extension

1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select: `e:\ResumSync\chrome-extension`

## Usage

1. Go to http://localhost:3000
2. Upload a PDF resume
3. Use Chrome extension to add jobs from any job posting page
4. Click "Find Matches" on your resume to see matching jobs

## Notes

- Backend uses SQLite (no database installation needed)
- Keep both Command Prompts open while using the app
- First run downloads ML model automatically
