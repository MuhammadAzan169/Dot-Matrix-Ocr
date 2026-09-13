# Dot Matrix OCR — Backend

FastAPI service that runs the image pipeline (illumination correction →
thresholding → connected components → DBSCAN → deskew → digit-block joining)
and then reads the digits with a vision model via OpenRouter.

Deployed to **Render (free tier)** as a Docker web service.

## Endpoints

| Method | Path           | Purpose                                            |
| ------ | -------------- | -------------------------------------------------- |
| GET    | `/`            | Service banner                                      |
| GET    | `/health`      | Liveness probe (also used to wake the free instance) |
| GET    | `/docs`        | Swagger UI                                          |
| POST   | `/api/process` | `multipart/form-data` with `file`; returns every pipeline stage as base64 plus `ocr_result` |

## Environment variables

See [.env.example](.env.example). Only `OPENROUTER_API_KEY` is required.

| Variable             | Default           | Notes                                       |
| -------------------- | ----------------- | ------------------------------------------- |
| `OPENROUTER_API_KEY` | —                 | Required. Set as a secret in Render.         |
| `OCR_MODEL`          | `openrouter/free` | Vision model used for the final read.        |
| `ALLOWED_ORIGINS`    | `*`               | Comma-separated. Set to your Vercel URL(s).  |
| `PORT`               | `10000`           | Render injects this automatically.           |
| `KEEP_UPLOADS`       | `0`               | `1` keeps intermediate images in `uploads/`. |
| `UPLOAD_DIR`         | `backend/uploads` | Where intermediate images are written.       |

`.env` is loaded automatically from this folder, whatever directory you start
the process from. Real environment variables always win, which is how Render
and docker-compose override it.

## Run locally

Docker (matches production), from this folder:

```bash
OPENROUTER_API_KEY=sk-... docker compose up --build
# http://localhost:10000/docs
```

Without Docker:

```bash
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env      # then fill in your key
python app.py             # API only, http://localhost:10000
```

To get the UI as well, run the launcher at the repository root instead — it
serves this same app plus `frontend/` on one port:

```bash
python ../app.py          # http://localhost:8000
```

## Deploy to Render

*New → Web Service* → connect the repo, then:

| Field             | Value      |
| ----------------- | ---------- |
| Root Directory    | `backend`  |
| Runtime           | `Docker`   |
| Dockerfile Path   | `./Dockerfile` |
| Instance Type     | `Free`     |
| Health Check Path | `/health`  |

Add the environment variables from the table above — `OPENROUTER_API_KEY` as a
secret. [render.yaml](render.yaml) holds the same settings in blueprint form;
Render only auto-detects a blueprint at the repository root, so copy it there
if you would rather use *New → Blueprint* than fill in the form.

After the first deploy, copy the service URL
(`https://<name>.onrender.com`) into `frontend/config.js`, and set
`ALLOWED_ORIGINS` to your Vercel domain.

## Free-tier notes

These shape how the service is configured, so they are worth knowing:

- **It sleeps.** After ~15 minutes idle the instance spins down; the next
  request pays a ~50s cold start. The frontend pings `/health` on page load to
  start that wake-up early.
- **512 MB RAM, 0.1 CPU.** The Dockerfile runs a single uvicorn worker on
  purpose — OpenCV and scikit-learn will OOM the instance with more.
- **Ephemeral disk, no persistent volume.** `/api/process` deletes its session
  directory once the images are encoded into the response, so nothing
  accumulates.
- **The training code is not deployed.** [ocr/](ocr/) sits in this folder
  because it is the same Python side of the project, but `.dockerignore`
  excludes it from the build — 33 MB of dataset and `.pt` weights that `app.py`
  never imports. Its files are tracked with Git LFS via
  [.gitattributes](.gitattributes).
