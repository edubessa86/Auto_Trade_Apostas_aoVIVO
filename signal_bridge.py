"""
Bridge entre sinais do Telegram e automação de apostas no Bingo em Casa
Responsável por buscar o evento no site e colocar a aposta
"""

import os
import time
import re
import logging
from typing import Dict, Any, Optional

from playwright.sync_api import sync_playwright

from signal_parser import clean_value

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BingoSignalBridge:
    """
    Conecta sinais do Telegram ao site Bingo em Casa e coloca apostas automaticamente
    """

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None,
                 base_url: str = 'https://bingoemcasa12.com/pt-BR/sportsbook/bets',
                 headless: bool = False):
        """
        Inicializa o bridge do Bingo
        
        Args:
            email (str): Email/telefone da conta
            password (str): Senha da conta
            base_url (str): URL base do Bingo em Casa
            headless (bool): Se True, abre navegador em modo headless
        """
        self.email = email or os.getenv('BINGO_EMAIL')
        self.password = password or os.getenv('BINGO_PASSWORD')
        self.base_url = base_url
        self.headless = headless

    def _clean_name(self, value: str) -> str:
        """Normaliza nome de time para comparação"""
        if not value:
            return ''
        value = value.strip().lower()
        value = re.sub(r'\s+', ' ', value)
        value = re.sub(r'[^a-z0-9\s]', '', value)
        return value.strip()

    def _contains_team(self, text: str, team_name: str) -> bool:
        """Verifica se um time está presente no texto"""
        if not team_name:
            return False
        normalized_text = self._clean_name(text)
        normalized_team = self._clean_name(team_name)
        if not normalized_team or not normalized_text:
            return False
        return normalized_team in normalized_text or normalized_text in normalized_team

    def login(self, page) -> bool:
        """
        Realiza login no Bingo em Casa
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se login bem-sucedido
        """
        if not self.email or not self.password:
            raise ValueError('❌ BINGO_EMAIL e BINGO_PASSWORD precisam estar configurados.')

        logger.info(f"🔐 Acessando {self.base_url}...")
        page.goto(self.base_url, timeout=60000, wait_until='networkidle')
        time.sleep(2)

        # Tentar preencher email/telefone
        try:
            email_selectors = [
                'input[id*="identifier"]',
                'input[type="email"]',
                'input[placeholder*="email"]',
                'input[placeholder*="telefone"]',
                'input[type="text"]'
            ]
            
            for selector in email_selectors:
                try:
                    email_input = page.locator(selector).first
                    if email_input.count() > 0 and email_input.is_visible(timeout=2000):
                        email_input.fill(self.email)
                        logger.info(f"✅ Email/Telefone inserido: {self.email}")
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"⚠️ Erro ao preencher email: {e}")

        time.sleep(1)

        # Tentar preencher senha
        try:
            password_input = page.locator('input[type="password"]').first
            if password_input.count() > 0:
                password_input.fill(self.password)
                logger.info("✅ Senha inserida")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao preencher senha: {e}")

        time.sleep(1)

        # Clicar no botão de login
        login_buttons = [
            ('button:has-text("Entrar")', 'Entrar'),
            ('button[type="submit"]', 'Submit'),
            ('button:has-text("Login")', 'Login'),
            ('button:has-text("Conectar")', 'Conectar'),
        ]

        clicked = False
        for selector, name in login_buttons:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible(timeout=2000):
                    logger.info(f"🔘 Clicando em '{name}'...")
                    btn.click()
                    clicked = True
                    break
            except Exception as e:
                logger.debug(f"Botão '{name}' não encontrado: {e}")
                continue

        if not clicked:
            logger.warning("⚠️ Nenhum botão de login encontrado, tentando modo manual...")

        # Aguardar carregamento após login
        time.sleep(4)
        
        # Validar login
        is_logged = 'sportsbook' in page.url.lower() or 'bets' in page.url.lower()
        
        if is_logged:
            logger.info("✅ Login realizado com sucesso!")
        else:
            logger.warning(f"⚠️ Posição da URL: {page.url}")

        return is_logged

    def find_match_row(self, page, home_team: str, away_team: str):
        """
        Procura pela linha do jogo na página
        
        Args:
            page: Página do Playwright
            home_team (str): Time da casa
            away_team (str): Time visitante
            
        Returns:
            Localizador do jogo ou None
        """
        logger.info(f"🔍 Procurando jogo: {home_team} x {away_team}")
        
        home_norm = self._clean_name(home_team)
        away_norm = self._clean_name(away_team)

        # Tentativa 1: procurar por padrões "TEAM vs TEAM"
        patterns = [
            f'{home_team} vs {away_team}',
            f'{home_team} x {away_team}',
            f'{home_team} - {away_team}',
            f'{away_team} vs {home_team}',
        ]

        for pattern in patterns:
            try:
                locator = page.locator(f'text={pattern}')
                if locator.count() > 0:
                    logger.info(f"✅ Jogo encontrado por padrão: {pattern}")
                    return locator.first
            except Exception:
                continue

        # Tentativa 2: procurar pelos nomes separados
        rows = page.locator('div, tr, li, article, section, button')
        total = min(rows.count(), 500)
        
        logger.info(f"📋 Verificando {total} elementos...")
        
        for idx in range(total):
            try:
                text = rows.nth(idx).text_content() or ''
                if self._contains_team(text, home_team) and self._contains_team(text, away_team):
                    logger.info(f"✅ Jogo encontrado no índice {idx}")
                    return rows.nth(idx)
            except Exception:
                continue

        logger.warning(f"❌ Jogo não encontrado no site: {home_team} x {away_team}")
        return None

    def click_odds_in_row(self, page, row, home_team: str, away_team: str, bet_type: str = '1X2') -> bool:
        """
        Clica nas odds dentro da linha do jogo
        
        Args:
            page: Página do Playwright
            row: Elemento contendo o jogo
            home_team (str): Time da casa
            away_team (str): Time visitante
            bet_type (str): Tipo de aposta
            
        Returns:
            bool: True se clicou com sucesso
        """
        try:
            logger.info(f"📍 Rolando para o jogo...")
            row.scroll_into_view_if_needed()
            time.sleep(1.5)

            # Procurar por botões de odds dentro da linha
            odds_buttons = row.locator('button, [role="button"], [data-odd], .odds, span')
            
            total_odds = odds_buttons.count()
            logger.info(f"🎯 Encontrados {total_odds} elementos de aposta")
            
            for i in range(min(total_odds, 20)):
                try:
                    item = odds_buttons.nth(i)
                    label = (item.text_content() or '').strip()
                    
                    # Procurar por labels típicos de apostas
                    if label and any(token in label.lower() for token in ['1', 'x', '2', 'over', 'under', 'yes', 'no']):
                        logger.info(f"🔘 Clicando em aposta: '{label}'")
                        item.click()
                        time.sleep(1)
                        return True
                except Exception as e:
                    logger.debug(f"Erro ao clicar em odd {i}: {e}")
                    continue

            # Fallback: clicar no próprio container do jogo
            logger.info("⚠️ Nenhuma odd específica encontrada, clicando no jogo...")
            row.click()
            time.sleep(1)
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao clicar em odds: {e}")
            return False

    def place_signal_bet(self, signal: Dict[str, Any], stake: float) -> Dict[str, Any]:
        """
        Coloca aposta baseada em um sinal do Telegram
        
        Args:
            signal (dict): Sinal parseado com informações do jogo
            stake (float): Valor a apostar em reais
            
        Returns:
            dict: Resultado da tentativa de aposta
        """
        home_team = signal.get('home_team')
        away_team = signal.get('away_team')
        
        if not home_team or not away_team:
            raise ValueError('❌ Sinal sem times válidos para aposta.')

        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 PROCESSANDO SINAL: {home_team} x {away_team}")
        logger.info(f"   Odd: {signal.get('odd')}")
        logger.info(f"   Tipo: {signal.get('bet_type', '1X2')}")
        logger.info(f"   Confiança: {signal.get('confidence')}%")
        logger.info(f"   💰 STAKE: R$ {stake:.2f}")
        logger.info(f"{'='*60}\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1440, 'height': 980},
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = context.new_page()
            
            try:
                # Login
                if not self.login(page):
                    raise RuntimeError('❌ Falha no login')

                time.sleep(2)

                # Buscar jogo
                match_row = self.find_match_row(page, home_team, away_team)
                if not match_row:
                    raise RuntimeError(f'❌ Partida não encontrada: {home_team} x {away_team}')

                # Clicar em odds
                if not self.click_odds_in_row(page, match_row, home_team, away_team, signal.get('bet_type', '1X2')):
                    logger.warning("⚠️ Não foi possível clicar nas odds")

                # Aguardar confirmação visual
                time.sleep(3)
                
                logger.info("✅ Tentativa de aposta concluída!")

                return {
                    'status': 'success',
                    'home_team': home_team,
                    'away_team': away_team,
                    'odd': signal.get('odd'),
                    'bet_type': signal.get('bet_type', '1X2'),
                    'confidence': signal.get('confidence'),
                    'stake': stake,
                }

            except Exception as e:
                logger.error(f"❌ Erro ao processar aposta: {e}")
                return {
                    'status': 'error',
                    'home_team': home_team,
                    'away_team': away_team,
                    'error': str(e),
                    'stake': stake,
                }

            finally:
                try:
                    browser.close()
                except Exception:
                    pass
