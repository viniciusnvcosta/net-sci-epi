# Diagnóstico IRLS e primeira correção candidata

O [plano do ciclo](../../superpowers/plans/2026-10-29-irls-validacao-e-integracao.md)
fixou a mudança e seed independente 804 antes da execução. O plano ainda não
está em commit, portanto o Git não comprova sua anterioridade; não reescrever
o histórico para simular essa prova. As saídas e os hashes são preservados.

## Localização das falhas

Reexecução das dez réplicas inválidas da seed 204, com o mesmo harness e
dados, interceptando cada ajuste IRLS. As dez falhas ocorreram na grade,
nove em α=10⁻⁶ e uma em α≈2,7384×10⁻⁶; todas atingiram 100 iterações.
Isso não prova o motivo do critério de convergência nem torna dispensável a
verificação. O registro detalhado é
`results/l0-nb2-irls-diagnostic-20261029-v2.json` (SHA-256
`df35d57238d54c209b792f45a0564054238f0ae7d3fd4d010b0b64d5615ec92b`).
A v1 foi preservada, mas sua classificação de fase é incorreta: o Python 3.12
executa compreensões de lista sem a função `<listcomp>` esperada. A v2 usa
a linha de chamada; [script](irls-replay-20261029.py).

## Avaliação candidata

Alteração isolada: iniciar cada GLM NB2 pelo β do Poisson; intervalo, grade,
tolerância e limite de iterações mantidos. O lote antigo é regressão, o lote
804 é independente. Resultados em
`results/l0-nb2-irls-poisson-start-validation-20261029-v1.json` (SHA-256
`86ee4e2a7813d7b8aa5a4c625e19d88027524f332ad06beed516ff3dac04647e`),
com hashes dos códigos e todas as réplicas; [runner](irls-validation-20261029.py).

| Lote | Interiores válidos | Cobertura / 30 | Viés | 3 × EP Monte Carlo | Situação |
| --- | ---: | ---: | ---: | ---: | --- |
| 204, regressão | 22/30 | 20/30 | −0,00000809 | 0,00003076 | Falhou: oito IRLS inválidos. |
| 804, validação | 27/30 | 26/30 | −0,00001748 | 0,00002431 | Atendeu aos três limiares fixados; três IRLS inválidos. |

O lote 804 passou no limiar mínimo, mas o teste de regressão não passou. As
estimativas de viés usam somente ajustes válidos e não eliminam viés de
seleção. Não há evidência suficiente para declarar o estimador robusto ou
integrá-lo ao piloto. A mudança não foi aplicada ao código de produção e
nenhum novo piloto foi executado. Resultados anteriores permanecem intactos.
