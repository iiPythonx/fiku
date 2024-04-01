# Copyright (c) 2024 iiPython

# Modules
from typing import Literal
from calendar import isleap, monthrange
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse

from fiku import db, app
from fiku.models.listenbrainz import LBPayloadModel

# Initialization
Timespan = Literal["day", "week", "month", "year", "all"]
ItemType = Literal["artist", "track", "album"]
TimestampFormats = {
    "day": "%d %B %Y",
    "week": "Week %W %Y",
    "month": "%B %Y",
    "year": "%Y"
}

# Routes
@app.get("/api/now_playing")
async def api_now_playing() -> JSONResponse:
    now_playing = db.get_playing_now()
    return JSONResponse({
        "code": 200,
        "data": now_playing.model_dump(mode = "json") if isinstance(now_playing, LBPayloadModel) else None
    })

@app.get("/api/top_items")
async def api_top_items(item_type: ItemType, timespan: Timespan = "all") -> JSONResponse:
    return JSONResponse({
        "code": 200,
        "data": db.get_top_items(item_type, timespan = timespan)
    })

@app.get("/api/pulse")
async def api_pulse(timespan: Timespan = "day") -> JSONResponse:
    if timespan == "all":
        return JSONResponse({"code": 400})

    month_amount, week_amount, day_amount = 28 if timespan == "month" else 0, \
        7 if timespan == "week" else 0, 1 if timespan == "day" else 0
    total_offset = month_amount + week_amount + day_amount

    # Calculate date range
    results = []
    current = datetime.now().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    for _ in range(12):
        current = current.replace(day = 1 if timespan not in ["day", "week"] else current.day)

        # Calculate bounds
        normalized = current
        upper_bound = current + timedelta(total_offset + (monthrange(current.year, current.month)[1] - 29 if timespan == "month" else 0))
        if timespan == "year":
            normalized = current.replace(month = 1, day = 1)
            upper_bound = upper_bound.replace(month = 12, day = monthrange(current.year, 12)[1])

        results.append({
            "title": normalized.strftime(TimestampFormats[timespan]),
            "value": db.get_pulse(round(normalized.timestamp()), round(upper_bound.timestamp()))
        })
        current -= timedelta(
            (366 if isleap(current.year) else 365) if timespan == "year" else 0 + total_offset
        )

    results.reverse()
    return JSONResponse({
        "code": 200,
        "data": results
    })
