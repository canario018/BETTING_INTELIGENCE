from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests

from app.collectors.base import BaseSportsbookCollector
from app.collectors.schemas import OddPayload
from app.normalization.normalizer import build_raw_key, clean_text


class AltenarCouponCollector(BaseSportsbookCollector):
    """Coletor oficial do pipeline para payloads Altenar/GetCouponEvents.

    A estrutura é: events -> marketIds -> markets -> oddIds -> odds,
    com tabelas auxiliares de sports/champs/competitors.
    """

    ENDPOINT = "https://sb2frontend-altenar2.biahosted.com/api/widget/GetCouponEvents"

    MARKET_TYPES = {
        1: "MATCH_RESULT",
        10: "DOUBLE_CHANCE",
        11: "DRAW_NO_BET",
        18: "TOTAL_GOALS",
        29: "BOTH_TEAMS_TO_SCORE",
    }

    def __init__(self, sportsbook_name: str, integration: str, referer: str):
        super().__init__(sportsbook_name=sportsbook_name, api_endpoint=self.ENDPOINT)
        self.integration = integration
        self.referer = referer
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": referer,
        }

    def fetch_raw_data(self) -> dict[str, Any]:
        start_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT03:00:00.000Z")
        params = {
            "culture": "pt-BR",
            "timezoneOffset": 180,
            "integration": self.integration,
            "deviceType": 1,
            "numFormat": "en-GB",
            "countryCode": "BR",
            "eventCount": 0,
            "sportId": 66,
            "couponType": 3,
            "startDate": start_date,
        }
        response = requests.get(self.api_endpoint, headers=self.headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"Resposta inesperada da {self.sportsbook_name}: esperado objeto JSON")
        return data

    @staticmethod
    def _index(items: list[dict[str, Any]] | None) -> dict[Any, dict[str, Any]]:
        return {item.get("id"): item for item in (items or []) if isinstance(item, dict) and item.get("id") is not None}

    @staticmethod
    def _split_event_name(name: str, competitors: list[dict[str, Any]]) -> tuple[str, str]:
        if len(competitors) >= 2:
            return clean_text(competitors[0].get("name", "Home")), clean_text(competitors[1].get("name", "Away"))
        parts = re.split(r"\s+vs\.?\s+|\s+-\s+", clean_text(name), maxsplit=1, flags=re.I)
        if len(parts) == 2:
            return parts[0], parts[1]
        return clean_text(name) or "Home", "Away"

    @classmethod
    def _market_type(cls, market: dict[str, Any]) -> str:
        return cls.MARKET_TYPES.get(market.get("typeId"), "OTHER")

    @staticmethod
    def _selection_code(market_type: str, odd: dict[str, Any]) -> str:
        type_id = odd.get("typeId")
        name = clean_text(str(odd.get("name", ""))).lower()

        if market_type == "MATCH_RESULT":
            return {1: "HOME", 2: "DRAW", 3: "AWAY"}.get(type_id, "OTHER")
        if market_type == "TOTAL_GOALS":
            if type_id == 12 or "mais de" in name or "over" in name:
                return "OVER"
            if type_id == 13 or "menos de" in name or "under" in name:
                return "UNDER"
        if market_type == "BOTH_TEAMS_TO_SCORE":
            if type_id == 74 or name == "sim" or name == "yes":
                return "YES"
            if type_id == 76 or name == "não" or name == "nao" or name == "no":
                return "NO"
        if market_type == "DRAW_NO_BET":
            return {1: "HOME", 3: "AWAY"}.get(type_id, "OTHER")
        if market_type == "DOUBLE_CHANCE":
            return {9: "HOME_OR_DRAW", 10: "HOME_OR_AWAY", 11: "DRAW_OR_AWAY"}.get(type_id, "OTHER")
        return f"TYPE_{type_id}" if type_id is not None else "OTHER"

    @staticmethod
    def _extract_line(selection_name: str) -> float | None:
        match = re.search(r"(?:over|under|mais de|menos de|mais|menos)\s*([0-9]+(?:[.,][0-9]+)?)", selection_name, re.I)
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            return None

    def normalize_data(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        events = raw_data.get("events", [])
        markets = self._index(raw_data.get("markets"))
        odds = self._index(raw_data.get("odds"))
        sports = self._index(raw_data.get("sports"))
        champs = self._index(raw_data.get("champs"))
        competitors_index = self._index(raw_data.get("competitors"))

        records: list[dict[str, Any]] = []
        collected_at = datetime.now(timezone.utc)

        for event in events:
            if not isinstance(event, dict):
                continue
            event_id = event.get("id")
            if event_id is None:
                continue

            event_competitors = [
                competitors_index[cid]
                for cid in event.get("competitorIds", [])
                if cid in competitors_index
            ]
            event_name = clean_text(event.get("name", ""))
            home_team, away_team = self._split_event_name(event_name, event_competitors)
            sport = clean_text(sports.get(event.get("sportId"), {}).get("name", "Futebol"))
            league = clean_text(champs.get(event.get("champId"), {}).get("name", "Geral"))

            for market_id in event.get("marketIds", []):
                market = markets.get(market_id)
                if not market:
                    continue
                market_name = clean_text(market.get("name", "Mercado"))
                market_type = self._market_type(market)

                for odd_id in market.get("oddIds", []):
                    odd = odds.get(odd_id)
                    if not odd:
                        continue
                    price = odd.get("price", odd.get("val", odd.get("p")))
                    try:
                        price = float(price)
                    except (TypeError, ValueError):
                        continue
                    if price <= 1.0:
                        continue

                    selection_name = clean_text(odd.get("name", ""))
                    selection_code = self._selection_code(market_type, odd)
                    line = self._extract_line(selection_name)
                    raw_key = build_raw_key(
                        self.sportsbook_name, event_id, market_type,
                        home_team, away_team, selection_code, line
                    )
                    payload = {
                        "collected_at": collected_at,
                        "bookmaker": self.sportsbook_name,
                        "source_url": self.ENDPOINT,
                        "sport": sport,
                        "league": league,
                        "event_id": str(event_id),
                        "home_team": home_team,
                        "away_team": away_team,
                        "market_name": market_name,
                        "market_type": market_type,
                        "selection_name": selection_name,
                        "selection_code": selection_code,
                        "line": line,
                        "odd": price,
                        "currency": "BRL",
                        "raw_key": raw_key,
                    }
                    try:
                        records.append(OddPayload.model_validate(payload).model_dump())
                    except Exception:
                        continue

        return records
