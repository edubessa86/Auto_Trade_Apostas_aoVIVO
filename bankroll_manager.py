"""
Gerenciador de Banca para Apostas
Controla 5% da banca para testes e gerencia risco
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BankrollManager:
    """
    Gerencia a banca de apostas com estratégia de 5% por sinal
    """
    
    def __init__(self, initial_bankroll: float = 1000.0, risk_percent: float = 5.0):
        """
        Inicializa gerenciador de banca
        
        Args:
            initial_bankroll (float): Banca inicial em reais
            risk_percent (float): Percentual da banca a arriscar por aposta
        """
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.risk_percent = risk_percent
        self.bet_history = []
        self.log_file = 'bankroll_history.json'
        self._load_history()

    def _load_history(self):
        """Carrega histórico de apostas do arquivo"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.current_bankroll = data.get('current_bankroll', self.initial_bankroll)
                    self.bet_history = data.get('bet_history', [])
                    logger.info(f"✅ Histórico carregado. Banca atual: R$ {self.current_bankroll:.2f}")
            except Exception as e:
                logger.error(f"Erro ao carregar histórico: {e}")

    def _save_history(self):
        """Salva histórico de apostas no arquivo"""
        try:
            data = {
                'initial_bankroll': self.initial_bankroll,
                'current_bankroll': self.current_bankroll,
                'risk_percent': self.risk_percent,
                'bet_history': self.bet_history,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")

    def calculate_stake(self) -> float:
        """
        Calcula valor a apostar (5% da banca atual)
        
        Returns:
            float: Valor em reais a apostar
        """
        stake = (self.current_bankroll * self.risk_percent) / 100
        logger.info(f"💰 Banca Atual: R$ {self.current_bankroll:.2f} | Stake ({self.risk_percent}%): R$ {stake:.2f}")
        return round(stake, 2)

    def record_bet(self, bet_info: Dict[str, Any], result: str = 'pending') -> Dict[str, Any]:
        """
        Registra uma aposta no histórico
        
        Args:
            bet_info (dict): Informações da aposta
            result (str): 'win', 'loss', 'pending', 'cancelled'
            
        Returns:
            dict: Registro da aposta
        """
        stake = self.calculate_stake()
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'home_team': bet_info.get('home_team'),
            'away_team': bet_info.get('away_team'),
            'odd': bet_info.get('odd'),
            'bet_type': bet_info.get('bet_type', '1X2'),
            'stake': stake,
            'confidence': bet_info.get('confidence'),
            'result': result,
            'bankroll_before': self.current_bankroll,
            'bankroll_after': self.current_bankroll,
        }
        
        self.bet_history.append(record)
        self._save_history()
        
        logger.info(
            f"📝 Aposta Registrada:\n"
            f"   Time: {record['home_team']} x {record['away_team']}\n"
            f"   Odd: {record['odd']} | Stake: R$ {stake:.2f}\n"
            f"   Status: {result}\n"
        )
        
        return record

    def update_bet_result(self, bet_index: int, result: str, profit_loss: float = 0.0):
        """
        Atualiza resultado de uma aposta
        
        Args:
            bet_index (int): Índice da aposta no histórico
            result (str): 'win', 'loss', 'cancelled'
            profit_loss (float): Ganho/perda em reais
        """
        if 0 <= bet_index < len(self.bet_history):
            self.bet_history[bet_index]['result'] = result
            self.bet_history[bet_index]['profit_loss'] = profit_loss
            
            # Atualizar banca
            if result == 'win':
                self.current_bankroll += profit_loss
                logger.info(f"✅ Aposta Vencida! +R$ {profit_loss:.2f} | Nova Banca: R$ {self.current_bankroll:.2f}")
            elif result == 'loss':
                self.current_bankroll -= abs(profit_loss)
                logger.info(f"❌ Aposta Perdida! -R$ {abs(profit_loss):.2f} | Nova Banca: R$ {self.current_bankroll:.2f}")
            
            self.bet_history[bet_index]['bankroll_after'] = self.current_bankroll
            self._save_history()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calcula estatísticas da banca
        
        Returns:
            dict: Estatísticas gerais
        """
        total_bets = len(self.bet_history)
        won_bets = sum(1 for b in self.bet_history if b['result'] == 'win')
        lost_bets = sum(1 for b in self.bet_history if b['result'] == 'loss')
        pending_bets = sum(1 for b in self.bet_history if b['result'] == 'pending')
        
        total_staked = sum(b['stake'] for b in self.bet_history)
        total_profit = sum(b.get('profit_loss', 0) for b in self.bet_history if b['result'] == 'win')
        total_loss = sum(b.get('profit_loss', 0) for b in self.bet_history if b['result'] == 'loss')
        
        win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
        roi = ((self.current_bankroll - self.initial_bankroll) / self.initial_bankroll * 100) if self.initial_bankroll > 0 else 0
        
        return {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'total_profit_loss': self.current_bankroll - self.initial_bankroll,
            'total_bets': total_bets,
            'won_bets': won_bets,
            'lost_bets': lost_bets,
            'pending_bets': pending_bets,
            'win_rate': round(win_rate, 2),
            'roi': round(roi, 2),
            'total_staked': round(total_staked, 2),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
        }

    def print_statistics(self):
        """Exibe estatísticas formatadas"""
        stats = self.get_statistics()
        logger.info(
            f"\n{'='*70}\n"
            f"📊 ESTATÍSTICAS BANCÁRIAS\n"
            f"{'='*70}\n"
            f"💰 Banca Inicial: R$ {stats['initial_bankroll']:.2f}\n"
            f"💵 Banca Atual: R$ {stats['current_bankroll']:.2f}\n"
            f"📈 Lucro/Prejuízo: R$ {stats['total_profit_loss']:+.2f}\n"
            f"📊 ROI: {stats['roi']:+.2f}%\n\n"
            f"🎯 APOSTAS:\n"
            f"   Total: {stats['total_bets']}\n"
            f"   Vencidas: {stats['won_bets']} ({stats['win_rate']:.1f}%)\n"
            f"   Perdidas: {stats['lost_bets']}\n"
            f"   Pendentes: {stats['pending_bets']}\n\n"
            f"💸 VALORES:\n"
            f"   Total Apostado: R$ {stats['total_staked']:.2f}\n"
            f"   Total Ganho: R$ {stats['total_profit']:.2f}\n"
            f"   Total Perdido: R$ {stats['total_loss']:.2f}\n"
            f"{'='*70}\n"
        )
