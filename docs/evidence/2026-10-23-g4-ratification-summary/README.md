# HEADD L0 — ratificação G4 e balanço preliminar, 23/10/2026

O autor aprovou explicitamente em chat em **23/10/2026** a ratificação científica
limitada de **G4 para `P5-IMPL-2026-10-19-v1`**, aceitando clipping e limitações
do observável do [pacote de 22/10](../2026-10-22-p5-g4/README.md).
Ver [D-G4-2026-10-23](../../protocol-decisions.md#d-g4-2026-10-23).
Nenhum outro gate foi aprovado; `interpretation_allowed=false`.
**RQ1′ permanece inconclusiva**, sem conclusão de benefício ou ausência de benefício.

## Entregas frente ao plano global

O [plano global](../../superpowers/plans/headd-l0-global.md) separa implementação,
validação técnica e aprovação científica:

| Etapa | Entrega e estado vigente |
| --- | --- |
| P0 | Auditoria concluída; D-G0 autoriza B1*; E0 inconclusivo. |
| P1 | Dados, hashes, ordem canônica e coerência 13→1 em 132 meses validados tecnicamente (G1). |
| P2 | Componentes existentes; comportamento corrigido separado de paridade de primitivas. |
| P3 | NB2 convergente implementado/validado tecnicamente; E0*/FAR falharam; G2 não aprovado. |
| P4 | A/W, mapa, GEXF e 30 placebos entregues/validados tecnicamente; G3 não aprovado. |
| P5 | Simulador, fixture, fontes e diagnósticos entregues; G4 aprovado somente para o perfil fixo em 23/10. |
| P6 | Features locais/relacionais integradas e validadas tecnicamente; G5 não aprovado. |
| P7 | Runner reduzido e smoke implementados; D-COST representado; FAR/G6 não aprovados. |
| P8 | Camadas 0/1/2 incompletas; camada 1 não implementada; bancada não executada; G7 não aprovado. |
| P9 | Exportador descritivo/notebook entregues no PR #3, exit 2; sem interpretação autorizada. |

## Evidência preliminar preservada

No [diagnóstico E0*](../2026-10-21-e0-diagnostics/README.md), 13 pares regionais
usam 72 meses (60–131), com ambas as classes. AP média B1* = 0.5471615984892939
e z-score = 0.6781268454330207; ΔAP média = −0.13096524694372677;
B1* inferior em **12/13** regiões. O limite inferior histórico do IC95% é
−0.20186060618499926: E0* falhou `trivial_baseline`. PA tem 72 positivos e
0 negativos, AP indefinida e exclusão do pareamento regional. O diagnóstico
não demonstrou defeito independente que autorize corrigir/reexecutar E0*.

A FAR de avaliação usa **200×72 = 14.400 meses por par região/braço**,
alvo 1/60 e tolerância 1/300, banda inclusiva 0.013333333333333332–0.02.
Falharam ARAGUAIA/B1* (0.012986111111111111), XINGU/B1*
(0.012777777777777779) e RIO CAETES/zscore (0.01138888888888889),
todos abaixo da banda; calibração e avaliação são distintas.

Em [P5/G4](../2026-10-22-p5-g4/README.md), bytes oficiais, rótulos e seis
pares de medianas arquivadas foram verificados. Cada tabela-fonte tem
12.000 linhas (6.000 T/6.000 N). AR1 T>N nos três ruídos; CV T>N em env/dem,
mas white T<N (0.7695323012078741 < 0.8337873367675575). A fonte observa I
em 400 observações; contagens mensais não recebem gate artificial de sinal CV.
A fixture verifica álgebra, não reprodução exata de trajetórias upstream.

O diagnóstico fixo tem **64 T e 64 N independentes por ruído**: 384 realizações
primárias e 768 controles θ, total de 1.152 chamadas por pacote. Twins não
ampliam o denominador N independente. CV/AR1 válidos em **64/64** janelas
em cada uma das seis células; cinco checks técnicos passam em **384/384**
endereços; replay exato. No período `outbreak`, clipping de I white T/N =
**1478/43968 (3,36%)/2829/43968 (6,43%)**; dem =
**743/43968 (1,69%)/1335/43968 (3,04%)**; env = **0/43968** T e N.
S não sofreu clipping. Burn-in, twins, controles e denominadores completos
estão no pacote; não se inventou cutoff retrospectivo. Fluxos latentes mensais
realizados não foram reconstruídos independentemente.

O aceite G4 incorpora essas limitações e aceita o perfil sintético fixo;
não estima parâmetros de Pará nem afirma replicação exata das trajetórias
originais ou paridade de separação T/N entre I e contagens mensais.
Os **76 testes direcionados** e **466 testes, 1 deselectado**, além de Ruff,
são verificações anteriormente registradas em 22/10; não foram reexecutadas
nesta tarefa documental. Exit 2 dos pacotes indica interpretação bloqueada.

[D-REACH de 20/10](../../protocol-decisions.md#d-costd-reach--execução-condicionada-de-20102026),
com **200 T/célula**, registrou onset em vizinho em ε=.20: white
**165/200 (82,5%)**, env **132/200 (66%)**, dem **153/200 (76,5%)**.
Em ε=0 foram **0/200 por ruído** (600 T), com contagens não-semente iguais
às twins. O critério ≥50% passou, mas alcance não é ganho de detecção.
No smoke limitado a três detectores, D5 falhou em **5/12** réplicas e FAR
passou em apenas **28/858** pares; isto não estima a bancada completa.

## Limites e próximos gates

Faltam não-inferioridade da camada 0 (D-GT1), implementação/execução da
camada 1 e bancada completa das camadas obrigatórias 0/1/2, além de E0*,
FAR comparável e todos os demais gates aplicáveis. A bancada estimada em
82–105 h não foi executada. G4 não autoriza novos experimentos, reajustes,
outras aprovações ou inferência RQ1′.

Os manifests e o pacote de 22/10 preservam `pending` e
`scientific_review=not_requested`, estados históricos da execução. A decisão
posterior de 23/10 não reescreve artefatos, seeds, perfil ou hashes anteriores.
