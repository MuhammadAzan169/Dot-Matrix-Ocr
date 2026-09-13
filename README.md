# Dot Matrix OCR

Reads dot-matrix and laser-engraved digits off metal surfaces. A classical
OpenCV pipeline cleans and reconstructs the scattered dots into connected
glyphs, then a vision model reads the result.

The project runs two ways, from one codebase:

| | Local | Deployed |
| --- | --- | --- |
| How | `python app.py` — one server, one port | frontend on Vercel, backend on Render |
| UI ↔ API | same origin, no CORS | HTTPS across origins, CORS + `API_BASE_URL` |
| Cold start | none | ~50s after 15 min idle (Render free) |

## Layout

```
app.py        Local launcher — serves frontend/ and backend/ as one app
README.md     This file
.gitignore

frontend/     Static UI → Vercel
  index.html  styles.css  script.js
  config.js         generated — do not edit
  generate-config.js  bakes .env into config.js (Vercel's build command)
  .env  .env.example   API_BASE_URL, WAKE_BACKEND, MAX_UPLOAD_MB
  vercel.json  .vercelignore
  Dockerfile  .dockerignore  nginx.conf  docker-compose.yml  README.md

backend/      FastAPI + OpenCV API → Render (Docker, free tier)
  app.py  requirements.txt
  .env  .env.example    OPENROUTER_API_KEY, OCR_MODEL, ALLOWED_ORIGINS, ...
  Dockerfile  .dockerignore  docker-compose.yml
  render.yaml           Render service spec
  .gitattributes        Git LFS rules for the model weights below
  setup_local.ps1  README.md
  ocr/                  YOLO training, dataset, weights — research only
```

`backend/ocr/` sits with the backend because it is the same Python/ML side of
the project, but it is **not deployed**: `backend/.dockerignore` excludes it, so
its 33 MB of dataset and weights never enter the image. `backend/app.py` imports
none of it.

## Run everything locally

```bash
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env      # then add your OPENROUTER_API_KEY
python app.py
```

Open <http://localhost:8000>. The UI, the API, and `/docs` are all on that one
port, so there is no CORS and nothing to configure — `API_BASE_URL` is empty by
default, which makes the page call its own origin.

```bash
python app.py --port 5000     # different port
python app.py --reload        # restart on file changes
python app.py --host 0.0.0.0  # reachable from your phone on the same wifi
```

Prefer the split setup locally (closer to production, needs Docker):

```bash
docker compose -f backend/docker-compose.yml -f frontend/docker-compose.yml up --build
# UI http://localhost:8080   API http://localhost:10000
```

## Pipeline

1. Adaptive illumination correction (divide by a heavy Gaussian blur)
2. Binary threshold + morphological close
3. Connected components, filtered by area
4. DBSCAN over component centroids to drop background speckle
5. Deskew via `minAreaRect`, then crop
6. Vertical projection to split digit blocks
7. Tapered lines joining nearby dots within each block
8. Vision-model read of the reconstructed image (OpenRouter)

Every stage is returned to the UI as an image, so you can see where a bad read
went wrong.

## Deploying

Order matters — the frontend needs the backend's URL, and the backend needs the
frontend's origin for CORS.

1. **Backend → Render.** [backend/README.md](backend/README.md). New Web
   Service, Root Directory `backend`, Runtime `Docker`, Instance Type `Free`,
   Health Check Path `/health`. Set `OPENROUTER_API_KEY`. Copy the resulting
   `https://<name>.onrender.com`.
2. **Frontend → Vercel.** [frontend/README.md](frontend/README.md). Import the
   repo with Root Directory `frontend`, and set `API_BASE_URL` to the Render URL
   in the project's Environment Variables. The build command bakes it into
   `config.js`.
3. **Close the loop.** Set `ALLOWED_ORIGINS` on Render to your Vercel domain and
   redeploy the backend.

## What the free tier costs you

Every feature works on Render's free plan — nothing is disabled. Three
operational limits are worth knowing, and the code already accounts for each:

| Limit | Effect | What the code does |
| --- | --- | --- |
| Sleeps after ~15 min idle | First request takes ~50s | The page pings `/health` on load and tells the user the server is waking, instead of freezing the progress bar |
| 512 MB RAM, 0.1 CPU | Large images are slow | One uvicorn worker (more OOMs the instance); the UI rejects files over `MAX_UPLOAD_MB` before uploading |
| Ephemeral disk, no volume | Nothing persists between deploys | Intermediate images are returned inline as base64 and the session directory is deleted immediately, so nothing needs to persist |

Locally none of these apply: no sleep, your full CPU and RAM, and
`KEEP_UPLOADS=1` in `backend/.env` keeps every intermediate image on disk under
`backend/uploads/` for inspection.
