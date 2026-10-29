# Pacote de revisão geográfica e G3 — plano de implementação

> **Para execução:** usar `superpowers:executing-plans` em modo nativo, conforme
> a preferência SDD+TDD de baixo custo já informada; cada tarefa usa checkboxes.

**Objetivo:** preparar um pacote local, verificável e revisável da geografia
candidata, incluindo mapa, comparação com P4 e formulário de parecer.

**Arquitetura:** um módulo específico valida os insumos e o manifesto v2,
reconstrói apenas as geometrias para visualização e publica mapas e manifesto
de revisão em um diretório novo. Um dossiê Markdown versionado referencia o
pacote e suas limitações; não altera a candidata, o protocolo ou os gates.

**Stack:** Python ≥ 3.12, `uv`, pandas, geopandas, numpy, matplotlib, pytest e
ruff já existentes; sem novas dependências ou serviços.

**Spec:** [revisão geográfica e G3](../specs/2026-10-28-revisao-geografia-g3-design.md).

## Restrições globais

- Prazo de preparação: **30/10/2026, fim do dia, America/Fortaleza**;
  disponibilidade de revisão científica independente não é presumida.
- Executar no worktree `castro-data-provenance`, branch derivada de `develop`;
  preservar alterações preexistentes e os dados fornecidos pelo usuário.
- Preservar `data/raw/`, P4, candidata v1/v2, seeds, perfis e runs históricos;
  não sobrescrever nem apagar resultados. M, OD, GANF e bancada fora do escopo.
- Manifesto v2 esperado: SHA-256
  `7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0`;
  config de fontes e hashes em `configs/l0_fixed_geography.toml`.
- A/W/placebos são lidos e verificados, não regenerados. O mapa reconstrói a
  dissolução a partir das mesmas fontes e compara A calculada byte a byte com
  `adjacency.npy` antes de desenhar. Qualquer divergência bloqueia a publicação.
- D1 não aprovado, D2 suspenso, E0*/FAR reprovados; G4 restrito ao perfil fixo;
  G3 pendente, `interpretation_allowed=false`, RQ1′ inconclusiva.
- Não enviar mensagens, compartilhar dados ou alterar protocolo sem instrução
  explícita; não inventar revisor, parecer, data ou aceite científico.

## Review Focus

| Condição | Resultado exigido | Teste responsável |
| --- | --- | --- |
| Manifesto v2 ausente ou alterado | Falhar antes de produzir ou publicar mapas | `test_binding_rejects_manifest` |
| Insumo ou array com hash incorreto | Falhar antes de ler a geometria para o mapa | `test_binding_rejects_input_or_output` |
| Crosswalk omite ou troca Tailândia | Falhar antes de desenhar | `test_review_layers_require_tailandia` |
| A reconstruída ou ordem de rótulos não coincide com v2 | Falhar; não alegar correspondência visual | `test_review_layers_reject_graph_or_names` |
| Destino já existente ou erro durante a publicação | Preservar destino e não publicar pacote parcial como concluído | `test_publish_no_replace` |

## Estrutura de arquivos

- Criar `src/headd_l0/geography_review.py`: verificação das fontes, camadas de
  mapa, renderização e publicação separada, sem alterar o loader padrão P4.
- Criar `tests/test_geography_review.py`: fixtures pequenas e testes do vínculo
  com hashes, composição, matriz e publicação; não testar estética pixel a pixel.
- Criar `docs/evidence/2026-10-28-geography-review/README.md`: índice local,
  tabela de comparação, fontes, limitações e hashes verificados.
- Criar `docs/evidence/2026-10-28-geography-review/review-form.md`: formulário
  vazio para revisor científico; não incluir decisões como se fossem ocorridas.
- Saída não versionada: `results/l0-geography-review-20261028-v1/` com
  `mapa-regioes.png`, `comparacao-arestas.png` e `manifest.json`; nunca escrever
  em `results/l0-fixed-geography-candidate-v2/`.

---

### Task 1: Mapas ligados aos artefatos v2

**Files:**

- Create: `src/headd_l0/geography_review.py`
- Test: `tests/test_geography_review.py`

**Interfaces:**

- Consumes: `configs/l0_fixed_geography.toml`; `join_municipalities`,
  `select_pa_crosswalk` e `candidate_graph` de `headd_l0.fixed_geography`;
  manifesto e arrays v2; P4 identificado no TOML.
- Produces: `verify_binding(config_path: Path, manifest_path: Path) -> dict`
  verifica hash fixo do manifesto, hashes dos quatro insumos indicados nele,
  hashes dos três `.npy`, config e códigos-fonte usados para a construção;
  retorna o manifesto carregado. `review_layers(municipalities: gpd.GeoDataFrame,
  a: np.ndarray, names: tuple[str, ...]) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]`
  valida e devolve regiões dissolvidas e uma linha para Tailândia. `main(argv:
  list[str] | None = None) -> int` publica somente no destino indicado abaixo.

- [ ] **Step 1: Escrever testes de validação antes do código.** Fixtures sob
      `tmp_path` criam manifesto com digest esperado injetado via monkeypatch,
      fontes e arrays pequenos com hashes reais; uma fixture de polígonos com
      13 nomes canônicos inclui `municipality="150795"` na região Lago.
      Fixar os seguintes testes e asserções:

```python
def test_binding_rejects_manifest(binding_fixture):
    config, manifest, source, output = binding_fixture
    manifest.write_text('{}')
    with pytest.raises(ValueError, match='manifest'):
        verify_binding(config, manifest)

@pytest.mark.parametrize('which', ['source', 'output'])
def test_binding_rejects_input_or_output(binding_fixture, which):
    config, manifest, source, output = binding_fixture
    target = source if which == 'source' else output
    target.write_bytes(target.read_bytes() + b'X')
    with pytest.raises(ValueError, match='hash'):
        verify_binding(config, manifest)

def test_review_layers_require_tailandia(municipal_fixture, adjacency):
    municipal_fixture.loc[municipal_fixture.municipality == '150795', 'name'] = 'TOCANTINS'
    with pytest.raises(ValueError, match='Tailândia'):
        review_layers(municipal_fixture, adjacency, tuple(hierarchy().leaves))

def test_review_layers_reject_graph_or_names(municipal_fixture, adjacency):
    bad = adjacency.copy()
    bad[0, 1] = 1 - bad[0, 1]
    with pytest.raises(ValueError):
        review_layers(municipal_fixture, bad, tuple(hierarchy().leaves))
    with pytest.raises(ValueError):
        review_layers(municipal_fixture, adjacency, tuple(reversed(hierarchy().leaves)))

def test_publish_no_replace(review_cli_fixture):
    config, manifest, output = review_cli_fixture
    output.mkdir()
    (output / 'keep').write_text('preservar')
    with pytest.raises(FileExistsError):
        main([str(config), str(manifest), str(output)])
    assert (output / 'keep').read_text() == 'preservar'
    assert not (output / 'manifest.json').exists()
```

      Completar as fixtures com fontes mínimas e, em teste separado de erro de
      renderização, simular exceção antes de `_publish` e exigir destino final
      ausente. No teste de hash parametrizado, alterar o arquivo selecionado
      antes da chamada; não testar um único cenário duas vezes.
- [ ] **Step 2: Confirmar RED.** Rodar `uv run pytest tests/test_geography_review.py -v`;
      esperado: falha de importação do módulo ausente, sem falha das fixtures.
- [ ] **Step 3: Implementar interfaces.** Fixar o hash v2 acima em constante;
      usar `_sha256`/`_publish` existentes, `allow_pickle=False`, nomes de
      `hierarchy().leaves`, 144 municípios e `150795 → 15004`. Calcular A com
      `candidate_graph`; exigir igualdade exata à A fornecida antes de desenhar.
      Rejeitar fontes, arrays, configuração ou código com hash divergente.
- [ ] **Step 4: Renderizar e publicar.** Desenhar 13 regiões em cores distintas
      com rótulos e Tailândia destacada; para comparação, desenhar linhas entre
      pontos representativos das regiões para arestas adicionadas e removidas,
      com legenda que as identifica como representação esquemática. O manifesto
      novo registra hashes de insumos, A/P4, código, imagens, ordem e data; exige
      `status=review_package` e `interpretation_allowed=false`. Publicar
      atomicamente sem substituir destino; falhas preservam dados preexistentes.
- [ ] **Step 5: Confirmar GREEN.** Rodar `uv run pytest tests/test_geography_review.py -v`;
      esperado: todos os testes aprovados. Verificar também caminho de sucesso:
      duas imagens não vazias e seus SHA-256 iguais aos do manifesto novo.
- [ ] **Step 6: Conferir qualidade e registrar commit.** Executar
      `uv run ruff check .`, `uv run ruff format --check .` e `uv run pytest`;
      exigir saída verde. Commit local apenas do código/testes:
      `git commit -m "feat: prepare geography review maps"`.
- [ ] **Step 7: Gerar uma vez com fontes reais.** Da raiz do worktree, rodar
      `uv run python -m headd_l0.geography_review configs/l0_fixed_geography.toml results/l0-fixed-geography-candidate-v2/manifest.json results/l0-geography-review-20261028-v1`.
      Conferir hash fixo v2, hashes das imagens e correspondência exata da A;
      inspecionar visualmente os dois PNGs. Se destino existir, parar e reportar,
      sem removê-lo nem escolher outro ID para ocultar resultado.

**Aceite:** mapa e comparação utilizam a mesma composição/adjacência de v2;
origens e saídas rastreáveis; nenhum resultado histórico modificado.

### Task 2: Dossiê e formulário de parecer

**Files:**

- Create: `docs/evidence/2026-10-28-geography-review/README.md`
- Create: `docs/evidence/2026-10-28-geography-review/review-form.md`

**Interfaces:**

- Consumes: manifesto e imagens publicados pela Task 1, auditorias de 2013 e
  2009–2019 e [parecer preparatório](../../research/2026-10-28-parecer-decisao-geografia-l0.md).
- Produces: índice versionado e formulário vazio. Não produz parecer científico,
  G3 aprovado, upload ou autorização de uso experimental.

- [ ] **Step 1: Escrever o índice.** Identificar caminhos locais, hashes do
      manifesto v2 e do pacote de mapas, fontes, seed e código. A partir dos
      manifests, tabular 25/26 arestas, aresta adicionada, graus alterados e
      todas as linhas de W diferentes; não arredondar diferenças a zero.
- [ ] **Step 2: Documentar limites e acesso.** Registrar 7.592 grupos
      observados, 143 pares observados e 144 municípios na tabela; distinguir
      compatibilidade, linhagem e vigência. Listar arquivos locais não
      versionados, dependências e licença/redistribuição ainda não confirmadas.
      Nenhum microdado ou nome de contato deve entrar no pacote versionado.
- [ ] **Step 3: Escrever formulário.** Campos vazios para identificação e
      independência do revisor, competência, data, hashes examinados, evidência,
      achados, ressalvas e uma das opções `favorável com ressalvas`,
      `complementação necessária`, `não favorável`. Incluir cinco critérios
      propostos com `pass/fail/pending`, mas indicar que critérios ainda exigem
      ratificação e que o responsável decide G3 em etapa posterior.
- [ ] **Step 4: Validar.** Conferir cada link local versionado, hashes contra
      os manifests e imagens, contagens e diferenças contra os arrays, e rodar
      `git diff --check`. Abrir os PNGs e conferir rótulos e legenda. Um parecer
      ou dado faltante é `pending`, nunca preenchido com valor presumido.
- [ ] **Step 5: Commit e entrega.** Commit local somente dos dois documentos,
      `docs: prepare geography scientific review package`; relatar ao usuário
      que o revisor científico e sua autorização de acesso continuam pendentes.

**Aceite:** outra pessoa pode identificar e inspecionar o pacote com seus
insumos acessíveis, registrar discordância ou pedir complementação, sem
confundir parecer técnico com revisão científica ou G3 aprovado.

## Autorrevisão e limites

- Cobertura da spec: Task 1 cobre mapa, vínculo e imutabilidade; Task 2 cobre
  evidência, comparação, limitações, formulário e fluxo de decisão.
- A execução deste plano **não** ratifica os critérios prospectivos, não fornece
  parecer científico independente e não modifica `protocol-decisions.md`.
- Em caso de acesso indisponível, bytes diferentes ou prazo atingido, registrar
  impedimento com comandos e hashes observados e manter o pacote pendente.
