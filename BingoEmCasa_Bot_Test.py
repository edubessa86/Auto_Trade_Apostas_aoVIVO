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
        page.wait_for_load_state('networkidle', timeout=20000)
        time.sleep(2)

        # Campo de EMAIL/CELULAR
        email_input = page.locator('input[id*="identifier"], input[placeholder*="e-mail"], input[placeholder*="celular"]').first
        if not email_input.is_visible(timeout=3000):
            email_input = page.locator('input[type="email"], input[type="text"]').nth(0)

        if email_input.is_visible(timeout=3000):
            email_input.scroll_into_view_if_needed()
            email_input.click()
            time.sleep(0.5)
            email_input.fill(CREDENTIALS['email'])
            print(f"✅ Email/Celular inserido: {CREDENTIALS['email']}")
        else:
            print("⚠️ Campo de email não visível. Tentando continuar...")

        # Campo de SENHA
        password_input = page.locator('input[type="password"]').first
        if password_input.is_visible(timeout=3000):
            password_input.scroll_into_view_if_needed()
            password_input.click()
            time.sleep(0.5)
            password_input.fill(CREDENTIALS['password'])
            print("✅ Senha inserida")
        else:
            print("⚠️ Campo de senha não visível")

        # Botão ENTRAR
        candidates = [
            'button:has-text("Entrar")',
            'button:has-text("Log in")',
            'button[type="submit"]',
            'button[class*="login"]',
            'button[class*="primary"]',
        ]

        clicked = False
        for selector in candidates:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    print(f"✅ Botão encontrado com seletor: {selector}")
                    try:
                        btn.click(force=True, timeout=15000)
                    except:
                        btn.evaluate("el => el.click()")
                    clicked = True
                    break
            except Exception:
                pass

        if not clicked:
            print("⚠️ Nenhum botão de login clicável encontrado.")
            print("ℹ️ Pode ser que o login já esteja aberto no modal. Tente concluir manualmente.")
            input("🔴 PRESSIONE ENTER APÓS FAZER LOGIN MANUALMENTE...")
            return True

        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=20000)

        # Se o modal ainda estiver ativo, tenta fechar
        for selector in ['button[aria-label="Close"], button:has-text("Fechar"), [data-dismiss="modal"], [class*="close"]']:
            try:
                close_btn = page.locator(selector).first
                if close_btn.is_visible(timeout=2000):
                    close_btn.click(force=True, timeout=5000)
                    break
            except Exception:
                pass

        # Verifica login
        try:
            page.wait_for_selector('[class*="sport"], [class*="competition"], [class*="match"], section', timeout=10000)
            print("\n✅ >>> LOGIN REALIZADO COM SUCESSO! <<<\n")
            return True
        except Exception:
            print("\n⚠️ Login pode ter falhado; tentando continuar manualmente...")
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

            # Seletor mais amplo para não depender de uma estrutura rígida
            selectors = [
                '[class*="match"]',
                '[class*="event"]',
                '[class*="fixture"]',
                '[class*="offer"]',
                '[class*="game"]',
                'article',
                'li',
                'div'
            ]

            candidates = []
            for selector in selectors:
                try:
                    loc = page.locator(selector)
                    if loc.count() > 0:
                        candidates.append(loc)
                except Exception:
                    pass

            if not candidates:
                print("⏳ Nenhum candidato de jogo encontrado.")
                time.sleep(3)
                continue

            found = []
            for loc in candidates:
                try:
                    count = loc.count()
                    for i in range(min(count, 25)):
                        el = loc.nth(i)
                        try:
                            text = el.text_content(timeout=2000)
                        except Exception:
                            continue
                        if not text:
                            continue
                        clean = ' '.join(text.split())
                        if len(clean) < 8:
                            continue
                        if any(token in clean.lower() for token in ['vs', 'x', ':', 'h2h', 'live']):
                            found.append(clean[:200])
                except Exception:
                    continue

            # remove duplicados
            uniq = []
            for item in found:
                if item not in uniq:
                    uniq.append(item)

            if not uniq:
                print("⏳ Nenhum jogo com conteúdo útil encontrado.")
                time.sleep(3)
                continue

            print(f"✅ Encontrados {len(uniq)} blocos relevantes\n")

            for idx, item in enumerate(uniq[:5], start=1):
                print(f"🎮 Bloco {idx}:")
                print(f"   {item}")
                print()

            total_games += len(uniq[:5])

            # Tenta ir para próxima página
            print("\n⏳ Procurando botão de próxima página...")
            next_candidates = [
                'button:has-text("Próximo")',
                'button:has-text("Next")',
                'a:has-text("Próximo")',
                'a[class*="next"]',
                'button[class*="next"]'
            ]

            next_found = False
            for selector in next_candidates:
                try:
                    nxt = page.locator(selector).first
                    if nxt.is_visible(timeout=2000):
                        nxt.click(force=True, timeout=5000)
                        next_found = True
                        print("✅ Próxima página clicada\n")
                        page_num += 1
                        time.sleep(2)
                        break
                except Exception:
                    pass

            if not next_found:
                print("✅ Última página alcançada")
                running = False

        except Exception as e:
            print(f"❌ Erro: {e}")
            running = False

    print("\n" + "="*70)
    print(f"✅ INSPEÇÃO CONCLUÍDA")
    print(f"📊 Total de blocos relevantes encontrados: {total_games}")
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
            page.screenshot(path='bingo_home_debug.png')

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
