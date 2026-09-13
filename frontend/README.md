# Dot Matrix OCR — Frontend

Static UI (plain HTML/CSS/JS, no build step). Deployed to **Vercel**.

```
index.html           markup
styles.css           styles
script.js            upload flow, progress, result rendering
config.js            GENERATED — do not edit by hand
generate-config.js   writes config.js from the environment
.env / .env.example  the values it reads
vercel.json          build command, headers, routing
Dockerfile           optional nginx image for local preview
```

## Configuration

A static page cannot read a `.env` file, so `generate-config.js` bakes the
values into `config.js`, which `index.html` loads before `script.js`. Real
environment variables win over `.env`, so the same script serves both local use
and Vercel's build.

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_BASE_URL` | `""` | Backend base URL, no trailing slash. Empty = same origin. |
| `WAKE_BACKEND` | `true` | Ping `/health` on page load to start Render's cold start early. |
| `MAX_UPLOAD_MB` | `10` | Files larger than this are rejected before uploading. |

```bash
cp .env.example .env        # edit, then:
node generate-config.js
```

Leave `API_BASE_URL` empty for local work: the root `app.py` launcher serves
this UI and the API on one origin, so the page calls itself.

## Deploy to Vercel

1. Push the repo to GitHub.
2. Vercel → *Add New → Project* → import the repo.
3. **Root Directory: `frontend`**. Framework Preset: *Other*. The build command
   (`node generate-config.js`) and output directory (`.`) come from
   [vercel.json](vercel.json) — leave the dashboard fields empty.
4. Under *Settings → Environment Variables* add `API_BASE_URL` =
   `https://<your-service>.onrender.com`. Without it the page calls its own
   Vercel origin and every request 404s.
5. Deploy, then set `ALLOWED_ORIGINS` on the Render backend to the resulting
   `https://<project>.vercel.app` and redeploy the backend.

CLI equivalent:

```bash
cd frontend
vercel            # preview
vercel --prod     # production
```

## Run locally

Any static server works:

```bash
# Best: the whole stack on one port, no config needed
python ../app.py               # http://localhost:8000

# This folder alone (set API_BASE_URL in .env and regenerate config.js first)
python -m http.server 8080
docker compose up --build      # http://localhost:8080
```

## Note on uploads

The image is posted directly to Render, not proxied through Vercel. That is
deliberate — Vercel's serverless request body limit (4.5 MB) would reject
larger photos. CORS on the backend is what makes the direct call work.
