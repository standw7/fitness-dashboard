import json
import pathlib
from datetime import date, timedelta
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATA_DIR = pathlib.Path("/data")
FITNESS_LOG = DATA_DIR / "fitness_log.json"
READING_LOG = DATA_DIR / "reading_log.json"


def load_json(path: pathlib.Path) -> list:
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return data if isinstance(data, list) else []
        except Exception:
            pass
    return []


@app.get("/api/fitness")
def api_fitness():
    return load_json(FITNESS_LOG)


@app.get("/api/reading")
def api_reading():
    return load_json(READING_LOG)


@app.get("/api/stats")
def api_stats():
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    fitness = load_json(FITNESS_LOG)
    reading = load_json(READING_LOG)

    # Weekly exercise totals
    week_ex = [e for e in fitness if e.get("date", "") >= week_ago.isoformat()]
    month_ex = [e for e in fitness if e.get("date", "") >= month_ago.isoformat()]
    week_totals = {"pushups": 0, "situps": 0, "pullups": 0}
    month_totals = {"pushups": 0, "situps": 0, "pullups": 0}
    all_totals = {"pushups": 0, "situps": 0, "pullups": 0}
    for e in fitness:
        for k in all_totals:
            all_totals[k] += e.get(k, 0)
    for e in week_ex:
        for k in week_totals:
            week_totals[k] += e.get(k, 0)
    for e in month_ex:
        for k in month_totals:
            month_totals[k] += e.get(k, 0)

    # Weekly reading totals
    week_rd = [e for e in reading if e.get("date", "") >= week_ago.isoformat()]
    month_rd = [e for e in reading if e.get("date", "") >= month_ago.isoformat()]

    # Daily exercise data for charts (last 30 days)
    daily_ex = defaultdict(lambda: {"pushups": 0, "situps": 0, "pullups": 0})
    for e in month_ex:
        d = e.get("date", "")
        for k in ("pushups", "situps", "pullups"):
            daily_ex[d][k] += e.get(k, 0)

    # Daily reading data for charts (last 30 days)
    daily_rd = defaultdict(int)
    for e in month_rd:
        daily_rd[e.get("date", "")] += e.get("minutes", 0)

    # Generate last 30 days labels
    chart_dates = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]

    # Books read
    all_books = defaultdict(int)
    for e in reading:
        if e.get("book"):
            all_books[e["book"]] += e.get("minutes", 0)

    return {
        "week_exercise": week_totals,
        "month_exercise": month_totals,
        "all_exercise": all_totals,
        "week_sessions": len(week_ex),
        "week_reading_min": sum(e.get("minutes", 0) for e in week_rd),
        "week_reading_sessions": len(week_rd),
        "month_reading_min": sum(e.get("minutes", 0) for e in month_rd),
        "all_reading_min": sum(e.get("minutes", 0) for e in reading),
        "chart_dates": chart_dates,
        "chart_pushups": [daily_ex[d]["pushups"] for d in chart_dates],
        "chart_situps": [daily_ex[d]["situps"] for d in chart_dates],
        "chart_pullups": [daily_ex[d]["pullups"] for d in chart_dates],
        "chart_reading": [daily_rd[d] for d in chart_dates],
        "books": dict(all_books),
    }


def save_json(path: pathlib.Path, data: list):
    path.write_text(json.dumps(data, ensure_ascii=False))


@app.delete("/api/fitness/{index}")
def delete_fitness(index: int):
    data = load_json(FITNESS_LOG)
    if 0 <= index < len(data):
        removed = data.pop(index)
        save_json(FITNESS_LOG, data)
        return {"ok": True, "removed": removed}
    return {"ok": False, "error": "Invalid index"}


@app.delete("/api/reading/{index}")
def delete_reading(index: int):
    data = load_json(READING_LOG)
    if 0 <= index < len(data):
        removed = data.pop(index)
        save_json(READING_LOG, data)
        return {"ok": True, "removed": removed}
    return {"ok": False, "error": "Invalid index"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
