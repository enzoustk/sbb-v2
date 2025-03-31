"""builds a betting report and sends it on telegram"""

import pandas as pd
import logging
from data import load
from datetime import datetime
from telegram import message
from telegram import constants

def generate(
    start_date: str | None = None,
    end_date: str | None = None,
    ev_type: str | None = None,
    league: str | None = None,
    report_type: str = 'default'
):

    df = load.xlsx(
        start_date=start_date,
        end_date=end_date,
        ev_type=ev_type,
        league=league
    )

    
    date_range = df['time_sent'].dt.strftime('%d/%m').unique()
    interval = " a ".join(date_range[[0, -1]]) if len(date_range) > 1 else date_range[0]

    # Construção do título usando o template
    title = constants.REPORT_TITLE.format(
        interval=interval,
        league=league or 'Todas',
        betting_type=ev_type or 'Total',
        line_type='Dia 🗓️'
    )

    # Seção diária
    daily = df.groupby(df['time_sent'].dt.strftime('%d'))['profit'].sum()
    daily_report = "\n".join([
        constants.REPORT_BODY.format(
            period=day,
            emoji='✅' if profit > 0 else '❌',
            profit=f"{profit:.2f}u"
        )
        for day, profit in daily.items()
    ])

    # Seção de horários
    time_report = df.groupby('time_range')['profit'].sum().sort_index()
    time_section = constants.REPORT_TIME_RANGE_TITLE + "\n" + "\n".join([
        constants.REPORT_TIME_RANGE_BODY.format(
            time_range=tr,
            emoji='✅' if profit > 0 else '❌',
            profit=f"{profit:.2f}u"
        )
        for tr, profit in time_report.items()
    ])

    # Seção de tipos de aposta
    bet_sections = []
    for bet_type in df['bet_type'].unique():
        bt_df = df[df['bet_type'] == bet_type]
        total = bt_df['profit'].sum()
        emoji_status = '✅' if total > 0 else '❌'
        
        players_profit = pd.concat([
            bt_df.groupby('home_player')['profit'].sum(),
            bt_df.groupby('away_player')['profit'].sum()
        ]).groupby(level=0).sum()
        
        bet_sections.append(constants.REPORT_TOTAL.format(
            bet_type=bet_type,
            emoji=emoji_status,
            profit=f"{total:.2f}u",
            bet=len(bt_df),
            roi=f"{(total/len(bt_df)*100):.2f}%" if len(bt_df) else "0%",
            best_player=players_profit.idxmax(),
            best_player_profit=f"{players_profit.max():.2f}u",
            worst_player=players_profit.idxmin(),
            worst_player_profit=f"{players_profit.min():.2f}u"
        ))

    # Resultados totais
    total_profit = df['profit'].sum()
    total_line = constants.REPORT_BODY.format(
        period="Total",
        emoji='✅' if total_profit > 0 else '❌',
        profit=f"{total_profit:.2f}u | {len(df)} Tips | {(total_profit/len(df)*100):.2f}% ROI"
    )

    # Montagem final do relatório
    report = (
        f"{title}\n"
        f"{daily_report}\n\n"
        f"{total_line}\n\n"
        f"{time_section}\n\n"
        f"Por Aposta 🎯:\n\n" + "\n\n".join(bet_sections)
    )
    
    return report

