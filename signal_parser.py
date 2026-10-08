"""
Parser para sinais de apostas vindos do Telegram
Extrai informações estruturadas de mensagens de sinal
"""

import re
import unicodedata
from typing import Dict, Any, Optional


def normalize_text(value: str) -> str:
    """Normaliza texto removendo acentos e espaços extras"""
    if not value:
        return ""
    value = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', value).strip().lower()


def clean_value(raw: str) -> str:
    """Remove espaços extras de um valor"""
    return re.sub(r'\s+', ' ', (raw or '').strip())


def parse_signal_message(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Parseia uma mensagem de sinal do Telegram em um dicionário estruturado.
    
    Formatos suportados:
    - Time Casa: Flamengo | Time Visitante: Botafogo | Odd: 1.85
    - Flamengo vs Botafogo | Odd: 1.85
    - Home: Flamengo | Away: Botafogo
    
    Args:
        raw_text (str): Texto bruto da mensagem do Telegram
        
    Returns:
        dict: Dicionário com campos do sinal ou None se inválido
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    text = raw_text.replace('\r', '')
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    signal = {
        'raw_text': text,
        'home_team': None,
        'away_team': None,
        'time': None,
        'odd': None,
        'bet_type': None,
        'confidence': None,
        'recommendation': None,
    }

    # Parse linha por linha
    for line in lines:
        lower = line.lower()

        # Time da casa
        if 'casa' in lower and 'time' in lower:
            if ':' in line:
                signal['home_team'] = clean_value(line.split(':', 1)[1])
        elif 'home' in lower and ':' in line:
            signal['home_team'] = clean_value(line.split(':', 1)[1])
            
        # Time visitante
        elif ('visitante' in lower or 'fora' in lower) and 'time' in lower:
            if ':' in line:
                signal['away_team'] = clean_value(line.split(':', 1)[1])
        elif 'away' in lower and ':' in line:
            signal['away_team'] = clean_value(line.split(':', 1)[1])
            
        # Horário
        elif 'horário' in lower or 'hora' in lower or 'time' in lower:
            if ':' in line and any(c.isdigit() for c in line):
                time_part = line.split(':', 1)[1].strip()
                if re.match(r'\d{1,2}[:]\ d{2}', time_part):
                    signal['time'] = clean_value(time_part)
                    
        # Odd/Cotação
        elif 'odd' in lower or 'cotação' in lower:
            try:
                value = line.split(':', 1)[1].strip()
                signal['odd'] = float(re.sub(r'[^0-9,\.]', '', value).replace(',', '.'))
            except Exception:
                pass
                
        # Tipo de aposta
        elif 'tipo' in lower or 'mercado' in lower:
            if ':' in line:
                signal['bet_type'] = clean_value(line.split(':', 1)[1])
                
        # Confiança
        elif 'confiança' in lower or 'confidence' in lower:
            if ':' in line:
                try:
                    conf_value = re.sub(r'[^0-9,\.]', '', line.split(':', 1)[1])
                    if conf_value:
                        signal['confidence'] = float(conf_value.replace(',', '.'))
                except Exception:
                    pass
                    
        # Recomendação/Status
        elif 'recomendação' in lower or 'status' in lower or 'recommendation' in lower:
            if ':' in line:
                signal['recommendation'] = clean_value(line.split(':', 1)[1])

    # Fallback: extrair por "X vs Y"
    if not signal['home_team'] or not signal['away_team']:
        # Procurar padrões como "Flamengo vs Botafogo" ou "Flamengo x Botafogo"
        for separator in [' vs ', ' VS ', ' x ', ' X ', ' - ']:
            if separator in text:
                parts = text.split(separator)[0:2]
                if len(parts) == 2:
                    home = clean_value(parts[0].split('\n')[-1])
                    away = clean_value(parts[1].split('\n')[0])
                    if home and away and home != away:
                        signal['home_team'] = home
                        signal['away_team'] = away
                        break

    # Validar campos obrigatórios
    required = ['home_team', 'away_team']
    if any(signal[key] is None for key in required):
        print(f"[WARN] Sinal incompleto. Faltam: {[k for k in required if signal[k] is None]}")
        return None

    # Normalização fina
    signal['home_team'] = clean_value(signal['home_team'])
    signal['away_team'] = clean_value(signal['away_team'])
    signal['bet_type'] = signal['bet_type'] or '1X2'
    signal['recommendation'] = signal['recommendation'] or 'AUTO'
    
    return signal


def should_process_signal(signal: Dict[str, Any], min_odd: float = 1.20, min_confidence: float = 0.0) -> bool:
    """
    Valida se o sinal deve ser processado baseado em critérios
    
    Args:
        signal (dict): Sinal parseado
        min_odd (float): Odd mínima aceitável
        min_confidence (float): Confiança mínima aceitável (0-100)
        
    Returns:
        bool: True se o sinal deve ser processado
    """
    if not signal:
        return False
        
    # Validar odd
    if signal.get('odd') is not None:
        if signal['odd'] < min_odd:
            print(f"[WARN] Odd {signal['odd']} abaixo do mínimo {min_odd}")
            return False
            
    # Validar confiança
    confidence = signal.get('confidence')
    if confidence is not None and confidence < min_confidence:
        print(f"[WARN] Confiança {confidence}% abaixo do mínimo {min_confidence}%")
        return False
        
    return True
