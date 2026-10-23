# Documentação HEADD-Series L0

A entrada do projeto é o [README principal](../README.md). Em 23/10/2026,
RQ1′ permanece inconclusiva: G4 aprovado somente para o perfil fixo,
E0*/FAR reprovados, camadas incompletas e interpretação bloqueada.

## Guias e decisões atuais

- [Desenvolvimento e reprodução](development.md): ambiente, comandos e contratos;
  entradas datadas descrevem o estado de sua execução.
- [Decisões de protocolo](protocol-decisions.md): autoridade sobre regras e
  aprovações; D-G4-2026-10-23 registra o aceite científico limitado.
- [Plano global](superpowers/plans/headd-l0-global.md): estado vigente no topo,
  entregas P0–P9 e histórico de implementação abaixo; checkboxes não passam gates.
- [Fontes e perfil Gao](gao-source-preparation.md): proveniência, convenções e limites.
- [Referência CDADE](reference-provenance.md) e [migração](../MIGRATION.md):
  fontes fixadas, paridades e diferenças metodológicas.
- [Instruções de desenvolvimento](../AGENTS.md): invariantes e contratos.

## Evidência científica e técnica preservada

| Registro | Como ler |
| --- | --- |
| [23/10 — ratificação G4 e balanço preliminar](evidence/2026-10-23-g4-ratification-summary/README.md) | Síntese científica mais recente; G4 limitado, RQ1′ inconclusiva |
| [23/10 — relatório preliminar anterior à ratificação](evidence/2026-10-23-preliminary/README.md) | Snapshot preservado; seu G4 pendente antecede D-G4 |
| [22/10 — fontes e diagnósticos P5/G4](evidence/2026-10-22-p5-g4/README.md) | Bytes, medianas, clipping e replay; `pending` histórico não reescrito |
| [21/10 — diagnóstico E0*](evidence/2026-10-21-e0-diagnostics/README.md) | Auditoria somente leitura, AP/FAR e falhas preservadas |
| [PR #2 — resumos portáteis](evidence/pr-2/README.md) | Hashes e limites dos artefatos E0*/grafo históricos |

Os pacotes e manifests mantêm o estado da execução. A decisão posterior não
altera dados, resultados, seeds ou hashes. Testes, exit 0 de auditoria e
conclusão técnica não equivalem a aprovação científica.

## Especificações e planos de implementação

Estes documentos registram desenho e trabalho datado. Consulte primeiro o
protocolo e o estado vigente do plano global; planos não autorizam novos runs.

- [Arquitetura](superpowers/specs/headd-l0-architecture.md) e
  [ratificação científica de 21/10](superpowers/specs/2026-10-21-headd-l0-scientific-ratification-design.md).
- [Baseline/E0](superpowers/plans/headd-l0-e0.md),
  [grafo/simulador](superpowers/plans/headd-l0-graph-simulation.md) e
  [experimentos](superpowers/plans/headd-l0-experiments.md).
- [Continuidade de 19/10](superpowers/plans/2026-10-19-headd-l0-continuity.md),
  [diagnóstico de 21/10](superpowers/plans/2026-10-21-headd-l0-protocol-e0-diagnostics.md),
  [evidência P5/G4 de 22/10](superpowers/plans/2026-10-22-headd-l0-p5-g4-evidence.md) e
  [relatório preliminar de 23/10](superpowers/plans/2026-10-23-headd-l0-preliminary-report.md).
