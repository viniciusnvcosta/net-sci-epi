# Estado da implementação — 28/09/2026

Este registro acompanha a integração local dos componentes da branch
`feat/headd-l0-e0-audit` em `develop` e, em seguida, em `main`.
Este quadro registra a integração das Tasks 1–8. A atualização da Task 9,
seu diagnóstico e a preparação do ambiente estão em
[e0-task9-status.md](e0-task9-status.md), que substitui as pendências abaixo.

## Componentes e evidências

| Task | Entrega | Commit | Validação |
|---|---|---|---|
| 1 | Auditoria do CDADE no SHA fixado e ferramentas de teste | d72337c | Auditoria insuficiente para paridade; diagnóstico preservado |
| 2 | Contagens SIVEP e hierarquia | c60fb08 | Paridade exata com arrays exportados |
| 3 | NB2, S, bottom-up e MinT shrinkage | 29b9c91 | Coerência, shrinkage e ausência de look-ahead |
| 4 | Pool de seis detectores, incluindo FAST-MCD próprio | 38b5685 | 29 testes; revisão independente aprovada |
| 5 | EVT/GPD e calibração da FAR | 576e351, 39e8312 | 17 testes; revisão independente aprovada após correção de arredondamento |
| 6 | Seleção causal, competência e reset | f2df82f | 14 testes; revisão independente aprovada |
| 7 | Métricas e censura explícita | 11250b2 | 9 testes; revisão independente aprovada |
| 8 | Bootstrap pareado e protocolo estatístico | 43b07ef, 0ca1ad7 | 14 testes; fixtures adicionais atendem à revisão |
| 9 | Injeção, runner, configurações e gate E0* | — | Pendente |

TDD e registros de RED/GREEN dos componentes estão no workspace local
`.superpowers/sdd/2026-09-26-headd-l0-e0/` da worktree de implementação.
As revisões individuais das Tasks 4–8 verificam especificação e qualidade.
A revisão independente final das Tasks 1–8 aprovou esse escopo sem bloqueios;
as duas lacunas de cobertura da Task 8 foram verificadas e encerradas.
A cobertura adicional da Task 4 confirma que mudar uma coluna descartada
por ser constante no treino não altera o score.

Validação antes da integração: `uv run pytest -o addopts='' -q`, 119 testes
(incluindo os dois de referência); `uv run ruff check .` e
`uv run ruff format --check .` limpos. Os merges devem ser validados também
na pasta original. As decisões e diferenças metodológicas estão em
[protocol-decisions.md](protocol-decisions.md) e [MIGRATION.md](../MIGRATION.md).

## Limites e próximos passos

- E0 permanece **inconclusivo**; B1* está autorizado por D-G0.
  E0* ainda **não foi executado**. Testes dos componentes não aprovam esse gate.
- A conexão dos componentes por nomes de configuração, os artefatos finais
  em `results/<run_id>/` e seus manifests dependem da Task 9. Portanto, a
  definição de pronto do pipeline completo ainda não foi satisfeita.
- A Task 9 precisa conciliar duração de 3–6 meses com a proposta de
  truncamento no mês 131; a escolha foi submetida ao usuário e continua
  pendente. Também precisa compatibilizar PA independente na caracterização
  legada com PA coerente exigido pelo caminho B1*.
- O runner deve verificar explicitamente a convergência dos ajustes NB2;
  previsões finitas não bastam para aceitar um ajuste.
- A não-inferioridade D-GT1 usa 13 regiões; PA é reportado separadamente.
- As 409 médias reconciliadas negativas observadas permanecem sem clipping,
  conforme D2. O diagnóstico não foi usado para ajustar o modelo.
- Perfil do simulador e faixa de R0 continuam pendentes; não há resultado E1′.

## Preservação operacional

A pasta original é `/home/vinvs/projects/net-sci-epi`; a worktree de revisão
é `/home/vinvs/projects/net-sci-epi-e0`. A worktree permanece disponível,
inclusive com seus registros locais de revisão. Nenhum push é necessário.
As alterações locais prévias do usuário não integram commits de tarefa:
foram preservadas no stash `097f1fba3a1b6fb19ef7abb4cd2badf279b39b6c`
para reconciliação depois dos merges. `AGENTS.md` não versionado é preservado.
