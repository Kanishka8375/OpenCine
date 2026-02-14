1) What this backend needs to run
From the code:

FastAPI app entrypoint: backend/app/main.py. 

Celery task/worker app: backend/celery_worker.py and exported via backend/worker.py. 

Required services:

PostgreSQL (database_url)

Redis (redis_url)

S3 credentials/bucket for final upload

FFmpeg binary (used by ffmpeg-python)

Hugging Face/PyTorch dependencies from requirements. 

2) Shared project setup (all OS)
Run from repository root (/workspace/OpenCine equivalent on your machine):

cd OpenCine
cd backend
python -m venv .venv
Activate venv:

Linux/macOS:

source .venv/bin/activate
Windows PowerShell:

.\.venv\Scripts\Activate.ps1
Install dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt
3) Create .env file (important)
The app reads env vars from .env via pydantic-settings. 

Create backend/.env:

APP_NAME=OpenCine Backend
LOG_LEVEL=INFO

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/opencine
REDIS_URL=redis://localhost:6379/0

LLM_MODEL_ID=meta-llama/Meta-Llama-3.1-70B-Instruct
# Optional if using hosted/vLLM API:
LLM_API_URL=
LLM_API_KEY=

FLUX_MODEL_ID=black-forest-labs/FLUX.1-dev
IP_ADAPTER_ID=h94/IP-Adapter-FaceID
HUNYUAN_MODEL_ID=tencent/HunyuanVideo-I2V

OUTPUT_DIR=outputs
S3_BUCKET=your-s3-bucket-name
S3_REGION=us-east-1
These names map directly to Settings fields. 

4) Start PostgreSQL + Redis
You can use Docker on all platforms (easiest and consistent):

docker run --name opencine-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=opencine -p 5432:5432 -d postgres:16
docker run --name opencine-redis -p 6379:6379 -d redis:7
5) Install FFmpeg binary (OS-specific)
ffmpeg-python is just a wrapper; it needs system ffmpeg executable. 

Windows
winget install Gyan.FFmpeg
or choco install ffmpeg

Confirm:

ffmpeg -version
macOS
brew install ffmpeg

Confirm:

ffmpeg -version
Linux (Ubuntu/Debian)
sudo apt update && sudo apt install -y ffmpeg

Confirm:

ffmpeg -version
6) Start API server and Celery worker
Important: because main.py imports celery_worker as a top-level module, run commands from backend/ directory. 

Terminal A — FastAPI
cd backend
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Terminal B — Celery worker
Linux/macOS:
cd backend
source .venv/bin/activate
celery -A worker.celery worker --loglevel=info
Windows:
Celery prefork has issues on Windows. Use solo pool:

cd backend
.\.venv\Scripts\Activate.ps1
celery -A worker.celery worker --pool=solo --loglevel=info
Celery app export is in worker.py (celery object). 

7) Call the API
Create render job
curl -X POST http://localhost:8000/v1/renders \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A cinematic sci-fi short about a lone astronaut finding a hidden ocean on Mars","face_reference_image":null}'
Route and payload are defined in main.py + schemas. 

Check job status
curl http://localhost:8000/v1/renders/<JOB_ID>
Status endpoint exists here. 

Health check
curl http://localhost:8000/healthz
Health endpoint exists here. 

8) GPU/H100 notes (very important)
The project intentionally swaps active diffusion models via ModelManager.load_model() so only one heavy model is on GPU at a time. 

Flux and Hunyuan services both register with this manager and use CPU offload hooks. 

Hunyuan transformer is configured with 4-bit loading (load_in_4bit=True). 

9) Common issues checklist
ModuleNotFoundError: celery_worker → you launched uvicorn from wrong directory; run from backend/. 

FFmpeg errors → binary not installed on system PATH. 

DB connection error → verify DATABASE_URL and PostgreSQL container is running. 

Redis/Celery connection error → verify Redis up and REDIS_URL correct. 

S3 upload failure → set AWS creds + valid bucket/region. Upload happens at end of task. 

Commands I used to prepare this answer
pwd && find backend -maxdepth 3 -type f | sort
nl -ba backend/app/main.py | sed -n '1,220p'
