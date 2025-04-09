def main():
    from data.feature.engineering import calcular_features
    import pandas as pd
    from data.feature.constants import tempo
    DATA_PATH = "dados/database/dados_totais.csv"
    df = pd.read_csv(DATA_PATH)
    df = calcular_features(
        df,
        live = False,
        normalizar = True,
        tempo = tempo)
    df.to_excel('dados/exports/teste.xlsx')
    print("Execução feita com sucesso!")

if __name__ == '__main__':
    main()