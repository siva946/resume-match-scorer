# Production Deployment Guide

## ✅ All Issues Fixed

### Security
- ✅ JWT authentication with bcrypt password hashing
- ✅ CORS restricted to whitelisted domains
- ✅ Rate limiting (10 req/min, 100 req/hour)
- ✅ Input validation and sanitization
- ✅ File upload validation (MIME type, size limit)
- ✅ SQL injection prevention (parameterized queries)
- ✅ User data isolation (multi-tenant)

### Performance
- ✅ Database connection pooling
- ✅ Async processing with timeouts
- ✅ Pagination (max 50 jobs per request)
- ✅ Parallel job matching with asyncio
- ✅ Request timeouts (30s default)

### Reliability
- ✅ Structured logging
- ✅ Proper error handling
- ✅ Health check endpoint
- ✅ Database transaction management
- ✅ Graceful shutdown

### Production Database
- ✅ PostgreSQL with connection pooling
- ✅ Proper indexes
- ✅ Foreign key constraints
- ✅ User isolation

---

## 🚀 Deployment Steps

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with production values
nano .env
```

**Required .env values:**
```env
DATABASE_URL=postgresql://user:password@db-host:5432/resumsync
SECRET_KEY=<generate-32-char-random-string>
ALLOWED_ORIGINS=https://yourdomain.com
ENVIRONMENT=production
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb resumsync

# Run migrations (automatic on first start)
python -c "from database_production import init_db; init_db()"
```

### 3. Run Backend

**Development:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production (with Gunicorn):**
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit with production API URL
echo "REACT_APP_API_URL=https://api.yourdomain.com" > .env

# Build for production
npm run build

# Serve with nginx or deploy to Vercel/Netlify
```

### 5. Chrome Extension Setup

```bash
cd chrome-extension

# Edit config.js
nano config.js
```
Change:
```javascript
const CONFIG = {
  API_URL: 'https://api.yourdomain.com',
  TIMEOUT: 30000
};
```

**Package extension:**
1. Go to `chrome://extensions/`
2. Enable Developer mode
3. Click "Pack extension"
4. Select `chrome-extension` folder
5. Distribute the `.crx` file

---

## 🐳 Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: resumsync
      POSTGRES_USER: resumsync
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://resumsync:${DB_PASSWORD}@postgres:5432/resumsync
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
      ENVIRONMENT: production
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    command: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

  frontend:
    build: ./frontend
    environment:
      REACT_APP_API_URL: ${API_URL}
    ports:
      - "3000:80"

volumes:
  postgres_data:
```

### backend/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### frontend/Dockerfile

```dockerfile
FROM node:18 AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

**Run with Docker:**
```bash
docker-compose up -d
```

---

## 🔒 SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/resumsync

# Backend API
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }
}

# Frontend
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    root /var/www/resumsync/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 📊 Monitoring

### Health Check

```bash
curl https://api.yourdomain.com/health
```

Expected response:
```json
{"status": "healthy", "database": "connected"}
```

### Logs

```bash
# View backend logs
tail -f /var/log/resumsync/backend.log

# Docker logs
docker-compose logs -f backend
```

### Database Backup

```bash
# Backup
pg_dump -U resumsync resumsync > backup_$(date +%Y%m%d).sql

# Restore
psql -U resumsync resumsync < backup_20240101.sql
```

---

## 🔧 Environment Variables Reference

### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | - | PostgreSQL connection string |
| SECRET_KEY | Yes | - | JWT secret (32+ chars) |
| ALLOWED_ORIGINS | Yes | - | Comma-separated CORS origins |
| RATE_LIMIT_PER_MINUTE | No | 10 | API rate limit per minute |
| RATE_LIMIT_PER_HOUR | No | 100 | API rate limit per hour |
| MAX_FILE_SIZE_MB | No | 10 | Max PDF upload size |
| API_TIMEOUT_SECONDS | No | 30 | Request timeout |
| MAX_JOBS_PER_REQUEST | No | 50 | Max jobs in match request |
| ENVIRONMENT | No | development | Environment name |
| LOG_LEVEL | No | INFO | Logging level |

### Frontend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| REACT_APP_API_URL | Yes | - | Backend API URL |

---

## 🧪 Testing Production

### 1. Register User
```bash
curl -X POST https://api.yourdomain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### 2. Login
```bash
curl -X POST https://api.yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### 3. Upload Resume
```bash
TOKEN="your-jwt-token"
curl -X POST https://api.yourdomain.com/api/resume/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf"
```

### 4. Add Job
```bash
curl -X POST https://api.yourdomain.com/api/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Software Engineer","company":"Tech Corp","description":"Python developer needed..."}'
```

### 5. Get Matches
```bash
curl https://api.yourdomain.com/api/matches/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🚨 Troubleshooting

### Issue: 401 Unauthorized
**Solution:** Check JWT token is valid and not expired

### Issue: 429 Rate Limit
**Solution:** Wait 1 minute or increase rate limits in .env

### Issue: 408 Timeout
**Solution:** Reduce number of jobs or increase API_TIMEOUT_SECONDS

### Issue: Database connection failed
**Solution:** Check DATABASE_URL and PostgreSQL is running

### Issue: CORS error
**Solution:** Add frontend domain to ALLOWED_ORIGINS

---

## 📈 Performance Tuning

### Database
```sql
-- Add indexes for better performance
CREATE INDEX idx_resumes_created ON resumes(created_at DESC);
CREATE INDEX idx_jobs_created ON jobs(created_at DESC);
CREATE INDEX idx_users_email ON users(email);
```

### Backend
- Increase worker count: `gunicorn -w 8`
- Increase connection pool: `DB_POOL_SIZE=50`
- Enable caching for repeated matches

### Frontend
- Enable gzip compression in nginx
- Use CDN for static assets
- Implement lazy loading

---

## ✅ Production Checklist

- [ ] Changed SECRET_KEY to random 32+ char string
- [ ] Set ALLOWED_ORIGINS to production domains only
- [ ] Configured PostgreSQL with strong password
- [ ] Enabled SSL/HTTPS with valid certificate
- [ ] Set up database backups
- [ ] Configured logging and monitoring
- [ ] Tested all API endpoints
- [ ] Updated Chrome extension config
- [ ] Set up rate limiting
- [ ] Configured firewall rules
- [ ] Set ENVIRONMENT=production
- [ ] Removed debug endpoints
- [ ] Tested authentication flow
- [ ] Verified file upload limits
- [ ] Set up error tracking (Sentry)

---

## 🎉 All Production Issues Resolved!

Your application is now production-ready with:
- ✅ Enterprise-grade security
- ✅ Scalable architecture
- ✅ Proper error handling
- ✅ User authentication
- ✅ Rate limiting
- ✅ Database optimization
- ✅ Comprehensive logging
- ✅ Health monitoring
