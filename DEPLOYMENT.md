# Deployment Guide

## Local Deployment

### Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432

## Production Deployment

### Backend on Render

1. **Create PostgreSQL Database**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "PostgreSQL"
   - Name: `jobalytics-db`
   - Copy the Internal Database URL

2. **Deploy Backend**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - Name: `jobalytics-backend`
     - Root Directory: `backend`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add Environment Variable:
     - `DATABASE_URL`: Paste the Internal Database URL from step 1
   - Click "Create Web Service"

3. **Note Backend URL**
   - Copy your backend URL: `https://jobalytics-backend.onrender.com`

### Frontend on Vercel/Netlify

#### Vercel
```bash
cd frontend
npm install -g vercel
vercel
```

Set environment variable:
- `REACT_APP_API_URL`: Your Render backend URL

#### Netlify
```bash
cd frontend
npm run build
npx netlify-cli deploy --prod --dir=build
```

Set environment variable in Netlify dashboard:
- `REACT_APP_API_URL`: Your Render backend URL

### Frontend on Render

1. Click "New +" → "Static Site"
2. Connect repository
3. Configure:
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `build`
4. Add Environment Variable:
   - `REACT_APP_API_URL`: Your backend URL
5. Click "Create Static Site"

## Chrome Extension Setup

1. Update `chrome-extension/content.js` with production backend URL:
   ```javascript
   const API_URL = 'https://jobalytics-backend.onrender.com';
   ```

2. Load extension in Chrome:
   - Go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `chrome-extension` folder

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Server port (auto-set by Render)

### Frontend
- `REACT_APP_API_URL`: Backend API URL

## Post-Deployment

1. Test resume upload: `POST /api/resume/upload`
2. Test job creation: `POST /api/jobs`
3. Test matching: `GET /api/matches/{resume_id}`
4. Verify Chrome extension connects to production backend

## Troubleshooting

- **Model download timeout**: First deployment may take 5-10 minutes for ML model download
- **CORS errors**: Ensure backend allows frontend origin in CORS settings
- **Database connection**: Verify DATABASE_URL format matches PostgreSQL provider
- **Extension not working**: Check backend URL in extension code and CORS configuration
