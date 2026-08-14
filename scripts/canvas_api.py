#!/usr/bin/env python3
"""Small, dependency-free Canvas API client for the curriculum mirror."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_BASE = "https://verizoninnovativelearning.instructure.com/api/v1"


class Canvas:
    def __init__(self, base: str = DEFAULT_BASE, token_path: Path | None = None):
        self.base = base.rstrip("/")
        self.token_path = token_path or Path.home() / ".canvas_token"
        self.token = os.environ.get("CANVAS_TOKEN", "").strip()
        if not self.token:
            self.token = self.token_path.read_text(encoding="utf-8").strip()
        if not self.token:
            raise RuntimeError(
                "Canvas token is empty. Set CANVAS_TOKEN or create ~/.canvas_token."
            )

    def request(self, method: str, path: str, data: dict | None = None):
        url = path if path.startswith("http") else self.base + path
        body = None
        headers = {"Authorization": f"Bearer {self.token}"}
        if data is not None:
            body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        for attempt in range(4):
            request = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    raw = response.read()
                    payload = json.loads(raw) if raw else None
                    return payload, response.headers
            except urllib.error.HTTPError as exc:
                if exc.code != 429 and exc.code < 500:
                    raise
                if attempt == 3:
                    raise
                retry_after = exc.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")

    def get(self, path: str):
        payload, _ = self.request("GET", path)
        return payload

    def paged(self, path: str) -> list[dict]:
        rows: list[dict] = []
        next_url = path
        while next_url:
            payload, headers = self.request("GET", next_url)
            if not isinstance(payload, list):
                raise TypeError(f"Expected a list from {next_url}")
            rows.extend(payload)
            next_url = None
            for part in headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";", 1)[0].strip().strip("<>")
                    break
        return rows

    def download(self, url: str) -> bytes:
        for attempt in range(4):
            request = urllib.request.Request(
                url, headers={"Authorization": f"Bearer {self.token}"}
            )
            try:
                with urllib.request.urlopen(request, timeout=300) as response:
                    return response.read()
            except (urllib.error.HTTPError, urllib.error.URLError) as exc:
                if isinstance(exc, urllib.error.HTTPError):
                    if exc.code != 429 and exc.code < 500:
                        raise
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")


def stable_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def env_course_id(default: int = 23402) -> int:
    return int(os.environ.get("VILS_CANVAS_COURSE_ID", default))
