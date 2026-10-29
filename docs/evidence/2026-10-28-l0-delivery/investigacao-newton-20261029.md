# Investigação dos ajustes NB2 — 29/10

O `statsmodels` instalado é 0.15.0. A inspeção de
`NegativeBinomial.fit` confirma: `newton` opera diretamente em α; `bfgs`
opera em log α e converte de volta no retorno. Em `_fit_newton`, o laço usa
`np.any(abs(newparams - oldparams) > tol)`: quando todas as comparações são
falsas devido a NaN, ele termina antes de `maxiter` e registra convergência.
O projeto já rejeita o resultado se parâmetros forem não finitos.

Na reprodução diagnóstica da série sintética original, `retall=True` mostra
as sequências de α: Marajó I `0,001 → -0,00004917 → NaN`; Marajó II
`0,001 → -0,00274508 → NaN`; Xingu `0,001 → -0,00064306 → NaN`.
Nos três, Newton retornou `converged=true`. Isso demonstra o passo fora do
domínio e a indicação enganosa de convergência para esses ajustes; não prova
que o ótimo de todos eles é interior.

Foi executado um ensaio diagnóstico com BFGS, mesma série sintética, 500
iterações máximas e tolerância padrão da biblioteca. No painel sintético,
Marajó I teve α=0,000335914 e convergência declarada; Xingu teve α=0,000330333,
mas BFGS não declarou convergência; Marajó II também não convergiu. Alguns
ajustes que Newton havia considerado válidos igualmente não convergiram com
BFGS. Logo uma troca simples por BFGS não basta para declarar o piloto válido.
Detalhes e diferenças de log-verossimilhança com o ajuste Poisson estão em
[comparação BFGS](comparacao-bfgs-20261029.txt), reproduzível pelo
[script](comparacao-bfgs-20261029.py), que utiliza o diagnóstico anterior.

Na fixture real versionada `tests/reference/data.npz`, os 14 ajustes BFGS
declararam convergência; o maior desvio absoluto entre os sete parâmetros
de cada série e o resultado Newton foi aproximadamente 5,02×10⁻⁶. É uma
comparação exploratória, não uma tolerância previamente registrada nem prova
de igualdade de scores, limiares ou FAR; E0* e seus resultados históricos
não foram reexecutados nem alterados.

Poisson é o limite de NB2 quando α tende a zero; o contrato técnico atual,
entretanto, exige `alpha > 0` na validação e na amostragem de nulos. Suportar
α=0 requer uma implementação explícita também para amostragem Poisson e uma
decisão prospectiva sobre diagnóstico de fronteira, erro numérico e aplicação.
Uma dispersão de Pearson inferior ou superior a 1, isoladamente, não prova
onde está o máximo da verossimilhança. Um teste de razão de verossimilhança
com significância não é automaticamente equivalente a declarar o MLE na
fronteira; uma tolerância em α precisa levar em conta escala e precisão.

Ainda faltam um teste de regressão que falhe para o caso interior observado,
critério de fronteira justificável, testes Poisson e binomial para esse
critério, validação dos 14 ajustes reais com tolerâncias declaradas e revisão
da implementação. Nenhuma nova regra foi congelada nem houve novo piloto com
correção. A repetição idêntica anterior apenas confirmou reprodutibilidade.
