def main():
    
    from data.process import load
    from model.splits.data import split_data
    from model.splits.process import process_splits

    """
    CARREGAMENTO E PRÉ-PROCESSAMENTO DOS DADOS:
    1- Lê o arquivo CSV com os dados,
    2 - Divide dados em treino e teste antes de tudo, evitando data leakage,
    3- Calcula features e limpa o dataset respeitando os splits:
    """
    
    all_data = load()
    raw_splits = split_data(
        df = all_data,
        date_col = 'date',
        test_size_frac = 0.2,
        n_splits = 3,
        gap = 0
        )
    splits = process_splits(raw_splits)
    #----------------------------------------------------------------------#
    
    from utils import print_gap
    from model.pipeline.train import train_model, train_baseline
    from model.pipeline.eval import ModelEvaluator, compare_models, save_evaluation_report

    """
    TREINAMENTO E AVALIAÇÃO DO MODELO
    Treinar o modelo para cada train_split,
    Avaliar o modelo em cada test_split, usando o lookbackdata correto.
    """
    
    all_results = {}
    
    for fold, (train_split, test_split) in enumerate(splits):
        print_gap(f"\nFold {fold + 1}/{len(splits)}")
        
        # Treinamento
        baseline = train_baseline("PoissonRegressor", train_split)
        model = train_model("XGBRegressor", train_split)
        
        # Avaliação
        evaluator = ModelEvaluator(test_split)
        
        baseline_metrics = evaluator.evaluate(baseline, "Baseline")
        model_metrics = evaluator.evaluate(model, "XGBPoisson")
        
        # Dentro do loop principal:
        all_results[f"fold{fold+1}_baseline"] = baseline_metrics
        all_results[f"fold{fold+1}_model"] = model_metrics

    # Na análise agregada:
    df_results = compare_models(all_results)
    
    # NOVO: Backtesting completo
    from simulation.backtest import run_full_backtest

    final_test_split = splits[-1][1]  # Pega o último split de teste

    backtest_results = run_full_backtest(
        test_data=final_test_split,
        models={'Baseline': baseline, 'Model': model}
    )
    
    save_evaluation_report(df_results, "model_performance")
    backtest_results.to_excel("dados/exports/backtest_results.xlsx", index=False)
    
    # Visualização rápida
    print_gap("Desempenho Médio:", df_results.mean().to_string())
    #----------------------------------------------------------------------#
    
if __name__ == "__main__":
    main()