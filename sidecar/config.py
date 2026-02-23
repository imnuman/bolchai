import json
import os
from pathlib import Path
from pydantic import BaseModel


class BolchaiSettings(BaseModel):
    model: str = "gpt-4o"
    api_key: str = ""
    api_base: str = ""
    auto_run: bool = False
    custom_instructions: str = ""
    context_window: int = 128000
    max_tokens: int = 4096
    temperature: float = 0.0

    @classmethod
    def settings_path(cls) -> Path:
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path.home() / ".config"
        path = base / "Bolchai"
        path.mkdir(parents=True, exist_ok=True)
        return path / "settings.json"

    @classmethod
    def load(cls) -> "BolchaiSettings":
        path = cls.settings_path()
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self):
        path = self.settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2))
