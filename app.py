"""
Local all-in-one launcher.

In production the two halves are deployed apart and talk over the network:

    browser -> frontend/ on Vercel  --HTTPS--> backend/ on Render

That split is what the deployment config describes. Locally it is a nuisance:
two servers, two ports, a config file to point one at the other, and CORS in
between. So this launcher mounts both halves into a single ASGI app on a single
port, with no CORS and no cold starts, while running the exact same backend
code that Render runs.

    python app.py                 # http://localhost:8000
    python app.py --port 5000
    python app.py --reload        # restart on file changes

Nothing here is imported by either deployment; it is a development entry point
only.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

for directory, label in ((BACKEND_DIR, "backend"), (FRONTEND_DIR, "frontend")):
    if not directory.is_dir():
        sys.exit(f"error: {label}/ not found next to {Path(__file__).name}")

# Import backend/app.py as-is. It anchors its own .env and uploads directory to
# backend/, so importing it from here changes none of its behaviour.
#
# It is loaded by path under a distinct module name: this launcher is also
# called app.py, and a plain `from app import app` would re-import this file.
sys.path.insert(0, str(BACKEND_DIR))

import importlib.util  # noqa: E402

from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

_spec = importlib.util.spec_from_file_location("backend_app", BACKEND_DIR / "app.py")
assert _spec and _spec.loader
backend_app = importlib.util.module_from_spec(_spec)
sys.modules["backend_app"] = backend_app
_spec.loader.exec_module(backend_app)

api = backend_app.app

logger = logging.getLogger("launcher")


def _index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


# The backend owns "/" for its JSON service banner, and FastAPI keeps the first
# route that matches. Drop it so the UI can take that path locally; the banner
# is only there to answer "is this thing up?", which /health does better.
api.router.routes = [
    route for route in api.router.routes
    if not (getattr(route, "path", None) == "/" and "GET" in getattr(route, "methods", set()))
]


# Serve the UI from the same origin as the API. frontend/config.js leaves
# API_BASE_URL empty by default, which makes the page call this same server —
# so the browser sees one origin and every API route keeps working untouched.
@api.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    return _index()


# StaticFiles mounted last so it never shadows /api, /health or /docs, which are
# already registered on the router above it.
api.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend",
)

# The object uvicorn serves, also usable as `uvicorn app:app --reload` from the
# repository root.
app = api


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full Dot Matrix OCR stack locally.")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)),
                        help="port to listen on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="restart when source files change")
    args = parser.parse_args()

    import uvicorn

    configured = bool(os.getenv("OPENROUTER_API_KEY"))
    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"

    print()
    print("  Dot Matrix OCR — full stack, one port")
    print(f"    UI        {url}")
    print(f"    API docs  {url}/docs")
    print(f"    Health    {url}/health")
    print(f"    OCR key   {'found' if configured else 'MISSING — set OPENROUTER_API_KEY in backend/.env'}")
    print()

    if args.reload:
        # reload needs an import string rather than the app object
        uvicorn.run("app:app", host=args.host, port=args.port, reload=True,
                    app_dir=str(ROOT),
                    reload_dirs=[str(ROOT), str(BACKEND_DIR), str(FRONTEND_DIR)])
    else:
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
