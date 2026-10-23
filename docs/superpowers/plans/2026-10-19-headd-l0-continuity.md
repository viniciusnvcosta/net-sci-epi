# HEADD-Series L0 Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar até 23/10/2026 um pacote preliminar reproduzível do estado científico atual e preparar, sem antecipar decisões pendentes, a continuação P5–P9 da bancada E1′.

**Architecture:** O fechamento preliminar reutiliza os artefatos imutáveis de E0\* e P4, publica somente resumos/hash pequenos e mantém `interpretation_allowed=false`. A continuação segue gates sequenciais: decisão P5 → simulador de uma região → acoplamento → runner/FAR → E1 técnico → inferência condicionada → relatório.

**Tech Stack:** Python ≥3.12, uv, numpy, pandas, scipy, scikit-learn/PyOD, river, networkx, geobr/geopandas/libpysal, pyarrow, pytest, ruff e GitHub Actions.

**Spec:** [Arquitetura e decisões](../specs/headd-l0-architecture.md), [decisões de protocolo](../../protocol-decisions.md), [plano global](headd-l0-global.md), [AGENTS.md](../../../AGENTS.md), [README §5](../../../README.md#5--protocolo-experimental-e1).

## Global Constraints

- O prazo de resultados preliminares é 23/10/2026.
- E0 permanece inconclusivo; E0\* e FAR falharam no run preservado de 30/09.
- `interpretation_allowed=false` até que uma decisão de protocolo explícita altere o gate.
- Não ajustar pool, parâmetros, seed, tolerância FAR ou perfil Gao para resgatar resultados.
- Dados brutos são imutáveis; artefatos derivados são regeneráveis e ficam fora do Git.
- Uma variável por braço, FAR fixa, sem look-ahead e contagens antes de taxas.
- O perfil científico P5 deve ser decidido antes da implementação de `simulate.py`.
- Camada 1 é prioritária; Φ/B3, B-Gao e SEIRS permanecem opcionais.
- Cada nova função pública recebe teste; cada tarefa termina com Ruff, pytest e commit local.

## Review Focus

- Distinguir validação técnica, aprovação de gate e autorização de interpretação.
- Verificar que hashes publicados correspondem aos artefatos preservados, sem versionar resultados volumosos.
- Confirmar independência entre streams de calibração e avaliação.
- Confirmar ε=0 sem propagação além do fundo endêmico.
- Preservar censura e denominadores quando onset/detecção não ocorrer.
- Bloquear comparação de braços quando a FAR não estiver dentro da tolerância predefinida.

---

### Task 1: Fechar o pacote preliminar reproduzível

**Files:**

- Verify: `docs/evidence/pr-2/e0-star-summary.json`
- Verify: `docs/evidence/pr-2/graph-summary.json`
- Modify: `docs/development.md`
- Modify: `README.md`

- [x] **Step 1: Verificar os resumos JSON**

Run:

```bash
python -m json.tool docs/evidence/pr-2/e0-star-summary.json >/dev/null
python -m json.tool docs/evidence/pr-2/graph-summary.json >/dev/null
```

Expected: ambos os comandos retornam exit 0.

- [x] **Step 2: Verificar os hashes contra os artefatos locais**

Run:

```bash
sha256sum results/e0-star-scoring-20260930/manifest.json \
  results/e0-star-scoring-20260930/metrics.parquet \
  results/e0-star-scoring-20260930/far.parquet \
  data/processed/graph/manifest.json \
  data/processed/graph/adjacency.npy \
  data/processed/graph/W.npy \
  data/processed/graph/S.npy \
  data/processed/graph/placebos.npy
```

Expected: os digests coincidem com `docs/evidence/pr-2/*.json`.

- [x] **Step 3: Atualizar o texto preliminar sem reinterpretar os gates**

Documentar no README/desenvolvimento: E0 inconclusivo, E0\*/FAR falharam,
P4/P6 validados tecnicamente, P5 pendente e nova data 23/10/2026.

- [x] **Step 4: Verificar a documentação**

Run:

```bash
rg -n "23/10/2026|interpretation_allowed=false|E0\*.*failed" README.md docs
```

Expected: prazo e bloqueios aparecem sem afirmação de E1 interpretável.

- [x] **Step 5: Commit**

```bash
git add README.md docs/development.md docs/evidence/pr-2
git commit -m "docs: preserve preliminary evidence and revised deadline"
```

Concluída em 19/10/2026 no commit `083c1c7`; JSON válido, dez hashes conferidos
contra os artefatos locais e linguagem de gates revisada.

### Task 2: Resolver o gate científico P5 antes de codificar

**Files:**

- Modify: `docs/protocol-decisions.md`
- Modify: `docs/gao-source-preparation.md`
- Modify: `docs/superpowers/specs/headd-l0-architecture.md`
- Create: `tests/reference/gao_manifest.json`

- [ ] **Step 1: Reabrir a evidência congelada**

Conferir as equações, tabelas e hashes já registrados. Não baixar nova fonte
nem alterar o critério enquanto a decisão estiver pendente.

- [ ] **Step 2: Apresentar a decisão ao responsável científico**

Submeter, com os valores observados, duas decisões independentes:

1. alvo de paridade: equações do suplemento, executável predecessor ou modelo
   explicitamente corrigido; e
2. critério de separação: paridade com os rótulos/tabelas oficiais, aceitando a
   direção observada de CV branco, ou gate AR1/CV direcional anterior, que
   mantém P5 bloqueado para ruído branco.

A decisão do perfil deve ainda fixar: estados/inputs determinísticos, `dt`,
inovações e saída esperada de um passo; escala demográfica, resets, burn-in,
crossing e tempo físico; incidência latente, integerização, θ, calendário e
intervalos parciais; conversão de N/transmissão, estados iniciais, parâmetros
endêmicos/sazonais, comprimento de treino e janelas T/N.

Stop condition: não implementar simulador antes de aprovação explícita e
datada de uma opção. A decisão deve dizer se substitui ou apenas qualifica o
critério anterior.

- [ ] **Step 3: Registrar a decisão e o manifesto de referência**

Adicionar ID, data, racional, tabelas/hashes e critérios exatos. Criar
`tests/reference/gao_manifest.json` apontando para a fixture aprovada e seu
SHA-256; não versionar dados de licença incerta sem autorização.

- [ ] **Step 4: Validar o manifesto sem criar um commit vermelho**

Validar JSON, hashes, shape, rótulos e completude do perfil com um comando de
leitura descartável. O teste automatizado do manifesto será escrito no início
da Task 3 e commitado junto com a implementação que o faz passar.

- [ ] **Step 5: Commit**

```bash
git add docs/protocol-decisions.md docs/gao-source-preparation.md \
  docs/superpowers/specs/headd-l0-architecture.md tests/reference/gao_manifest.json
git commit -m "docs: approve Gao parity profile for P5"
```

### Task 3: Implementar e validar o simulador de uma região

**Files:**

- Create: `src/headd_l0/simulate.py`
- Modify: `tests/test_simulate.py`
- Modify: `configs/simulation.toml`

- [ ] **Step 1: Escrever os testes de contrato**

Começar pelo contrato de `tests/reference/gao_manifest.json`: hash, shape,
rótulos e perfil divergentes devem falhar. Cobrir também `SimConfig` congelada,
`SimResult`, shapes `(1, 132)`, seeds via `Generator`, ruídos `white/env/dem`,
clipping de compartimentos, somas semanais para meses e observação binomial por θ.

- [ ] **Step 2: Executar o teste e observar a falha**

```bash
uv run pytest tests/test_simulate.py -q
```

Expected: FAIL por API ausente/incompleta.

- [ ] **Step 3: Implementar o mínimo integrador Euler–Maruyama**

Implementar somente o perfil aprovado em P5. Não adicionar SEIRS, hhh4 ou
dependências novas. A assinatura pública é:

```python
def simulate(cfg: SimConfig, W: np.ndarray, rng: np.random.Generator) -> SimResult:
    """Simulate one outbreak/null replicate under the approved profile."""
```

- [ ] **Step 4: Validar paridade/separação conforme a decisão P5**

Rodar a fixture congelada e registrar métricas por ruído, sem alterar faixas
após observar os resultados.

- [ ] **Step 5: Verificar e commit**

```bash
uv run pytest tests/test_simulate.py -q
uv run ruff check src/headd_l0/simulate.py tests/test_simulate.py
uv run ruff format --check src/headd_l0/simulate.py tests/test_simulate.py
git add src/headd_l0/simulate.py tests/test_simulate.py configs/simulation.toml
git commit -m "feat: add approved single-region outbreak simulator"
```

### Task 4: Adicionar acoplamento, twin run e onsets

**Files:**

- Modify: `src/headd_l0/simulate.py`
- Modify: `tests/test_simulate.py`
- Create: `src/headd_l0/calibrate.py`
- Create: `tests/test_calibrate.py`
- Create: `configs/endemic_calibration.toml`

- [ ] **Step 1: Escrever testes de acoplamento e causalidade**

Cobrir `C=(1-ε)I+εW`, ε=0 sem propagação além do fundo, twin com o mesmo stream,
onset da seed por R0>1, onset remoto por excesso >2 SD e determinismo por seed.

- [ ] **Step 2: Escrever teste da calibração endêmica**

Exigir medianas regionais calculadas somente do treino, nomes na ordem canônica
e manifest com hash da entrada/config/commit.

- [ ] **Step 3: Executar os testes e observar as falhas**

```bash
uv run pytest tests/test_simulate.py tests/test_calibrate.py -q
```

- [ ] **Step 4: Implementar o mínimo para passar**

Manter a API pública `simulate(cfg, W, rng) -> SimResult`; usar
`SeedSequence(root).spawn(n)` no chamador, não RNG global.

- [ ] **Step 5: Verificar e commit**

```bash
uv run pytest tests/test_simulate.py tests/test_calibrate.py -q
uv run ruff check src/headd_l0/simulate.py src/headd_l0/calibrate.py tests
git add src/headd_l0/simulate.py src/headd_l0/calibrate.py \
  tests/test_simulate.py tests/test_calibrate.py configs/endemic_calibration.toml
git commit -m "feat: couple regional simulations with shared twin noise"
```

### Task 5: Integrar o runner P7 e calibrar FAR sem vazamento

**Files:**

- Modify: `src/headd_l0/run.py`
- Modify: `src/headd_l0/threshold.py`
- Modify: `tests/test_run.py`
- Modify: `tests/test_threshold.py`
- Create: `configs/e1_smoke.toml`
- Create: `configs/e1_bench.toml`

- [ ] **Step 1: Escrever teste end-to-end mínimo**

Usar 1 ruído × 2 ε × 2 T + 2 N. Verificar braços B0/B1\*/B2/30 placebos,
mesmos replicates/features compartilháveis, uma variável relacional por braço,
streams disjuntos e manifest completo.

- [ ] **Step 2: Escrever teste de bloqueio FAR**

Um braço fora de `1/60 ± 0.2×1/60` deve permanecer nos artefatos, mas não pode
produzir comparação interpretável de lead time.

- [ ] **Step 3: Executar e observar as falhas**

```bash
uv run pytest tests/test_run.py tests/test_threshold.py -q
```

- [ ] **Step 4: Implementar o runner mínimo**

Reutilizar detectores, reconciliação, seleção, threshold e features existentes.
Não criar registry/factory novo; usar dicts locais aos módulos donos.

- [ ] **Step 5: Rodar smoke duas vezes**

Executar com a mesma seed em dois `run_id` novos e comparar hashes dos artefatos
determinísticos, desconsiderando timestamp e caminho de saída.

- [ ] **Step 6: Verificar e commit**

```bash
uv run pytest tests/test_run.py tests/test_threshold.py -q
uv run ruff check .
uv run ruff format --check .
git add src/headd_l0/run.py src/headd_l0/threshold.py tests configs/e1_smoke.toml configs/e1_bench.toml
git commit -m "feat: wire deterministic E1 smoke runner and FAR gate"
```

### Task 6: Executar D-COST, D-REACH e a bancada condicionada

**Files:**

- Modify: `docs/reference-provenance.md`
- Modify: `docs/protocol-decisions.md`
- Output: `results/<new-run-id>/manifest.json`
- Output: `results/<new-run-id>/metrics.parquet`

- [ ] **Step 1: Executar D-COST antes de inspecionar efeitos**

Medir o smoke no hardware registrado e aplicar os cortes predefinidos de
48 h/96 h. Não escolher orçamento depois de observar Δ lead time.

- [ ] **Step 2: Executar D-REACH**

Confirmar que cada célula ε/ruído tem surtos que alcançam regiões suficientes;
células sem alcance são reportadas como sem poder, não como efeito nulo.

- [ ] **Step 3: Executar a bancada autorizada**

```bash
uv run python -m headd_l0.run configs/e1_bench.toml
```

Expected: novo diretório imutável com config, seeds, SHA, versões, métricas e
status de todos os gates. Exit não zero é aceitável para gate científico falho,
desde que o manifest finalize explicitamente o estado.

- [ ] **Step 4: Auditar comparabilidade antes da estatística**

Checar FAR por braço, conjuntos de replicates, censura, denominadores, ε=0 e
preservação de grau dos placebos.

- [ ] **Step 5: Commit somente documentação/proveniência**

```bash
git add docs/reference-provenance.md docs/protocol-decisions.md
git commit -m "docs: record E1 cost reach and execution gates"
```

### Task 7: Calcular P8 e produzir P9 sem ultrapassar os gates

**Files:**

- Modify: `src/headd_l0/evaluate.py`
- Modify: `src/headd_l0/stats.py`
- Modify: `tests/test_evaluate.py`
- Modify: `tests/test_stats.py`
- Create: `notebooks/e1_results.ipynb`
- Modify: `README.md`

- [ ] **Step 1: Escrever testes estatísticos de referência**

Cobrir bootstrap pareado estratificado por ε, rank entre 30 placebos, ε=0,
Friedman→Wilcoxon→DM→Cliff na ordem aprovada e casos censurados.

- [ ] **Step 2: Executar e observar as falhas**

```bash
uv run pytest tests/test_evaluate.py tests/test_stats.py -q
```

- [ ] **Step 3: Implementar somente lacunas necessárias**

Não adicionar point-adjusted F1, GNN, mobilidade, novas camadas ou métricas não
predefinidas. Lead time é primário; AUC-PR e NAB são secundários.

- [ ] **Step 4: Gerar notebook e tabelas a partir dos artefatos**

O notebook deve ler `results/<run_id>/` e verificar o manifest. Se
`interpretation_allowed=false`, deve primeiro persistir tabelas/figuras
descritivas marcadas como não interpretáveis e o relatório de limitações; em
seguida, o comando exportador termina com exit 2 e mensagem explícita. Se a
interpretação estiver autorizada, produz também a inferência e termina com
exit 0.

- [ ] **Step 5: Verificação final**

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -o addopts='' -q
uv build
```

- [ ] **Step 6: Commit**

```bash
git add src/headd_l0/evaluate.py src/headd_l0/stats.py tests \
  notebooks/e1_results.ipynb README.md
git commit -m "feat: report gated E1 preliminary results"
```

## Entrega de 23/10/2026

Se P5 não estiver decidido ou qualquer gate posterior falhar até 23/10, a
entrega preliminar é o pacote reproduzível do estado atual: E0 inconclusivo,
E0\*/FAR falhos, P4/P6 tecnicamente validados, P5 pendente, hashes e limitações.
Isso é uma conclusão válida do protocolo; não autoriza tuning nem expansão do
grafo. Tasks 2–7 continuam sequencialmente após decisão explícita.
