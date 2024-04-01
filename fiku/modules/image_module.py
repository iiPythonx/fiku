# Copyright (c) 2024 iiPython

# Modules
import sqlite3
from typing import List
from base64 import b64encode

from fastapi.responses import RedirectResponse

from fiku import db, config, session
from fiku.config import data_path

# Handle authorization
async def reauthorize_spotify() -> str:
    authorization = b64encode(f"{config.spotify.app_id}:{config.spotify.app_secret}".encode()).decode()

    async with session.post(
		"https://accounts.spotify.com/api/token",
		headers = {
			"Authorization": f"Basic {authorization}",
			"User-Agent": "Fiku 1.0 https://github.com/iiPythonx/Fiku"
        },
		data = {"grant_type": "client_credentials"}
	) as resp:
        access_token = (await resp.json())["access_token"]
        db.set_authorization("spotify", access_token)
        return access_token

# Handle caching
class FikuImageCache():
    def __init__(self) -> None:
        self.conn = sqlite3.connect(data_path / "image_cache.sqlite3")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Setup initial tables
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS images (
            cache_key       TEXT,
            image_url       TEXT
        )""")

    def _key(self, args: List[str | None]) -> str:
        return ":".join([str(a) for a in args])

    def find(self, *args) -> str | None:
        self.cursor.execute(
            "SELECT image_url FROM images WHERE cache_key = ?",
            (self._key(args),)
        )
        return (self.cursor.fetchone() or {"image_url": None})["image_url"]

    def cache(self, *args, url: str) -> None:
        self.cursor.execute(
            "INSERT INTO images VALUES (?, ?)",
            (self._key(args), url)
        )
        self.conn.commit()

image_cache = FikuImageCache()

# Main methods
async def fetch_image(artist: str, album: str | None, track: str | None) -> RedirectResponse:
    cached_url = image_cache.find(artist, album, track)
    if cached_url is not None:
        return RedirectResponse(cached_url)

    access_token = db.get_authorization("spotify") or await reauthorize_spotify()
    print(access_token)

    search_item = (album or track) or ""
    search_type = (track and "track" or album and "album") or "artist"

    for _ in range(2):
        async with session.get(
            "https://api.spotify.com/v1/search",
            params = {
                "q": f"{search_item} artist:{artist}",
                "type": search_type,
                "access_token": access_token
            }
        ) as response:
            response = await response.json()
            if "error" in response:
                access_token = await reauthorize_spotify()
                print("remade access tkoen")
                continue

            valid_items = response[search_type + "s"]["items"]
            if not valid_items:
                image_cache.cache(artist, album, track, url = "/static/placeholder.png")
                return RedirectResponse("/static/placeholder.png")

            final_url = valid_items[0].get("album", valid_items[0])["images"][0]["url"]
            image_cache.cache(artist, album, track, url = final_url)

            return RedirectResponse(final_url)

    return RedirectResponse("/static/placeholder.png")
