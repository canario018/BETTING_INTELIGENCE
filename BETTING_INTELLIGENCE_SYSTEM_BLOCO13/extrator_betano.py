import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def iniciar_robo_betano():
    print("[1/6] Configurando o navegador...")
    
    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    try:
        url_alvo = "https://www.betano.bet.br/sport/futebol/jogos-de-hoje/"
        print(f"[2/6] Acessando: {url_alvo}")
        driver.get(url_alvo)
        
        wait = WebDriverWait(driver, 10)
        
        # PASSO 1: Clicar em Permitir Cookies / Cache ("Permitir Todos")
        try:
            print("[3/6] Clicando em Permitir Todos (Cookies/Cache)...")
            botao_cookies = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Permitir Todos')]"))
            )
            driver.execute_script("arguments[0].click();", botao_cookies)
            print("-> Cookies/Cache permitidos!")
            time.sleep(1)
        except Exception as e:
            print(f"-> Aviso nos cookies: {e}")

        # PASSO 2: Clicar em "Permitir" no pop-up de outros dispositivos (se aparecer como alerta nativo ou elemento)
        try:
            print("[4/6] Lidar com a permissão de outros dispositivos...")
            # Tenta via alerta nativo do navegador caso seja um diálogo do sistema
            try:
                alerta = driver.switch_to.alert
                alerta.accept() # Equivalente a clicar em "Permitir"
                print("-> Alerta de dispositivos aceito via nativo!")
            except:
                # Se for um elemento HTML injetado na página
                botao_permitir_app = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Permitir')]"))
                )
                driver.execute_script("arguments[0].click();", botao_permitir_app)
                print("-> Botão Permitir dispositivos clicado na tela!")
            time.sleep(1)
        except Exception as e:
            print(f"-> Aviso no pop-up de dispositivos: {e}")

        # PASSO 3: Clicar em SIM para maior de 18 anos
        try:
            print("[5/6] Clicando em 'SIM' para maior de 18 anos...")
            botao_sim = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'sim', 'SIM')='SIM']"))
            )
            driver.execute_script("arguments[0].click();", botao_sim)
            print("-> Maioridade confirmada (SIM clicado)!")
            time.sleep(2)
        except Exception as e:
            print(f"-> Erro ao clicar no SIM: {e}")

        # PASSO 4: Clicar na aba "Próximos" para gerar os dados de rede
        try:
            print("[6/6] Clicando na aba 'Próximos'...")
            botao_proximos = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Próximos')]"))
            )
            driver.execute_script("arguments[0].click();", botao_proximos)
            print("-> Aba 'Próximos' acionada com sucesso!")
        except Exception as e:
            print(f"-> Erro ao achar o botão 'Próximos': {e}")

        # Aguarda as requisições de API carregarem
        print("Aguardando carregamento dos dados de rede (Network)...")
        time.sleep(5)
        
        # Coleta os logs da aba Network
        logs = driver.get_log('performance')
        urls_capturadas = set()
        
        for entry in logs:
            try:
                log_json = json.loads(entry['message'])
                message = log_json.get('message', {})
                
                if message.get('method') == 'Network.requestWillBeSent':
                    request = message.get('params', {}).get('request', {})
                    url = request.get('url', '')
                    
                    if any(termo in url for termo in ['/api/', '/sport/', 'soccer', 'events', 'leagues']):
                        urls_capturadas.add(url)
            except Exception:
                continue
                
        print("\n" + "="*60)
        print(f"URLs de Fetch/XHR encontradas ({len(urls_capturadas)}):")
        print("="*60)
        for i, url in enumerate(sorted(urls_capturadas), 1):
            print(f"{i}. {url}\n")
            
    except Exception as e:
        print(f"Ocorreu um erro durante a execução: {e}")
        
    finally:
        print("Fechando o navegador...")
        driver.quit()

if __name__ == "__main__":
    iniciar_robo_betano()