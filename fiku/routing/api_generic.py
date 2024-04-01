# Copyright (c) 2024 iiPython

# Modules
from fastapi.responses import JSONResponse

from fiku import db, app
from fiku.models.listenbrainz import LBPayloadModel

# Routes
@app.get("/api/now_playing")
async def api_now_playing() -> JSONResponse:
    now_playing = db.get_playing_now()
    return JSONResponse({
        "code": 200,
        "data": now_playing.model_dump(mode = "json") if isinstance(now_playing, LBPayloadModel) else None
    })

@app.get("/api/top_items")
async def api_top_items(item_type: str, timespan: str = "all") -> JSONResponse:
    if item_type not in ["artist", "track", "album"]:
        return JSONResponse({"code": 400}, status_code = 400)

    return JSONResponse({
        "code": 200,
        "data": db.get_top_items(item_type, timespan = timespan)
    })
