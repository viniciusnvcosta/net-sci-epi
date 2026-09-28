# Comandos verificados na pasta original

Verificação de 28/09/2026 em `/home/vinvs/projects/net-sci-epi`, após integrar
a Task 9. Ferramentas: **uv 0.12.19**, **Ruff 0.16.9**.

## Preparação e validação: exit 0

```bash
cd ~/projects/net-sci-epi
uv sync --locked
uv run python -m headd_l0.data configs/data.toml
uv run pytest -o addopts='' -q
uv run ruff check .
uv run ruff format --check .
uv build
```

| Comando | Resultado observado |
| --- | --- |
| `uv sync --locked` | Ambiente sincronizado com o lock; 149 pacotes verificados |
| `uv run python -m headd_l0.data configs/data.toml` | Preparação SIVEP concluída; outputs em `data/processed/sivep/`, manifest em `results/data/manifest.json` |
| `uv run pytest -o addopts='' -q` | **135 passed**; sem exclusão de testes por marcadores |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 25 files already formatted |
| `uv build` | sdist e wheel em `dist/` |

A preparação lê raw no caminho definido em `configs/data.toml` e não o altera.
Os arquivos de `data/processed/`, `results/` e `dist/` são regeneráveis e ignorados.
Os testes de integridade/paridade usam fixtures versionadas; o importador
transitório não é mais necessário na suíte atual.

## Pré-gate E0*: execução concluída, gate reprovado

```bash
uv run python -m headd_l0.run configs/e0_star.toml
```

**Exit 2**, por decisão do protocolo; não é um comando de aprovação do gate.
Gera `results/e0-star-preflight/{injection.npz,events.parquet,tasks.parquet,manifest.json}`.
Com seed 42, PA tem 72 meses positivos e zero negativos na janela de teste:
`gates.E0_star.status = "failed"`, motivo `single_class:PA`.
E0 permanece inconclusivo; `interpretation_allowed = false`.

Esse run já existe na pasta original. A CLI impede sobrescrita. Para repetir,
use uma cópia da configuração com outro `run_id`, mantendo a seed e o protocolo.
Não apague resultados existentes nem procure uma seed que passe o gate.

## Limite da preparação

A injeção, os diagnósticos e a função `check_e0_star` estão disponíveis.
A pipeline completa B1*/z-score com calibração FAR e as simulações L0 ainda
serão conectadas pelos planos de grafo/simulação e experimentos. O comando
`configs/e1_bench.toml` não está disponível nesta etapa. Nenhum resultado E1′
foi produzido ou autorizado para interpretação.

Próximos passos e diagnóstico: [estado da Task 9](e0-task9-status.md).
