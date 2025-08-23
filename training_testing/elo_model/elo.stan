data {
  int<lower=1> N;                  // nº de jogos
  int<lower=1> T;                  // nº de times/jogadores
  int<lower=1> K;                  // nº de pontos de tempo (ex.: semanas)
  array[N] int<lower=1, upper=T> home;
  array[N] int<lower=1, upper=T> away;
  array[N] int<lower=1, upper=3> y;        // 1=H, 2=D, 3=A
  array[N] int<lower=1, upper=K> t_idx;    // índice temporal do jogo
  vector<lower=0, upper=1>[N] w;           // 1=treino, 0=teste (não entra na like)
  real<lower=0> s;                         // escala Elo (fixe: 400)
}

parameters {
  // Ratings dinâmicos (random walk não-centrado)
  vector[T] theta0;
  matrix[T, K-1] eta;
  real<lower=0> tau;
  real<lower=0> sigma0;

  // Empates dinâmicos: lambda_t = log(nu_t)
  real lambda0;
  vector[K-1] z_lambda;
  real<lower=0> sigma_lambda;
}

transformed parameters {
  matrix[T, K] theta;
  vector[K] lambda;
  vector<lower=0>[K] nu_t;

  // Trajetória dos ratings
  for (i in 1:T) theta[i,1] = theta0[i];
  for (k in 2:K)
    for (i in 1:T)
      theta[i,k] = theta[i,k-1] + tau * eta[i,k-1];

  // Identificabilidade: centraliza por tempo
  for (k in 1:K) {
    real m = mean(theta[,k]);
    for (i in 1:T) theta[i,k] -= m;
  }

  // Random walk para log-nu
  lambda[1] = lambda0;
  for (k in 2:K)
    lambda[k] = lambda[k-1] + sigma_lambda * z_lambda[k-1];

  // nu_t > 0
  for (k in 1:K)
    nu_t[k] = exp(lambda[k]);
}

model {
  // Priors
  theta0 ~ normal(0, sigma0);
  to_vector(eta) ~ normal(0, 1);
  tau ~ normal(0, 50);         // half-normal (via lower=0)
  sigma0 ~ normal(0, 200);

  lambda0 ~ normal(log(0.5), 0.5);  // mediana ~0.5 em nu
  z_lambda ~ normal(0, 1);
  sigma_lambda ~ normal(0, 0.5);    // half-normal

  // Verossimilhança ponderada (apenas w=1 contribui)
  for (n in 1:N) {
    int i = home[n];
    int j = away[n];
    int k = t_idx[n];
    real c = log(10) / (2*s);
    real r = exp(c * (theta[i,k] - theta[j,k]));
    real denom = r + inv(r) + 2 * nu_t[k];
    vector[3] p;
    p[1] = r / denom;              // P(H)
    p[2] = 2 * nu_t[k] / denom;    // P(D)
    p[3] = inv(r) / denom;         // P(A)
    target += w[n] * categorical_lpmf(y[n] | p);
  }
}

generated quantities {
  vector[N] log_lik;
  array[N] vector[3] pred_probs;
  array[N] int y_rep;

  for (n in 1:N) {
    int i = home[n];
    int j = away[n];
    int k = t_idx[n];
    real c = log(10) / (2*s);
    real r = exp(c * (theta[i,k] - theta[j,k]));
    real denom = r + inv(r) + 2 * nu_t[k];
    vector[3] p;
    p[1] = r / denom;
    p[2] = 2 * nu_t[k] / denom;
    p[3] = inv(r) / denom;

    pred_probs[n] = p;
    log_lik[n] = categorical_lpmf(y[n] | p);
    y_rep[n] = categorical_rng(p);
  }
}
