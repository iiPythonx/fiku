# Copyright (c) 2024 iiPython

# Modules
from typing import List, Literal
from pydantic import BaseModel

# Models
class LBAdditionalInfoModel(BaseModel):
    duration_ms: int
    release_mbid: str
    artist_mbids: List[str]
    recording_mbid: str
    tags: List[str] | None = None
    tracknumber: int | None = None

    # Handle client
    submission_client: str | None = None
    submission_client_version: str | None = None

class LBTrackMetadataModel(BaseModel):
    additional_info: LBAdditionalInfoModel | None = None
    artist_name: str
    track_name: str
    release_name: str

class LBPayloadModel(BaseModel):
    listened_at: int | None = None
    track_metadata: LBTrackMetadataModel

class LBSubmitModel(BaseModel):
    listen_type: Literal["single", "playing_now"]
    payload: List[LBPayloadModel]