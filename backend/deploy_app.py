import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import original app
from main import app

# Start background database backup thread
if os.getenv("COZE_PROJECT_ENV") == "PROD":
    try:
        from db_backup import start_background_backup
        start_background_backup()  # interval is fixed at 60s in db_backup.py
    except Exception as e:
        print(f"[deploy_app] Failed to start backup thread: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")
INDEX_HTML = os.path.join(DIST_DIR, "index.html")

if os.path.isdir(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    ep_dir = os.path.join(DIST_DIR, "element-plus")
    if os.path.isdir(ep_dir):
        app.mount("/element-plus", StaticFiles(directory=ep_dir), name="element-plus")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        if os.path.isfile(INDEX_HTML):
            return FileResponse(INDEX_HTML)
        return {"detail": "frontend not built"}

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        if path.startswith("api/"):
            return {"detail": "Not Found"}
        if os.path.isfile(INDEX_HTML):
            return FileResponse(INDEX_HTML)
        return {"detail": "frontend not built"}
