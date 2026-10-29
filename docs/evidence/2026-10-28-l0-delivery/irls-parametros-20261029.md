# IRLS: critério de convergência por parâmetros

O [plano prospectivo](../../superpowers/plans/2026-10-29-irls-parametros-validacao.md)
e a seed independente 904 foram commitados em `17c06ef` antes da execução.
O [harness original](nb2_profile_harness.py) e a candidata anterior por início
Poisson permanecem inalterados. A única alteração da
[nova candidata](nb2_profile_params.py) é usar `tol_criterion="params"`
no GLM NB2, com tolerância absoluta 10⁻¹⁰ e relativa zero.

Na réplica 2 da seed 204, com 600 meses e α exatamente
`exp(log(1e-6)) = 1.0000000000000004e-6`, o IRLS pela deviance não
convergiu em 100 iterações. Os coeficientes já variavam menos de 10⁻¹⁰
desde aproximadamente a terceira iteração; ao final variavam da ordem de
10⁻¹⁵, enquanto diferenças de deviance oscilavam em torno de 10⁻¹⁰–10⁻⁹.
Com o critério sobre parâmetros, o mesmo ajuste convergiu em quatro iterações
e retornou coeficientes finitos. O critério antigo usava atol=10⁻¹⁰, rtol=0;
o resultado confirma a causa numérica nesse caso específico.

| Lote | Papel | Válidos interiores | Cobertura / 30 | Viés | EP Monte Carlo | Critérios |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 204 | regressão | 30/30 | 28/30 | −0,00000824 | 0,00000848 | Passaram |
| 804 | regressão | 30/30 | 27/30 | −0,00002299 | 0,00000867 | Passaram |
| 904 | independente | 30/30 | 30/30 | −0,000000805 | 0,00000711 | Passaram |

Os três grupos também passaram no limite de viés de três EP Monte Carlo.
O resultado por réplica, a trajetória e os hashes do código estão em
`results/l0-nb2-irls-params-validation-20261029-v1.json`, SHA-256
`3f8b35b1bde84e1904cfff8581f7b6ec93fc4f90d4e07e8bfe535538574b9724`;
[script de execução](irls-params-validation.py). A regra de escore é local,
e a grade finita não prova máximo global; cobertura em 30 amostras é uma
verificação limitada. Esses resultados não ratificam o estimador em produção.

Faltam repetir com a candidata os controles Poisson/binomial e a comparação
das 14 séries reais, além de revisar os critérios e o caminho de integração.
Nenhum piloto foi refeito nem gate aprovado; E0*/FAR históricos não mudaram.
