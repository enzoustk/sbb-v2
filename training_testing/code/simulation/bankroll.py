from datetime import datetime

class BankrollManager:
    def __init__(self, initial_capital=1000, risk_per_trade=0.02):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.history = []
    
    def calculate_stake(self):
        """
        Calcula o valor a apostar baseado no capital atual.
        FIXME: Adicionar um parâmetro para definir se vai ser: Kelly, Fixo ou Percentual.
        Por enquanto, será fixo.
        """
        return self.risk_per_trade
    
    def update(self, profit_loss):
        """Atualiza o capital e registra o histórico"""
        self.capital += profit_loss
        self.history.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'capital': self.capital,
            'profit_loss': profit_loss
        })
    
    def get_summary(self):
        """Retorna um resumo estatístico"""
        return {
            'current_capital': self.capital,
            'total_profit': self.capital - self.initial_capital,
            'max_drawdown': self._calculate_max_drawdown()
        }
    
    def _calculate_max_drawdown(self):
        """Calcula o maior drawdown histórico"""
        peak = self.initial_capital
        max_dd = 0
        for entry in self.history:
            peak = max(peak, entry['capital'])
            dd = (peak - entry['capital']) / peak
            max_dd = max(max_dd, dd)
        return max_dd
