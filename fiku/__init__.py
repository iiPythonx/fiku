# Copyright (c) 2024 iiPython

# Modules
import aiohttp
from fastapi import FastAPI

from .config import config  # noqa: F401
from .database import db  # noqa: F401

# Initialization
app = FastAPI()
session = aiohttp.ClientSession()

# Routing
from .routing import (  # noqa: E402
    api_generic,        # noqa: F401
    api_listenbrainz,   # noqa: F401
    api_frontend        # noqa: F401
)
