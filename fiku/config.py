# Copyright (c) 2024 iiPython

# Modules
import orjson
from pathlib import Path

# Initialization
data_path = Path.home() / ".local/share/fiku"
data_path.mkdir(parents = True, exist_ok = True)

config_path = data_path / "config.json"
if not config_path.is_file():
    exit(f"fiku: missing config file in {data_path}!")

# Handle configuration
class FikuDictWrapper():
    def __init__(self, value: dict) -> None:
        for k, v in value.items():
            setattr(self, k, v if not isinstance(v, dict) else FikuDictWrapper(v))

class FikuConfig():
    def __init__(self) -> None:
        for k, v in orjson.loads(config_path.read_text()).items():
            setattr(self, k, v if not isinstance(v, dict) else FikuDictWrapper(v))

config = FikuConfig()
