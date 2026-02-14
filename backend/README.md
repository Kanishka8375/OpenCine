# OpenCine Backend Run Guide (Linux / macOS / Windows)

This guide is written for the current backend implementation in this repository.

## What this backend needs

- Python 3.11+ (3.12 works)
- PostgreSQL
- Redis
- ffmpeg binary on PATH
- AWS credentials + S3 bucket (for final upload)

The API process starts with FastAPI (`app.main:app`).
The async long job processor is Celery (`worker.celery`).

---

## 1) Python environment

From repo root:

```bash
cd backend
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> If `python` is not found on Linux, use `python3` exactly as you already did.

---

## 2) Environment variables

Create `.env` from template:

```bash
cp .env.example .env
```

Update at least:

- `DATABASE_URL`
- `REDIS_URL`
- `S3_BUCKET`
- optional `LLM_API_URL` / `LLM_API_KEY`

---

## 3) Install ffmpeg

### Linux (Ubuntu)

```bash
sudo apt update && sudo apt install -y ffmpeg
ffmpeg -version
```

### macOS

```bash
brew install ffmpeg
ffmpeg -version
```

### Windows

```powershell
winget install Gyan.FFmpeg
ffmpeg -version
```

---

## 4) Start PostgreSQL + Redis

You can run these either with Docker or native services.

## Option A — Docker (recommended)

### If Docker is newly installed and you see permission denied on `/var/run/docker.sock`

Run once, then **logout/login**:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker ps
```

Now start services:

```bash
docker run --name opencine-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=opencine -p 5432:5432 -d postgres:16
docker run --name opencine-redis -p 6379:6379 -d redis:7
```

## Option B — Native services (no Docker)

### Ubuntu

```bash
sudo apt install -y postgresql redis-server
sudo systemctl enable --now postgresql
sudo systemctl enable --now redis-server
```

Create DB/user:

```bash
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';" || true
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "CREATE DATABASE opencine OWNER postgres;" || true
```

---

## 5) Run API + worker

Use **two terminals** from `backend/` with venv activated.

### Terminal A: FastAPI

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal B: Celery

Linux/macOS:

```bash
celery -A worker.celery worker --loglevel=info
```

Windows:

```powershell
celery -A worker.celery worker --pool=solo --loglevel=info
```

---

## 6) Smoke test

```bash
curl http://localhost:8000/healthz
```

Queue a render:

```bash
curl -X POST http://localhost:8000/v1/renders \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A cinematic journey through a neon city","face_reference_image":null}'
```

Check status:

```bash
curl http://localhost:8000/v1/renders/<JOB_ID>
```

---

## Troubleshooting mapped to your logs

### 1) `python: command not found`
Use `python3` to create the virtual environment:

```bash
python3 -m venv .venv
```

### 2) `docker: permission denied ... /var/run/docker.sock`
Your user is not in docker group (or shell not refreshed).

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Then retry `docker ps` and the `docker run` commands.

### 3) `ModuleNotFoundError: No module named 'f5_tts'`
This backend treats F5-TTS as optional and falls back to silent WAV generation.
You can proceed without blocking startup.

### 4) `psycopg.OperationalError: connection refused`
Postgres is not running/reachable at `127.0.0.1:5432`.
Fix by starting Postgres (Docker or native), then retry `uvicorn`.

### 5) Large model downloads are huge
`torch`, diffusion models, and quantized backends are large; first install/start may take significant time and disk.

### 6) `SyntaxError` in `app/services/audio_gen.py` (like `except Exception:`)
This usually means your local file is stale/corrupted from an older conflicting checkout.

Run these commands from `backend/`:

```bash
git pull
source .venv/bin/activate
python -m compileall app/services/audio_gen.py
```

If compile still fails, restore just that file from git and retry:

```bash
git checkout -- app/services/audio_gen.py
python -m compileall app/services/audio_gen.py
```

---

## Production notes

- This project expects GPU nodes for model inference.
- Keep Redis/Postgres reachable from both API and worker.
- Ensure AWS credentials are available in environment for boto3 upload.
