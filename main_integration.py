import asyncio
import os
from typing import Optional

from dotenv import load_dotenv

from signal_bridge import BingoSignalBridge
from telegram_listener import create_telegram_listener
from signal_parser import parse_signal_message, should_process_signal


load_dotenv()


async def watch_telegram_signals():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN não definido no ambiente.')

    listener = create_telegram_listener(token=token, chat_id=int(chat_id) if chat_id else None)
    bridge = BingoSignalBridge(
        email=os.getenv('BINGO_EMAIL'),
        password=os.getenv('BINGO_PASSWORD')
    )

    task = asyncio.create_task(listener.start_listening())
    try:
        while True:
            signal = await listener.get_signal(timeout=10)
            if not signal:
                continue

            parsed = parse_signal_message(signal.get('raw_text', ''))
            if not parsed:
                continue

            if not should_process_signal(parsed, min_odd=1.20, min_confidence=0):
                continue

            print(f'\n[OK] Sinal recebido: {parsed["home_team"]} x {parsed["away_team"]} | Odd: {parsed.get("odd")}')
            try:
                result = bridge.place_signal_bet(parsed)
                print('[OK] Tentativa de aposta enviada para o Bingo em Casa:', result)
            except Exception as exc:
                print(f'[ERR] Erro ao processar sinal: {exc}')
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    asyncio.run(watch_telegram_signals())
