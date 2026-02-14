# OpenCine

OpenCine is a long-form AI video generation backend built with **FastAPI + Celery + Diffusers**.

This repository currently contains the backend implementation under `backend/`, including:

- FastAPI API for render job submission and status tracking
- Celery worker orchestration for long-running video generation jobs
- VRAM-aware model manager for heavy diffusion pipelines
- Script generation, image generation, video generation, audio synthesis, and final stitching/upload flow

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── services/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── celery_worker.py
│   ├── worker.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
└── README.md
```

## Quick Start

1. Move to backend directory:

```bash
cd backend
```

2. Follow the complete setup and run instructions in:

- [`backend/README.md`](backend/README.md)

That guide includes Linux/macOS/Windows setup, environment variables, PostgreSQL + Redis bootstrapping, worker startup, and troubleshooting.

## Notes

- This project is designed for GPU inference environments.
- For production, ensure Postgres, Redis, and S3 credentials are configured.
