from __future__ import annotations

import requests


class BaseSportsbookCollector:
    def __init__(self, sportsbook_name: str, api_endpoint: str):
        self.sportsbook_name = sportsbook_name
        self.api_endpoint = api_endpoint
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
        }

    def fetch_raw_data(self):
        response = requests.get(self.api_endpoint, headers=self.headers, timeout=15)
        response.raise_for_status()
        return response.json()

    def normalize_data(self, raw_data):
        return []

    def collect(self):
        return self.normalize_data(self.fetch_raw_data())
