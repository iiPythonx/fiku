# Copyright (c) 2024 iiPython

# Modules
import time
import orjson
import sqlite3

from typing import List, Literal

from .config import data_path
from .models.listenbrainz import LBPayloadModel

# Initialization
TIMESPAN_VALUES = {
    "day": 86400,
    "week": 604800,
    "month": 2629746,
    "year": 31556952
}

# Database class
class FikuDB():
    def __init__(self) -> None:
        self.conn = sqlite3.connect(data_path / "db.sqlite3")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Setup initial tables
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS scrobbles (
            listened_at     INTEGER,
            artist_name     TEXT,
            track_name      TEXT,
            release_name    TEXT,
            additional      TEXT
        )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS authorization (
            service        TEXT,
            authorization  TEXT
        )""")

        # Handle 'now playing'
        self._playing_now = None

    def submit_scrobble(self, scrobble: LBPayloadModel) -> None:
        self.cursor.execute(
            "INSERT INTO scrobbles VALUES (?, ?, ?, ?, ?)",
            (
                scrobble.listened_at,
                scrobble.track_metadata.artist_name,
                scrobble.track_metadata.track_name,
                scrobble.track_metadata.release_name,
                orjson.dumps(scrobble.track_metadata.additional_info.model_dump(mode = "json"))
            )
        )
        self.conn.commit()

    def set_playing_now(self, playing_now: LBPayloadModel) -> None:
        self._playing_now = playing_now

    def get_playing_now(self) -> LBPayloadModel | None:
        return self._playing_now
    
    def get_recent_scrobbles(self, limit: int = 12) -> List[dict]:
        self.cursor.execute("SELECT * FROM scrobbles ORDER BY listened_at DESC LIMIT ?", (limit,))
        return [
            { **scrobble, **{"additional": orjson.loads(scrobble["additional"])} }
            for scrobble in self.cursor.fetchall()
        ]
    
    def get_scrobbles_of(
        self,
        artist: str,
        item_type: Literal["artist", "track", "album"],
        item_name: str
    ) -> int:
        item_type = {"artist": "artist_name", "track": "track_name", "album": "release_name"}[item_type]

        # Send off SQL query
        extra = f"AND {item_type} = ?" if item_type != "artist" else ""
        self.cursor.execute(
            f"SELECT COUNT(*) FROM scrobbles WHERE artist_name = ? {extra}",
            (artist, item_name) if item_type != "artist" else (artist,)
        )
        return self.cursor.fetchone()[0]

    def get_artist_albums(self, artist: str) -> List[str]:
        self.cursor.execute("SELECT release_name FROM scrobbles WHERE artist_name = ? GROUP BY release_name", (artist,))
        return [x["release_name"] for x in self.cursor.fetchall()]

    def get_top_tracks(self, artist: str, album: str | None = None) -> List[dict]:
        extra = "AND release_name = ?" if album is not None else ""
        self.cursor.execute(
            f"SELECT track_name, release_name, COUNT(*) as count FROM scrobbles WHERE artist_name = ? {extra} GROUP BY track_name ORDER BY COUNT(track_name) DESC LIMIT 16",
            (artist,) if album is None else (artist, album)
        )
        return [
            {"track": x["track_name"], "album": x["release_name"], "count": x["count"]}
            for x in self.cursor.fetchall()
        ]

    def get_top_items(
        self,
        item_type: Literal["artist", "track", "album"],
        limit: int = 14,
        timespan: str = "all"
    ) -> List[dict]:
        upper_bound = time.time()
        lower_bound = (upper_bound - TIMESPAN_VALUES[timespan]) if timespan != "all" else 0

        # This seems sketchy I know, although there's no possibility for SQL injection right here.
        # Additionally, using ? doesn't seem to let me control grouping dynamically.
        item_type = {"artist": "artist_name", "track": "track_name", "album": "release_name"}[item_type]
        self.cursor.execute(
            f"SELECT artist_name, track_name, release_name FROM scrobbles WHERE listened_at BETWEEN ? and ? GROUP BY {item_type} ORDER BY COUNT({item_type}) DESC LIMIT ?",
            (lower_bound, upper_bound, limit)
        )
        return [
            {
                "artist": x["artist_name"],
                "track": x["track_name"],
                "album": x["release_name"]
            }
            for x in self.cursor.fetchall()
        ]
    
    def get_pulse(
        self,
        lower_bound: int,
        upper_bound: int,
        artist: str | None = None,
        album: str | None = None,
        track: str | None = None
    ) -> int:
        filters, bindings = "" if artist is None else "AND artist_name = ?", \
            [lower_bound, upper_bound] if artist is None else [lower_bound, upper_bound, artist]

        if (track or album):
            filters += " AND {} = ?".format("track_name" if track is not None else "release_name")
            bindings.append(track or album)

        self.cursor.execute(
            f"SELECT COUNT(*) FROM scrobbles WHERE listened_at BETWEEN ? and ? {filters}",
            bindings
        )
        return self.cursor.fetchone()[0]

    # Handle authorization
    def get_authorization(self, service: str) -> str | None:
        self.cursor.execute("SELECT authorization FROM authorization WHERE service = ?", (service,))
        return (self.cursor.fetchone() or {"authorization": None})["authorization"]
    
    def set_authorization(self, service: str, authorization: str) -> None:
        if self.get_authorization(service) is None:
            self.cursor.execute("INSERT INTO authorization VALUES (?, ?)", (service, authorization))

        else:
            self.cursor.execute("UPDATE authorization SET authorization = ? WHERE service = ?", (service, authorization))

        self.conn.commit()

db = FikuDB()
