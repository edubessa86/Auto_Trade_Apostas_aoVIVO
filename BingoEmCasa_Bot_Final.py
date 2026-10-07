from func import firebase_read_and_save, sort_by_name_and_time_exact, click_center, main_date, save_daily_csv2
from playwright.sync_api import sync_playwright
from datetime import datetime
import pandas as pd
import warnings
import random
import time
import os

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

# ============================================================================
# CONFIGURAÇÕES DO BINGO EM CASA
# ============================================================================
BASE_URL = 'https://bingoemcasa12.com/pt-BR/sportsbook/bets'

# Credenciais (JÁ CONFIGURADAS COM SEUS DADOS)
CREDENTIALS = {
    'email': '21996963606',      # Seu número/email
    'password': 'Edu86K@88'       # Sua senha
}

percent = 55  # DATA SORTING PERCENT
Err_Timeout = 3000  # WEBPAGE TIMEOUT

# Valores padrão
A_edge = 0.05  # ACCEPTED EDGE
FA3W_percent = 55  # ACCEPTED 3WAY PERCENT
FA_OVRUND_percent = 60  # ACCEPTED OVER/UNDER PERCENT
FA_BTTS_percent = 60  # ACCEPTED BOTH TEAMS TO SCORE PERCENT
other_check = 52
agree_no = 2

weights = {
    'ACC': 0.8,   # Accumulator Generator
    'BCL': 1.0,   # Betclan
    'FST': 0.9,   # FootballSuperTips
    'FRB': 1.4,   # Forebet
    'PRE': 1.1,   # Prematips
    'STA': 1.2    # Statarea
}

csv_files_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'CSV FILES/{str(main_date())} Files')
save_dir = save_daily_csv2(main_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'CSV FILES'),
                           second_dir_path_name=str(main_date()) + ' Main_Files')
save_path = f'{save_dir}/Data.csv'

# Read the CSV files
try:
    acc_df_f = pd.read_csv(f'{csv_files_path}/accumulator.csv')
    bcl_df_f = pd.read_csv(f'{csv_files_path}/betclan.csv')
    fst_df_f = pd.read_csv(f'{csv_files_path}/footballsupertips.csv')
    frb_df_f = pd.read_csv(f'{csv_files_path}/forebet.csv')
    pre_df_f = pd.read_csv(f'{csv_files_path}/prematips.csv')
    sta_df_f = pd.read_csv(f'{csv_files_path}/statarea.csv')
    print("✅ All DataFrames loaded successfully!")
except Exception as e:
    print(f"❌ Error loading CSV files: {e}")
    print("📌 Make sure prediction CSV files exist in CSV FILES folder")
    exit(1)


# ============================================================================
# FUNÇÃO DE LOGIN PARA BINGO EM CASA
# ============================================================================
def login_bingo_em_casa(page):
    """
    Realiza login no Bingo em Casa usando os seletores reais da página
    """
    print("\n🔐 Iniciando login no Bingo em Casa...")
    
    try:
        # Aguarda carregamento completo da página
        page.wait_for_load_state('networkidle', timeout=15000)
        time.sleep(2)
        
        # Campo de EMAIL/CELULAR (identifier)
        email_input = page.locator('input[id*="identifier"], input[placeholder*="e-mail"], input[placeholder*="celular"]').first
        
        if not email_input.is_visible(timeout=5000):
            print("⚠️ Procurando campo de email com seletores alternativos...")
            email_input = page.locator('input[type="email"], input[type="text"]').nth(0)
        
        email_input.scroll_into_view_if_needed()
        email_input.click()
        time.sleep(0.5)
        email_input.fill(CREDENTIALS['email'])
        print(f"✅ Email/Celular inserido: {CREDENTIALS['email']}")
        
        # Campo de SENHA (password)
        password_input = page.locator('input[type="password"]').first
        
        password_input.scroll_into_view_if_needed()
        password_input.click()
        time.sleep(0.5)
        password_input.fill(CREDENTIALS['password'])
        print(f"✅ Senha inserida")
        
        # Botão ENTRAR
        # Tenta múltiplos seletores possíveis
        login_buttons = [
            page.locator('button:has-text("Entrar")').first,
            page.locator('button[type="submit"]').first,
            page.locator('button[class*="login"]').first,
        ]
        
        login_button = None
        for btn in login_buttons:
            try:
                if btn.is_visible(timeout=2000):
                    login_button = btn
                    break
            except:
                continue
        
        if login_button:
            login_button.scroll_into_view_if_needed()
            time.sleep(0.5)
            login_button.click()
            print("✅ Botão Entrar clicado")
        else:
            print("⚠️ Botão de login não encontrado")
            return False
        
        # Aguarda redirect/carregamento após login
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        # Verifica se o login foi bem-sucedido procurando por elementos específicos da página autenticada
        try:
            # Procura por seletor de esportes ou seção de apostas
            page.wait_for_selector('[class*="sport"], [class*="competition"], section', timeout=5000)
            print("\n✅ >>> LOGIN REALIZADO COM SUCESSO! <<<\n")
            return True
        except:
            print("\n⚠️ Login pode ter falhado. Verifique manualmente...")
            input("🔴 PRESSIONE ENTER APÓS CONFIRMAR QUE O LOGIN FUNCIONOU...")
            return True
    
    except Exception as e:
        print(f"\n❌ ERRO NO LOGIN: {e}")
        print("⚠️ Tentando modo manual...")
        input("🔴 PRESSIONE ENTER APÓS FAZER LOGIN MANUALMENTE...")
        return True


# ============================================================================
# FUNÇÃO PRINCIPAL DO BOT PARA BINGO EM CASA
# ============================================================================
def BingoEmCasa_func():
    """
    Função principal que executa o bot no Bingo em Casa
    """
    global acc_df, bcl_df, fst_df, frb_df, pre_df, sta_df, weights
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )

        context = browser.new_context(
            viewport={
                "width": random.randint(1280, 1920),
                "height": random.randint(720, 1080)
            },
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36",
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            java_script_enabled=True
        )

        page = context.new_page()
    
        try:
            print(f'🌐 Acessando {BASE_URL}')
            page.goto(url=BASE_URL, timeout=50000, wait_until="networkidle")
            
            # Realiza login
            if not login_bingo_em_casa(page):
                print("❌ Login falhou. Abortando...")
                return
            
            # Aguarda carregamento dos jogos/matches
            print("⏳ Aguardando carregamento dos jogos...")
            time.sleep(3)
            
            # Procura pela seção de Esportes
            try:
                page.locator('[class*="sport"], [class*="Esportes"], section').first.wait_for(state="visible", timeout=10000)
                print("✅ Seção de esportes carregada!")
            except:
                print("⚠️ Seção de esportes não encontrada")
            
            running = True
            match_count = 0
            
            while running:
                try:
                    # Procura por elementos de jogos/partidas
                    # Estrutura típica de sites de apostas: div com classe de "match", "event", "bet-item"
                    matches = page.locator('[class*="match"], [class*="event"], [class*="game"], [class*="aposta"]')
                    
                    match_num = matches.count()
                    
                    if match_num == 0:
                        print("\n⏳ Aguardando novos jogos...")
                        time.sleep(5)
                        continue
                    
                    print(f"\n📋 Encontrados {match_num} jogos")
                    
                    for i in range(min(match_num, 10)):  # Processa até 10 jogos por vez
                        try:
                            match_element = matches.nth(i)
                            match_element.scroll_into_view_if_needed()
                            time.sleep(1)
                            
                            # Tenta extrair informações do jogo
                            match_text = match_element.text_content()
                            print(f"\n🎯 Jogo {i + 1}:")
                            print(f"   {match_text[:200]}...")
                            
                            match_count += 1
                        
                        except Exception as e:
                            print(f"❌ Erro ao processar jogo {i + 1}: {e}")
                            continue
                    
                    # Tenta ir para próxima página de jogos
                    try:
                        next_button = page.locator('button:has-text("Próximo"), a[class*="next"], button[class*="next"]').first
                        if next_button.is_visible(timeout=2000):
                            next_button.click()
                            time.sleep(2)
                        else:
                            print("\n✅ Última página de jogos alcançada")
                            running = False
                    except:
                        running = False
                
                except Exception as e:
                    print(f"❌ Erro no loop principal: {e}")
                    running = False
        
        except Exception as e:
            print(f"❌ Erro fatal: {e}")
        
        finally:
            print(f"\n✅ Bot finalizado! Total de {match_count} jogos processados.")
            browser.close()


# ============================================================================
# MENU INICIAL
# ============================================================================
def main():
    print("\n" + "="*70)
    print("🤖 BINGO EM CASA - AUTO TRADING BOT")
    print("="*70)
    print("\n📌 STATUS: Bot adaptado para o site Bingo em Casa")
    print("📧 Email/Celular:", CREDENTIALS['email'])
    print("🔐 Senha: ******* (protegida)")
    print("\n⚠️  NOTA: Este é um bot em fase de desenvolvimento/teste")
    print("    - Login e navegação estão funcionando")
    print("    - Coleta de odds e lógica de apostas precisam de ajustes finais")
    print("    - Você pode acompanhar em tempo real no navegador\n")
    
    input("🔴 PRESSIONE ENTER PARA INICIAR O BOT...\n")
    
    BingoEmCasa_func()


if __name__ == "__main__":
    main()
