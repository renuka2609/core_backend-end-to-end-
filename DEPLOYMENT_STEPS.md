# Complete GitHub Deployment & System Setup Guide

## Step-by-Step Instructions (Complete R-01 to R-10 Deployment)

### Phase 1: Local Git Setup

#### Step 1.1: Verify Git Initialization
```bash
cd "d:\AIDS\internship\core_backend(end to end)"
git status
# Should show "On branch main" - Git already initialized ✓
```

#### Step 1.2: Verify All Files Committed
```bash
git log --oneline -5
# Should show your recent commits ✓
```

---

### Phase 2: GitHub Repository Setup

#### Step 2.1: Create GitHub Account (if needed)
- Go to https://github.com/signup
- Sign up with your email
- Verify your email
- ✓ Account ready

#### Step 2.2: Create New Repository
1. Go to https://github.com/new
2. Fill in:
   - **Repository name**: `core_backend`
   - **Description**: `Core Backend Assessment Management System – State Machine, Audit Trail, Security`
   - **Visibility**: `Private` (or Public)
   - **Initialize**: Leave unchecked (repo not empty)
3. Click "Create repository"
4. ✓ GitHub repo created

#### Step 2.3: Add Remote & Push to GitHub

```bash
# Add remote to your local repository
git remote add origin https://github.com/YOUR_USERNAME/core_backend.git

# Verify remote added
git remote -v
# Should show:
# origin  https://github.com/YOUR_USERNAME/core_backend.git (fetch)
# origin  https://github.com/YOUR_USERNAME/core_backend.git (push)

# Push to GitHub
git push -u origin main

# If prompted for authentication:
# Use your GitHub personal access token (if 2FA enabled)
# Or GitHub will open a browser for authentication
```

**Success indicators**:
- No errors during push
- ✓ Repository visible on GitHub
- ✓ All files uploaded

#### Step 2.4: Verify GitHub Repository

```bash
# Visit your repository
# https://github.com/YOUR_USERNAME/core_backend

# Verify contents:
# ✓ All 59 files present
# ✓ Recent commit visible
# ✓ Branch shows "main"
# ✓ Two commits visible in history
```

---

### Phase 3: Production Deployment Setup

#### Step 3.1: Set Up Production Environment

**Option A: Local Production Simulation**

```bash
# Create production directory
mkdir d:\deployment\core_backend
cd d:\deployment\core_backend

# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/core_backend.git .

# Create virtual environment
python -m venv venv

# Activate environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Option B: Linux/Ubuntu Production Server**

```bash
# SSH into production server
ssh user@your-server-ip

# Install Python 3.10+
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv python3-pip

# Create app directory
mkdir -p /var/www/core_backend
cd /var/www/core_backend

# Clone repository
git clone https://github.com/YOUR_USERNAME/core_backend.git .

# Create virtual environment
python3.10 -m venv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### Step 3.2: Configure Production Settings

Create `.env` file:

```bash
# Windows
copy .env.example .env
# OR create manually
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=core_backend_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
REDIS_URL=redis://localhost:6379/0
EOF
```

#### Step 3.3: Run Migrations & Setup Database

```bash
# Local/develpment
python manage.py makemigrations --skip-checks
python manage.py migrate

# Production with PostgreSQL
python manage.py migrate --database default

# Create superuser
python manage.py createsuperuser
# Enter: admin
# Email: admin@your-domain.com
# Password: strong-password-here
```

#### Step 3.4: Load Seed Data

```bash
python seed_p0_ready.py

# Verify:
# ✓ Organizations created
# ✓ Users created (admin, reviewer, vendor)
# ✓ Vendors created
# ✓ Templates created
# ✓ Assessments created
```

---

### Phase 4: Local Testing

#### Step 4.1: Run Development Server

```bash
cd "d:\AIDS\internship\core_backend(end to end)"

# Activate environment
.\.venv\Scripts\Activate.ps1

# Start server
python manage.py runserver

# Server running at: http://localhost:8000
```

#### Step 4.2: Test API Endpoints

```bash
# In a new terminal/PowerShell window

# 1. Get authentication token
$response = Invoke-RestMethod -Uri 'http://localhost:8000/api/login/' `
  -Method POST `
  -Headers @{'Content-Type'='application/json'} `
  -Body '{"username":"test_admin","password":"TestPass123!"}'

$token = $response.access

# 2. Test vendors endpoint
Invoke-RestMethod -Uri 'http://localhost:8000/api/vendors/vendors/' `
  -Method GET `
  -Headers @{ 'Authorization' = "Bearer $token" }

# 3. Test assessments endpoint
Invoke-RestMethod -Uri 'http://localhost:8000/api/assessments/assessments/' `
  -Method GET `
  -Headers @{ 'Authorization' = "Bearer $token" }

# 4. Test audit endpoint
Invoke-RestMethod -Uri 'http://localhost:8000/api/audit/events/' `
  -Method GET `
  -Headers @{ 'Authorization' = "Bearer $token" }
```

#### Step 4.3: Run Test Suite

```bash
# Activate environment
.\.venv\Scripts\Activate.ps1

# Run all assessment tests (R-06)
python manage.py test assessments.test_state_machine -v 1

# Run all audit tests (R-07)
python manage.py test audit.test_audit_api -v 1

# Run validation tests (R-08)
python manage.py test config.test_validation -v 1

# Run security tests (R-09)
python manage.py test config.test_security -v 1

# Run all tests
python manage.py test --silenced=<add any warnings to suppress>
```

**Expected Results**: ✅ 75+ TESTS PASSING

---

### Phase 5: Production Deployment (Linux/Ubuntu)

#### Step 5.1: Install Production Dependencies

```bash
sudo apt-get install -y \
  postgresql \
  postgresql-contrib \
  redis-server \
  nginx \
  supervisor

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl start nginx
```

#### Step 5.2: Configure PostgreSQL

```bash
# Connect to PostgreSQL
sudo sudo -u postgres psql

# Create database and user
CREATE DATABASE core_backend_db;
CREATE USER core_backend WITH PASSWORD 'your-secure-password';
ALTER ROLE core_backend SET client_encoding TO 'utf8';
ALTER ROLE core_backend SET default_transaction_isolation TO 'read committed';
ALTER ROLE core_backend SET default_transaction_deferrable TO on;
ALTER ROLE core_backend SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE core_backend_db TO core_backend;
\q
```

#### Step 5.3: Configure Nginx

```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/core_backend
```

Paste this configuration:

```nginx
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    client_max_body_size 10M;
    
    location /static/ {
        alias /var/www/core_backend/staticfiles/;
    }
    
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/core_backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5.4: Configure Supervisor

```bash
# Create supervisor config
sudo nano /etc/supervisor/conf.d/core_backend.conf
```

Paste this configuration:

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
user=www-data
```

Update supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start core_backend
```

#### Step 5.5: Set Up SSL/TLS (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Update Nginx config for HTTPS
sudo nano /etc/nginx/sites-available/core_backend
```

Add HTTPS configuration:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers (automatically added by middleware)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # ... rest of server config ...
}
```

Reload Nginx:

```bash
sudo systemctl reload nginx
```

#### Step 5.6: Verify Production Deployment

```bash
# Check service status
sudo supervisorctl status
# Should show: core_backend RUNNING pid ...

# Check logs
sudo tail -f /var/log/core_backend.log

# Test API
curl -X GET https://your-domain.com/api/vendors/vendors/

# Verify security headers
curl -I https://your-domain.com/
# Should show all security headers
```

---

### Phase 6: Backup & Monitoring Setup

#### Step 6.1: Setup Automated Backups

```bash
# Create backup directory
sudo mkdir -p /var/backups/core_backend

# Create backup script
sudo nano /usr/local/bin/backup_core_backend.sh
```

Paste this script:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/core_backend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U core_backend core_backend_db | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Keep backups for 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

Make executable and add to cron:

```bash
sudo chmod +x /usr/local/bin/backup_core_backend.sh

# Add cron job
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup_core_backend.sh
```

#### Step 6.2: Configure Monitoring

```bash
# Install Prometheus/Grafana (optional but recommended)
# Or use simple log monitoring

# Monitor logs for errors
sudo tail -f /var/log/core_backend.log | grep -E "ERROR|CRITICAL"

# Monitor rate limiting
sudo grep "Rate limit" /var/log/core_backend.log

# Monitor security events
sudo grep -E "Brute|Auth|CRITICAL" /var/log/core_backend.log
```

---

## Comprehensive Verification Checklist

### Local Development ✓
- [ ] Git repository initialized
- [ ] All files committed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database migrations run
- [ ] Seed data loaded
- [ ] Development server starts
- [ ] API endpoints respond
- [ ] Tests pass (75+)
- [ ] Security headers present

### GitHub Repository ✓
- [ ] Repository created
- [ ] Remote added
- [ ] Code pushed
- [ ] README visible
- [ ] All files present
- [ ] Commit history shows 2 commits
- [ ] Branch is "main"

### Production Environment ✓
- [ ] Environment file configured
- [ ] Database created
- [ ] Migrations run
- [ ] Superuser created
- [ ] Seed data loaded
- [ ] Gunicorn configured
- [ ] Nginx configured
- [ ] SSL/TLS enabled
- [ ] Supervisor configured
- [ ] Application running

### Security Verification ✓
- [ ] All 9 security headers present
- [ ] HTTP→HTTPS redirect works
- [ ] Rate limiting active
- [ ] Auth endpoints protected
- [ ] Org scoping enforced
- [ ] Audit logging working
- [ ] State machine strict
- [ ] Input validation active
- [ ] Error messages safe
- [ ] No stack traces in responses

### Testing Complete ✓
- [ ] State machine tests pass (44)
- [ ] Audit tests pass (18)
- [ ] Validation tests pass (15+)
- [ ] Security tests pass (18+)
- [ ] Endpoint tests pass
- [ ] Permission tests pass
- [ ] All 75+ tests pass

---

## Quick Reference Commands

### Git Commands
```bash
git status                    # Check status
git log --oneline            # View commits
git push origin main         # Push to GitHub
git pull origin main         # Pull from GitHub
```

### Development Commands
```bash
.\.venv\Scripts\Activate.ps1          # Activate venv (Windows)
source venv/bin/activate              # Activate venv (Linux)
python manage.py runserver            # Start dev server
python manage.py test                 # Run tests
python manage.py migrate              # Run migrations
python seed_p0_ready.py               # Load seed data
```

### Production Commands (Linux)
```bash
sudo supervisorctl status             # Check service
sudo supervisorctl restart core_backend  # Restart app
sudo tail -f /var/log/core_backend.log   # View logs
sudo systemctl status nginx           # Check nginx
```

---

## Troubleshooting

### Git Push Issues

```bash
# If "fatal: could not read Username"
# Create personal access token on GitHub:
# Settings → Developer settings → Personal access tokens → Generate new token

# Use token as password when prompted
# Or configure in git config:
git config --global credential.helper store
# Then push again when prompted
```

### Database Connection Issues

```python
# Check database connection in Django
python manage.py dbshell

# If error, verify:
# 1. Database server running (sudo systemctl status postgresql)
# 2. Credentials correct in .env
# 3. User has proper permissions
```

### Tests Failing

```bash
# Clear cache
python manage.py clear_cache

# Rebuild database
python manage.py flush
python manage.py migrate

# Reload seed data
python seed_p0_ready.py

# Run tests again
python manage.py test assessments.test_state_machine
```

### Nginx Not Starting

```bash
# Test configuration
sudo nginx -t

# View error log
sudo tail -f /var/log/nginx/error.log

# Check if port 80/443 in use
sudo lsof -i :80
sudo lsof -i :443
```

---

## Success Criteria: Project Complete ✅

1. ✅ R-01 to R-10 fully implemented
2. ✅ 75+ tests passing
3. ✅ Security baseline met
4. ✅ Code pushed to GitHub
5. ✅ Documentation complete
6. ✅ Deployable to production
7. ✅ All security checks passed
8. ✅ Audit logging working
9. ✅ State machine strict
10. ✅ Ready for UAT

---

## Next Steps

1. **Immediate** (Today):
   - Complete Phases 1-4
   - Verify local tests pass
   - Push to GitHub

2. **Short-term** (This week):
   - Set up production environment
   - Configure databases
   - Deploy to server
   - Run security tests

3. **Medium-term** (Next 2 weeks):
   - UAT testing
   - Performance testing
   - Security audit
   - Penetration testing

4. **Long-term** (Post-UAT):
   - Production monitoring
   - Log aggregation
   - ML-based anomaly detection
   - Advanced security features

---

## Support Resources

| Resource | Location |
|----------|----------|
| API Documentation | `/api/docs/` (Swagger UI) |
| Threat Model | `R10_THREAT_MODEL_AND_CLOSURE.md` |
| State Machine | `R06_R07_IMPLEMENTATION.md` |
| Deployment | `GITHUB_AND_DEPLOYMENT.md` |
| Project Completion | `PROJECT_COMPLETION_REPORT.md` |
| GitHub Repository | `https://github.com/YOUR_USERNAME/core_backend` |

---

**Status**: ✅ **READY FOR DEPLOYMENT**  
**Last Updated**: 2026-03-12  
**Version**: 1.0.0
