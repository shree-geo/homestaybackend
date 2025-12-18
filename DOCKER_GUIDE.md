# 🐳 How to Run GrihaStay Backend with Docker

## Quick Start Commands

### 1. Start the Application (First Time)

```bash
cd /home/shree/grihaStayPro
docker compose up --build
```

**What happens:**
- Downloads PostgreSQL with PostGIS image
- Builds the Django backend container
- Installs all Python dependencies
- Starts both containers
- Initializes the database
- Runs migrations
- Starts the Django server

**Wait time:** First build takes 3-5 minutes (downloads and builds everything)

---

### 2. Start the Application (After First Build)

```bash
cd /home/shree/grihaStayPro
docker compose up
```

**What happens:**
- Uses existing built images (much faster!)
- Starts both containers
- Server ready in ~10 seconds

---

### 3. Start in Background (Detached Mode)

```bash
cd /home/shree/grihaStayPro
docker compose up -d
```

**What happens:**
- Runs containers in background
- You get your terminal back
- Services keep running

---

### 4. Stop the Application

```bash
# If running in foreground (Ctrl+C), then:
docker compose down

# OR if running in background:
cd /home/shree/grihaStayPro
docker compose down
```

---

### 5. View Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Database only
docker compose logs -f db

# Last 100 lines
docker compose logs --tail=100
```

---

### 6. Check Running Containers

```bash
docker compose ps

# OR
docker ps
```

---

### 7. Rebuild After Code Changes

```bash
# If you changed Python code
docker compose up --build

# OR force rebuild
docker compose build --no-cache
docker compose up
```

---

### 8. Clean Start (Remove Everything)

```bash
# Stop and remove containers, networks, volumes
docker compose down -v

# Then start fresh
docker compose up --build
```

**⚠️ Warning:** This deletes all database data!

---

## 🔍 Verify It's Working

### Check Health

```bash
# In another terminal while docker is running
curl http://localhost:8000/api/health/
```

**Expected response:**
```json
{"status": "healthy", "message": "GrihaStay API is running"}
```

---

### Check Database

```bash
# Check if database is accessible
docker compose exec db psql -U postgres -d grihastay -c "SELECT COUNT(*) FROM tenants;"
```

---

### Access Django Shell

```bash
docker compose exec backend python manage.py shell
```

---

### Run Django Commands

```bash
# Create superuser for admin panel
docker compose exec backend python manage.py createsuperuser

# Run migrations
docker compose exec backend python manage.py migrate

# Collect static files
docker compose exec backend python manage.py collectstatic
```

---

## 🐛 Troubleshooting

### Problem: Port Already in Use

**Error:** `port 8000 or 5432 already in use`

**Solution:**
```bash
# Find and kill process using port 8000
sudo lsof -ti:8000 | xargs kill -9

# Find and kill process using port 5432
sudo lsof -ti:5432 | xargs kill -9
```

---

### Problem: Database Connection Failed

**Error:** `could not connect to server`

**Solution:**
```bash
# Wait for database to start (takes ~10 seconds)
# Check database logs
docker compose logs db

# Restart services
docker compose restart
```

---

### Problem: Permission Denied on entrypoint.sh

**Error:** `permission denied: ./entrypoint.sh`

**Solution:**
```bash
chmod +x /home/shree/grihaStayPro/backend/entrypoint.sh
docker compose up --build
```

---

### Problem: Build Fails

**Error:** Various build errors

**Solution:**
```bash
# Clean everything and rebuild
docker compose down -v
docker system prune -f
docker compose up --build
```

---

### Problem: Can't Access API

**Check:**
1. Is Docker running? `docker compose ps`
2. Check logs: `docker compose logs backend`
3. Check ports: `netstat -tulpn | grep 8000`
4. Try localhost: `curl http://localhost:8000/api/health/`

---

## 📊 Container Status

### Healthy System Shows:

```bash
$ docker compose ps
NAME                    STATUS          PORTS
grihastay_backend       Up 2 minutes    0.0.0.0:8000->8000/tcp
grihastay_db            Up 2 minutes    0.0.0.0:5432->5432/tcp
```

---

## 🎯 Complete Workflow

### First Time Setup:

```bash
# 1. Navigate to project
cd /home/shree/grihaStayPro

# 2. Build and start (wait 3-5 minutes)
docker compose up --build

# 3. In another terminal, test the API
curl http://localhost:8000/api/health/

# 4. Register your first tenant
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "My Homestay",
    "user_name": "admin",
    "email": "admin@example.com",
    "password": "Admin@123",
    "full_name": "Admin User"
  }'

# 5. Stop (Ctrl+C in the docker terminal)
docker compose down
```

---

### Daily Development:

```bash
# Start in background
cd /home/shree/grihaStayPro
docker compose up -d

# View logs if needed
docker compose logs -f

# When done
docker compose down
```

---

## 🔄 Common Commands Summary

| Action | Command |
|--------|---------|
| First start | `docker compose up --build` |
| Normal start | `docker compose up` |
| Start background | `docker compose up -d` |
| Stop | `docker compose down` |
| View logs | `docker compose logs -f` |
| Check status | `docker compose ps` |
| Rebuild | `docker compose build` |
| Clean restart | `docker compose down -v && docker compose up --build` |
| Access shell | `docker compose exec backend bash` |
| Run command | `docker compose exec backend python manage.py <command>` |

---

## 🌐 Access Points

Once running:

- **API Base URL:** http://localhost:8000/api/
- **Health Check:** http://localhost:8000/api/health/
- **Django Admin:** http://localhost:8000/admin/
- **Database:** localhost:5432 (from host machine)

---

## ✅ Success Indicators

You know it's working when:

1. ✅ `docker compose ps` shows both containers as "Up"
2. ✅ `curl http://localhost:8000/api/health/` returns JSON
3. ✅ Logs show "Django started successfully"
4. ✅ No error messages in `docker compose logs`

---

## 📖 Next Steps

Once Docker is running:

1. Read **QUICKSTART.md** for API examples
2. Import **GrihaStay_Postman_Collection.json** into Postman
3. Try the registration and login endpoints
4. Build your React frontend

---

**Happy Coding! 🚀**

For detailed API documentation, see **README.md**
