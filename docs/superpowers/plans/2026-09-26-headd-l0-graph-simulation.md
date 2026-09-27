# HEADD-Series L0 Graph and Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produzir A/W e 30 placebos, validar SIR de uma região e sua extensão para 13 regiões, e entregar features relacionais causais.

**Architecture:** `graph.py` trata estrutura estática; `simulate.py` produz contagens e onsets, sem conhecer detectores; `features.py` recebe somente contagens observáveis e W. O simulador de uma região é gate obrigatório anterior ao acoplamento.

**Tech Stack:** Python ≥3.12, uv, numpy/scipy, pandas, networkx, geobr, geopandas, libpysal, pyarrow, pytest/ruff.

**Spec:** [Arquitetura §§5–8](../specs/2026-09-26-headd-l0-architecture.md), README §5, AGENTS; contratos de dados em [E0 tarefa 2](2026-09-26-headd-l0-e0.md#task-2-dados-hierarquia-e-proveniência--default).

## Global Constraints

- “Validate a single region first”; ruídos `white`, `env`, `dem`.
- “ε = 0 must yield zero spread from the seed beyond the endemic background”.
- `C = (1 − ε)·I + ε·W`; `λᵢ = βᵢ(t) · Σⱼ Cᵢⱼ Iⱼ/Nⱼ`.
- “Weekly Euler–Maruyama → monthly sums; clip negative compartments at zero; binomial observation with testing rate θ.”
- 13 regiões ×132 meses; onset seed = cruzamento R0=1; demais = excesso >2 SD em relação à gêmea.
- “Raw data is immutable.” / “No look-ahead.” / `numpy.random.Generator`.
- 30 placebos conexos com mesma sequência de graus; falhar se não conseguir draws.
- Sem seirsplus, M, hhh4 completo ou GNN. B3/B-Gao/SEIRS são opcionais fora deste plano.

## Review Focus

- API retorna municípios apesar de pedir regiões: tarefa 1 verifica cardinalidade/códigos antes de construir A.
- Ilha, nomes desalinhados ou sequência não rewirável: tarefa 1 falha claramente sem laços artificiais.
- Correntes aleatórias divergem por branch T/N: tarefa 3 exige identidade exata fora da semente em ε=0.
- SD nula, incidência fracionária e mês com semana parcial: tarefas 2/3 verificam convenções pré-registradas.
- Série constante, zeros ou sufixo futuro: tarefa 4 mantém valores finitos e prefixos idênticos.

---

## Arquivos e dependências

Criar `src/headd_l0/graph.py`, `simulate.py`, `features.py` e `tests/test_graph.py`, `test_simulate.py`, `test_features.py`. Configs `l0_graph.toml`, `sim_single.toml`; fixtures `tests/reference/gao_single.npz` e `gao_manifest.json`. `docs/protocol-decisions.md` guarda escolhas aprovadas. Não adicionar módulo genérico de entidades/configuração.

Tarefa 1 depende só de dados/S. Tarefa 2 depende de fixtures científicas e decisões numéricas. Tarefa 3 exige tarefa 2 aprovada e grafo válido; tarefa 4 usa grafo e contagens, não labels/onsets. Todos os novos contratos recebem testes. Checks ao final de cada tarefa: ruff check, ruff format --check e pytest rápido; testes slow são executados no gate indicado.

### Task 1: Geometria, A/W e placebos — default / rewiring think

**Files:** Create `src/headd_l0/graph.py`, `tests/test_graph.py`, `configs/l0_graph.toml`; Modify `MIGRATION.md` (novo componente, sem porte).

**Interfaces:** Consome `data.hierarchy()` e `reconcile.summing_matrix`. Produz `build_adjacency(regions: gpd.GeoDataFrame, names: tuple[str,...]) -> np.ndarray`; `adjacency() -> tuple[np.ndarray,tuple[str,...]]` lê cache canônico em processed; `row_normalize(A: np.ndarray) -> np.ndarray`; `placebos(A: np.ndarray,n: int,rng: np.random.Generator) -> list[np.ndarray]`; `centralities(A: np.ndarray,names: tuple[str,...]) -> pd.DataFrame`; `export_graph(A: np.ndarray,names: tuple[str,...],path: Path) -> None`. CLI `python -m headd_l0.graph configs/l0_graph.toml` adquire/valida/cacheia malha e registra run.

- [ ] **Step 1: Escrever `test_queen_edges_and_canonical_names`, `test_wrong_geography_level_rejected`, `test_placebos_preserve_labeled_degrees`, `test_islands_rejected`, `test_unrewirable_graph_fails`, `test_normalization_and_exports`.** Fixture geométrica sintética de quatro polígonos cobre toque por vértice (queen), nomes embaralhados e polígono sem contato. Fixture conectada de 13 nós para 30 draws: circulante com offsets 1,2, sem depender da malha real.

```python
draws = placebos(A, 30, np.random.default_rng(42))
assert len(draws) == len({B.tobytes() for B in draws}) == 30
for B in draws:
    np.testing.assert_array_equal(B.sum(axis=1), A.sum(axis=1))
    assert np.array_equal(B, B.T) and not np.diag(B).any()
    assert nx.is_connected(nx.from_numpy_array(B))
    assert not np.array_equal(B, A)
np.testing.assert_allclose(row_normalize(A).sum(axis=1), 1)
with pytest.raises(ValueError):
    row_normalize(np.zeros((13, 13)))
```

Grafo completo/estrela sem alternativas deve levantar RuntimeError dentro do orçamento, não retornar cópias de A. Exportar/reler GEXF deve manter 13 nomes/arestas; centralidades de ciclo têm grau uniforme.

- [ ] **Step 2:** `uv run pytest tests/test_graph.py -v` → FAIL, módulo ausente.
- [ ] **Step 3: Implementar.** Obter `geobr.read_health_region(code_state="PA",geometry_level="micro",year=2013)` somente após confirmar suporte na versão resolvida; 2013 é proposta explícita de vintage. Verificar os 13 códigos, dissolver municípios por código quando necessário, mapear nomes canônicos por tabela auditável. Validar ausência de geometrias vazias; registrar reparos topológicos. Construir Queen com libpysal e reordenar A pela ordem de data, nunca por ordem de download. Primária desconexa gera erro/diagnóstico; não aplicar fallback k-NN silencioso.
- [ ] **Step 4: Implementar placebos.** Trocas duplas rejeitando self-loop, duplicação e desconexão; 10×|E| trocas aceitas antes de registrar cada candidato, máximo 1.000×|E| tentativas por candidato e 10.000 candidatos no total. Valores propostos devem constar no manifesto. Rejeitar duplicatas/original, conservar graus por identidade do nó. Sem promessa de mistura uniforme; registrar distância de arestas a A e diversidade entre draws.
- [ ] **Step 5:** Testes/checks → PASS; rodar CLI de integração com rede uma vez. Verificar `A.shape==(13,13)`, nomes exatos, W e 30 hashes distintos. Artefatos: geometrias/adjacency/placebos/centralities em processed, cópias ou referências por hash no run, GEXF de S/A/placebos separados e mapa diagnóstico. Registrar custo real da aquisição; não afirmar conectividade sem executar.
- [ ] **Step 6:** `git add src/headd_l0/graph.py tests/test_graph.py configs/l0_graph.toml MIGRATION.md` e `git commit -m "feat: build regional adjacency and degree-preserving placebos"`.

### Task 2: Uma região e observação mensal — think

**Files:** Create `src/headd_l0/simulate.py`, `tests/test_simulate.py`, `configs/sim_single.toml`, `tests/reference/gao_single.npz`, `tests/reference/gao_manifest.json`; Modify `docs/protocol-decisions.md`, `MIGRATION.md`.

**Interfaces:** `SimConfig` congelada com campos obrigatórios `noise: str, label: str, months: int, start: str, populations: tuple[float,...], initial_infected: tuple[float,...], recovery: float, mortality: float, recruitment: tuple[float,...], beta_start: float, beta_end: float, ramp_start_week: int, ramp_end_week: int, sigma_s: float, sigma_i: float, testing_rate: float, epsilon: float, endemic: tuple[float,...], seasonal_amplitude: float, seasonal_phase: float, seed_region: int, train_months: int`. Sem defaults científicos ocultos. `SimResult` da spec; `simulate(cfg: SimConfig,W: np.ndarray,rng: np.random.Generator) -> SimResult`. Helpers numéricos internos recebem inovações explícitas para testes; etapa atual aceita n_regions=1/ε=0. O componente interno será reutilizado por inject_epidemic na camada 1 com ν=0; não criar outro integrador. Perfil completo de simulação deve ser referenciado explicitamente, conforme D-GT4.

- [ ] **Step 1: Fixar a parametrização antes de escrever o integrador.** Ler suplemento equações 1–3 e código oficial; registrar versão/hash, unidade temporal, parametrização β SI versus β SI/N, parâmetros T/N e janelas das figuras F–H em `gao_manifest.json`. Exportar pequenas trajetórias determinísticas de um passo e as estatísticas de referência. Registrar as escolhas para converter incidência contínua em contagem (proposta: arredondamento estocástico do fluxo acumulado) e para agregar calendário. Aprovar `docs/protocol-decisions.md`; se a fonte não definir um parâmetro, a tarefa encerra com bloqueio identificado, não com número inventado.
- [ ] **Step 2: Escrever `test_sde_one_step_matches_reference`, `test_demographic_diffusion_covariance`, `test_weekly_calendar_conserves_incidence`, `test_binomial_observation_extremes`, `test_single_region_t_n_separation` (slow).** Helper interno do passo recebe gaussianas da fixture, tolerância `1e-10`. Difusão demográfica deve reproduzir a matriz de covariância da eq.3, não ruído aditivo independente. Forçar θ=0/1 e clipping.

```python
result = simulate(cfg_single, np.zeros((1, 1)), np.random.default_rng(42))
assert result.counts.shape == (1, 132)
assert np.issubdtype(result.counts.dtype, np.integer)
assert (result.counts >= 0).all()
np.testing.assert_array_equal(result.counts, repeated.counts)
assert np.median(ar1_t) > np.median(ar1_n)
assert np.median(cv_t) > np.median(cv_n)
```

`repeated` é mesma chamada/seed; ar1/cv calculados no teste com fórmulas independentes e janelas pré-onset do manifesto. Parametrizar os três ruídos; não escolher seeds pela separação. Fixture de fluxo semanal constante deve conservar total ao atravessar mês/ano bissexto.

- [ ] **Step 3:** `uv run pytest tests/test_simulate.py -m 'not slow' -v` → FAIL.
- [ ] **Step 4: Implementar o SIR de uma região.** Euler–Maruyama com dt em unidades documentadas e `sqrt(dt)`; clipping em zero; integrar fluxos de infecção para casos, sem somar I como incidência. Verificar limites físicos e contabilizar projeções. Integração inclui intervalos parciais nas fronteiras do calendário. Observação binomial recebe inteiro não negativo; θ validado [0,1]. CLI lê `configs/sim_single.toml`, grava parâmetros, curvas e diagnósticos em results.
- [ ] **Step 5:** Testes rápidos/checks → PASS; `uv run pytest -o addopts='' tests/test_simulate.py -m slow -v` e `uv run python -m headd_l0.simulate configs/sim_single.toml` → separação AR1/CV em **cada ruído**, tanto no observável usado para referência quanto diagnóstico da adaptação mensal. Se falhar, não acoplar/não ajustar parâmetros mirando o teste; reportar discrepância de observável/escala. Ainda não chamar isso de reprodução completa do artigo.
- [ ] **Step 6:** `git add src/headd_l0/simulate.py tests/test_simulate.py configs/sim_single.toml tests/reference/gao_single.npz tests/reference/gao_manifest.json docs/protocol-decisions.md MIGRATION.md` e `git commit -m "feat: validate single-region stochastic outbreak simulator"`.

### Task 3: Endemia, acoplamento, gêmeas e onsets — think

**Files:** Modify `src/headd_l0/simulate.py`, `tests/test_simulate.py`, `docs/protocol-decisions.md`, `MIGRATION.md`; Create `configs/endemic.toml`.

**Interfaces:** Consome `DataBundle.counts[:,:60]`, W e SimConfig. Produz `EndemicCalibration(nu: tuple[float,...], targets: tuple[float,...], training_months: int, parameters_hash: str)` e `calibrate_endemic(train_counts: np.ndarray,cfg: SimConfig,rng: np.random.Generator) -> EndemicCalibration`; estende `simulate` sem mudar assinatura. O motor compartilhado deve disponibilizar fluxo/casos importados observados por região e mês para o adaptador da camada 1, sem mudar SimResult ou os onsets da camada 2 silenciosamente. `onset` é -1 para N e regiões sem excesso; não usar zeros como sentinel de ausência.

- [ ] **Step 1: Escrever `test_zero_coupling_isolates_seed`, `test_twin_uses_same_innovations`, `test_seed_onset_crossing`, `test_neighbor_onset_exceeds_frozen_sd`, `test_endemic_fit_uses_only_training`, `test_rng_reproducibility`.** Fixture de excesso/SD testa fronteira estrita >2SD; SD=0 usa >0, documentando sensibilidadade.

```python
result = simulate(cfg_epsilon_zero, W, np.random.default_rng(42))
others = np.arange(13) != result.seed_region
np.testing.assert_array_equal(result.counts[others], result.twin_counts[others])
assert (result.onset[others] == -1).all()
assert result.counts.shape == result.twin_counts.shape == (13, 132)
assert null_result.label == "N" and (null_result.onset == -1).all()
```

Também testar C identidade em ε=0, linhas somam 1 e orientação de W com grafo assimétrico de teste; β só cresce na semente.

- [ ] **Step 2:** `uv run pytest tests/test_simulate.py -k 'coupling or twin or onset or endemic' -v` → FAIL.
- [ ] **Step 3: Implementar calibração condicional de ν.** Fixar Nᵢ/θ/demais parâmetros aprovados; resolver ν por região para aproximar mediana observada de treino com simulações N independentes e números comuns, tolerância proposta `max(1 caso, 10% da mediana)`; teto 30 iterações e diagnóstico se falhar. Não usar meses de avaliação. Registrar objetivo, erro, seed e parâmetros em processed; CLI `python -m headd_l0.simulate configs/endemic.toml` regenera. A não identificabilidade de ν/θ é descrita na spec.
- [ ] **Step 4: Implementar extensão acoplada.** Aplicar fórmula de λ/C da spec e os parâmetros endêmicos; mesmas gaussianas/uniformes pré-geradas por canal/tempo/região nas duas trajetórias. Na observação, usar quantil binomial com mesmo uniforme, não duas chamadas binomiais cuja sequência dependa do n. Gêmea mantém β sem surto. Onset seed por R0; demais pelo excesso **observado** e SD de treino da gêmea congelada. Guardar SD/β/limiares em params. Não alimentar ground truth no pipeline de detecção.
- [ ] **Step 5:** Tests/checks e validação single-region → PASS; relatório para ε=0/.05/.20 usa mesmas seeds por célula e inclui frequências de onsets ausentes, clipping e erro de calibração. Antes de executar braços, medir D-REACH: fração de T com onset em ao menos um vizinho da semente, por ε/célula; mínimo proposto≥50% em ε=.20. Abaixo disso marcar sem poder, não negativo, sem tuning pós-avaliação. Esse diagnóstico precede o piloto/execução de braços. Não exigir ganho B2 neste teste do gerador. Para camada 1, testar que o modo ν=0 não cria casos espontâneos em regiões não-semente quando ε=0; usar a definição de onset própria dessa camada.
- [ ] **Step 6:** `git add src/headd_l0/simulate.py tests/test_simulate.py configs/endemic.toml docs/protocol-decisions.md MIGRATION.md` e `git commit -m "feat: add coupled simulations with common-random-number twins"`.

### Task 4: Representações causais e indicadores — default / Moran think

**Files:** Create `src/headd_l0/features.py`, `tests/test_features.py`; Modify `MIGRATION.md`.

**Interfaces:** `FeatureBatch` da spec; `local_features(counts: np.ndarray) -> FeatureBatch`; `hierarchy_features(counts: np.ndarray,S: np.ndarray) -> FeatureBatch`; `neighbor_features(counts: np.ndarray,W: np.ndarray,window: int=12) -> FeatureBatch`; `rolling_ews(series: np.ndarray,window: int) -> tuple[np.ndarray,np.ndarray]` retorna indicadores `[time,5]` e máscara de validade mesma shape. `FEATURES` chaves local/hierarchy/neighbors. Não escalar com dados do teste; escalador de detector aprende no fit.

- [ ] **Step 1: Escrever `test_neighbor_hand_calculation`, `test_prefix_invariance`, `test_constant_series_finite_with_invalid_mask`, `test_node_and_feature_axes`, `test_local_moran_hand_calculation`, `test_hierarchy_features_count_units`.**

```python
x = np.array([[1., 2., 3.], [10., 20., 30.]])
W = np.array([[0., 1.], [1., 0.]])
batch = neighbor_features(x, W, window=2)
np.testing.assert_array_equal(batch.values[:, :, 0], W @ x)
np.testing.assert_array_equal(batch.values[:, 1:, 1], W @ x[:, :-1])
np.testing.assert_array_equal(batch.values[:, :, 2], x - W @ x)
assert batch.names == ("neighbor_now", "neighbor_lag1", "neighbor_difference", "local_moran")
ews, valid = rolling_ews(np.zeros(132), 12)
assert np.isfinite(ews).all() and not valid[:, 1:3].any()
```

Alterar x[:,90:] → features até 89 idênticas; warmup só usa passado e possui validade, nunca backfill.

- [ ] **Step 2:** `uv run pytest tests/test_features.py -v` → FAIL.
- [ ] **Step 3: Implementar.** Local: `(x_t,x_(t−1),x_t−x_(t−1))`; hierarquia: mesmos três mais `(PA_t, x_i−PA_t/13)` nas folhas e zeros para contraste agregado, eixos `[14,time,5]`. É representação de contagens, não definição da posição de MinT (D5 permanece gate). Vizinhos somente 13 folhas; runner acrescenta zeros relacionais à linha PA. Moran instantâneo `z_i*(W@z)_i/m2`, z centrado espacialmente e m2=mean(z²), depois média dos últimos 12 valores; m2 zero →0. EWS SD ddof=1, CV=SD/mean, AR1 Pearson defasada, skewness e kurtosis Pearson (normal=3); constantes →zero com máscara falsa para estatística indefinida. Lag inicial =0 e warmup excluído. Todas as features em t usam ≤t.
- [ ] **Step 4:** Testes/checks → PASS; substituir W real por placebo só muda valores, não shape, nomes ou janelas. Nomes de colunas estáveis são gravados no manifest.
- [ ] **Step 5:** `git add src/headd_l0/features.py tests/test_features.py MIGRATION.md` e `git commit -m "feat: add causal hierarchy and neighborhood features"`.

## Critério de saída

A/W e 30 draws válidos, validação single-region, ε=0 isolado, onsets auditáveis e invariância de prefixo. Os dados sintéticos não são versionados; seeds/config e fixtures pequenas permitem regeneração. Sem saída válida de D-G0, esses resultados são validação de infraestrutura, não evidência da RQ1′. Autorização futura de B1* não substitui validação do simulador, D5, FAR ou alcance.
