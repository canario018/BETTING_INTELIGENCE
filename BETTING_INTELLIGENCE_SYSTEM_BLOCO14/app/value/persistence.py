from app.value.models import ValueOpportunityModel, ValueObservationModel

def persist_value_opportunities(db, opportunities):
    count = 0
    for op in opportunities:
        row = ValueOpportunityModel(opportunity_key=op.opportunity_key, detected_at=op.detected_at, canonical_event_id=op.canonical_event_id, bookmaker=op.bookmaker, sport=op.sport, home_team=op.home_team, away_team=op.away_team, market_type=op.market_type, selection_code=op.selection_code, line=op.line, odd=op.odd, implied_probability=op.implied_probability, fair_probability=op.fair_probability, fair_odd=op.fair_odd, edge_percent=op.edge_percent, expected_value_percent=op.expected_value_percent, confidence=op.confidence, source=op.source)
        db.add(row)
        db.add(ValueObservationModel(opportunity_key=op.opportunity_key, observed_at=op.detected_at, bookmaker=op.bookmaker, odd=op.odd, fair_probability=op.fair_probability, fair_odd=op.fair_odd, edge_percent=op.edge_percent, expected_value_percent=op.expected_value_percent, confidence=op.confidence))
        count += 1
    db.commit(); return count
