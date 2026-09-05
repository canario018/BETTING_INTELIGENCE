import requests
import json
from datetime import datetime, timezone

def executar_pipeline_multibet():
    print("[1/4] Consultando o menu de esportes e campeonatos ativos na Multibet...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://multi.bet.br/"
    }
    
    # 1. Requisição do Menu para capturar categorias e esportes dinamicamente
    url_menu = "https://sb2frontend-altenar2.biahosted.com/api/widget/GetClickableSportMenu?culture=pt-BR&timezoneOffset=180&integration=multibet.br&deviceType=1&numFormat=en-GB&countryCode=BR&period=0"
    
    try:
        resp_menu = requests.get(url_menu, headers=headers, timeout=10)
        if resp_menu.status_code == 200:
            dados_menu = resp_menu.json()
            with open("resposta_menu_multibet.json", "w", encoding="utf-8") as f:
                json.dump(dados_menu, f, ensure_ascii=False, indent=4)
            print("-> Menu de esportes mapeado e salvo com sucesso.")
        else:
            print("-> Aviso: Não foi possível baixar o menu, prosseguindo para os eventos...")
    except Exception as e:
        print(f"-> Erro ao consultar o menu: {e}")

    print("\n[2/4] Gerando data atual e consultando a grade de eventos e odds...")
    
    # Gera a data atual no formato dinâmico da Altenar
    data_atual = datetime.now(timezone.utc).strftime("%Y-%m-%dT03:00:00.000Z")
    url_eventos = f"https://sb2frontend-altenar2.biahosted.com/api/widget/GetCouponEvents?culture=pt-BR&timezoneOffset=180&integration=multibet.br&deviceType=1&numFormat=en-GB&countryCode=BR&eventCount=0&sportId=66&couponType=3&startDate={data_atual}"
    
    try:
        response = requests.get(url_eventos, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            print("[3/4] Dados de eventos obtidos com sucesso! Processando...")
            
            # Salva o JSON bruto principal
            with open("resposta_bruta_multibet.json", "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            
            # Dicionários de apoio para traduzir IDs em nomes legíveis
            champs_dict = {champ["id"]: champ.get("name", "Liga") for champ in dados.get("champs", [])}
            
            odds_dict = {}
            for odd in dados.get("odds", []):
                o_id = odd.get("id")
                o_price = odd.get("price", odd.get("val", odd.get("p", None)))
                if o_id and o_price:
                    odds_dict[o_id] = o_price

            eventos = dados.get("events", [])
            print(f"\n[4/4] Exibindo {len(eventos)} confrontos mapeados e prontos para análise +EV:\n")
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
            print("\nPipeline da Multibet executado com sucesso!")
            
        else:
            print(f"Erro na requisição de eventos: Status {response.status_code}")
            
    except Exception as e:
        print(f"Ocorreu um erro no processo: {e}")

if __name__ == "__main__":
    executar_pipeline_multibet()