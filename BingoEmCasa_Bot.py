
from func import firebase_read_and_save, place_bet, sort_by_name_and_time_exact, click_center, main_date, save_daily_csv2
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
CREDENTIALS = {
    'email': 'seu_email@gmail.com',      # 🔴 COLOQUE SEU EMAIL AQUI
    'password': 'sua_senha'               # 🔴 COLOQUE SUA SENHA AQUI
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
acc_df_f = pd.read_csv(f'{csv_files_path}/accumulator.csv')
bcl_df_f = pd.read_csv(f'{csv_files_path}/betclan.csv')
fst_df_f = pd.read_csv(f'{csv_files_path}/footballsupertips.csv')
frb_df_f = pd.read_csv(f'{csv_files_path}/forebet.csv')
pre_df_f = pd.read_csv(f'{csv_files_path}/prematips.csv')
sta_df_f = pd.read_csv(f'{csv_files_path}/statarea.csv')

print("All DataFrames ready! Bingo em Casa Bot starting...")


# ============================================================================
# FUNÇÃO DE LOGIN PARA BINGO EM CASA
# ============================================================================
def login_bingo_em_casa(page):
    """
    Realiza login no Bingo em Casa
    """
    print("🔐 Iniciando login no Bingo em Casa...")
    
    try:
        # Aguarda campo de email
        page.wait_for_selector('input[type="email"]', timeout=10000)
        email_input = page.locator('input[type="email"]').first
        email_input.fill(CREDENTIALS['email'])
        print(f"✅ Email inserido: {CREDENTIALS['email']}")
        
        # Aguarda campo de senha
        page.wait_for_selector('input[type="password"]', timeout=5000)
        password_input = page.locator('input[type="password"]').first
        password_input.fill(CREDENTIALS['password'])
        print("✅ Senha inserida")
        
        # Clica no botão de login
        login_button = page.locator('button[type="submit"]').first
        login_button.click()
        time.sleep(3)
        
        # Aguarda carregamento da página
        page.wait_for_load_state('networkidle', timeout=15000)
        print("✅ Login realizado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        raise


# ============================================================================
# FUNÇÃO PARA EXTRAIR DADOS DE MATCHES DO BINGO EM CASA
# ============================================================================
def extract_match_data_bingo(page, match_element):
    """
    Extrai dados de um match do Bingo em Casa
    Retorna: (data, hora, time_casa, time_visitante)
    """
    try:
        # Tenta encontrar elementos de dados do match
        # ⚠️ NOTA: Estes seletores podem precisar ser ajustados conforme a estrutura HTML real do site
        
        match_text = match_element.text_content()
        lines = [line.strip() for line in match_text.split('\n') if line.strip()]
        
        # Estrutura esperada pode variar
        data = lines[0] if len(lines) > 0 else None
        time_str = lines[1] if len(lines) > 1 else None
        teams = lines[2] if len(lines) > 2 else None
        
        if not (data and time_str and teams):
            return None
            
        # Parse dos times (formato esperado: "Time_A vs Time_B")
        if ' vs ' in teams.lower():
            home_team, away_team = [t.strip() for t in teams.split('vs')]
        elif ' x ' in teams.lower():
            home_team, away_team = [t.strip() for t in teams.split('x')]
        else:
            return None
        
        return {
            'data': data,
            'hora': time_str,
            'time_casa': home_team,
            'time_visitante': away_team
        }
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados do match: {e}")
        return None


# ============================================================================
# FUNÇÃO PARA EXTRAIR ODDS DO BINGO EM CASA
# ============================================================================
def extract_odds_bingo(page, match_element):
    """
    Extrai as odds (cotações) de um match
    Retorna: {'1': odd_1, 'x': odd_x, '2': odd_2, 'over': odd_over, 'under': odd_under, 'bts': odd_bts, 'ots': odd_ots}
    """
    try:
        odds_data = {}
        
        # ⚠️ NOTA: Ajuste os seletores conforme a estrutura HTML real do Bingo em Casa
        odds_elements = match_element.locator('[class*="odd"], [class*="quota"], [data-odd]')
        
        # Tenta extrair as odds (pode precisar de ajuste)
        for i in range(min(odds_elements.count(), 7)):  # 7 tipos de odds
            try:
                odd_value = odds_elements.nth(i).text_content().strip()
                if i == 0:
                    odds_data['1'] = float(odd_value)
                elif i == 1:
                    odds_data['x'] = float(odd_value)
                elif i == 2:
                    odds_data['2'] = float(odd_value)
                elif i == 3:
                    odds_data['over'] = float(odd_value)
                elif i == 4:
                    odds_data['under'] = float(odd_value)
                elif i == 5:
                    odds_data['bts'] = float(odd_value)
                elif i == 6:
                    odds_data['ots'] = float(odd_value)
            except:
                continue
        
        return odds_data if odds_data else None
        
    except Exception as e:
        print(f"❌ Erro ao extrair odds: {e}")
        return None


# ============================================================================
# FUNÇÃO PARA COLOCAR APOSTA NO BINGO EM CASA
# ============================================================================
def place_bet_bingo(page, odd_value, edge_amt, main_amt=100):
    """
    Coloca uma aposta no Bingo em Casa
    ⚠️ NOTA: Este código precisa ser adaptado à interface real do site
    """
    try:
        print(f"💰 Colocando aposta com odd {odd_value} e edge {edge_amt}...")
        
        amt_to_bet = round((edge_amt * main_amt) + 5)
        
        # Clica no elemento de aposta
        page.click('button[class*="bet"], a[class*="bet"]')
        time.sleep(1)
        
        # Preenche o valor
        stake_input = page.locator('input[placeholder*="alor"], input[placeholder*="Valor"]').first
        if stake_input:
            stake_input.fill(str(amt_to_bet))
            time.sleep(1)
        
        # Confirma a aposta
        confirm_button = page.locator('button[class*="confirm"], button[class*="Confirmar"]').first
        if confirm_button:
            confirm_button.click()
            time.sleep(2)
            print(f"✅ Aposta colocada: R${amt_to_bet}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao colocar aposta: {e}")
        return False


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
            login_bingo_em_casa(page)
            
            # Aguarda carregamento dos matches
            page.wait_for_selector('[class*="match"], [class*="evento"], [data-match]', timeout=15000)
            
            running = True
            match_count = 0
            
            while running:
                try:
                    # Tenta localizar todos os matches na página
                    matches = page.locator('[class*="match-item"], [class*="evento-item"], [class*="bet-item"]')
                    match_num = matches.count()
                    
                    print(f"\n📋 Encontrados {match_num} matches")
                    
                    if match_num == 0:
                        print("✅ Nenhum novo match encontrado. Finalizando...")
                        running = False
                        break
                    
                    # Processa cada match
                    for i in range(match_num):
                        try:
                            match_element = matches.nth(i)
                            match_element.scroll_into_view_if_needed()
                            time.sleep(1)
                            
                            # Extrai dados do match
                            match_data = extract_match_data_bingo(page, match_element)
                            
                            if not match_data:
                                continue
                            
                            print(f"\n🎯 Match {i + 1}: {match_data['time_casa']} vs {match_data['time_visitante']}")
                            print(f"   Data: {match_data['data']} | Hora: {match_data['hora']}")
                            
                            # Verifica se já foi processado
                            pp_target = f"{match_data['data']}-{match_data['hora']}-{match_data['time_casa']}-{match_data['time_visitante']}"
                            
                            try:
                                pp_data_df = pd.read_csv(save_path)['INFO'].to_list()
                            except:
                                pp_data_df = []
                            
                            if pp_target in pp_data_df:
                                print(f"⏭️  Match já foi processado, pulando...")
                                continue
                            
                            # Busca dados nas previsões
                            acc_df = sort_by_name_and_time_exact(acc_df_f, match_data['time_casa'], 
                                                                  match_data['time_visitante'], 
                                                                  match_data['hora'], percent)
                            bcl_df = sort_by_name_and_time_exact(bcl_df_f, match_data['time_casa'], 
                                                                  match_data['time_visitante'], 
                                                                  match_data['hora'], percent)
                            fst_df = sort_by_name_and_time_exact(fst_df_f, match_data['time_casa'], 
                                                                  match_data['time_visitante'], 
                                                                  match_data['hora'], percent)
                            frb_df = sort_by_name_and_time_exact(frb_df_f, match_data['time_casa'], 
                                                                  match_data['time_visitante'], 
                                                                  match_data['hora'], percent)
                            pre_df = sort_by_name_and_time_exact(pre_df_f, match_data['time_casa'], 
                                                                  match_data['time_visitante'], 
                                                                  match_data['hora'], percent)
                            sta_df = sort_by_name_and_time_exact(sta_df_f, match_data['time_casa'], 
                                                                  match_data['time_visitante'], 
                                                                  match_data['hora'], percent)
                            
                            # Aplica pesos
                            acc_df['weight'] = weights['ACC']
                            bcl_df['weight'] = weights['BCL']
                            fst_df['weight'] = weights['FST']
                            frb_df['weight'] = weights['FRB']
                            pre_df['weight'] = weights['PRE']
                            sta_df['weight'] = weights['STA']
                            
                            # Concatena e calcula consenso
                            all_df = [acc_df, bcl_df, fst_df, frb_df, pre_df, sta_df]
                            old_new_df = pd.concat(all_df, ignore_index=True)
                            new_df = old_new_df.drop_duplicates(subset=['NAME'], keep='first')
                            
                            if len(new_df) >= agree_no:
                                # Calcula probabilidades ponderadas
                                cols_to_convert = ['HOME PER', 'DRAW PER', 'AWAY PER', 'OVER 2_5', 'UNDER 2_5', 'BTS', 'OTS']
                                for col in cols_to_convert:
                                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
                                new_df['weight'] = pd.to_numeric(new_df['weight'], errors='coerce')
                                
                                home_per = round((new_df['HOME PER'] * new_df['weight']).sum() / new_df['weight'].sum(), 2)
                                draw_per = round((new_df['DRAW PER'] * new_df['weight']).sum() / new_df['weight'].sum(), 2)
                                away_per = round((new_df['AWAY PER'] * new_df['weight']).sum() / new_df['weight'].sum(), 2)
                                
                                print(f"📊 Consenso: Casa {home_per}% | Empate {draw_per}% | Visitante {away_per}%")
                                
                                # Extrai odds
                                odds = extract_odds_bingo(page, match_element)
                                
                                if odds:
                                    print(f"💹 Odds disponíveis: {odds}")
                                    
                                    # Verifica oportunidades de aposta
                                    if max(home_per, draw_per, away_per) >= FA3W_percent:
                                        # Lógica de apostas pode ser adicionada aqui
                                        pass
                        
                        except Exception as e:
                            print(f"❌ Erro ao processar match {i + 1}: {e}")
                            continue
                    
                    # Tenta ir para próxima página
                    try:
                        next_button = page.locator('a[class*="next"], button[class*="next"]').first
                        if next_button and next_button.is_enabled():
                            next_button.click()
                            time.sleep(2)
                        else:
                            running = False
                    except:
                        running = False
                
                except Exception as e:
                    print(f"❌ Erro no loop principal: {e}")
                    running = False
        
        except Exception as e:
            print(f"❌ Erro fatal: {e}")
        
        finally:
            browser.close()
            print("\n✅ Bot finalizado!")


# ============================================================================
# EXECUÇÃO
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 BINGO EM CASA - AUTO TRADING BOT")
    print("="*60 + "\n")
    
    BingoEmCasa_func()

