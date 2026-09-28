# HEADD-Series L0 Experiments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar os braços com baseline autorizado, executar camadas 0/1/2 a FAR fixa e produzir conclusão rastreável sobre RQ1′, com camada 3 qualitativa.

**Architecture:** Um runner TOML compõe os componentes previamente testados; cada réplica é gerada uma vez e reutilizada por todos os braços. Seeds, partições e métodos são comuns. Avaliação e estatística consomem artefatos completos, incluindo falhas/censura.

**Tech Stack:** Python ≥3.12, uv, numpy/pandas/scipy, pyarrow, notebooks/matplotlib/seaborn, pytest/ruff; componentes dos planos E0 e L0.

**Spec:** [Arquitetura](../specs/2026-09-26-headd-l0-architecture.md), [plano global](2026-09-26-headd-l0-global.md), README §5; [baseline/E0](2026-09-26-headd-l0-e0.md), [grafo/simulação](2026-09-26-headd-l0-graph-simulation.md).

## Global Constraints

- “One variable per arm.” Pool/reconciliação/seleção/limiar idênticos entre B1\*/B2/placebo; representações e parâmetros aprendidos podem diferir.
- FAR = 1/60 por região-mês, calibrada em réplicas N independentes da avaliação.
- 3 ruídos ×3 ε ×(500 T+500 N) = 9.000 avaliações; 30 placebos; 13×132 por réplica.
- E0 registrado como **inconclusivo** (D-G0, 27/09, saída (i)); B1\* corrigido é o baseline autorizado e o gate que libera o E1′ é o E0\*. Rótulo `B1*` em todo artefato e texto.
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

Modificar `run.py`, `inject.py`, `tests/test_run.py`, `tests/test_inject.py`; criar configs `e1_smoke.toml`, `e1_bench.toml`, `e1_real.toml`, `e1_local.toml`, testes de integração em `tests/test_run.py`, notebooks `01_l0_network.ipynb`, `02_e1_results.ipynb`. Atualizar README/MIGRATION só nas seções correspondentes.

Revisão aprovada: [D-G0, D-E0\*, D2, D3, D5, D6, D-GT1–4, D-COST e D-REACH](../../protocol-decisions.md) (27/09). Camada 0 usa `inject_original_bounded`; camada 1 substitui o pulso por epidemia reutilizando simulate.py; camada 2 conserva seu mecanismo/onsets; camada 3 é qualitativa. Gate inválido ou alcance insuficiente é inconclusivo.

**Rota decidida:** D-G0 autorizou B1\* com E0 inconclusivo, e D5 fixou a conexão MinT: previsões NB2 um passo à frente reconciliadas por MinT(Shrink), com detectores sobre resíduos padronizados (E0 Task 3). Para interpretar E1′, exigir o E0\* aprovado (E0 Task 9, executado na camada 0 da Task 4), FAR comparável e os demais gates aplicáveis válidos.

Não criar módulos adicionais preventivamente. Se run.py exceder 400 linhas, extrair exclusivamente parsing/dataclasses para `config.py` com `tests/test_config.py`, mantendo orquestração em run.py e ajustando imports em um único commit. Essa divisão depende do tamanho real.

### Task 1: Runner, configs, artefatos e composição dos braços — longContext

**Files:** Modify `src/headd_l0/run.py`, `tests/test_run.py`, `MIGRATION.md`; Create `configs/e1_smoke.toml`, `configs/e1_bench.toml`.

**Interfaces:** Consome funções/tipos dos dois planos anteriores. Produz `ArmSpec(name: str,residuals: str,graph_id: str | None)`, com `residuals ∈ {"base","reconciled"}`, `ExperimentConfig(name: str,run_id: str,root_seed: int,raw_dir: Path,output_dir: Path,train_months: int,window: int,epsilon_levels: tuple[float,...],noise_types: tuple[str,...],n_transition: int,n_null: int,n_calibration: int,n_placebos: int,target_far: float,detectors: tuple[str,...],reconciliation: str,selector: str,threshold: str,simulation: SimConfig | None,injection: InjectionConfig | EpidemicInjectionConfig | None,real_null: RealNullConfig | None,layer: str,baseline_id: str)`, `RunResult(path: Path,status: str,metrics: pd.DataFrame)`; todas congeladas.

`load_config(path: Path) -> ExperimentConfig`, `build_arms(n_placebos: int) -> tuple[ArmSpec,...]`, `run(cfg: ExperimentConfig) -> RunResult`, `main() -> int`. Entrada oficial: `uv run python -m headd_l0.run configs/e1_bench.toml`. Tipos de operação `name` são `e0_parity`, `e1_smoke`, `e1_bench`, `e1_real`, `e1_local`; nome não seleciona algoritmo oculto. Tipos da injeção/nulo são definidos na Task 4 e só exigidos nos modos correspondentes. `baseline_id` é `B1*` (D-G0); nenhum artefato usa `B1` ou "CDADE v1". Configs de preparação continuam nas CLIs de seus módulos.

- [ ] **Step 1: Escrever `test_config_rejects_unknown_components`, `test_manifest_is_complete`, `test_run_id_is_not_overwritten`, `test_reordering_arms_preserves_seeds`, `test_one_variable_per_arm`, `test_labels_never_reach_pipeline`, `test_gate_blocks_interpretation`.** Fixtures pequenas usam componentes determinísticos substituídos para isolar orquestração; smoke real é Step 4.

```python
arms = build_arms(30)
assert len(arms) == 33
assert arms[0] == ArmSpec("B0", "base", None)
assert arms[1] == ArmSpec("B1*", "reconciled", None)
assert arms[2] == ArmSpec("B2", "reconciled", "observed")
assert set(manifest) >= {"config", "root_seed", "seeds", "git_sha", "reference_sha",
                         "timestamp_utc", "data_hashes", "graph_hashes", "gates"}
assert calibration_ids.isdisjoint(evaluation_ids)
np.testing.assert_array_equal(first_order_counts, second_order_counts)
```

Comparar configurações resolvidas dos braços removendo apenas `name/residuals/graph_id`; devem coincidir. Fit/transform recebem somente contagens e janelas; teste passa máscaras embaralhadas e exige scores iguais. Config inválida e dados ausentes geram erro, sem métricas de sucesso vazias.

- [ ] **Step 2:** `uv run pytest tests/test_run.py -v` → FAIL nos novos casos.
- [ ] **Step 3: Implementar.** `tomllib` → validação → dataclass. Seeds raiz spawn(6): dados, calibração, avaliação, placebos, detectores, bootstrap; criar todas as children pela ordem canônica, antes de iterar braços. Registrar entropy/spawn_key; tarefas da mesma réplica compartilham dados/seeds de detector. Previsões NB2 e reconciliação MinT(Shrink) são calculadas uma vez por réplica e compartilhadas (D5). B0 usa features locais dos resíduos base y − μ̂; B1\* usa features locais dos resíduos reconciliados y − P·μ̂; B2 acrescenta neighbors com W real sobre os mesmos resíduos (PA com zeros relacionais); placebo troca só W. Teste demonstra que o MinT recebe contagens previstas, nunca scores; nenhum ramo substitui a reconciliação por normalização de scores.

Config final: root_seed=42, train_months=60, window=12, ε=(0,.05,.20), ruídos white/env/dem, 500/500/200 por célula, n_placebos=30, target_far=1/60, seis detectores, mint_shrink/meta_des/evt_gpd. Estes complementos só são usados após revisão da spec. Smoke: 2 T+2 N por célula, 2 placebos e 2 N de calibração; exercita fallback de cauda curta, sem alegação estatística.

- [ ] **Step 4:** Testes/checks → PASS; `uv run python -m headd_l0.run configs/e1_smoke.toml` → todos os artefatos/manifest e status smoke. Repetir em outro run_id: mesmas contagens/scores/métricas, exceto timestamp/id/hash do manifesto. O smoke é técnico e não analisa RQ1′ em nenhuma rota. Se E0 estiver indisponível sem autorização D-G0 por B1*, registrar bloqueio da interpretação; com essa autorização, os demais modos ainda dependem de D5 e dos próprios gates.
- [ ] **Step 5:** `git add src/headd_l0/run.py tests/test_run.py configs/e1_smoke.toml configs/e1_bench.toml MIGRATION.md` e `git commit -m "feat: wire reproducible experiment arms and manifests"`.

### Task 2: Calibração FAR e piloto antecipado — think / longContext

**Files:** Modify `src/headd_l0/run.py`, `tests/test_run.py`, `configs/e1_bench.toml`, `docs/protocol-decisions.md`.

**Interfaces:** Usa `threshold.calibration_report` por `(arm,region,noise,epsilon)`, fit de pool por réplica em meses 0–59, scores monitorados nos meses 60–131. Grava `calibration.parquet`: arm,graph_id,region,noise,epsilon,threshold,target_far,achieved_far,n,method,replicate_ids. Valores aprendidos diferentes não violam “mesmo limiar”: o método/target é que são comuns. Na camada 1, nulos vêm da NB sazonal/tendência da Task 4, ajustada apenas no treino, com avaliação N independente; bootstrap em blocos é diagnóstico secundário.

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
- [ ] **Step 3: Integrar calibração independente.** Usar 200 N adicionais por célula; salvar thresholds antes da avaliação. Produzir FAR N avaliada e IC por reamostragem de réplica. Pré-registrar critério de comparabilidade: proposta de desvio absoluto máximo `1/300` do alvo para a FAR pontual de cada braço/região/célula, e IC95% das diferenças B2−B1\*/real−placebo dentro de ±1/300. Falha vira `far_not_comparable`; não recalibrar olhando N de avaliação. Esse critério é adicional e requer revisão junto à §7.
- [ ] **Step 4: Verificar calibração e executar o piloto na janela antecipada D-COST.** Testes/checks → PASS. O piloto de custo deve ocorrer ~02/10, logo após detectores e simulador acoplado, antes do calendário original desta tarefa. Usar10T+10N,30placebos e calibração reduzida; medir tempo/RAM por componente. Se seleção ainda não existe, registrar custo não medido e completar a medição quando disponível, sem inverter a ordem de porte. Congelar hardware/orçamento/gatilho antes do piloto e não inspecionar efeitos. Registrar o hardware (CPU, núcleos, RAM, SO/WSL) em `docs/reference-provenance.md` antes do piloto. Gatilhos da [D-COST](../../protocol-decisions.md) sobre a projeção da execução completa nesse hardware: acima de **48 h** → degrau (a), placebos em 100T fixas/célula, B2 no mesmo subconjunto para rank, calibração e N de avaliação completas; acima de **96 h** → degrau (b), 200T+200N/célula; se ainda insuficiente → degrau (c), cortar opcionais. A escada é aplicada antes de ver qualquer efeito, não corta a camada 0 e não altera a ordem de porte. Gravar IDs por seed antes dos resultados, nível da escada e tamanho efetivo. Memória processa uma réplica por vez.
- [ ] **Step 5:** `git add src/headd_l0/run.py tests/test_run.py configs/e1_bench.toml docs/protocol-decisions.md` e `git commit -m "feat: separate null calibration from FAR evaluation"`.

### Task 3: Bancada sintética e inferência primária — longContext / think

**Files:** Modify `src/headd_l0/run.py`, `tests/test_run.py`, `configs/e1_bench.toml`; Create `notebooks/02_e1_results.ipynb` inicialmente com leitura da bancada sintética.

**Interfaces:** Usa `simulate`, `detection_outcome`, `observed_far`, `classification_metrics`, `paired_bootstrap`, `placebo_rank`. Gera tabelas tidy da spec, `onsets.parquet` e `statistics.json`; preserva dados de censura e máscaras de regiões alcançadas. Agregação primária por réplica usa a média nas mesmas regiões com onset definido no gerador, independentemente do braço; diferenças entre braços nunca mudam a população avaliada.

- [ ] **Step 1: Escrever `test_primary_analysis_is_paired`, `test_missing_onset_excluded_consistently`, `test_no_detection_kept_in_bootstrap`, `test_placebo_criterion`, `test_zero_coupling_equivalence_gate`.** Fixtures de resultados manuais: B2 quatro meses antes, um surto perdido e uma região sem onset.

```python
assert primary["gain"]["estimate"] == 4.0
assert primary["n_replicates"] == configured_n_transition
assert primary["placebo_rank"] == 29 / 30
assert summary["hypothesis_supported"] is False  # ε=0 fora da margem aprovada
assert missed_region_included and no_onset_region_excluded
```

Fixture de empate com 2 placebos deve manter fração estrita e ordem determinística. Alterar somente timestamps futuros não muda alarmes passados no smoke completo.

- [ ] **Step 2:** `uv run pytest tests/test_run.py -k 'primary or onset or detection or placebo or equivalence' -v` → FAIL.
- [ ] **Step 3: Implementar inferência.** Primeiro bootstrap pareado Δ restricted_lead B2−baseline por ε e ruído, 10.000 draws, IC95%; depois fração dos 30 placebos superados na mesma estatística agregada. Mesmas regiões/replicates/bootstrap indices em cada comparação. No rank, B2 e todos os placebos usam os mesmos IDs pré-fixados por D-COST; não usar B2 completo contra placebo reduzido. Antes dos braços, checar D-REACH por ε/célula; mínimo proposto≥50% de T com algum vizinho alcançado em ε=.20. Falha marca insufficient_power, sem conclusão negativa e sem ajuste do gerador. Critério proposto: IC>0 em ambos ε>0, equivalência ±1 mês em ε=0 e rank>.95, além da rota E0 aprovado **ou** D-G0/B1* autorizado com E0 inconclusivo, FAR comparável, D5 e demais gates válidos. Publicar também efeitos por ruído sem selecionar estratos favoráveis. FAR permanece separada de desempenho em T.

ROC-AUC T/N usa um score por réplica: máximo regional no prefixo monitorado 60–83, cutoff fixo proposto 83. O cruzamento seed deve ser posterior ao cutoff por configuração validada; se não for, esse diagnóstico não é pré-onset e deve ser marcado. Não alinhar corte de features ao onset futuro. AP por região e métricas de tempo têm máscaras temporais explícitas; não comparar AP macro com tabela E0 por tarefa.

- [ ] **Step 4:** Testes/checks e smoke → PASS; após todos os gates, `uv run python -m headd_l0.run configs/e1_bench.toml` → dimensão inicial de 9.000 réplicas avaliadas,1.800N de calibração separadas e33braços, ou dimensão reduzida estritamente conforme D-COST, com hashes, IDs e justificativa. Assertar contagens contra configuração resolvida, não contra um total fixo incompatível com a redução. Gêmeas custam integrações adicionais mas não aumentam n de avaliação. Verificar contagens por célula/arm antes de interpretar tabelas. Não prometer que o resultado científico será positivo.
- [ ] **Step 5:** `git add src/headd_l0/run.py tests/test_run.py configs/e1_bench.toml notebooks/02_e1_results.ipynb` e `git commit -m "feat: run paired synthetic benchmark and placebo inference"`.

### Task 4: Camadas 0/1, nulos paramétricos e análise real — default / inferência think

**Files:** Modify `src/headd_l0/inject.py`, `tests/test_inject.py`, `src/headd_l0/run.py`, `tests/test_run.py`, `MIGRATION.md`; Create `configs/e1_real.toml`, `configs/e1_local.toml`. Reutiliza `simulate.py` e contratos de E0; não criar segundo simulador nem manter inject_propagated/pulso como sensibilidade.

**Interfaces:** Preservar `InjectionConfig`, `InjectionResult`, `inject_original_bounded` da E0 Task 9. Acrescentar configuração congelada:

```python
@dataclass(frozen=True)
class EpidemicInjectionConfig:
    epsilon: float
    size_multipliers: tuple[float, ...]
    r0_range: tuple[float, float]
    testing_rate: float
    intro_month_range: tuple[int, int]
    train_months: int


def inject_epidemic(counts: np.ndarray, W: np.ndarray,
                    rng: np.random.Generator,
                    cfg: EpidemicInjectionConfig, k: float) -> InjectionResult: ...
```

Nulos ([D-GT3](../../protocol-decisions.md)): o modelo é fixo, NB2 com tendência e dois pares de harmônicos, ajustado por região nos meses 0–59. O ajuste reusa `forecast.fit_nb2`/`NB2Fit` da E0 Task 3 (mesmo modelo das previsões do MinT); acrescentar `sample_nb2(fit: NB2Fit, months: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray` em `forecast.py`, saída `[n,n_series,len(months)]` inteira não negativa. Sem `RealNullConfig`: não há escolhas de modelo em aberto. Não criar abstração de modelos nulos genéricos.

**Gate de desenho:** D-GT4 fixou tamanho (casos observados em excesso na semente, alvo k × max(mediana mensal de treino, 1), k ∈ {1,3,6}, realizado sempre reportado), introdução uniforme em 72–118, θ igual ao da bancada e truncamento permitido e contado no mês 131. **Pendentes com o usuário:** a faixa de R0 e o perfil completo do simulador (D-GT2/D-GT4), a fixar após a validação de uma região. O contrato de EpidemicInjectionConfig deve referenciar esse perfil/hash sem configuração global oculta. O motor expõe `EpidemicFlows` (grafo/simulação Task 3). Não inventar esses valores: a tarefa para neste ponto até a decisão.

- [ ] **Step 1: Escrever os testes de injeção.** `test_epsilon_zero_leaves_non_seed_untouched`, `test_training_months_untouched`, `test_size_relative_to_training_median`, `test_onsets_exact_and_censored`, `test_aggregate_recomputed`, `test_real_counts_not_mutated`, `test_deterministic_given_seed`. Asserção do tamanho usa a definição aprovada em D-GT4, não igualdade arbitrária após binomial.

```python
out = inject_epidemic(counts, W, np.random.default_rng(42), cfg_zero, k=1)
others = np.arange(13) != out.seed_region
np.testing.assert_array_equal(out.counts[others], counts[others])
np.testing.assert_array_equal(out.counts[:, :60], counts[:, :60])
np.testing.assert_array_equal(counts, original_copy)
assert (out.onset[others] == -1).all()
np.testing.assert_array_equal(aggregated[0], out.counts.sum(axis=0))
```

- [ ] **Step 2:** `uv run pytest tests/test_inject.py -k 'epsilon or training or size or onset or aggregate or mutated or deterministic' -v` → FAIL nas novas funções ausentes.
- [ ] **Step 3: Implementar o adaptador após resolver D-GT4.** Reutilizar componente de surto com ν=0, outras regiões inicialmente sem surto e acoplamentoC; impedir casos espontâneos fora da semente no controle ε=0. Somar casos observados não negativos a cópia do SIVEP, recomputar PA e não aplicar θ duas vezes. k=(1,3,6), alvo=k×max(mediana de treino da semente, 1); introdução uniforme 72–118 inclusive. Semente onset=introdução; demais primeiro mês de caso importado observado≥1, ausência−1. Não alterar onsetsR0/2SD da camada 2.
- [ ] **Step 4: Escrever testes dos nulos.** `test_null_fit_uses_training_only` altera meses≥60 e exige coeficientes idênticos; `test_null_panels_have_integer_counts` exige shape(200,13,132), inteiros≥0; `test_null_aggregate_is_sum` verificaPA; `test_null_sampling_deterministic` compara mesma seed; `test_null_calibration_evaluation_disjoint` verifica IDs/streams distintos. Fit inválido deve produzir diagnóstico explícito, não modelo substituto silencioso.
- [ ] **Step 5:** `uv run pytest tests/test_inject.py -k null -v` → FAIL.
- [ ] **Step 6: Implementar nulos (D-GT3 decidida).** Reusar `forecast.fit_nb2` (statsmodels já declarado), ajuste só meses 0–59 de cada região; se um ajuste não convergir, registrar a falha, calibrar essa região pelo bootstrap em blocos do treino e marcá-la em todos os artefatos. Gerar200 painéis de calibração (200 séries por região), com PA calculado, e conjunto N independente de avaliação cujo tamanho foi fixado antes da execução. Manifestar parâmetros, fórmula, seeds, adequação no treino e falhas. FAR 1/60, tolerância 1/300. Nas demais regiões, blocos do treino são apenas diagnóstico, sem substituir silenciosamente o nulo principal.
- [ ] **Step 7: Escrever testes das análises por camada.** `test_local_layer_uses_bounded_injection` exige `inject_original_bounded` com seeds da camada 0, PA calculado pela soma das regiões e máscara PA pela união regional; `test_e0_star_runs_before_e1` exige o E0\* avaliado antes de qualquer resultado; `test_noninferiority_resamples_regions` verifica pares B1\*/B2, bootstrap sobre as 13 regiões, limite inferior do IC ≥ −0,02 e PA reportado à parte; `test_real_primary_uses_epidemic_onsets` verifica definição camada 1; `test_real_gate_blocks_unresolved_choices` impede conclusão antes dos critérios aprovados; `test_secondary_stops_at_friedman` preserva ordem estatística. Se B1* autorizado, teste exige baseline_idB1* e E0inconclusive, sem substituir tabelas de paridade.
- [ ] **Step 8:** `uv run pytest tests/test_run.py -k 'local_layer or noninferiority or real_primary or real_gate or secondary' -v` → FAIL.
- [ ] **Step 9: Integrar configurações e inferência.** Camada 0 usa e1_local.toml e `inject_original_bounded`; executa primeiro o E0\* (B1\* contra o z-score móvel causal) e, com ele aprovado, a não-inferioridade: limite inferior do IC 95% da média de ΔAUC-PR(B2 − B1\*) ≥ −0,02, bootstrap pareado de 10.000 reamostras sobre as 13 regiões, PA reportado à parte. Falha é custo do método, não refutação de RQ1′. Camada1 usa e1_real.toml,100seeds propostas compartilhadas entre braços, estratos ε/k e perfil de ruído fixado. Antes dos braços medir D-REACH; executar bootstrap pareado→rankplacebo→critério conjunto como na camada 2, com equivalência ε=0 e FAR válida. Reutilizar os mesmos fundos reais não cria100observações epidemiológicas independentes; explicitar inferência condicional aos fundos e injeções.

Preservar análise secundária: AP por região/método agregada sobre seeds antes de ranks; Friedman→Wilcoxon/Bonferroni→DM/HAC→Cliff/IC95%, interrompendo se Friedman p>.05. DM usa perdas quadráticas de alarmes0/1 versus máscara0/1 e lag12; Cliff usa AP por região. Bootstrap temporal em blocos pode diagnosticar estabilidade, mas não é o gerador nulo principal; o pulso ad hoc foi removido sem sensibilidade paralela.

- [ ] **Step 10:** Testes completos/checks → PASS; executar `uv run python -m headd_l0.run configs/e1_local.toml` e `uv run python -m headd_l0.run configs/e1_real.toml` somente com gates/desenho resolvidos. Outputs distinguem layer/baseline_id/ε/k/seed, nulo e censura. A ausência de decisões gera status blocked, não resultados artificiais.
- [ ] **Step 11:** `git add src/headd_l0/inject.py tests/test_inject.py src/headd_l0/run.py tests/test_run.py configs/e1_real.toml configs/e1_local.toml MIGRATION.md` e `git commit -m "feat: evaluate layered epidemic injections and parametric nulls"`.

### Task 5: Rede, resultados e reprodução da entrega — longContext

**Files:** Create `notebooks/01_l0_network.ipynb`; Modify `notebooks/02_e1_results.ipynb`, `README.md`, `MIGRATION.md`.

**Interfaces:** Consome exclusivamente artefatos dos runs completos e `graph.centralities`. Sem fitting/calibração dentro dos notebooks. Figuras PNG/SVG exportadas sob run; tabela Spearman por grau, intermediação e autovetor versus ordem de detecção em cada réplica, resumida por réplica. Empates recebem rank médio; sem detecção recebe posição censurada após os detectados e é identificada na legenda.

- [ ] **Step 1: Escrever verificação de entrada nos notebooks.**

```python
assert manifest["gates"]["interpretation"] == "allowed"  # D-G0 route (i), E0* passed; all other gates valid
baseline_id = manifest["baseline_id"]
assert (baseline_id, manifest["gates"]["G0"]["decision"], manifest["gates"]["E0"]["status"]) == (
    "B1*", "authorize_b1_star", "inconclusive"
)
assert manifest["gates"]["E0_star"]["passed"]
assert metrics["baseline_id"].eq(baseline_id).all()
assert set(metrics["arm"]) >= {"B0", "B1*", "B2"}
assert metrics["replicate"].notna().all()
```

O braço e o baseline se chamam `B1*` em identificadores, títulos, tabelas e legendas (D-G0). Se o E0\*, a FAR ou o alcance falhar, abrir seção de diagnóstico com status bloqueado/insufficient_power, sem figuras como evidência de RQ1′. O E0 permanece inconclusivo. Conferir também contagens esperadas por célula e referências de config/hash.

- [ ] **Step 2: Gerar mapa/figuras e tabelas.** A e exemplo placebo; distribuição de graus e centralidades; Δ por ε com IC; posição nos placebos; FAR por braço; detecção/censura; análises das camadas0/1 separadas e camada 3 qualitativa com fontes verificadas. Declarar que A gera as camadas 1/2 e B2 é oráculo; priorizar comparação com placebos/padrão ε. Spearman é complementar/exploratório; não tratá-lo como teste causal. Usar outputs de stats.py, sem recalcular p-values em células diferentes.
- [ ] **Step 3: Atualizar README somente nos hunks de§5.2/§5.4 e MIGRATION.** Comandos uv, dependências adicionadas, proveniência, definição de lead/censura, tamanho efetivo de amostra, G0/E0, limites da observação mensal e grafo oráculo, proxies reais de nulo. Critério não satisfeito é reportado como resultado negativo para a bancada; dado/gate inválido é inconclusivo, não refutação científica. Nenhum opcional é acionado para modificar essa conclusão. Documentar limitação da soma epidêmica sem interação/depleção compartilhada; eventos documentados são qualitativos e suas fontes devem ser verificadas antes da descrição.
- [ ] **Step 4: Verificar reprodução.** Checks ruff/format/pytest; `uv run jupyter nbconvert --execute --to notebook --output-dir results/<run_id>/notebooks notebooks/01_l0_network.ipynb notebooks/02_e1_results.ipynb` → execução completa, sem reestimar parâmetros. Conferir figuras e tabelas visualmente. Dados originais continuam com mesmos hashes; nenhum arquivo do CDADE original foi alterado.
- [ ] **Step 5:** `git add notebooks/01_l0_network.ipynb notebooks/02_e1_results.ipynb README.md MIGRATION.md` e `git commit -m "docs: report reproducible network experiment results"`. Ao executar futuramente, incluir apenas os hunks de README produzidos nesta tarefa; preservar alterações do usuário.

## Extensões opcionais

Φ/B3 exige primeiro mapeamento auditado dos 11 rótulos de exame e dados reais; B-Gao exige split por réplica e cinco EWS; SEIRS exige nova validação numérica. São planos separados após a entrega obrigatória e nova priorização, sem instalar bibliotecas ou criar stubs antecipadamente. A interpretação de resultado negativo permanece válida sem essas extensões.
