# Construção da geografia candidata — plano de implementação

> **Execução:** `superpowers:executing-plans` em modo nativo. Esta proposta
> detalha o trabalho; a construção de artefatos permanece condicionada à
> decisão de desenho descrita no [parecer](../../research/2026-10-28-parecer-decisao-geografia-l0.md).

**Objetivo:** produzir, em execução identificada e separada, uma adjacência
Queen candidata compatível com a composição municipal fixa da série L0.

**Arquitetura:** módulo separado para leitura e validação da composição e
construção da candidata, reutilizando as primitivas de `graph.py`. Não alterar
o leitor P4 nem a seleção padrão do grafo. Publicação em diretório novo apenas
após validação; qualquer erro deixa a execução sem estado de sucesso.

**Stack:** Python ≥3.12, geopandas, pandas, numpy, libpysal e pytest existentes;
sem dependências novas.

**Spec:** [geografia da série fixa](../specs/2026-10-28-geografia-serie-fixa-design.md).

**Estado em 28/10:** desenho retrospectivo e construção técnica aprovados pelo
usuário. A implementação, a revisão técnica e as duas saídas preservadas estão
descritas no [registro de execução](../../research/2026-10-28-execucao-geografia-candidata.md).
Revisão científica independente e decisão de uso experimental continuam pendentes.

## Restrições globais

- Dados, resultados, perfil e gates históricos imutáveis; sem M, OD, GANF ou
  execução de bancada; 30 placebos não provam uniformidade de amostragem.
- Fonte nacional da relação é CSV `;` sem cabeçalho, 5.658 linhas; selecionar
  PA e excluir somente agregado `150000 → 15000`. Preservar hashes da spec.
- Fixar 144 municípios, 13 regiões, Tailândia `150795 → 15004`, Queen e ordem
  `hierarchy().leaves`; P4 é comparador e não deve ser modificado.
- Seed 42 e orçamento de `_draw_placebos` existente para esta construção
  candidata; se não houver 30 placebos válidos, falhar sem publicar sucesso.
- A seleção prospectiva, verificação técnica, revisão científica independente,
  aprovação de uso, G3 e interpretação são estados distintos.

## Foco de revisão

Cada condição é coberta nos testes da tarefa indicada.

| Condição | Resposta exigida | Tarefa |
| --- | --- | --- |
| Agregado estadual ou município externo | Excluir apenas agregado conhecido; rejeitar município externo após seleção | 1 |
| Município ausente, duplicado ou código numérico malformado | Falhar antes de gerar A | 1 |
| Região desconhecida ou nome inconsistente | Falhar sem substituir nome | 1 |
| Geometria inválida ou grafo não conexo | Falhar sem reparo silencioso | 2 |
| Diretório já existente ou placebos incompletos | Não sobrescrever nem publicar sucesso | 3 |

## Estrutura de arquivos

- Criar `src/headd_l0/fixed_geography.py`: validação, construção e CLI explícita.
- Criar `tests/test_fixed_geography.py`: fixtures sintéticas, validações e CLI.
- Criar `configs/l0_fixed_geography.toml`: insumos com hashes da spec, seed 42,
  número de placebos 30 e destino novo `results/l0-fixed-geography-candidate-v1`.
- Não mudar `src/headd_l0/graph.py`, `graph_io.py` nem configs P4.

## Tarefa 1: associação municipal segura

**Interfaces:** `select_pa_crosswalk(relation: pd.DataFrame) -> pd.DataFrame`
retorna colunas string `municipality`, `region`; `join_municipalities(municipalities:
gpd.GeoDataFrame, relation: pd.DataFrame, names: pd.DataFrame) -> gpd.GeoDataFrame`
retorna 144 linhas com `name` canônico e geometria. A relação já lida tem duas
colunas `municipality`, `region`; nomes têm `region`, `status`, `name`, `level`.

- [ ] Escrever testes para linha `150000;15000`, município externo ao recorte,
      município PA ausente/duplicado, `code_muni6` numérico inteiro versus
      string e número fracionário, região desconhecida e nome divergente. Os
      dois formatos válidos devem casar; outros casos devem gerar `ValueError`.
- [ ] Executar `uv run pytest tests/test_fixed_geography.py -k crosswalk -v`;
      verificar falha por módulo/função ausente.
- [ ] Implementar as interfaces, usando conversão validada para seis dígitos,
      merge `validate="one_to_one"` e comparação exata dos 144 códigos da
      geometria PA com a relação; exigir códigos e nomes canônicos e Tailândia.
- [ ] Reexecutar os testes focados; exigir aprovação e nenhuma linha descartada
      da seleção PA exceto o agregado identificado. Commit local `feat: validate
      fixed regional geography`.

## Tarefa 2: A e W candidatas

**Interfaces:** `candidate_graph(municipalities: gpd.GeoDataFrame) -> tuple[np.ndarray,
np.ndarray]` consome o resultado da Tarefa 1 e retorna A, W em ordem canônica.

- [ ] Escrever testes de fixture com 13 regiões: Queen conhecida, simetria,
      diagonal zero, W com soma 1, geometria vazia/inválida e região isolada
      rejeitadas. Testar que troca da entrada de Tailândia altera somente a
      composição especificada na fixture; não fixar grafo real em teste sintético.
- [ ] Executar `uv run pytest tests/test_fixed_geography.py -k candidate_graph -v`;
      confirmar falha por função ausente.
- [ ] Implementar dissolução por `name` após validação de geometrias, seguida de
      `build_adjacency` e `row_normalize` existentes, sem reparo geométrico.
- [ ] Reexecutar testes focados; exigir aprovação. Commit local `feat: build
      fixed-series candidate adjacency`.

## Tarefa 3: execução identificada e auditoria

**Interfaces:** `main(argv: list[str] | None = None) -> int` lê um TOML com
`relation`, `names`, `geometry`, `p4_adjacency`, respectivos hashes SHA-256,
`output_dir`, `root_seed=42` e `n_placebos=30`. Saídas `adjacency.npy`, `W.npy`,
`placebos.npy` e `manifest.json`; nomes e códigos de entrada são registrados.

- [ ] Escrever testes com fixtures e monkeypatch de `_draw_placebos` para hash
      incorreto, destino existente, falha no gerador, placebo duplicado, desconexo
      ou com graus incorretos; exigir erro e ausência de publicação de sucesso.
      Testar sucesso com 30 placebos válidos e manifesto com hashes recalculáveis,
      seed, orçamento, ordem, arestas, graus e comparação com P4.
- [ ] Executar `uv run pytest tests/test_fixed_geography.py -k publication -v`;
      verificar falha por CLI ausente.
- [ ] Implementar a CLI com hashes conferidos antes da leitura e publicação
      atômica sem substituir destino; capturar falha de placebo como erro,
      nunca como aprovação. Separar qualquer diretório temporário do destino
      histórico e não remover arquivos alheios.
- [ ] Rodar os testes focados, `uv run ruff check .`, `uv run ruff format --check .`
      e `uv run pytest`; corrigir somente regressões atribuíveis à mudança.
- [ ] Após autorização da decisão de desenho, executar uma vez com insumos e
      hashes verificados. Comparar as 25 arestas P4 às da candidata; a expectativa
      é 26 e uma adição Lago–Metropolitana II. Divergência bloqueia conclusão e
      exige diagnóstico, não ajuste de parâmetros. Registrar hashes e comandos.
- [ ] Solicitar revisão científica independente com o parecer, manifesto e
      limitações; o autor da implementação não se autoatribui a revisão.
      Commit local `feat: export auditable candidate geography`.

## Revisão final

Conferir cobertura da spec e dos cinco riscos, links, diff e arquivos locais;
relatar resultados dos testes e ausência de revisão independente, se aplicável.
Mesmo se os testes passarem, não registrar G3 ou uso experimental como aprovados
sem decisão prospectiva própria. Nunca modificar nem publicar dados individuais.
