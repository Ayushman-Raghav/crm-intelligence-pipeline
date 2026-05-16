import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import OUTPUT_DIR

FULL_REPORT   = PROJECT_ROOT / OUTPUT_DIR / "full_report.json"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
MAIN_PY       = PROJECT_ROOT / "main.py"

app = FastAPI(title="CRM Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline = {
    "status":          "idle",
    "last_run":        None,
    "last_duration_s": None,
    "error":           None,
}

def load_report():
    if not FULL_REPORT.exists():
        return []
    with open(FULL_REPORT, encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/accounts")
def get_accounts():
    return load_report()

@app.get("/api/accounts/{account_id}")
def get_account(account_id: str):
    for acc in load_report():
        if acc.get("account_id") == account_id:
            return acc
    raise HTTPException(status_code=404, detail="Account not found")

@app.get("/api/summary")
def get_summary():
    report = load_report()
    if not report:
        return {"total": 0, "red": 0, "amber": 0, "green": 0,
                "mrr_at_risk": 0, "total_mrr": 0, "last_updated": None}
    red   = [a for a in report if a.get("health_score") == "Red"]
    amber = [a for a in report if a.get("health_score") == "Amber"]
    green = [a for a in report if a.get("health_score") == "Green"]
    return {
        "total":       len(report),
        "red":         len(red),
        "amber":       len(amber),
        "green":       len(green),
        "total_mrr":   sum(a.get("mrr") or 0 for a in report),
        "mrr_at_risk": sum(a.get("mrr") or 0 for a in red),
        "last_updated": datetime.fromtimestamp(
            FULL_REPORT.stat().st_mtime).isoformat() if FULL_REPORT.exists() else None,
    }

@app.get("/api/pipeline/status")
def pipeline_status():
    return _pipeline

@app.post("/api/pipeline/run")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    if _pipeline["status"] == "running":
        return JSONResponse({"message": "Already running"}, status_code=409)
    background_tasks.add_task(_run_pipeline_bg)
    return {"message": "Pipeline started"}

async def _run_pipeline_bg():
    _pipeline["status"] = "running"
    _pipeline["error"]  = None
    start = datetime.now()
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(MAIN_PY),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        _, stderr = await proc.communicate()
        _pipeline["last_duration_s"] = int((datetime.now() - start).total_seconds())
        _pipeline["last_run"]        = datetime.now().isoformat()
        if proc.returncode != 0:
            _pipeline["error"] = stderr.decode(errors="replace")[-600:]
    except Exception as exc:
        _pipeline["error"] = str(exc)
    finally:
        _pipeline["status"] = "idle"

if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")

@app.get("/")
def serve_dashboard():
    index = DASHBOARD_DIR / "index.html"
    if not index.exists():
        return JSONResponse({"error": "Dashboard not built yet"}, status_code=404)
    return FileResponse(str(index))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8080, reload=True)