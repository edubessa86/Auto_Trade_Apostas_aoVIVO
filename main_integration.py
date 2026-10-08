"""
Integração Principal: Telegram → Parser → Bingo em Casa
Escuta sinais do Telegram, parseia informações e coloca apostas automaticamente
Com gerenciamento de banca (5% por aposta)
"""

import asyncio
import logging
import os
from typing import Awaitable

from dotenv import load_dotenv

from signal_bridge import BingoSignalBridge
from telegram_listener import create_telegram_listener
from signal_parser import parse_signal_message, should_process_signal
from bankroll_manager import BankrollManager

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('betting_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BettingAutomation:
    """Automação de apostas a partir de sinais do Telegram com gerenciamento de banca"""

    def __init__(self):
        """Inicializa a automação"""
        # Configurações do Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        # Configurações do Bingo
        self.bingo_email = os.getenv('BINGO_EMAIL')
        self.bingo_password = os.getenv('BINGO_PASSWORD')
        self.bingo_url = os.getenv('BINGO_BASE_URL', 'https://bingoemcasa12.com/pt-BR/sportsbook/bets')

        # Configurações de apostas
        self.min_odd = float(os.getenv('MIN_ODD', '1.20'))
        self.min_confidence = float(os.getenv('MIN_CONFIDENCE', '0.0'))
        
        # Banca
        initial_bankroll = float(os.getenv('DEFAULT_BANKROLL', '1000'))
        risk_percent = float(os.getenv('BANKROLL_RISK_PERCENT', '5'))
        self.bankroll = BankrollManager(initial_bankroll=initial_bankroll, risk_percent=risk_percent)

        # Validar configurações
        if not self.telegram_token:
            raise ValueError('❌ TELEGRAM_BOT_TOKEN não configurado no .env')
        if not self.bingo_email or not self.bingo_password:
            raise ValueError('❌ BINGO_EMAIL e BINGO_PASSWORD não configurados no .env')

        # Inicializar bridge
        self.bridge = BingoSignalBridge(
            email=self.bingo_email,
            password=self.bingo_password,
            base_url=self.bingo_url,
            headless=False  # Mostrar navegador
        )

        # Estatísticas
        self.stats = {
            'signals_received': 0,
            'signals_parsed': 0,
            'signals_processed': 0,
            'bets_attempted': 0,
            'bets_success': 0,
            'bets_failed': 0,
        }

    async def process_signal(self, raw_text: str) -> None:
        """
        Processa um sinal do Telegram
        
        Args:
            raw_text (str): Texto bruto da mensagem
        """
        self.stats['signals_received'] += 1
        logger.info(f"📨 Sinal recebido ({self.stats['signals_received']})")

        try:
            # Parsear sinal
            signal = parse_signal_message(raw_text)
            if not signal:
                logger.warning("⚠️ Não foi possível fazer parse do sinal")
                return

            self.stats['signals_parsed'] += 1
            logger.info(f"✅ Sinal parseado: {signal['home_team']} x {signal['away_team']}")

            # Validar sinal
            if not should_process_signal(signal, min_odd=self.min_odd, min_confidence=self.min_confidence):
                logger.info("⏭️ Sinal não atende aos critérios mínimos")
                return

            self.stats['signals_processed'] += 1
            
            # Calcular stake (5% da banca)
            stake = self.bankroll.calculate_stake()
            
            logger.info(f"🎯 Processando: {signal['home_team']} x {signal['away_team']} | Odd: {signal.get('odd')} | Stake: R$ {stake:.2f}")

            # Registrar aposta no histórico
            bet_record = self.bankroll.record_bet(signal, result='pending')

            # Colocar aposta
            self.stats['bets_attempted'] += 1
            result = self.bridge.place_signal_bet(signal, stake=stake)

            if result.get('status') == 'success':
                self.stats['bets_success'] += 1
                logger.info(f"✅ Aposta colocada com sucesso!")
            else:
                self.stats['bets_failed'] += 1
                logger.error(f"❌ Erro na aposta: {result.get('error', 'Desconhecido')}")

        except Exception as e:
            self.stats['bets_failed'] += 1
            logger.error(f"❌ Erro ao processar sinal: {e}")

        # Mostrar estatísticas
        self._print_stats()

    def _print_stats(self):
        """Mostra estatísticas da sessão"""
        logger.info(
            f"\n📊 ESTATÍSTICAS DA SESSÃO:\n"
            f"   Sinais Recebidos: {self.stats['signals_received']}\n"
            f"   Sinais Parseados: {self.stats['signals_parsed']}\n"
            f"   Sinais Processados: {self.stats['signals_processed']}\n"
            f"   Apostas Tentadas: {self.stats['bets_attempted']}\n"
            f"   Apostas Sucesso: {self.stats['bets_success']}\n"
            f"   Apostas Falhadas: {self.stats['bets_failed']}\n"
        )
        self.bankroll.print_statistics()

    async def run(self):
        """Inicia a automação"""
        logger.info("="*70)
        logger.info("🤖 AUTOMAÇÃO DE APOSTAS - TELEGRAM → BINGO EM CASA")
        logger.info("="*70)
        logger.info(f"📲 Telegram Token: {self.telegram_token[:30]}...")
        logger.info(f"💰 Bingo Email: {self.bingo_email}")
        logger.info(f"🎯 Odd Mínima: {self.min_odd}")
        logger.info(f"📈 Confiança Mínima: {self.min_confidence}%")
        logger.info(f"💵 Banca Inicial: R$ {self.bankroll.initial_bankroll:.2f}")
        logger.info(f"💸 Risco por Aposta: {self.bankroll.risk_percent}%")
        logger.info("="*70 + "\n")

        # Criar listener
        listener = create_telegram_listener(
            token=self.telegram_token,
            chat_id=int(self.telegram_chat_id) if self.telegram_chat_id else None,
            signal_handler=self.process_signal
        )

        # Iniciar escuta
        await listener.start_listening()


async def main():
    """Função principal"""
    try:
        automation = BettingAutomation()
        await automation.run()
    except KeyboardInterrupt:
        logger.info("\n⛔ Automação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
