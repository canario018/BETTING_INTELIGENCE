from __future__ import annotations

import itertools
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from app.database.models import OddSnapshotModel


@dataclass(frozen=True)
class ArbitrageLeg:
    bookmaker: str
    selection_code: str
    selection_name: str
    odd: float


@dataclass(frozen=True)
class Surebet:
    event_key: str
    home_team: str
    away_team: str
    market_type: str
    line: float | None
    probability_sum: float
    profit_percent: float
    legs: tuple[ArbitrageLeg, ...]


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).strip().lower()
    return text


def _event_key(row: OddSnapshotModel) -> tuple:
    teams = tuple(sorted((_norm(row.home_team), _norm(row.away_team))))
    return (_norm(row.sport), teams, row.market_type, row.line)


def latest_rows(db: Session, lookback_hours: int = 24) -> list[OddSnapshotModel]:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=lookback_hours)
    rows = (
        db.query(OddSnapshotModel)
        .filter(OddSnapshotModel.collected_at >= cutoff)
        .order_by(OddSnapshotModel.collected_at.desc(), OddSnapshotModel.id.desc())
        .all()
    )
    latest: dict[tuple, OddSnapshotModel] = {}
    for row in rows:
        key = (_event_key(row), row.bookmaker, row.selection_code, row.line)
        if key not in latest:
            latest[key] = row
    return list(latest.values())


def _allowed_universe(market_type: str) -> tuple[str, ...] | None:
    if market_type == "MATCH_RESULT":
        return ("HOME", "DRAW", "AWAY")
    if market_type == "TOTAL_GOALS":
        return ("OVER", "UNDER")
    if market_type == "BOTH_TEAMS_TO_SCORE":
        return ("YES", "NO")
    return None


def find_surebets(
    rows: Iterable[OddSnapshotModel],
    min_profit_percent: float = 0.10,
    max_outcomes: int = 3,
) -> list[Surebet]:
    grouped: dict[tuple, list[OddSnapshotModel]] = {}
    for row in rows:
        if row.market_type not in {"MATCH_RESULT", "TOTAL_GOALS", "BOTH_TEAMS_TO_SCORE"}:
            continue
        if row.selection_code == "OTHER" or row.odd <= 1:
            continue
        grouped.setdefault(_event_key(row), []).append(row)

    results: list[Surebet] = []
    for key, group in grouped.items():
        universe = _allowed_universe(key[2])
        if not universe or len(universe) > max_outcomes:
            continue

        by_selection: dict[str, list[OddSnapshotModel]] = {s: [] for s in universe}
        for row in group:
            if row.selection_code in by_selection:
                by_selection[row.selection_code].append(row)

        # Um surebet só é considerada se todas as saídas do universo conhecido
        # estiverem presentes. Isso evita falso positivo com um 1X2 incompleto.
        if any(not by_selection[s] for s in universe):
            continue

        best_combo = None
        for combo in itertools.product(*(by_selection[s] for s in universe)):
            books = [r.bookmaker for r in combo]
            if len(set(books)) != len(books):
                continue
            probability_sum = sum(1.0 / r.odd for r in combo)
            if best_combo is None or probability_sum < best_combo[0]:
                best_combo = (probability_sum, combo)

        if best_combo is None:
            continue

        probability_sum, combo = best_combo
        if probability_sum >= 1.0:
            continue
        profit_percent = (1.0 / probability_sum - 1.0) * 100.0
        if profit_percent < min_profit_percent:
            continue

        first = combo[0]
        legs = tuple(
            ArbitrageLeg(r.bookmaker, r.selection_code, r.selection_name, r.odd)
            for r in combo
        )
        results.append(
            Surebet(
                event_key="|".join(map(str, key)),
                home_team=first.home_team,
                away_team=first.away_team,
                market_type=first.market_type,
                line=first.line,
                probability_sum=probability_sum,
                profit_percent=profit_percent,
                legs=legs,
            )
        )

    return sorted(results, key=lambda x: x.profit_percent, reverse=True)


def analyze_database(db: Session, lookback_hours: int = 24, min_profit_percent: float = 0.10) -> list[Surebet]:
    rows = latest_rows(db, lookback_hours)
    return find_surebets(rows, min_profit_percent=min_profit_percent)
