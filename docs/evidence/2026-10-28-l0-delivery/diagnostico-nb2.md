# Diagnóstico NB2 do primeiro painel do piloto

Reprodução diagnóstica do endereço original `white`, ε=0, T, piloto 0,
seed raiz 20261028, com as mesmas entradas identificadas no manifesto do
piloto. Não é um novo piloto nem altera seus resultados. O
[script](diagnostico-nb2.py) e os [14 registros](diagnostico-nb2.json)
conservam os valores por série e os avisos. A dispersão residual mostrada é
Pearson Σ((y−μ̂)²/μ̂)/(60−6), com μ̂ do ajuste Poisson sobre os 60 meses de
treino; não é a variância dividida pela média dos resíduos brutos.

Em 10 das 14 séries o resultado é inválido por parâmetros não finitos. O
otimizador relatou `converged=true` nesses dez casos, apesar dos parâmetros
NaN; por isso descrevê-los apenas como “otimizador não convergiu” é impreciso.
O aviso dominante foi `invalid value encountered in log`; Tocantins também
apresentou overflow e divisão inválida. O α final desses dez ajustes é NaN,
portanto não se pode afirmar que foi estimado na fronteira zero.

Das dez séries inválidas, sete têm dispersão Pearson inferior a 1 (Baixo
Amazonas, Carajás, Metropolitanas I–III, Rio Caetés e Tocantins); Marajó I,
Marajó II e Xingu têm valores superiores a 1. Isso torna a hipótese de
equidispersão ou subdispersão plausível para parte dos casos, mas não demonstra
uma causa única. A rotina usa Newton e os avisos apontam problema numérico;
um valor Pearson alto também não prova sobredispersão NB2.

Uma série Poisson independente, seed 42, média de geração 50 e 60 valores,
reproduz saída inválida no mesmo ajuste; o teste
`tests/test_nb2_boundary_diagnostic.py` fixa esse exemplo. Isso não significa
que toda série Poisson falhe nem demonstra que Poisson é o substituto correto
para o piloto. Nenhum fallback foi implementado: uma mudança de modelo, mesmo
prospectiva e aplicada igualmente aos braços, exige critério operacional,
validação de calibração e decisão própria, pois altera o contrato NB2
ratificado. O piloto, D-COST e a bancada continuam pendentes.

MD5 da cópia local `integrated_dataset.csv`:
`d701e1865074ac3ce08277d0a51053c3`. Ainda falta comparar com o MD5 da mesma
versão oficial no Synapse; esse valor sozinho não prova identidade da fonte.
