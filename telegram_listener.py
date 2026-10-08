"""
Listener do Telegram para receber sinais de apostas
Escuta mensagens do canal/grupo e dispara processamento de apostas
"""

import logging
from typing import Optional, Callable, Awaitable

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramSignalListener:
    """Escuta sinais do Telegram via bot"""

    def __init__(self, token: str, chat_id: Optional[int] = None, 
                 signal_handler: Optional[Callable[[str], Awaitable[None]]] = None):
        """
        Inicializa o listener
        
        Args:
            token (str): Token do bot Telegram
            chat_id (int): ID do chat para filtrar (None = todos)
            signal_handler (callable): Função assíncrona para processar sinais
        """
        self.token = token
        self.chat_id = chat_id
        self.signal_handler = signal_handler
        self.application: Optional[Application] = None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Trata mensagens recebidas"""
        if not update.message or not update.message.text:
            return

        # Filtrar por chat se configurado
        if self.chat_id and update.effective_chat.id != self.chat_id:
            return

        message_text = update.message.text
        
        # Indicadores de sinal
        signal_keywords = ['time casa', 'time visitante', 'odd', 'sinal', 'aposta', 'home', 'away']
        is_signal = any(keyword in message_text.lower() for keyword in signal_keywords)

        if is_signal:
            logger.info(f"📨 Mensagem de sinal recebida de {update.effective_user.username or update.effective_user.id}")
            logger.debug(f"Texto: {message_text[:100]}...")
            
            # Chamar handler customizado se existir
            if self.signal_handler:
                try:
                    await self.signal_handler(message_text)
                except Exception as e:
                    logger.error(f"❌ Erro no handler: {e}")
                    try:
                        await update.message.reply_text(f"❌ Erro: {str(e)[:100]}")
                    except Exception:
                        pass

    async def start_listening(self):
        """Inicia o listener em polling contínuo"""
        try:
            logger.info("🚀 Iniciando Telegram Listener...")
            logger.info(f"   Token: {self.token[:20]}...")
            logger.info(f"   Chat ID: {self.chat_id or 'Todos'}")

            # Criar application
            self.application = Application.builder().token(self.token).build()

            # Adicionar handler para mensagens de texto
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )

            # Iniciar polling
            logger.info("🟢 Listener ativo! Aguardando sinais do Telegram...")
            await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

        except Exception as e:
            logger.error(f"❌ Erro ao iniciar listener: {e}")
            raise

    async def stop_listening(self):
        """Para o listener"""
        if self.application:
            await self.application.stop()
            logger.info("⛔ Listener parado")


def create_telegram_listener(token: str, chat_id: Optional[int] = None,
                            signal_handler: Optional[Callable[[str], Awaitable[None]]] = None) -> TelegramSignalListener:
    """
    Factory function para criar um listener
    
    Args:
        token (str): Token do bot
        chat_id (int): ID do chat (opcional)
        signal_handler (callable): Função para processar sinais (opcional)
        
    Returns:
        TelegramSignalListener: Instância do listener
    """
    return TelegramSignalListener(token=token, chat_id=chat_id, signal_handler=signal_handler)
