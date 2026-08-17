import json
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"
_cache: dict[str, dict[str, str]] = {}


def load_locale(locale: str) -> dict[str, str]:
    if locale not in _cache:
        path = LOCALES_DIR / f"{locale}.json"
        fallback = LOCALES_DIR / "uk.json"
        with open(path if path.exists() else fallback, encoding="utf-8") as f:
            _cache[locale] = json.load(f)
    return _cache[locale]


def t(key: str, locale: str = "uk", **kwargs) -> str:
    messages = load_locale(locale if locale in ("uk", "en") else "uk")
    text = messages.get(key, key)
    return text.format(**kwargs) if kwargs else text
