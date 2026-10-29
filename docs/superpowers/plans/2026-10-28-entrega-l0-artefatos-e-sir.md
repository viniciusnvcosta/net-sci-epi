# Entrega L0 — plano de implementação

> **Para execução:** usar `superpowers:executing-plans` em modo nativo, com
> SDD e TDD de baixo custo. Cada tarefa termina em verificação e commit local.

**Objetivo:** entregar grafo candidato rastreável e apresentação corrigida;
preparar e, se orçamento e pré-condições permitirem, executar demonstração SIR
exploratória; especificar GANF para estudo futuro.

**Arquitetura:** quatro entregas independentes — grafo/população, reprodução da
série, apresentação e protocolo/runner exploratório — coordenadas por um índice
de evidências. O runner exploratório é separado de `e1_bench`; ele lê artefatos
identificados e nunca altera os gates ou os runs anteriores.

**Stack:** Python ≥3.12, uv, numpy, pandas, geopandas, networkx, pytest, ruff;
PPTX: `python-pptx` somente se necessário, instalado com `uv add` e registrado.

**Spec:** [entrega L0](../specs/2026-10-28-entrega-l0-protocolo-exploratorio-design.md).

## Restrições globais

- Prazo de preparação: 30/10/2026, fim do dia, America/Fortaleza. Prioridade:
  grafo + evidências + apresentação; não sacrificar estes para uma bancada.
- Branch `docs/l0-delivery-protocol` criada de `develop`; `main` intocada.
  Preservar alterações preexistentes, PPT original, dados brutos e v1/v2/P4.
- Candidata v2 SHA-256 `7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0`;
  os dados e resultados estão no worktree irmão `castro-data-provenance` e não
  devem ser copiados cegamente, alterados, nem presumidos disponíveis noutro host.
- `interpretation_allowed=false`; G3 pendente, E0*/FAR históricos reprovados,
  G4 limitado a P5, RQ1′ inconclusiva. Sem reexecução de E0*; sem M, OD, GANF
  ou GNN implementados. Nenhum upload ou contato externo.
- Escrita somente em destinos novos; publicação atômica sem substituição, hashes
  de entradas/saídas e erro que impeça pacote parcial parecer completo.
- Trabalhar com `UV_PROJECT_ENVIRONMENT=/home/vinvs/projects/net-sci-epi/.venv`,
  `UV_CACHE_DIR=/tmp/headd-uv`, `MPLCONFIGDIR=/tmp/headd-mpl`, `PYTHONPATH=src`
  e `uv run --no-sync` quando o ambiente instalado for suficiente. Se necessário
  adicionar dependência, `uv add` na branch; registrar motivo e custo.

## Review Focus

| Falha | Comportamento | Teste |
| --- | --- | --- |
| Censo de 2010 não tem um município criado depois | Não duplicar nem inventar população; compatibilizar apenas com prova territorial e regional | `test_pre2013_aggregation` (Task 1) |
| Matriz ou crosswalk divergente | Nenhum pacote completo; motivo e hashes | `test_export_rejects_bad_binding` (Task 1) |
| Painel tem uma célula ausente ou contagens diferentes | Reportar diferença; não igualar ausência clínica a zero | `test_panel_missing_and_difference` (Task 2) |
| Runner lê placebo diferente de v2 ou altera A do gerador | Falhar antes de simular; prova de invariância da entrada | `test_candidate_binding_and_generator` (Task 4) |
| Destino já existe ou execução falha no meio | Não substituir nem publicar manifesto final | `test_publish_atomic_no_replace` (Tasks 1 e 4) |

## Estrutura e dependências

- `src/headd_l0/delivery_graph.py`, `tests/test_delivery_graph.py`: consumo de
  candidato e população, validação e exportação GraphML.
- `src/headd_l0/panel_reproduction.py`, `tests/test_panel_reproduction.py`:
  agregação em blocos e serialização canônica; sem alterar loader histórico.
- `docs/evidence/2026-10-28-l0-delivery/`: índice e dados de proveniência;
  `results/l0-delivery-graph-v1/` e `results/l0-panel-reproduction-v1/`:
  saídas locais novas e independentes.
- `docs/protocols/2026-10-28-sir-exploratorio.md`,
  `configs/l0_exploratory.toml`, `src/headd_l0/exploratory.py`,
  `tests/test_exploratory.py`: contrato pré-registrado, runner isolado e piloto.
- `docs/research/2026-10-28-ganf-protocolo-futuro.md`: apenas desenho.
- `results/l0-delivery-slides-v1/`: cópia do PPT; preservar arquivo original.
  Se dependência ou edição fiel indisponível, apresentar roteiro de correções e
  declarar PPT pendente; não trocar formato final silenciosamente.

## Task 1: População de 2010 e exportação do grafo

**Consumes:** manifesto v2 e `configs/l0_fixed_geography.toml` do worktree irmão;
fonte oficial IBGE Censo 2010 por município, população residente total.
**Produces:** `export_graph(a, w, regions, population, output) -> None` e pacote
GraphML direcionado + manifesto + referência por hash aos mapas e matrizes.

- [ ] Adquirir fonte oficial e documentação da população total residente,
      ano e licença; registrar URL, data, SHA-256, tabela e unidade. A
      [sinopse do IBGE](https://www.ibge.gov.br/estatisticas/sociais/saude/9662-censo-demografico-2010.html?lang=pt-BR)
      descreve dados municipais; verificar bytes e colunas da tabela escolhida.
      Se acesso falhar, registrar impedimento e seguir com Tasks 2 e 3.
- [ ] Resolver compatibilidade temporal antes de somar: Mojuí dos Campos foi
      instalado em 2013 e desmembrado de Santarém ([IBGE](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15761-areas-dos-municipios.html?edicao=30133&t=downloads));
      na relação candidata `150475` e `150680` pertencem ambos a `15002`.
      Contar a população de 2010 do município ancestral uma vez, e não atribuir
      um valor inventado a Mojuí. Verificar explicitamente outros desmembramentos,
      cardinalidade e correspondência regional; qualquer ancestral que cruza
      regiões exige documentação/fonte adicional e bloqueia soma exata.
- [ ] Escrever testes: `test_pre2013_aggregation` com um ancestral e dois
      descendentes na mesma região soma uma vez, e com regiões diferentes falha;
      `test_export_rejects_bad_binding` adultera matriz ou mapa; `test_graphml_roundtrip`
      exige 13 nós, 52 arcos, códigos, população, tipo Queen e peso W orientado
      da linha `i` para coluna `j`; `test_publish_atomic_no_replace` preserva
      destino e falha de renderização não publica manifesto final.
- [ ] Rodar `uv run --no-sync pytest tests/test_delivery_graph.py -q`; esperado
      RED por módulo ausente. Implementar validação, agregação e exportação com
      `networkx.write_graphml`; usar `_publish` e `allow_pickle=False`.
- [ ] Rodar teste focado GREEN, Ruff e round-trip; gerar pacote somente após
      commit do código, sem sobrescrever. Validar 25/26 arestas e 1 adição,
      hashes dos arquivos e atributo populacional não negativo.
- [ ] Commit apenas código/testes/documentação próprios:
      `feat: export traceable candidate geography`.

## Task 2: Reprodução semântica do painel

**Consumes:** `integrated_dataset.csv` local, CSV regional L0, `data.hierarchy()`.
**Produces:** `canonical_panel(groups: DataFrame) -> tuple[np.ndarray, np.ndarray]` com
contagens positivas e totais `(13,132)` e identidade canônica; relatório imutável com
comparação de ambos painéis e hashes de entradas.

- [ ] Escrever `test_panel_missing_and_difference`: fixture com região-mês
      ausente falha; uma contagem alterada é reportada; categorias negativas
      são excluídas somente do numerador, grupos observados sem uma categoria
      valem zero nessa categoria. `test_canonical_panel_order` embaralha linhas
      e obtém arrays e hashes idênticos. A canonicalização fixa ordem das 13
      regiões, `MONTHS`, dtype `int64` little-endian e bytes C-contíguos;
      hash inclui identificação de shape, nomes, meses e os dois arrays.
- [ ] Rodar testes para RED; implementar leitura em blocos com as seis colunas
      já utilizadas na auditoria, sem imprimir ou publicar microdados.
- [ ] Rodar testes GREEN e commitar o código; processar fonte de 4,4 GB após verificar
      SHA-256 `0a82aaecb02c5854149e22235a9e460abd82780d824c54ae5bd0fbd17902d05e`,
      registrar bytes/tamanho antes e depois, comparar valores e hashes
      canônicos com `data.load_sivep` da base L0. A igualdade esperada é
      resultado a medir, não condição para reexecutar E0*. Em caso de falha,
      preservar discrepâncias e seguir com slides de limitação.
- [ ] Acrescentar ao índice os resultados sobre 7.592 contagens, Bonito, as
      versões e IDs `syn21555930` dataset / `syn21555933` dicionário com
      [fonte primária](https://pmc.ncbi.nlm.nih.gov/articles/PMC7271548/).
- [ ] Commit `feat: reproduce regional surveillance panel` antes da execução
      real; depois, commit separado do índice de resultados.

## Task 3: Apresentação e dossiê

**Consumes:** PPT original `/mnt/c/Users/vinic/Downloads/HEADD-Series L0_ Metodologia, Resultados Preliminares.pptx`,
resultado Tasks 1–2 e evidências históricas. **Produces:** cópia PPTX nova,
hash, relação de alterações por slide e índice `docs/evidence/2026-10-28-l0-delivery/README.md`.

- [ ] Extrair textos/estrutura de todos os slides e localizar por conteúdo,
      não apenas por número, as afirmações 500 T/500 N, 9.000 e poder/alcance.
      Registrar SHA-256 original antes e depois; nunca alterar arquivo original.
- [ ] Corrigir a cópia mantendo estilo e objetos: orçamento original versus
      D-COST camada 2 (200 T, 200 N avaliação e 200 N calibração por célula;
      100 T fixados para placebos), alcance como propagação, "testar", estado
      das etapas PA/E0*/FAR, candidato e RQ1′ inconclusiva. Inserir figura e
      fonte da população somente se verificadas; se não, sinalizar pendência.
- [ ] Verificar PPTX abre, número de slides, textos alterados, preservação do
      original por hash e leitura dos slides; se ferramenta de renderização
      disponível, inspecionar visualmente; se não, declarar ausência de inspeção.
      Registrar versão da biblioteca e hashes do PPTX resultante.
- [ ] Atualizar índice com caminhos, hashes, bloqueios, acesso e limites;
      validar links locais versionados e `git diff --check`.
- [ ] Commit `docs: prepare l0 presentation evidence`. A saída PPTX é local e
      não versionada; o índice é versionado. Esta tarefa não depende da Task 4.

## Task 4: Congelar protocolo, runner e piloto exploratório

**Consumes:** candidata v2 (A,W, 30 placebos e nomes), P5 fixo, componentes em
`e1.py`, `rolling_zscore`, FAR e avaliação existentes. **Produces:** contrato
prospectivo, runner isolado e medição de custo; nenhuma alteração do E1 histórico.

- [ ] Antes de implementar ou medir, gravar em `configs/l0_exploratory.toml`
      e `docs/protocols/2026-10-28-sir-exploratorio.md`: perfil P5, ruído
      `white` apenas, `ε=[0.0,0.2]`, treinos meses 0–59, avaliação 60–131,
      janela 12, FAR alvo `1/60`, tolerância `1/300`, seleção antecipada dos
      placebos v2 índices 0,1,2, A/P4 e braços B1*, B2(A), B2(P4),
      B2(placebo-00..02), z-score causal. A configuração prevê 200 N para
      calibração e 200 N para avaliação por célula, em streams disjuntos;
      se não couber no prazo, não fazer comparação de lead time a FAR fixa.
      Fixar seed raiz independente `20261028`, streams por SeedSequence para
      piloto/calibração/avaliação/detectores e endereço estável por célula,
      rótulo e índice; não compartilhar réplicas do piloto. Definir labels T/N,
      onsets/twin e restricted lead time usando contratos de `simulate.py` e
      `evaluate.py`; registrar denominadores, casos inválidos e IC apenas como
      descritivos. Todos os braços usam a mesma realização e não há seleção
      baseada em resultado. O número de T e IDs usados efetivamente serão
      fixados após piloto em commit antes de resultados, escolhidos por ordem
      prefixa de 00..02 e custos, não por desempenho.
- [ ] Registrar que o gerador usa A candidata em todas as condições, P4 é
      sensibilidade somente no detector, e três placebos não estimam rank 30.
      Z-score recebe séries com janela causal 12 e sem vizinhança. Antes de
      rodar, comparar hashes de inputs, nomes, W, placebos, geometria P4 e
      conexidade, e assegurar vetor de graus por região e unicidade dos 30.
      Commit documental/config `docs: freeze exploratory sir protocol`.
- [ ] Escrever testes `test_candidate_binding_and_generator`: corromper
      manifesto/array causa erro antes de simular, simulador recebe W(A) e não
      W(P4) mesmo quando o braço usa P4; placebo é exatamente array v2. Testar
      seeds e streams disjuntos com replay, `rolling_zscore` sem futuro,
      controles N T e 13×72, invariância da série entre braços, FAR por braço,
      falha fechada de NB2 e `interpretation_allowed=false`. Testar falha
      durante escrita e destino existente com `test_publish_atomic_no_replace`.
- [ ] Rodar testes RED; implementar módulo isolado (não modificar restrições
      de `ExperimentConfig` ou o runner de produção). Reutilizar `simulate`,
      `_score`, threshold e avaliação onde contratos suportarem; adaptar zscore
      por braço independente com mesmos meses e nulos. Registrar configuração,
      código, commits, sementes, hashes, dados, tempos, memória, ausências e
      resultados parciais; nunca registrar gate aprovado pelo runner exploratório.
- [ ] Rodar testes GREEN, Ruff e suite completa, depois commit
      `feat: add isolated exploratory sir runner`. Se a integração de z-score,
      FAR ou NB2 não puder ser validada, parar Task 4 e manter a entrega como
      documentação; não simular substitutos nem alterar E0*.
- [ ] Registrar CPU, RAM, SO, Python e bibliotecas reais em
      `docs/reference-provenance.md` sem IDs sensíveis; registrar GPU se
      disponível, sem assumir aceleração. Executar piloto identificado e
      separado: uma T e uma N para cada ε, `white`, os cinco braços relacionais
      previstos mais B1* e z-score; medir tempo por simulação e por braço e pico
      de memória, sem reportar métricas de desempenho como resultado final.
      Projetar custo com 200 N calibração e 200 N avaliação por célula, os T do
      orçamento vigente e componentes inexistentes explicitamente estimados.
      Verificar requisitos de D-COST; incompletos significam `pending`.
- [ ] Registrar orçamento/IDs/seed e commit antes de execução real, somente
      com base no piloto e tempo restante. Executar se couberem validações e
      nulos; senão publicar impedimento descritivo, sem mudar FAR ou gates.
      Resultados em `results/l0-sir-exploratory-20261028-v1/`, atômicos, com
      manifesto, seeds, partitions, denominadores, hashes e limites; não incluir
      piloto, RQ1′ confirmatório ou inferência sobre dados reais.

## Task 5: Protocolo GANF futuro e revisão final

**Consumes:** spec, literatura existente e documentação original GANF.
**Produces:** `docs/research/2026-10-28-ganf-protocolo-futuro.md` e revisão
independente de código/artefatos, sem implementação ou treino GANF.

- [ ] Consultar artigo e código originais, citar URLs primárias e definir
      matriz/mascaramento, direção e loss exatamente como a fonte permite.
      Formular condições grafo fixo, aprendido e sem relações; treino,
      validação e teste temporais, otimização somente no treino, estabilidade,
      detecção, FAR, comparabilidade e limitações de inferência causal.
- [ ] Registrar pré-requisitos de dados, capacidade e comparação justa, e que
      grafo aprendido não é necessariamente mobilidade ou grafo SIR ótimo.
      Sem escolha de hiperparâmetros por desempenho no teste, sem execução.
- [ ] Revisar todos os hashes e indicadores `pending`, links, ausência de
      referências a resultados inexistentes, conteúdo dos slides e custos;
      rodar Ruff e testes pertinentes. Pedir uma revisão técnica independente
      do conjunto, que não substitui parecer científico. Corrigir achados
      importantes com testes; preservar evidência negativa e alterações locais.
- [ ] Commit `docs: specify future ganf evaluation`; informar ao usuário
      entregas completas, bloqueios e limites, e preservar worktrees/dados.

## Ordem e stop conditions

1. Tasks 1–3 têm prioridade e independência; acesso ausente a um insumo não
   impede as demais. Task 4 começa somente com protocolo prospectivo committed
   e artefatos verificados; piloto antes de dimensionar, commit antes da execução.
2. Prazo, falta de dados, validade NB2 ou calibração insuficiente: manter
   demonstração pendente ou exclusivamente descritiva, com causa verificável.
3. Nenhuma etapa ratifica G3 ou altera o resultado histórico. Não reorganizar
   arquivos que os manifests referenciam; sem push/merge/publicação.
