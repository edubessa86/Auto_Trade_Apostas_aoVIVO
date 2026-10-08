"""
Módulo de Escuta Telegram
Recebe sinais do robo_ao_vivo via Telegram e processa as apostas
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio
from datetime import datetime
import json
import os

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('telegram_listener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramSignalListener:
    """
    Classe para escutar sinais do Telegram do robo_ao_vivo
    """
    
    def __init__(self, token: str, chat_id: int = None):
        """
        Inicializa o listener do Telegram
        
        Args:
            token (str): Token do bot Telegram
            chat_id (int): ID do chat para filtrar sinais (opcional)
        """
        self.token = token
        self.chat_id = chat_id
        self.signals_queue = asyncio.Queue()
        self.signals_log = []
        
    async def handle_signal_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Trata mensagens de sinal do robo_ao_vivo
        Formato esperado de sinal:
        
        SINAL ✅
        🏠 Time Casa: Flamengo
        🚗 Time Visitante: Botafogo
        ⏰ Horário: 20:00
        📊 Tipo: 1X2
        💰 Odd: 1.85
        📈 Confiança: 85%
        🎯 Recomendação: VERDE ✅
        """
        
        try:
            message_text = update.message.text
            
            # Verificar se é um sinal válido
            if not self._is_valid_signal(message_text):
                logger.info(f"Mensagem recebida (não é sinal): {message_text[:50]}...")
                return
            
            # Parsear o sinal
            signal = self._parse_signal(message_text)
            
            if signal:
                # Adicionar timestamp
                signal['timestamp'] = datetime.now().isoformat()
                signal['user_id'] = update.effective_user.id
                signal['chat_id'] = update.effective_chat.id
                
                # Adicionar à fila
                await self.signals_queue.put(signal)
                
                # Registrar no log
                self.signals_log.append(signal)
                self._save_signal_log()
                
                logger.info(f"✅ Sinal capturado: {signal['home_team']} vs {signal['away_team']}")
                
                # Enviar confirmação
                await update.message.reply_text(
                    f"✅ Sinal capturado!\n"
                    f"{signal['home_team']} vs {signal['away_team']}\n"
                    f"Odd: {signal['odd']}\n"
                    f"Aguardando colocação de aposta...",
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar sinal: {e}")
            await update.message.reply_text(
                f"❌ Erro ao processar sinal: {str(e)}",
                parse_mode='Markdown'
            )
    
    def _is_valid_signal(self, text: str) -> bool:
        """Verifica se a mensagem é um sinal válido"""
        signal_indicators = ['SINAL', 'Time Casa', 'Time Visitante', 'Odd', 'Tipo']
        return sum(indicator in text for indicator in signal_indicators) >= 3
    
    def _parse_signal(self, text: str) -> dict:
        """
        Parseia o texto do sinal e extrai informações
        
        Returns:
            dict: Dicionário com dados do sinal
        """
        try:
            signal = {}
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if 'Time Casa:' in line:
                    signal['home_team'] = line.split('Time Casa:')[1].strip()
                elif 'Time Visitante:' in line or 'Time Visitante:' in line:
                    signal['away_team'] = line.split('Time Visitante:')[1].strip()
                elif 'Horário:' in line:
                    signal['time'] = line.split('Horário:')[1].strip()
                elif 'Tipo:' in line:
                    signal['bet_type'] = line.split('Tipo:')[1].strip()
                elif 'Odd:' in line:
                    try:
                        odd_str = line.split('Odd:')[1].strip()
                        signal['odd'] = float(odd_str)
                    except:
                        pass
                elif 'Confiança:' in line:
                    try:
                        conf_str = line.split('Confiança:')[1].strip().replace('%', '')
                        signal['confidence'] = float(conf_str)
                    except:
                        pass
                elif 'Recomendação:' in line or 'Status:' in line:
                    signal['recommendation'] = line.split(':')[1].strip()
            
            # Validar se tem os campos essenciais
            required_fields = ['home_team', 'away_team', 'odd', 'bet_type']
            if all(field in signal for field in required_fields):
                return signal
            else:
                logger.warning(f"Sinal incompleto. Faltam: {[f for f in required_fields if f not in signal]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parsing do sinal: {e}")
            return None
    
    async def start_listening(self):
        """Inicia o listener do Telegram"""
        try:
            # Criar application
            application = Application.builder().token(self.token).build()
            
            # Adicionar handlers
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_signal_message)
            )
            
            # Iniciar polling
            logger.info("🟢 Telegram Listener iniciado! Aguardando sinais...")
            await application.run_polling()
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar listener: {e}")
            raise
    
    async def get_signal(self, timeout: int = None):
        """
        Obtém próximo sinal da fila
        
        Args:
            timeout (int): Timeout em segundos (None = indefinido)
            
        Returns:
            dict: Sinal capturado
        """
        try:
            signal = await asyncio.wait_for(
                self.signals_queue.get(),
                timeout=timeout
            )
            return signal
        except asyncio.TimeoutError:
            return None
    
    def _save_signal_log(self):
        """Salva log de sinais em arquivo"""
        try:
            log_file = 'signals_log.json'
            with open(log_file, 'w') as f:
                json.dump(self.signals_log, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Erro ao salvar log de sinais: {e}")


def create_telegram_listener(token: str, chat_id: int = None) -> TelegramSignalListener:
    """
    Factory function para criar listener do Telegram
    
    Args:
        token (str): Token do bot Telegram
        chat_id (int): ID do chat (opcional)
        
    Returns:
        TelegramSignalListener: Instância do listener
    """
    return TelegramSignalListener(token=token, chat_id=chat_id)


if __name__ == "__main__":
    # Exemplo de uso
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN não definido nas variáveis de ambiente")
    
    listener = create_telegram_listener(token=TOKEN)
    
    # Iniciar listener
    asyncio.run(listener.start_listening())
