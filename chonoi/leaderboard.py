"""Persistent local top-ten leaderboard (TICKET-04 extension)."""

import json
import os

DEFAULT_STORE = "leaderboard.json"


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError("leaderboard store must contain an entries array")
    for item in entries:
        if (not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip()
                or not isinstance(item.get("score"), int) or isinstance(item.get("score"), bool)
                or not isinstance(item.get("days_completed"), int)
                or not isinstance(item.get("seed"), int)):
            raise ValueError("leaderboard entry is invalid")
    return entries


def record(path, name, score, days_completed, seed):
    """Append one result; stable sorting preserves earlier entries on score ties."""
    entries = _read(path)
    entries.append({"name": name, "score": score, "days_completed": days_completed, "seed": seed})
    entries = sorted(entries, key=lambda entry: -entry["score"])[:10]
    _write(path, entries)


def export(path, out_path):
    entries = sorted(_read(path), key=lambda entry: -entry["score"])[:10]
    _write(out_path, entries)


def _write(path, entries):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"entries": entries}, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    os.replace(tmp, path)
