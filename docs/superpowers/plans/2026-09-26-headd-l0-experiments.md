# HEADD-Series L0 Experiments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar B0/B1/B2/30 placebos, executar as bancadas a FAR fixa e produzir uma conclusão rastreável sobre RQ1′.

**Architecture:** Um runner TOML compõe os componentes previamente testados; cada réplica é gerada uma vez e reutilizada por todos os braços. Seeds, partições e métodos são comuns. Avaliação e estatística consomem artefatos completos, incluindo falhas/censura.

**Tech Stack:** Python ≥3.12, uv, numpy/pandas/scipy, pyarrow, notebooks/matplotlib/seaborn, pytest/ruff; componentes dos planos E0 e L0.

**Spec:** [Arquitetura](../specs/2026-09-26-headd-l0-architecture.md), [plano global](2026-09-26-headd-l0-global.md), README §5; [baseline/E0](2026-09-26-headd-l0-e0.md), [grafo/simulação](2026-09-26-headd-l0-graph-simulation.md).

## Global Constraints

- “One variable per arm.” Pool/reconciliação/seleção/limiar idênticos entre B1/B2/placebo; representações e parâmetros aprendidos podem diferir.
- FAR = 1/60 por região-mês, calibrada em réplicas N independentes da avaliação.
- 3 ruídos ×3 ε ×(500 T+500 N) = 9.000 avaliações; 30 placebos; 13×132 por réplica.
- E0: 14 tarefas, |ΔAUC-PR|≤.01 e mesmo ranking antes de interpretar E1.
- Bootstrap pareado → placebo rank → critério conjunto; secundário Friedman → Wilcoxon/Bonferroni → DM/HAC → Cliff/IC95%.
- “No look-ahead.” / “Counts, not proportions.” / dados raw imutáveis.
- Frozen dataclasses; `Generator`/`SeedSequence`; manifests com seeds, config, git hash e timestamp.
- Sem push, expansão para M/GNN ou ajuste pós-hoc para resgatar hipótese.

## Review Focus

- Reordenar braços ou acrescentar placebo muda a realização aleatória: tarefa 1 testa estabilidade de seed e igualdade dos dados.
- Réplica de calibração aparece na avaliação: tarefas 1/2 rejeitam sobreposição por identidade, não só por valor de seed.
- YAML legado, nomes inexistentes ou configuração científica incompleta: tarefa 1 falha antes de gerar dados.
- Surto não alcança uma região ou não é detectado: tarefa 3 conserva os denominadores corretos e a censura.
- Hipótese nula/controle ε=0 não é suportado: tarefa 5 reporta critério não satisfeito, sem acionar opcionais.

---

## Pré-condições e mapa de arquivos

Modificar `run.py`, `inject.py`, `tests/test_run.py`, `tests/test_inject.py`; criar configs `e1_smoke.toml`, `e1_bench.toml`, `e1_real.toml`, testes de integração em `tests/test_run.py`, notebooks `01_l0_network.ipynb`, `02_e1_results.ipynb`. Atualizar README/MIGRATION só nas seções correspondentes.

**Antes da Task 1:** G0/D5 resolvidos com fonte de quantidades de contagem e erros de treino do reconciliador, E0 demonstrado ou bloqueio explícito; decisões da spec §7 revisadas. Sem isso, implementar apenas validação/config/artifacts e smoke isolado dos componentes; não inventar a conexão MinT ou chamar o smoke de B1.

Não criar módulos adicionais preventivamente. Se run.py exceder 400 linhas, extrair exclusivamente parsing/dataclasses para `config.py` com `tests/test_config.py`, mantendo orquestração em run.py e ajustando imports em um único commit. Essa divisão depende do tamanho real.

### Task 1: Runner, configs, artefatos e composição dos braços — longContext

**Files:** Modify `src/headd_l0/run.py`, `tests/test_run.py`, `MIGRATION.md`; Create `configs/e1_smoke.toml`, `configs/e1_bench.toml`.

**Interfaces:** Consome funções/tipos dos dois planos anteriores. Produz `ArmSpec(name: str,use_hierarchy: bool,graph_id: str | None)`, `ExperimentConfig(name: str,run_id: str,root_seed: int,raw_dir: Path,output_dir: Path,train_months: int,window: int,epsilon_levels: tuple[float,...],noise_types: tuple[str,...],n_transition: int,n_null: int,n_calibration: int,n_placebos: int,target_far: float,detectors: tuple[str,...],reconciliation: str,selector: str,threshold: str,simulation: SimConfig | None,injection: InjectionConfig | None)`, `RunResult(path: Path,status: str,metrics: pd.DataFrame)`; todas congeladas.

`load_config(path: Path) -> ExperimentConfig`, `build_arms(n_placebos: int) -> tuple[ArmSpec,...]`, `run(cfg: ExperimentConfig) -> RunResult`, `main() -> int`. Entrada oficial: `uv run python -m headd_l0.run configs/e1_bench.toml`. Tipos de operação `name` são `e0_parity`, `e1_smoke`, `e1_bench`, `e1_real`; nome não seleciona algoritmo oculto. Configs de preparação continuam nas CLIs de seus módulos.

- [ ] **Step 1: Escrever `test_config_rejects_unknown_components`, `test_manifest_is_complete`, `test_run_id_is_not_overwritten`, `test_reordering_arms_preserves_seeds`, `test_one_variable_per_arm`, `test_labels_never_reach_pipeline`, `test_gate_blocks_interpretation`.** Fixtures pequenas usam componentes determinísticos substituídos para isolar orquestração; smoke real é Step 4.

```python
arms = build_arms(30)
assert len(arms) == 33
assert arms[0] == ArmSpec("B0", False, None)
assert arms[1] == ArmSpec("B1", True, None)
assert arms[2] == ArmSpec("B2", True, "observed")
assert set(manifest) >= {"config", "root_seed", "seeds", "git_sha", "reference_sha",
                         "timestamp_utc", "data_hashes", "graph_hashes", "gates"}
assert calibration_ids.isdisjoint(evaluation_ids)
np.testing.assert_array_equal(first_order_counts, second_order_counts)
```

Comparar configurações resolvidas dos braços removendo apenas `name/use_hierarchy/graph_id`; devem coincidir. Fit/transform recebem somente contagens e janelas; teste passa máscaras embaralhadas e exige scores iguais. Config inválida e dados ausentes geram erro, sem métricas de sucesso vazias.
- [ ] **Step 2:** `uv run pytest tests/test_run.py -v` → FAIL nos novos casos.
- [ ] **Step 3: Implementar.** `tomllib` → validação → dataclass. Seeds raiz spawn(6): dados, calibração, avaliação, placebos, detectores, bootstrap; criar todas as children pela ordem canônica, antes de iterar braços. Registrar entropy/spawn_key; tarefas da mesma réplica compartilham dados/seeds de detector. B0 usa local; B1 usa hierarchy; B2 acrescenta neighbors com W real; placebo troca só W. A posição de MinT deve ser exatamente a decisão resolvida em D5, com teste que demonstre unidades de contagem; nenhum ramo pode substituí-la por normalização de scores.

Config final: root_seed=42, train_months=60, window=12, ε=(0,.05,.20), ruídos white/env/dem, 500/500/200 por célula, n_placebos=30, target_far=1/60, seis detectores, mint_shrink/meta_des/evt_gpd. Estes complementos só são usados após revisão da spec. Smoke: 2 T+2 N por célula, 2 placebos e 2 N de calibração; exercita fallback de cauda curta, sem alegação estatística.
- [ ] **Step 4:** Testes/checks → PASS; `uv run python -m headd_l0.run configs/e1_smoke.toml` → todos os artefatos/manifest e status smoke. Repetir em outro run_id: mesmas contagens/scores/métricas, exceto timestamp/id/hash do manifesto. Capturar aviso claro se E0 indisponível; só smoke técnico permitido, sem análise de RQ1′.
- [ ] **Step 5:** `git add src/headd_l0/run.py tests/test_run.py configs/e1_smoke.toml configs/e1_bench.toml MIGRATION.md` e `git commit -m "feat: wire reproducible experiment arms and manifests"`.

### Task 2: Calibração FAR e piloto de custo — think / longContext

**Files:** Modify `src/headd_l0/run.py`, `tests/test_run.py`, `configs/e1_bench.toml`, `docs/protocol-decisions.md`.

**Interfaces:** Usa `threshold.calibration_report` por `(arm,region,noise,epsilon)`, fit de pool por réplica em meses 0–59, scores monitorados nos meses 60–131. Grava `calibration.parquet`: arm,graph_id,region,noise,epsilon,threshold,target_far,achieved_far,n,method,replicate_ids. Valores aprendidos diferentes não violam “mesmo limiar”: o método/target é que são comuns.

- [ ] **Step 1: Escrever `test_threshold_ignores_evaluation_scores`, `test_calibration_uses_null_only`, `test_no_twins_counted_as_independent_nulls`, `test_region_specific_far`.**

```python
assert all(row["label"] == "N" for row in calibration_replicates)
assert not (set(calibration_ids) & set(evaluation_ids))
assert np.array_equal(thresholds_before, thresholds_after_changing_evaluation)
assert np.all(calibration_far <= 1 / 60)
assert np.all(n_eligible == 200 * 72)
```

Simular região com escala de scores 100× outra para provar que threshold/FAR não são agrupados por escala. Gêmeas T carregam papel `counterfactual`, não `evaluation_null`.
- [ ] **Step 2:** `uv run pytest tests/test_run.py -k 'calibration or threshold or null or far' -v` → FAIL.
- [ ] **Step 3: Integrar calibração independente.** Usar 200 N adicionais por célula; salvar thresholds antes da avaliação. Produzir FAR N avaliada e IC por reamostragem de réplica. Pré-registrar critério de comparabilidade: proposta de desvio absoluto máximo `1/300` do alvo para a FAR pontual de cada braço/região/célula, e IC95% das diferenças B2−B1/real−placebo dentro de ±1/300. Falha vira `far_not_comparable`; não recalibrar olhando N de avaliação. Esse critério é adicional e requer revisão junto à §7.
- [ ] **Step 4:** Testes/checks → PASS; piloto com 10 T+10 N, 30 placebos e calibração reduzida mede wall time, RAM e custo por réplica. Gravar estimativa de duração completa e parâmetros do hardware no manifest. Não interpretar efeito nem usar esse piloto para escolher ε/seed/limiar. Memória deve processar uma réplica por vez e persistir resultados em partes.
- [ ] **Step 5:** `git add src/headd_l0/run.py tests/test_run.py configs/e1_bench.toml docs/protocol-decisions.md` e `git commit -m "feat: separate null calibration from FAR evaluation"`.

### Task 3: Bancada sintética e inferência primária — longContext / think

**Files:** Modify `src/headd_l0/run.py`, `tests/test_run.py`, `configs/e1_bench.toml`; Create `notebooks/02_e1_results.ipynb` inicialmente com leitura da bancada sintética.

**Interfaces:** Usa `simulate`, `detection_outcome`, `observed_far`, `classification_metrics`, `paired_bootstrap`, `placebo_rank`. Gera tabelas tidy da spec, `onsets.parquet` e `statistics.json`; preserva dados de censura e máscaras de regiões alcançadas. Agregação primária por réplica usa a média nas mesmas regiões com onset definido no gerador, independentemente do braço; diferenças entre braços nunca mudam a população avaliada.

- [ ] **Step 1: Escrever `test_primary_analysis_is_paired`, `test_missing_onset_excluded_consistently`, `test_no_detection_kept_in_bootstrap`, `test_placebo_criterion`, `test_zero_coupling_equivalence_gate`.** Fixtures de resultados manuais: B2 quatro meses antes, um surto perdido e uma região sem onset.

```python
assert primary["gain"]["estimate"] == 4.0
assert primary["n_replicates"] == 500
assert primary["placebo_rank"] == 29 / 30
assert summary["hypothesis_supported"] is False  # ε=0 fora da margem aprovada
assert missed_region_included and no_onset_region_excluded
```

Fixture de empate com 2 placebos deve manter fração estrita e ordem determinística. Alterar somente timestamps futuros não muda alarmes passados no smoke completo.
- [ ] **Step 2:** `uv run pytest tests/test_run.py -k 'primary or onset or detection or placebo or equivalence' -v` → FAIL.
- [ ] **Step 3: Implementar inferência.** Primeiro bootstrap pareado Δ restricted_lead B2−B1 por ε e ruído, 10.000 draws, IC95%; depois fração dos 30 placebos superados na mesma estatística agregada. Mesmas regiões/replicates/bootstrap indices em cada comparação. Critério proposto: IC>0 em ambos ε>0, equivalência ±1 mês em ε=0 e rank>.95, além dos gates E0/FAR. Publicar também efeitos por ruído sem selecionar estratos favoráveis. FAR permanece separada de desempenho em T.

ROC-AUC T/N usa um score por réplica: máximo regional no prefixo monitorado 60–83, cutoff fixo proposto 83. O cruzamento seed deve ser posterior ao cutoff por configuração validada; se não for, esse diagnóstico não é pré-onset e deve ser marcado. Não alinhar corte de features ao onset futuro. AP por região e métricas de tempo têm máscaras temporais explícitas; não comparar AP macro com tabela E0 por tarefa.
- [ ] **Step 4:** Testes/checks e smoke → PASS; após todos os gates, `uv run python -m headd_l0.run configs/e1_bench.toml` → 9.000 réplicas avaliadas, 1.800 N de calibração separadas, 33 braços, hashes e status completo. Gêmeas custam integrações adicionais mas não aumentam n de avaliação. Verificar contagens por célula/arm antes de interpretar tabelas. Não prometer que o resultado científico será positivo.
- [ ] **Step 5:** `git add src/headd_l0/run.py tests/test_run.py configs/e1_bench.toml notebooks/02_e1_results.ipynb` e `git commit -m "feat: run paired synthetic benchmark and placebo inference"`.

### Task 4: Injeção semi-real e protocolo secundário — default / inferência think

**Files:** Modify `src/headd_l0/inject.py`, `tests/test_inject.py`, `src/headd_l0/run.py`, `tests/test_run.py`, `MIGRATION.md`; Create `configs/e1_real.toml`.

**Interfaces:** Acrescenta `inject_propagated(counts: np.ndarray,A: np.ndarray,rng: np.random.Generator,cfg: InjectionConfig,*,train_end: int=60,attenuation: float=.5) -> InjectionResult`. Config original conserva defaults; tipo de perturbação = pulso positivo de 3 SD de treino, proposta do semi-real. Injeta semente num mês uniforme entre 72 e 118; vizinhos de primeira ordem um mês depois, amplitude .5, sem cascata para segunda ordem. Contagens reais originais não sofrem edição; devolver cópia.

- [ ] **Step 1: Escrever `test_neighbor_lag_is_one_month`, `test_attenuation_and_unchanged_non_neighbors`, `test_injection_uses_training_scale`, `test_aggregate_recomputed`, `test_secondary_stops_at_friedman`, `test_real_blocks_keep_methods_paired`.**

```python
out = inject_propagated(counts, A, np.random.default_rng(42), InjectionConfig())
s = out.seed_region
neighbors = A[s].astype(bool)
assert np.all(out.onset[neighbors] == out.onset[s] + 1)
np.testing.assert_array_equal(counts, original_copy)
np.testing.assert_array_equal(out.counts[:, :60], counts[:, :60])
np.testing.assert_array_equal(aggregated[0], out.counts.sum(axis=0))
```

Contagem adicionada = inteiro arredondado da amplitude, ≥1 na semente se SD zero; vizinho usa arredondamento da mesma amplitude×.5. Máscara/onset seguem alterações efetivas, não marcar caso em célula sem mudança. Verificar não vizinhos intactos.
- [ ] **Step 2:** `uv run pytest tests/test_inject.py tests/test_run.py -k 'propagat or neighbor or attenuation or secondary or blocks' -v` → FAIL.
- [ ] **Step 3: Implementar injeção e runner real.** 100 seeds propostas de injeção compartilhadas entre braços, treinamento 60 meses e features idênticas ao sintético. Recalcular PA por soma de folhas, distinto da injeção independente de E0. Null real = série sem injeção; não afirmar ausência de surtos naturais. Calibrar em blocos do período de treino com comprimento 12 e streams separados, reportando a limitação de FAR relativa ao proxy nulo.

Estatística: AP por região/método, média sobre seeds antes de ranks (seeds não viram novas regiões); bootstrap temporal circular de 12 meses dentro de cada região com índices pareados. Protocolo Friedman→Wilcoxon Bonferroni→DM→Cliff. Para DM usar erro quadrático dos alarmes 0/1 versus máscara 0/1 (perda de classificação), lag fixo 12, não supor que score é probabilidade; descrever essa escolha pré-registrada. Cliff compara métricas AP por região, com bootstrap95%, não escala arbitrária de scores. Sementes compartilham a mesma série real e não são observações independentes.
- [ ] **Step 4:** Testes/checks → PASS; `uv run python -m headd_l0.run configs/e1_real.toml` → outputs por região/seed/braço e sequência estatística respeitada, sem resultados substitutos para testes ausentes. Se Friedman p>.05, DM/Cliff ficam skipped com motivo, como exige AGENTS.
- [ ] **Step 5:** `git add src/headd_l0/inject.py tests/test_inject.py src/headd_l0/run.py tests/test_run.py configs/e1_real.toml MIGRATION.md` e `git commit -m "feat: evaluate propagated injections on real SIVEP counts"`.

### Task 5: Rede, resultados e reprodução da entrega — longContext

**Files:** Create `notebooks/01_l0_network.ipynb`; Modify `notebooks/02_e1_results.ipynb`, `README.md`, `MIGRATION.md`.

**Interfaces:** Consome exclusivamente artefatos dos runs completos e `graph.centralities`. Sem fitting/calibração dentro dos notebooks. Figuras PNG/SVG exportadas sob run; tabela Spearman por grau, intermediação e autovetor versus ordem de detecção em cada réplica, resumida por réplica. Empates recebem rank médio; sem detecção recebe posição censurada após os detectados e é identificada na legenda.

- [ ] **Step 1: Escrever verificação de entrada nos notebooks.**

```python
assert manifest["gates"]["e0"] == "passed"
assert set(metrics["arm"]) >= {"B0", "B1", "B2"}
assert metrics["replicate"].notna().all()
```

Se E0/FAR falhar, abrir seção de diagnóstico com status bloqueado, não figuras intituladas como evidência de RQ1′. Conferir também contagens esperadas por célula e referências de config/hash.
- [ ] **Step 2: Gerar mapa/figuras e tabelas.** A e exemplo placebo; distribuição de graus e centralidades; Δ por ε com IC; posição nos placebos; FAR por braço; detecção/censura; análise semi-real separada. Spearman é complementar/exploratório; não tratá-lo como teste causal. Usar outputs de stats.py, sem recalcular p-values em células diferentes.
- [ ] **Step 3: Atualizar README e MIGRATION.** Comandos uv, dependências adicionadas, proveniência, definição de lead/censura, tamanho efetivo de amostra, G0/E0, limites da observação mensal e grafo oráculo, proxies reais de nulo. Critério não satisfeito é reportado como resultado negativo para a bancada; dado/gate inválido é inconclusivo, não refutação científica. Nenhum opcional é acionado para modificar essa conclusão.
- [ ] **Step 4: Verificar reprodução.** Checks ruff/format/pytest; `uv run jupyter nbconvert --execute --to notebook --output-dir results/<run_id>/notebooks notebooks/01_l0_network.ipynb notebooks/02_e1_results.ipynb` → execução completa, sem reestimar parâmetros. Conferir figuras e tabelas visualmente. Dados originais continuam com mesmos hashes; nenhum arquivo do CDADE original foi alterado.
- [ ] **Step 5:** `git add notebooks/01_l0_network.ipynb notebooks/02_e1_results.ipynb README.md MIGRATION.md` e `git commit -m "docs: report reproducible network experiment results"`. Ao executar futuramente, incluir apenas os hunks de README produzidos nesta tarefa; preservar alterações do usuário.

## Extensões opcionais

Φ/B3 exige primeiro mapeamento auditado dos 11 rótulos de exame e dados reais; B-Gao exige split por réplica e cinco EWS; SEIRS exige nova validação numérica. São planos separados após a entrega obrigatória e nova priorização, sem instalar bibliotecas ou criar stubs antecipadamente. A interpretação de resultado negativo permanece válida sem essas extensões.
