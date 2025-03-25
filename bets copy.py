def _get_excel_columns(self):
    return
    {
        'Horário Envio': self.time_sent.strftime("%H:%M"),
        'Liga': self.league,
        'Partida': self.home_str + 'vs. ' + self.away_str,
        'Tipo Aposta': self.bet_type.capitalize(),
        'Linha': f'{self.line:2f}',
        'Resultado' : self.result.replace('_', ' ').capitalize(),
        'Odd': f'{self.odds:2f}',
        'Lucro': f'{self.profit:2f}',
        'Intervalo': self.time_range,

        
    }
