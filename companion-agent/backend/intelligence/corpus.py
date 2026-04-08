"""Offline corpus manager - fallback when LLM is unavailable."""

from __future__ import annotations

import json
import random
from pathlib import Path

from config import settings


_CORPUS_CACHE: dict[str, list[dict]] = {}


def _load_corpus(name: str) -> list[dict]:
    if name in _CORPUS_CACHE:
        return _CORPUS_CACHE[name]
    path = settings.corpus_dir / f"{name}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    _CORPUS_CACHE[name] = data
    return data


def pick_line(state: str, time_period: str, **kwargs) -> str:
    corpus = _load_corpus(state)
    if not corpus:
        corpus = _load_corpus("companion")
    if not corpus:
        return "嗯，你在。"

    candidates = []
    for entry in corpus:
        cond = entry.get("condition", {})
        match = True
        if "time" in cond and cond["time"] != time_period:
            match = False
        if match:
            candidates.append(entry)

    if not candidates:
        candidates = corpus

    return random.choice(candidates).get("text", "嗯。")
