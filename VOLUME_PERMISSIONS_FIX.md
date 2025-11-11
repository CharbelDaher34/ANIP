# Docker Volume Permissions Fix

## 🐛 Problem

The `airflow-init` container failed with:

```
PermissionError: [Errno 13] Permission denied: '/opt/airflow/logs/scheduler'
ValueError: Unable to configure handler 'processor'
```

### Root Cause

Docker volume mounts created with **incorrect ownership**:
- Volumes created by Docker are owned by `root:root`
- Airflow containers run as `airflow` user (UID `50000`)
- Without proper permissions, Airflow cannot create log directories

---

## ✅ Solution

### Quick Fix (Already Applied)

```bash
# Fix Airflow volumes (UID 50000)
sudo chown -R 50000:0 volumes/airflow/

# Fix MLruns volume (world-writable for multi-user access)
sudo chmod -R 777 volumes/mlruns/
```

### Automated Fix (Use This)

We've created a script to automate this:

```bash
./scripts/fix_permissions.sh
```

---

## 📋 Volume Ownership Requirements

| Volume | Owner | Reason |
|--------|-------|--------|
| `volumes/airflow/` | `50000:0` | Airflow user (UID 50000) |
| `volumes/mlruns/` | `777` (all) | Shared by MLflow (root), Spark (185), Airflow (50000) |
| `volumes/postgres/` | Container-managed | Postgres container manages its own permissions |

---

## 🔍 Why This Happens

### Docker Volume Behavior

1. **First mount**: Docker creates directories as `root:root` with mode `755`
2. **Container user mismatch**: Container runs as non-root user (50000)
3. **Permission denied**: Non-root user cannot write to root-owned directories

### User IDs in Containers

```bash
# Check container UIDs
docker exec anip-airflow-scheduler id
# uid=50000(airflow) gid=0(root) groups=0(root)

docker exec anip-mlflow id
# uid=0(root) gid=0(root) groups=0(root)

docker exec spark-master id
# uid=185(spark) gid=185(spark) groups=185(spark)
```

---

## 🚀 Setup Instructions

### For Fresh Installation

```bash
# 1. Clone repository
git clone <repo-url> anip
cd anip

# 2. Create .env file
cp .env.example .env
# Edit .env with your values

# 3. Fix permissions BEFORE first start
./scripts/fix_permissions.sh

# 4. Start services
docker compose up -d
```

### For Existing Installation

```bash
# 1. Stop services
docker compose down

# 2. Fix permissions
./scripts/fix_permissions.sh

# 3. Restart services
docker compose up -d
```

---

## 🔒 Security Considerations

### Why 777 for mlruns?

The `mlruns` directory is shared by **three different users**:
- **MLflow** (UID 0 - root)
- **Spark** (UID 185)
- **Airflow** (UID 50000)

**Options considered:**

1. ✅ **Mode 777** (world-writable)
   - **Pros:** Simple, works for all users
   - **Cons:** Less secure (local development only!)
   - **Use case:** Development environments

2. ❌ **Shared GID** (e.g., group 1000)
   - **Pros:** More secure
   - **Cons:** Requires modifying all Dockerfiles
   - **Use case:** Production environments

3. ❌ **Named volumes**
   - **Pros:** Docker-managed
   - **Cons:** Harder to inspect/backup
   - **Use case:** Production with orchestration

**For production**, consider:
- Using a shared GID across all containers
- Using Docker secrets and named volumes
- Implementing proper file access controls

---

## 🛠️ Troubleshooting

### Check Current Permissions

```bash
ls -lah volumes/
```

**Expected output:**
```
drwxr-xr-x   4 50000 root  airflow/
drwxrwxrwx   2 root  root  mlruns/
drwx------  19 <uid> root  postgres/
```

### Re-run Permission Fix

```bash
./scripts/fix_permissions.sh
```

### Manual Permission Fix

```bash
# Airflow
sudo chown -R 50000:0 volumes/airflow/

# MLruns
sudo chmod -R 777 volumes/mlruns/
```

### Check Container Logs

```bash
# Airflow init logs
docker compose logs airflow-init

# Scheduler logs
docker compose logs airflow-scheduler

# MLflow logs
docker compose logs mlflow
```

---

## 📚 Related Documentation

- [Docker Volume Permissions](https://docs.docker.com/storage/volumes/#use-a-volume-with-docker-compose)
- [Airflow in Docker](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Understanding Docker User Namespaces](https://docs.docker.com/engine/security/userns-remap/)

---

## ✅ Verification

After applying the fix, verify everything works:

```bash
# Check volumes
ls -lah volumes/

# Start services
docker compose up -d

# Check Airflow init succeeded
docker compose logs airflow-init | tail -20

# Check Airflow UI
curl -s http://localhost:8080/health | jq .

# Check log directories were created
ls -lah volumes/airflow/logs/
```

---

**Status:** ✅ Fixed and documented  
**Priority:** High (Blocking)  
**Category:** Infrastructure / DevOps

