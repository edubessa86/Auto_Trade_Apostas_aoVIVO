from playwright.sync_api import sync_playwright
from datetime import datetime
import random
import time

# ============================================================================
# CONFIGURAÇÕES DO BINGO EM CASA - MODO TESTE
# ============================================================================
BASE_URL = 'https://bingoemcasa12.com/pt-BR/sportsbook/bets'

# Credenciais
CREDENTIALS = {
    'email': '21996963606',
    'password': 'Edu86K@88'
}

# ============================================================================
# FUNÇÃO DE LOGIN
# ============================================================================
def login_bingo_em_casa(page):
    """
    Realiza login no Bingo em Casa
    """
    print("\n🔐 Iniciando login no Bingo em Casa...")
    
    try:
        # Aguarda carregamento completo
        page.wait_for_load_state('networkidle', timeout=15000)
        time.sleep(2)
        
        # Campo de EMAIL/CELULAR
        email_input = page.locator('input[id*="identifier"], input[placeholder*="e-mail"], input[placeholder*="celular"]').first
        
        if not email_input.is_visible(timeout=5000):
            print("⚠️ Procurando campo de email com seletores alternativos...")
            email_input = page.locator('input[type="email"], input[type="text"]').nth(0)
        
        email_input.scroll_into_view_if_needed()
        email_input.click()
        time.sleep(0.5)
        email_input.fill(CREDENTIALS['email'])
        print(f"✅ Email/Celular inserido: {CREDENTIALS['email']}")
        
        # Campo de SENHA
        password_input = page.locator('input[type="password"]').first
        password_input.scroll_into_view_if_needed()
        password_input.click()
        time.sleep(0.5)
        password_input.fill(CREDENTIALS['password'])
        print(f"✅ Senha inserida")
        
        # Botão ENTRAR
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
        
        # Aguarda após login
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        try:
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
# FUNÇÃO PARA INSPECIONAR JOGOS (MODO TESTE)
# ============================================================================
def inspect_games_test_mode(page):
    """
    Modo teste: apenas lista os jogos encontrados sem processar
    """
    print("\n" + "="*70)
    print("🧪 MODO TESTE - INSPEÇÃO DE JOGOS")
    print("="*70 + "\n")
    
    running = True
    page_num = 1
    total_games = 0
    
    while running:
        try:
            print(f"\n📄 Página {page_num}:")
            print("-" * 70)
            
            time.sleep(2)
            
            # Procura por elementos de jogos
            matches = page.locator('[class*="match"], [class*="event"], [class*="game"], [class*="aposta"]')
            match_num = matches.count()
            
            if match_num == 0:
                print("⏳ Nenhum jogo encontrado. Aguardando...")
                time.sleep(3)
                continue
            
            print(f"✅ Encontrados {match_num} jogos\n")
            
            for i in range(min(match_num, 5)):  # Mostra até 5 jogos por página
                try:
                    match_element = matches.nth(i)
                    match_element.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    
                    match_text = match_element.text_content()
                    # Limpa e formata o texto
                    clean_text = ' '.join(match_text.split())[:150]
                    
                    print(f"🎮 Jogo {total_games + i + 1}:")
                    print(f"   {clean_text}...")
                    
                    # Tira screenshot do jogo
                    try:
                        match_element.screenshot(path=f"game_{total_games + i + 1}.png")
                        print(f"   📸 Screenshot salvo: game_{total_games + i + 1}.png")
                    except:
                        pass
                    
                    print()
                
                except Exception as e:
                    print(f"❌ Erro ao inspecionar jogo: {e}\n")
                    continue
            
            total_games += min(match_num, 5)
            
            # Tenta ir para próxima página
            print("\n⏳ Procurando botão de próxima página...")
            try:
                next_button = page.locator('button:has-text("Próximo"), a[class*="next"], button[class*="next"]').first
                if next_button.is_visible(timeout=2000) and next_button.is_enabled():
                    next_button.click()
                    print("✅ Próxima página clicada\n")
                    page_num += 1
                    time.sleep(2)
                else:
                    print("✅ Última página alcançada")
                    running = False
            except:
                print("✅ Última página alcançada")
                running = False
        
        except Exception as e:
            print(f"❌ Erro: {e}")
            running = False
    
    print("\n" + "="*70)
    print(f"✅ INSPEÇÃO CONCLUÍDA")
    print(f"📊 Total de jogos encontrados: {total_games}")
    print("="*70 + "\n")


# ============================================================================
# FUNÇÃO PRINCIPAL - MODO TESTE
# ============================================================================
def main_test_mode():
    """
    Executa o bot em modo teste
    """
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
            
            # Login
            if not login_bingo_em_casa(page):
                print("❌ Login falhou")
                return
            
            # Modo teste: inspeciona jogos
            inspect_games_test_mode(page)
            
            print("\n✅ Teste concluído!")
            print("📝 Próximos passos:")
            print("   1. Verifique os screenshots dos jogos gerados")
            print("   2. Rode os scrapers para gerar CSVs de previsão")
            print("   3. Execute o bot final: python BingoEmCasa_Bot_Final.py")
            
            input("\n🔴 PRESSIONE ENTER PARA SAIR...")
        
        except Exception as e:
            print(f"❌ Erro fatal: {e}")
        
        finally:
            browser.close()


# ============================================================================
# MENU
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🤖 BINGO EM CASA - BOT TESTE")
    print("="*70)
    print("\n📌 Este é o MODO TESTE que:")
    print("   ✅ Faz login no Bingo em Casa")
    print("   ✅ Localiza os jogos/partidas")
    print("   ✅ Lista os jogos encontrados")
    print("   ✅ Tira screenshots para inspeção")
    print("   ❌ Não coloca apostas (apenas visualiza)")
    print("\n⚠️  Após este teste, você precisa rodar os scrapers")
    print("   para gerar os CSVs de previsão\n")
    
    main_test_mode()
