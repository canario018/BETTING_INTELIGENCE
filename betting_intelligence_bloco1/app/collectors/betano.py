import requests
from app.collectors.base import BaseSportsbookCollector

class BetanoCollector(BaseSportsbookCollector):
    def __init__(self, api_endpoint=None):
        # Endpoint padrão capturado no DevTools para futebol/tendências/ligas
        default_endpoint = "https://www.betano.bet.br/api/sports/FOOT/hot/trending/leagues/10008/events"
        super().__init__(sportsbook_name="Betano", api_endpoint=api_endpoint or default_endpoint)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.betano.bet.br/"
        }

    def fetch_raw_data(self):
        # Parâmetros extraídos da sua URL de captura
        params = {
            "req": "s,stnf,c,mb"
        }
        
        try:
            response = requests.get(self.api_endpoint, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            print(f"Erro na API da Betano: {response.status_code}")
            return {}
        except Exception as e:
            print(f"Falha de conexão com a Betano: {e}")
            return {}

    def normalize_data(self, raw_data):
        normalized_records = []
        
        # A Betano costuma estruturar a resposta dentro de blocos de dados ou eventos da liga
        data_block = raw_data.get("data", {})
        events = data_block.get("events", []) or raw_data.get("events", [])
        
        for event in events:
            event_id = event.get("id")
            event_name = event.get("name") or f"{event.get('participants', [{}])[0].get('name')} vs {event.get('participants', [{}][1].get('name', ''))}"
            
            for market in event.get("markets", []):
                market_name = market.get("name")
                
                for selection in market.get("selections", []):
                    selection_name = selection.get("name")
                    odd_value = selection.get("price") or selection.get("odds")
                    
                    if event_id and market_name and odd_value:
                        normalized_records.append({
                            "sportsbook": self.sportsbook_name,
                            "event_id": str(event_id),
                            "event_name": event_name,
                            "market_name": market_name,
                            "selection_name": selection_name,
                            "odd_value": float(odd_value)
                        })
                        
        return normalized_records