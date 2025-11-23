# Quick Reference Card

## 📦 Data Sizes

### Backend Requirements
- **Disk Space**: ~600 MB (ML model + dependencies)
- **RAM**: 512 MB minimum, 1 GB recommended
- **ML Model**: 80-90 MB (all-MiniLM-L6-v2)

### Data Transfer (Frontend ↔ Backend)
- **Resume Upload**: 100 KB - 5 MB → 2 KB response
- **Job Creation**: 5-50 KB → 1 KB response
- **Get Matches**: 1 KB → 10-100 KB (for 10 jobs)
- **Embeddings**: 1.5 KB per resume/job (384 dimensions)

---

## 🔄 Local vs Production

| Component | Local Dev | Production |
|-----------|-----------|------------|
| **Database** | SQLite (no install) | PostgreSQL (Render) |
| **Backend Import** | `database_sqlite` | `database_postgres` |
| **Frontend URL** | `localhost:3000` | Vercel URL |
| **Backend URL** | `localhost:8000` | Render URL |
| **Extension API** | `localhost:8000` | Production URL |

---

## ⚡ Quick Commands

### Local Development (SQLite)
```bash
# Backend
cd backend
pip install -r requirements.txt
# Edit main.py: use database_sqlite
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

### Deploy to Production
```bash
# 1. Switch to PostgreSQL in main.py
# 2. Push to GitHub
git add .
git commit -m "Deploy to production"
git push origin main

# 3. Deploy frontend
cd frontend
vercel --prod
```

---

## 🌐 URLs After Deployment

- **Frontend**: https://your-app.vercel.app
- **Backend**: https://your-app.onrender.com
- **API Docs**: https://your-app.onrender.com/docs
- **Health Check**: https://your-app.onrender.com/health

---

## 💰 Cost Breakdown

### Free Tier (Testing)
- Render Backend: Free (sleeps after 15 min)
- Render PostgreSQL: Free (90 days)
- Vercel Frontend: Free (unlimited)
- **Total**: $0/month

### Production (Recommended)
- Render Backend Starter: $7/month (1 GB RAM, always on)
- Render PostgreSQL Starter: $7/month (persistent)
- Vercel Frontend: Free
- **Total**: $14/month

---

## 🔧 Critical Files to Update Before Deploy

1. **backend/main.py** (line 8)
   ```python
   from database_postgres import init_db, ResumeDB, JobDB, MatchDB
   ```

2. **chrome-extension/popup.js**
   ```javascript
   const API_URL = 'https://your-backend.onrender.com';
   ```

3. **backend/main.py** (CORS origins)
   ```python
   allow_origins=["https://your-frontend.vercel.app", ...]
   ```

---

## ✅ Pre-Deploy Checklist

- [ ] Using `database_postgres` in main.py
- [ ] Updated extension API URL
- [ ] Added `*.db` to .gitignore
- [ ] Committed all changes
- [ ] Created Render PostgreSQL database
- [ ] Set DATABASE_URL on Render
- [ ] Set REACT_APP_API_URL on Vercel
- [ ] Updated CORS origins

---

## 🚨 Common Errors & Fixes

| Error | Fix |
|-------|-----|
| "init_db not defined" | Check import statement in main.py |
| "Connection refused" | PostgreSQL not running (use SQLite locally) |
| "CORS error" | Add frontend URL to CORS origins |
| "Model timeout" | Wait 5-10 min on first deploy |
| "Cold start delay" | Upgrade to paid plan or ping every 10 min |

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **SentenceTransformers**: https://www.sbert.net/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
