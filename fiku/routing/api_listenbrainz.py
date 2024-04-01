# Copyright (c) 2024 iiPython

# Modules
from typing import Annotated

from fastapi import Header
from fastapi.responses import JSONResponse

from fiku import db, config, app
from fiku.models.listenbrainz import LBSubmitModel

# Routes
@app.post("/api/listenbrainz/1/submit-listens")
async def api_listenbrainz_submit(
    authorization: Annotated[str, Header()],
    listen_data: LBSubmitModel
) -> JSONResponse:
    if authorization != config.authorization:
        return JSONResponse({"code": 401}, status_code = 401)

    match listen_data.listen_type:
        case "playing_now":
            db.set_playing_now(listen_data.payload[0])

        case "single":
            for scrobble in listen_data.payload:
                db.submit_scrobble(scrobble)

    return JSONResponse({"code": 200})
