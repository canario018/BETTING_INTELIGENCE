from __future__ import annotations

import requests


class BaseSportsbookCollector:
    def __init__(self, sportsbook_name: str, api_endpoint: str):
        self.sportsbook_name = sportsbook_name
        self.api_endpoint = api_endpoint
        self.last_http_status = None
        self.last_response_bytes = None
        self.last_collected_at = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
        }

    def fetch_raw_data(self):
        response = requests.get(self.api_endpoint, headers=self.headers, timeout=15)
        self.last_http_status = response.status_code
        self.last_response_bytes = len(response.content)
        self.last_collected_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        response.raise_for_status()
        return response.json()

    def normalize_data(self, raw_data):
        return []

    def collect(self):
        return self.normalize_data(self.fetch_raw_data())
