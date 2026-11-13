"""Именованные сессии: один JSON-файл на диалог."""
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile


class Session:
    def __init__(self, directory, name, secret=""):
        reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                    *(f"LPT{i}" for i in range(1, 10))}
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name) or name.upper() in reserved:
            raise ValueError("ID сессии: 1–64 латинские буквы, цифры, дефис или подчёркивание.")
        self.path = Path(directory) / (name + ".json")
        self.secret = secret

    def load(self, prompt):
        system = {"role": "system", "content": prompt}
        if not self.path.exists():
            return [system]
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not all(isinstance(m, dict) and
                m.get("role") in ("user", "system", "tool", "assistant") for m in data):
            raise ValueError("Некорректный формат файла сессии.")
        return [system] + [m for m in data if m["role"] != "system"]

    def save(self, messages):
        def clean(value):
            if isinstance(value, str) and self.secret:
                return value.replace(self.secret, "[скрыто]")
            if isinstance(value, list):
                return [clean(v) for v in value]
            if isinstance(value, dict):
                return {k: clean(v) for k, v in value.items()}
            return value

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=self.path.parent, suffix=".tmp", delete=False,
                                mode="w", encoding="utf-8") as tmp:
            name = tmp.name
            try:
                json.dump(clean(messages), tmp, ensure_ascii=False, indent=2)
            except BaseException:
                tmp.close()
                Path(name).unlink(missing_ok=True)
                raise
        try:
            os.replace(name, self.path)
        finally:
            Path(name).unlink(missing_ok=True)
