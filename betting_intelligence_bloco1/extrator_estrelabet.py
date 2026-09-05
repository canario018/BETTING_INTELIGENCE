import requests
import json
from datetime import datetime, timezone

def extrair_estrelabet():
    print("[1/2] Consultando a API de eventos da EstrelaBet...")
    
    # Gera a data atual no formato da Altenar
    data_atual = datetime.now(timezone.utc).strftime("%Y-%m-%dT03:00:00.000Z")
    
    # URL correta de eventos por cupom da Altenar para a EstrelaBet
    url_api = f"https://sb2frontend-altenar2.biahosted.com/api/widget/GetCouponEvents?culture=pt-BR&timezoneOffset=180&integration=estrelabet&deviceType=1&numFormat=en-GB&countryCode=BR&eventCount=0&sportId=66&couponType=3&startDate={data_atual}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.estrelabet.bet.br/"
    }
    
    try:
        response = requests.get(url_api, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            print("[2/2] Dados obtidos com sucesso! Salvando arquivo bruto...")
            
            with open("resposta_bruta_estrelabet.json", "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            print("-> Arquivo 'resposta_bruta_estrelabet.json' atualizado.")
            
            champs_dict = {champ["id"]: champ.get("name", "Liga") for champ in dados.get("champs", [])}
            
            odds_dict = {}
            for odd in dados.get("odds", []):
                o_id = odd.get("id")
                o_price = odd.get("price", odd.get("val", odd.get("p", None)))
                if o_id and o_price:
                    odds_dict[o_id] = o_price

            eventos = dados.get("events", [])
            print(f"\n[Sucesso] {len(eventos)} eventos encontrados:\n")
            print("=" * 115)
            print(f"{'CAMPEONATO':<25} | {'PARTIDA':<35} | {'DATA/HORA':<17} | {'ODDS DISPONÍVEIS'}")
            print("=" * 115)

            for evento in eventos:
                partida = evento.get("name", "Partida")
                data_hora = evento.get("startDate", "")[:16].replace("T", " ")
                champ_id = evento.get("champId", 0)
                campeonato = champs_dict.get(champ_id, "Liga")
                
                market_ids = evento.get("marketIds", [])
                precos = []
                
                for m_id in market_ids:
                    if m_id in odds_dict:
                        precos.append(str(odds_dict[m_id]))

                str_odds = " | ".join(precos[:3]) if precos else "Disponíveis no JSON"

                print(f"{campeonato[:23]:<25} | {partida[:33]:<35} | {data_hora:<17} | {str_odds}")

            print("=" * 115)
            print("\nMapeamento da EstrelaBet concluído com sucesso!")
            
        else:
            print(f"Erro na requisição: Status {response.status_code}")
            
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    extrair_estrelabet()