import requests
import json
from datetime import datetime, timezone

def atualizar_url_e_buscar_dados():
    print("[1/3] Calculando a data atual para a requisição...")
    
    # Pega a data atual em UTC formatada no padrão exigido pela API da Altenar (ex: 2026-09-07T03:00:00.000Z)
    # Você pode ajustar o horário base se necessário
    data_atual = datetime.now(timezone.utc).strftime("%Y-%m-%dT03:00:00.000Z")
    
    # Monta a URL dinamicamente atualizada
    url_api = f"https://sb2frontend-altenar2.biahosted.com/api/widget/GetCouponEvents?culture=pt-BR&timezoneOffset=180&integration=lotogreen&deviceType=1&numFormat=en-GB&countryCode=BR&eventCount=0&sportId=66&couponType=3&startDate={data_atual}"
    
    print(f"-> URL gerada com sucesso para a data: {data_atual}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://lotogreen.bet.br/"
    }
    
    try:
        print("[2/3] Consultando a API da Lotogreen com a nova URL...")
        response = requests.get(url_api, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            print("-> Dados obtidos com sucesso!")
            
            # [3/3] Salvando os dados atualizados para alimentar seus modelos ou Power BI
            nome_arquivo = "lotogreen_atualizado.json"
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
                
            print(f"-> Arquivo '{nome_arquivo}' atualizado e salvo com sucesso!")
            
            if "Events" in dados:
                print(f"-> Total de eventos carregados nesta varredura: {len(dados['Events'])}")
                
            return dados
        else:
            print(f"-> Erro na requisição. Código de status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"-> Ocorreu um erro na conexão: {e}")
        return None

if __name__ == "__main__":
    atualizar_url_e_buscar_dados()