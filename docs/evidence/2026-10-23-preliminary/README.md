# Relatório preliminar HEADD L0 — 23/10/2026

## Decisão

O resultado preliminar de RQ1′ é **inconclusivo**. A evidência disponível não
permite concluir se a adjacência geográfica melhora a detecção de surtos sob
FAR comparável. Falha de gate e comparação indisponível não demonstram ausência
de benefício. Um resultado negativo válido seria conclusivo, mas exige as
camadas 0, 1 e 2 completas e todos os gates aplicáveis aprovados.

Este registro resume evidência preservada; não relata nova execução ou decisão
científica. Regras e perfil ratificados não equivalem a gates aprovados.

## Estado dos gates e camadas

| Item | Estado em 23/10 | Evidência e motivo |
| --- | --- | --- |
| E0 | Inconclusivo | D-G0 registrou o resultado; não é conclusão sobre RQ1′. |
| E0* | Falhou | B1* não superou o baseline causal z-score conforme o gate `trivial_baseline`; limite inferior histórico do IC pareado: −0,20186060618499926. |
| FAR real | Falhou | Três pares fora da banda bilateral pré-fixada; detalhes abaixo. |
| G4 | Pendente | Bytes/fontes e replay verificados, mas revisão científica explícita dos diagnósticos fixos, inclusive clipping, aguarda decisão. |
| Camada 0 | Não elegível para conclusão | E0* falhou; a comparação de não inferioridade B2−B1* do D-GT1 não foi concluída. |
| Camada 1 | Não concluída | Injeção epidêmica em contagens reais e runner ainda não implementados. |
| Camada 2 | Não executada | O smoke/D-REACH não é a comparação da bancada; bancada completa ausente. |
| Interpretação RQ1′ | Bloqueada | `interpretation_allowed=false`. |

## Evidência descritiva preservada

O [diagnóstico somente leitura de E0* (21/10)](../2026-10-21-e0-diagnostics/README.md)
audita o run de 30/09, sem corrigir baseline, recalibrar limiares ou refazer
gates. Nas 13 regiões, a média de AP foi 0,5471615985 para B1* e 0,6781268454
para z-score causal; B1* teve AP menor em 12/13 regiões. A perda média pareada
de AP(B1*−z-score) foi −0,1309652469. Esses valores descrevem desempenho no
run preservado e sustentam a falha E0*; não estimam o efeito de adjacência.

A FAR avaliada usou 14.400 meses por tarefa/braço. Falharam ARAGUAIA/B1*,
XINGU/B1* e RIO CAETES/zscore; as três FAR ficaram abaixo da banda alvo
`1/60 ± 1/300`. Os 14 ajustes NB2 convergiram; a falha não foi atribuída a
fallback ou ajuste inválido. O limiar, tolerância, seed, pool e seletor não
foram alterados. PA teve 72 meses positivos e zero negativos, portanto AP
indefinida; permanece apenas descritiva.

O [pacote P5/G4 (22/10)](../2026-10-22-p5-g4/README.md) registra checks das
fontes oficiais e seis pares de medianas arquivadas reproduzidos, 384 realizações
mensais primárias concluídas (192 T, 192 N), 64 T e 64 N por ruído, janelas
AR1/CV válidas em todas as células e replay exato. Os controles técnicos
registrados passaram. Na caracterização arquivada, AR1(T)>AR1(N) nos três
ruídos; CV(T)<CV(N) em white e CV(T)>CV(N) em env/dem. Na adaptação mensal,
medianas são descritivas e não recebem sinais CV impostos pela fonte.

Clipping de I na fase de surto da execução mensal inclui 1.478/43.968 passos
para T/white (3,36%) e 743/43.968 para T/dem (1,69%); clipping de S foi zero.
A documentação pede revisão científica para clipping white e dem. Não há
limiar numérico de clipping/validade aprovado; este relatório não cria um.
A verificação de fonte, equações, testes técnicos e replay não constituem
aprovação de G4.

D-REACH passou como checagem prévia de alcance: em ε=0, nas 600 realizações T,
não houve onset fora da região semente e as contagens dessas regiões
coincidiram com as gêmeas; em ε=0,20 a fração
com onset em vizinho excedeu 50% nos três ruídos. Isso não mede detecção nem
substitui camada 2. O smoke D-COST teve falhas técnicas D5/FAR em cobertura
parcial; não foi inferência da bancada.

## Por que o resultado não é conclusivo

- E0* e a FAR real falharam no run preservado. O diagnóstico não encontrou
  defeito de implementação independente que autorizasse correção e nova rodada.
- G4 aguarda revisão científica explícita dos diagnósticos fixos; em particular,
  a frequência de clipping white/dem não tem cutoff ratificado.
- Não há comparação de camada 0 que passe não inferioridade; camada 1 está
  incompleta e camada 2 não foi executada. D-REACH é pré-requisito de alcance,
  não efeito de detecção.
- Sem gates aprovados, cobertura completa e FAR comparável, nem conclusão
  positiva nem negativa sobre RQ1′ é autorizada. Incompletude não é evidência
  de efeito nulo.

## Próximas etapas elegíveis

1. Registrar decisão científica explícita sobre G4 após revisar clipping e os
   demais diagnósticos fixos, sem inventar cutoff retrospectivo.
2. Manter a falha E0*/FAR histórica; só considerar novo gate sob plano separado
   se surgir defeito de implementação demonstrado independentemente por teste.
3. Após pré-requisitos, completar a comparação obrigatória de camada 0, planejar
   camada 1 sob spec própria e executar camadas 1/2 com IDs, denominadores,
   FAR e gates pré-registrados. Relatar resultado válido, inclusive se negativo.

## Fontes e protocolo

- [Diagnóstico E0* e FAR, 21/10](../2026-10-21-e0-diagnostics/README.md)
  ([JSON](../2026-10-21-e0-diagnostics/diagnostics.json)).
- [Evidência P5/G4, 22/10](../2026-10-22-p5-g4/README.md)
  ([JSON](../2026-10-22-p5-g4/verification.json)).
- [Decisões de protocolo](../../protocol-decisions.md), especialmente D-G0,
  D-E0*-R1 e D-RATIFY-2026-10-21.
- [Spec de ratificação](../../superpowers/specs/2026-10-21-headd-l0-scientific-ratification-design.md),
  §§1, 4 e 5; [plano global](../../superpowers/plans/headd-l0-global.md).
