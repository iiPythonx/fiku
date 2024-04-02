# Copyright (c) 2024 iiPython

# Modules
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from humanfriendly import format_timespan

from fiku import app, db
from fiku.modules import image_module

# Initialization
app.mount("/static", StaticFiles(
    directory = Path(__file__).parents[1] / "public/static"
), name = "static")

# Setup templating
def app_context(request: Request) -> Dict[str, Any]:
    return {
        "db": db,
        "escape": lambda s: s.replace("\"", "\\\"").replace("'", "\\'"),
        "format_time": lambda t: format_timespan(time.time() - t, max_units = 1) + " ago"
    }

templates = Jinja2Templates(
    directory = Path(__file__).parents[1] / "public/jinja",
    context_processors = [app_context]
)

# Routes
@app.get("/")
async def load_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "start.jinja2")

@app.get("/about")
async def load_about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "about.jinja2")

@app.get("/artist")
async def load_artist(request: Request, artist: str) -> HTMLResponse:
    return templates.TemplateResponse(request, "artist.jinja2", {"artist": artist})

@app.get("/image")
async def load_image(
    artist: str,
    album: str | None = None,
    track: str | None = None
) -> RedirectResponse:
    return await image_module.fetch_image(artist, album, track)
