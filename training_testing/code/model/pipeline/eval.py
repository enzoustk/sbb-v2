# evaluate.py
from typing import Dict
from utils import print_gap
from scipy.stats import norm, gaussian_kde
from data.feature.constants import TARGET_COL, MODEL_FEATURES
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os, numpy as np, pandas as pd, seaborn as sns, matplotlib.pyplot as plt

class ModelEvaluator:
    def __init__(self, test_split, max_value: float = 5.0):
        self.X = test_split.filter(items=list(MODEL_FEATURES))
        self.y_true = test_split[TARGET_COL].values.astype(float)
        self.max_value = max_value
        self.bins = np.linspace(0, max_value, num=50)

    def _calculate_probabilistic_metrics(self, y_pred: np.ndarray) -> Dict:
        """Métricas para variáveis contínuas"""
        # Calcular densidade de probabilidade
        kde = gaussian_kde(y_pred)
        prob_density = kde(self.y_true)
        
        # Log probability com clipping para evitar underflow
        log_prob = np.log(np.clip(prob_density, 1e-8, None))
        
        return {
            'log_probability': np.mean(log_prob),
            'energy_score': self._energy_score(y_pred)
        }

    def _energy_score(self, y_pred):
        """Score baseado em distâncias para distribuições contínuas"""
        diff = y_pred[:, None] - self.y_true[None, :]
        return -np.mean(np.abs(diff).mean(axis=1))

    def _calculate_distribution_metrics(self, y_pred: np.ndarray) -> Dict:
        """Métricas de distribuição contínua"""
        from scipy.stats import ks_2samp
        
        # Teste de Kolmogorov-Smirnov
        ks_stat, ks_pvalue = ks_2samp(self.y_true, y_pred)
        
        return {
            'ks_statistic': ks_stat,
            'ks_pvalue': ks_pvalue
        }

    def _calculate_point_metrics(self, y_pred: np.ndarray) -> Dict:
        """Métricas tradicionais de regressão"""
        return {
            'mae': mean_absolute_error(self.y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(self.y_true, y_pred)),
            'r2': r2_score(self.y_true, y_pred)
        }

    def evaluate(self, model, model_name: str) -> Dict:
        """Executa avaliação completa para um modelo"""
        # Previsões contínuas
        y_pred = model.predict(self.X)
        
        metrics = {}
        metrics.update(self._calculate_point_metrics(y_pred))
        metrics.update(self._calculate_probabilistic_metrics(y_pred))
        metrics.update(self._calculate_distribution_metrics(y_pred))
        
        # Plotar distribuições
        self._plot_density_comparison(y_pred, model_name)
        
        return metrics

    def _plot_density_comparison(self, y_pred, model_name):
        """Salva gráfico em arquivo sem mostrar na tela"""
        plt.figure(figsize=(10, 6))
        sns.kdeplot(self.y_true, label='Real', bw_adjust=0.5)
        sns.kdeplot(y_pred, label='Previsto', bw_adjust=0.5)
        plt.title('Comparação de Densidade: Real vs Previsto')
        plt.xlabel('Gols por Minuto')
        plt.legend()
        
        # Cria o diretório se não existir
        plot_dir = 'dados/plots'
        os.makedirs(plot_dir, exist_ok=True)
        
        # Usar nome do modelo no filename (sanitizado)
        safe_name = model_name.lower().replace(" ", "_")
        # Salvar em arquivo
        plt.savefig(f'{plot_dir}/density_comparison_{safe_name}.png')
        plt.close()

    def _predict_proba(self, model, X) -> np.ndarray:
        """Retorna matriz de densidades de probabilidade"""
        y_pred = model.predict(X)
        std = y_pred.std()
        
        # Criar grid de valores
        x_grid = np.linspace(0, self.max_value, 100)
        
        # Calcular densidades
        probas = np.zeros((len(X), len(x_grid)))
        for i, mu in enumerate(y_pred):
            probas[i] = norm.pdf(x_grid, loc=mu, scale=std)
        
        # Normalizar
        probas /= probas.sum(axis=1, keepdims=True)
        return probas

def compare_models(results: Dict[str, Dict], baseline_keyword: str = '_baseline') -> pd.DataFrame:
    """Compara modelos agregando resultados por tipo (baseline vs modelo)"""
    # Converter para DataFrame
    df = pd.DataFrame(results).T
    
    # Separar baseline e modelos
    baseline_mask = df.index.str.contains(baseline_keyword)
    df_baseline = df[baseline_mask].mean().to_frame('Baseline')
    df_model = df[~baseline_mask].mean().to_frame('Model')
    
    # Juntar resultados
    df_combined = pd.concat([df_baseline, df_model], axis=1)
    
    # Calcular melhorias
    df_combined['Improvement (%)'] = ((df_combined['Baseline'] - df_combined['Model']) / 
                                     df_combined['Baseline']) * 100
    
    return df_combined

def save_evaluation_report(results: pd.DataFrame, filename: str):
    """Salva resultados formatados"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = "dados/exports/"
    full_name = f"{file_path}{filename}_{timestamp}.csv"
    
    # Resetar índice para métricas virarem coluna
    results.reset_index(names='Metric').to_csv(full_name, index=False)
    print_gap(f"Relatório salvo como {full_name}")