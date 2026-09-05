import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def iniciar_robo_captura():
    print("[1/6] Configurando o navegador com rastreamento de Network (Fetch/XHR)...")
    
    options = webdriver.ChromeOptions()
    # Ativa os logs de performance para monitorar a aba Network
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Opcional: Remova o comentário da linha abaixo caso queira rodar em segundo plano (headless)
    # options.add_argument("--headless=new")
    
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Passo 1: Entrar no Google e buscar / acessar a casa de apostas
        print("[2/6] Acessando o Google e navegando para a casa de apostas...")
        driver.get("https://www.google.com")
        time.sleep(1.5)
        
        # URL alvo (ajuste se estiver testando outra casa, como a Superbet do seu print)
        url_alvo = "https://superbet.bet/apostas/futebol?day=hoje"
        print(f"[3/6] Entrando diretamente em: {url_alvo}")
        driver.get(url_alvo)
        
        # Pausa inicial para o site renderizar a interface visual e pop-ups
        print("Aguardando carregamento inicial da página...")
        time.sleep(4)
        
        wait = WebDriverWait(driver, 10)
        
        # Tratamento de Cookies / Termos (se houver)
        try:
            botao_cookies = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Aceitar') or contains(., 'Permitir') or contains(., 'Concordar')]"))
            )
            driver.execute_script("arguments[0].click();", botao_cookies)
            print("-> Cookies / Termos aceitos.")
            time.sleep(1)
        except Exception:
            print("-> Nenhum pop-up de cookies encontrado ou já aceito.")

        # Passo 2: Clicar no botão/aba "Próximo" (conforme destacado no seu fluxo)
        try:
            print("[4/6] Localizando e clicando na aba 'Próximo'...")
            # Varre variações comuns do botão (Próximo, Próximos, Next)
            botao_proximo = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Próximo') or contains(text(), 'Proximo')] | //button[contains(., 'Próximo')]"))
            )
            driver.execute_script("arguments[0].click();", botao_proximo)
            print("-> Aba 'Próximo' clicada com sucesso!")
        except Exception as e:
            print(f"-> Aviso: Botão 'Próximo' não localizado diretamente ({e}). Prosseguindo com a captura...")

        # Passo 3: Aguardar o tráfego de dados de rede (Fetch/XHR) popularem os campeonatos
        print("[5/6] Aguardando o carregamento dos pacotes de rede (Fetch/XHR)...")
        time.sleep(6)
        
        # Passo 4: Coleta e varredura dos logs de Network
        print("[6/6] Analisando requisições e extraindo URLs de campeonatos/APIs...")
        logs = driver.get_log('performance')
        urls_capturadas = set()
        
        for entry in logs:
            try:
                log_json = json.loads(entry['message'])
                message = log_json.get('message', {})
                
                # Filtra requisições de envio de rede (equivalente ao que passa no Network do F12)
                if message.get('method') == 'Network.requestWillBeSent':
                    request = message.get('params', {}).get('request', {})
                    url = request.get('url', '')
                    
                    # Filtra URLs relevantes de API, campeonatos, eventos, métricas ou odds
                    termos_relevantes = ['/api/', '/sport/', 'soccer', 'events', 'leagues', 'countries', 'prematch', 'markets']
                    if any(termo in url for termo in termos_relevantes):
                        urls_capturadas.add(url)
            except Exception:
                continue
                
        # Exibição organizada no terminal do VS Code
        print("\n" + "="*80)
        print(f"URLs de Fetch/XHR (Campeonatos/APIs) encontradas: {len(urls_capturadas)}")
        print("="*80)
        for i, url in enumerate(sorted(urls_capturadas), 1):
            print(f"{i}. {url}\n")
            
    except Exception as e:
        print(f"Ocorreu um erro durante a execução: {e}")
        
    finally:
        print("Fechando o navegador...")
        driver.quit()

if __name__ == "__main__":
    iniciar_robo_captura()