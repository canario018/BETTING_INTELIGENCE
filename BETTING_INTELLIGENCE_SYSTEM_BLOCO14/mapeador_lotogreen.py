import json

def extrair_odds_definitivo():
    print("Processando odds e eventos da Lotogreen...")
    
    try:
        with open("resposta_bruta_lotogreen.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            
        champs_dict = {champ["id"]: champ.get("name", "Liga") for champ in dados.get("champs", [])}
        
        # Mapeia as odds considerando as chaves padrão da Altenar (ex: id -> price/val)
        odds_dict = {}
        for odd in dados.get("odds", []):
            o_id = odd.get("id")
            o_price = odd.get("price", odd.get("val", odd.get("p", None)))
            if o_id and o_price:
                odds_dict[o_id] = o_price

        eventos = dados.get("events", [])
        
        print(f"\n[Sucesso] {len(eventos)} eventos mapeados com cotações:\n")
        print("=" * 115)
        print(f"{'CAMPEONATO':<25} | {'PARTIDA':<35} | {'DATA/HORA':<17} | {'ODDS (1X2 / PRINCIPAL)'}")
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
            
            # Se não achou pelo marketIds direto, tenta buscar nas ofertas/mercados internos
            if not precos and "markets" in dados:
                for m in dados["markets"]:
                    if m.get("eventId") == evento.get("id"):
                        for o in m.get("odds", []):
                            p = o.get("price", o.get("val"))
                            if p:
                                precos.append(str(p))

            str_odds = " | ".join(precos[:3]) if precos else "Disponíveis no JSON"

            print(f"{campeonato[:23]:<25} | {partida[:33]:<35} | {data_hora:<17} | {str_odds}")

        print("=" * 115)
        print("\nMapeamento de odds concluído com sucesso! Pronto para integrar ao seu modelo +EV.")

    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    extrair_odds_definitivo()