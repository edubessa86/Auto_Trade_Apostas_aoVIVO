import time

# ============================================================================
# LOGIN PARA BINGO EM CASA
# Estrutura específica para o site bingoemcasa12.com
# ============================================================================

def Login_BingoEmCasa(page):
    """
    Realiza login no Bingo em Casa
    Espera por elementos específicos do site
    """
    print("\n🔐 >>> INICIANDO LOGIN NO BINGO EM CASA... <<<\n")

    # Email/Telefone e Senha
    email_to_input = '21996963606'  # Seu número/email
    password_to_input = 'Edu86K@88'  # Sua senha

    try:
        # Tenta diferentes seletores possíveis para o campo de email/usuário
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            'input[placeholder*="email"]',
            'input[placeholder*="usuário"]',
            'input[placeholder*="telefone"]',
            'input[id*="email"]',
            'input[id*="username"]',
        ]
        
        email_input_elem = None
        for selector in email_selectors:
            try:
                email_input_elem = page.locator(selector).first
                if email_input_elem.is_visible(timeout=2000):
                    print(f"✅ Campo de email encontrado: {selector}")
                    break
            except:
                continue
        
        if email_input_elem:
            email_input_elem.scroll_into_view_if_needed()
            time.sleep(0.5)
            email_input_elem.click(timeout=5000)
            time.sleep(0.5)
            email_input_elem.fill(str(email_to_input), timeout=5000)
            print(f"✅ Email/Usuário inserido: {email_to_input}")
        else:
            print("⚠️  Campo de email não encontrado, tentando alternativas...")

        # Tenta diferentes seletores possíveis para o campo de senha
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[name="psd"]',
            'input[placeholder*="senha"]',
            'input[placeholder*="password"]',
            'input[id*="password"]',
            'input[id*="psd"]',
        ]
        
        password_input_elem = None
        for selector in password_selectors:
            try:
                password_input_elem = page.locator(selector).first
                if password_input_elem.is_visible(timeout=2000):
                    print(f"✅ Campo de senha encontrado: {selector}")
                    break
            except:
                continue
        
        if password_input_elem:
            password_input_elem.scroll_into_view_if_needed()
            time.sleep(0.5)
            password_input_elem.click(timeout=5000)
            time.sleep(0.5)
            password_input_elem.fill(str(password_to_input), timeout=5000)
            print(f"✅ Senha inserida")
        else:
            print("⚠️  Campo de senha não encontrado, tentando alternativas...")

        # Tenta diferentes seletores possíveis para o botão de login
        login_selectors = [
            'button[type="submit"]',
            'button[name="login"]',
            'button[name="logIn"]',
            'button[class*="login"]',
            'button[class*="entrar"]',
            'button[id*="login"]',
            'a[class*="login"]',
            'input[type="submit"]',
        ]
        
        login_button = None
        for selector in login_selectors:
            try:
                login_button = page.locator(selector).first
                if login_button.is_visible(timeout=2000):
                    print(f"✅ Botão de login encontrado: {selector}")
                    break
            except:
                continue
        
        if login_button:
            login_button.scroll_into_view_if_needed()
            time.sleep(0.5)
            login_button.click(timeout=5000)
            time.sleep(1)
            login_button.click(timeout=5000)
            print("✅ Botão de login clicado")
        else:
            print("⚠️  Botão de login não encontrado")

        # Aguarda carregamento após login
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)

        # Tenta encontrar indicador de sucesso (saldo, nome do usuário, etc)
        balance_selectors = [
            'span[id="j_balance"]',
            'span[class*="balance"]',
            'span[class*="saldo"]',
            'div[class*="user-info"]',
            'div[class*="account"]',
        ]
        
        balance_found = False
        for selector in balance_selectors:
            try:
                balance_elem = page.locator(selector).first
                if balance_elem.is_visible(timeout=5000):
                    balance_text = balance_elem.text_content()
                    print(f"\n✅ >>> LOGIN REALIZADO COM SUCESSO! <<<")
                    print(f"📊 Saldo/Info: {balance_text}\n")
                    balance_found = True
                    break
            except:
                continue
        
        if not balance_found:
            print("\n⚠️  Não foi possível confirmar o login automaticamente.")
            print("📋 Por favor, verifique manualmente se o login foi bem-sucedido...")
            input("🔴 PRESSIONE ENTER APÓS CONFIRMAR QUE O LOGIN FUNCIONOU...")
            print("✅ Continuando com o bot...\n")

    except Exception as e:
        print(f"\n❌ ERRO NO LOGIN: {e}")
        print("⚠️  Tentando modo manual...")
        input("🔴 PRESSIONE ENTER APÓS FAZER LOGIN MANUALMENTE...")
        print("✅ Continuando com o bot...\n")
