# GitHub Setup & Deployment Guide

## Quick Start

### 1. Initialize Git Repository

```bash
# Navigate to project directory
cd "d:\AIDS\internship\core_backend(end to end)"

# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: R-01 to R-10 complete implementation"
```

### 2. Create GitHub Repository

Go to https://github.com/new and create a new repository with:
- **Name**: `core_backend`
- **Description**: Core Backend Assessment Management System – State Machine, Audit Trail, Security
- **Visibility**: Private (or Public based on your preference)

### 3. Push to GitHub

```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/core_backend.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

### 4. Set Up Branch Protection (Optional but Recommended)

In GitHub repository settings:
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - [ ] Require pull request reviews before merging
   - [ ] Require status checks to pass before merging
   - [ ] Require branches to be up to date before merging

---

## Production Deployment Guide

### Prerequisites

- Python 3.10+
- PostgreSQL 12+ (or MySQL)
- Redis (for caching)
- Nginx (for reverse proxy)
- Supervisor (for process management)

### Environment Setup

#### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/core_backend.git
cd core_backend
```

#### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, generate it:

```bash
pip freeze > requirements.txt
```

### Configuration

#### 1. Environment Variables (.env)

Create `.env` file in project root:

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here-use-strong-random-string
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=core_backend_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Security
JWT_SECRET_KEY=your-jwt-secret-key
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis (for caching/rate limiting)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
```

#### 2. Update Django Settings

Update `config/settings.py` to use environment variables:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Load from environment
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

# Redis caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Database Setup

#### 1. Run Migrations

```bash
python manage.py makemigrations --skip-checks
python manage.py migrate --skip-checks
```

#### 2. Load Seed Data

```bash
python seed_p0_ready.py
```

#### 3. Create Superuser

```bash
python manage.py createsuperuser
```

### Security Hardening

#### 1. Update HTTPS Settings

In `config/settings.py`:

```python
# Only in production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

#### 2. Configure Nginx

Create `/etc/nginx/sites-available/core_backend`:

```nginx
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    client_max_body_size 10M;

    location /static/ {
        alias /var/www/core_backend/staticfiles/;
    }

    location /media/ {
        alias /var/www/core_backend/media/;
    }

    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/core_backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 3. Configure Supervisor

Create `/etc/supervisor/conf.d/core_backend.conf`:

```ini
[program:core_backend]
directory=/var/www/core_backend
command=/var/www/core_backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    config.wsgi:application
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/core_backend.log
environment=PATH="/var/www/core_backend/venv/bin",DEBUG="False"
```

Update Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start core_backend
```

### Deployment Checklist

- [ ] Clone repository
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Configure `.env` file
- [ ] Run migrations
- [ ] Load seed data
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Test locally: `python manage.py runserver`
- [ ] Configure Nginx
- [ ] Configure Supervisor/Gunicorn
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Verify security headers
- [ ] Run test suite
- [ ] Monitor logs
- [ ] Set up backups

### Post-Deployment Verification

```bash
# Check application status
sudo supervisorctl status

# View logs
tail -f /var/log/core_backend.log

# Test API endpoint
curl -X GET https://your-domain.com/api/vendors/vendors/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify security headers
curl -I https://your-domain.com/

# Check rate limiting
for i in {1..60}; do curl https://your-domain.com/api/; done
```

### Monitoring

#### 1. Application Logs

Monitor in real-time:

```bash
tail -f /var/log/core_backend.log
```

#### 2. Security Logs

Monitor failed authentication attempts:

```bash
grep "Brute\|Rate limit\|Auth" /var/log/core_backend.log
```

#### 3. Audit Logs

Access audit trail:

```bash
curl -X GET https://your-domain.com/api/audit/events/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Backup Strategy

#### 1. Database Backups

Daily backup:

```bash
# Create backup directory
mkdir -p /var/backups/core_backend

# Backup PostgreSQL
pg_dump -U postgres core_backend_db | gzip > /var/backups/core_backend/db_$(date +%Y%m%d_%H%M%S).sql.gz
```

Cron job (`/etc/cron.d/core_backend_backup`):

```cron
# Daily database backup at 2 AM
0 2 * * * root pg_dump -U postgres core_backend_db | gzip > /var/backups/core_backend/db_$(date +\%Y\%m\%d).sql.gz
```

#### 2. Retention Policy

```bash
# Keep backups for 30 days
find /var/backups/core_backend/ -name "db_*.sql.gz" -mtime +30 -delete
```

### Disaster Recovery

Restore from backup:

```bash
# Decompress backup
gunzip /var/backups/core_backend/db_20260312.sql.gz

# Restore database
psql -U postgres < /var/backups/core_backend/db_20260312.sql
```

### Scaling for Production

#### 1. Database Optimization

```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_assessment_org_status ON assessments_assessment(org_id, status);
CREATE INDEX idx_audit_event_resource ON audit_auditevent(resource_type, resource_id);
CREATE INDEX idx_audit_event_user ON audit_auditevent(user_id, created_at);

-- Enable full-text search
ALTER TABLE assessments_assessment ADD COLUMN search_vector tsvector;
CREATE INDEX idx_assessment_search ON assessments_assessment USING gin(search_vector);
```

#### 2. Redis Configuration

For production Redis:

```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis persistence
sudo nano /etc/redis/redis.conf
# Set: appendonly yes
# Set: appendfsync everysec

# Set max memory policy
# maxmemory 256mb
# maxmemory-policy allkeys-lru

# Start Redis
sudo systemctl restart redis-server
```

#### 3. Load Balancing

For multiple application instances, use HAProxy:

```
global
    maxconn 256

defaults
    mode http
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend web
    bind *:80
    default_backend apps

backend apps
    mode http
    balance roundrobin
    server app1 127.0.0.1:8001
    server app2 127.0.0.1:8002
    server app3 127.0.0.1:8003
```

---

## Continuous Integration / Continuous Deployment (CI/CD)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          python manage.py test --skip-checks
      
      - name: Check security
        run: |
          pip install bandit
          bandit -r . -ll

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to production
        run: |
          # Add your deployment script here
          echo "Deploying to production"
```

---

## Summary

This guide covers:
- ✅ GitHub repository setup
- ✅ Production deployment
- ✅ Security hardening
- ✅ Database setup
- ✅ Backup strategy
- ✅ Monitoring
- ✅ Scaling considerations
- ✅ CI/CD pipeline

For questions or issues, refer to the project documentation or GitHub Issues.
