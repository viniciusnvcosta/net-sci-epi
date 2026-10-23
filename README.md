# HEADD-Series L0 — Estrutura Relacional do Grafo

> Vinícius Nunes · <vnvc@ecomp.poli.br>

Estudo de detecção de surtos nas 13 regiões de saúde do Pará. A pergunta
**RQ1′** é se a adjacência geográfica, acrescentada ao ensemble CDADE como
features de vizinhança, antecipa a detecção a uma mesma taxa de falsos alarmes
(FAR), com ganho superior ao de grafos placebo que preservam graus.

## Estado científico — 23/10/2026

**RQ1′ permanece inconclusiva; `interpretation_allowed=false`.** E0 é
inconclusivo; E0* e FAR falharam. G4 foi aprovado pelo autor em 23/10
**somente para o perfil sintético fixo `P5-IMPL-2026-10-19-v1`**, aceitando
clipping e limitações do observável. Essa aprovação não passa outros gates,
não autoriza novos experimentos e não estabelece benefício ou ausência de benefício.

O [balanço científico atual](docs/evidence/2026-10-23-g4-ratification-summary/README.md)
reúne entregas P0–P9, denominadores, limitações e próximos gates.
As [decisões de protocolo](docs/protocol-decisions.md) prevalecem sobre planos
históricos. O [índice documental](docs/README.md) distingue guias atuais,
evidências imutáveis e especificações/planos históricos.

## Entregas e lacunas

| Entregue e validado tecnicamente | Limite científico / trabalho faltante |
| --- | --- |
| Dados SIVEP 2009–2019, ordem canônica e soma exata 13→1 em 132 meses | Contagens e fontes brutas permanecem imutáveis |
| Baseline B1*, detectores, NB2, reconciliação, seleção e limiares | E0*/FAR reprovados; G2 não aprovado |
| Grafo Queen A/W, mapa, GEXF e 30 placebos conexos preservando graus | G3 não aprovado; placebos não demonstram amostragem uniforme |
| Simulador metapopulacional, fixture e diagnósticos de fonte/mensais | G4 aprovado apenas para o perfil fixo e suas limitações |
| Features locais/relacionais, runner reduzido D-COST e smoke | G5/G6 não aprovados; smoke não representa bancada completa |
| Exportador descritivo e [notebook E1](notebooks/e1_results.ipynb) | Camada 1 e seu runner não implementados; bancada completa não executada |

A camada 0 ainda requer não-inferioridade; as camadas obrigatórias 0/1/2
estão incompletas. A projeção serial da bancada é 82–105 h no hardware
registrado. O [plano global](docs/superpowers/plans/headd-l0-global.md)
separa implementação, validação técnica e aprovação científica.

## Evidência preliminar

- **E0*:** AP média regional B1* = 0,54716 e z-score causal = 0,67813;
  ΔAP = −0,13097, com B1* inferior em 12/13 regiões. O limite inferior
  histórico do IC95% é −0,20186. PA tem 72 positivos/0 negativos e AP indefinida.
- **FAR:** três pares falharam abaixo da banda inclusiva [0,0133333; 0,02],
  para alvo 1/60 e tolerância 1/300; denominador de avaliação = 14.400
  meses por região/braço. O [diagnóstico E0*](docs/evidence/2026-10-21-e0-diagnostics/README.md)
  não estabeleceu defeito independente que autorize corrigir/reexecutar o gate.
- **P5/G4:** fontes oficiais e seis pares de medianas verificados;
  diagnósticos mensais com 64 T/64 N independentes por ruído, 384 realizações
  primárias e replay exato. AR1/CV válidos em 64/64 janelas por célula.
  Clipping de I em `outbreak`: white T/N = 3,36%/6,43%, dem = 1,69%/3,04%,
  env = 0%; S sem clipping. Os [denominadores e limites completos](docs/evidence/2026-10-22-p5-g4/README.md)
  integram o aceite G4; contagens mensais não recebem sinais CV impostos da fonte I.
- **D-REACH:** onset em vizinhos em ε=.20: white 165/200, env 132/200,
  dem 153/200; ε=0: 0/200 por ruído. Alcance não mede ganho de detecção.
  No smoke de três detectores, D5 falhou em 5/12 réplicas e FAR passou em
  somente 28/858 pares. Esses resultados não estimam a bancada completa.

## Ambiente e verificação

Python ≥3.12, ambiente e dependências fixados em `uv.lock`. Execute na raiz:

```bash
uv sync --locked
uv run pytest -o addopts='' -q
uv run ruff check .
uv run ruff format --check .
uv build
```

`-o addopts=''` remove a seleção rápida padrão e inclui testes `slow`,
`reference` e `integration`; alguns requerem dados/ambiente de referência
externos. Veja [reprodução e fontes](docs/development.md#ambiente-e-comandos)
e [proveniência da referência](docs/reference-provenance.md).
O build grava sdist/wheel em `dist/`.

Dados brutos são somente leitura; TOMLs distribuídos apontam para
`../hybrid-theory/data/raw`. Preparações geram `data/processed/` e manifests
em `results/`; ajuste caminhos antes de usar os comandos do guia.
Resultados publicados e evidências são imutáveis: repetições usam novos IDs,
sem substituir artefatos, seeds ou hashes de execuções anteriores.

Para auditar E0* **sem ajustar modelos nem escrever na origem**, indique um
run preservado que contenha os artefatos históricos completos:

```bash
uv run python -m headd_l0.e0_diagnostics \
  --source /caminho/para/e0-star-scoring-20260930 \
  --evidence docs/evidence/pr-2/e0-star-summary.json
```

O JSON sai em stdout; exit 0 confirma a auditoria, não aprovação científica.
A reprodução local original consta no [pacote E0*](docs/evidence/2026-10-21-e0-diagnostics/README.md#provenance-and-reproduction).
Para verificar fontes Gao locais em modo somente leitura:

```bash
uv run python - <<'PY'
import json
from pathlib import Path
from headd_l0.gao_sources import verify_sources
print(json.dumps(verify_sources(
    Path("data/processed/gao-p5-v1/Code.zip"),
    Path("data/processed/gao-p5-v1/supplement.pdf"),
    Path("tests/reference/gao_manifest.json")), indent=2))
PY
```

Ausência de bytes produz `pending`; bytes inválidos produzem `failed`.
O CLI de publicação G4 é `uv run python -m headd_l0.sim_validation configs/g4_validation.toml`.
Ele executa diagnósticos e escreve um pacote; uma reprodução autorizada exige
uma cópia do TOML com novo `run_id` e fontes locais verificadas. O ID distribuído
identifica a evidência histórica e não deve ser sobrescrito. O CLI continua
retornando exit 2 e manifests `pending`/`scientific_review=not_requested`:
a decisão posterior de 23/10 está no protocolo, sem reescrever esses estados
históricos. Nenhum desses comandos autoriza a bancada ou a inferência RQ1′.

## 5 · Protocolo experimental E1′

Os braços B1*, B2 e B2-placebo diferem apenas na informação relacional;
pool, reconciliação, seleção e alvo FAR permanecem iguais. As features são
causais e os limiares usam nulos de calibração distintos da avaliação.
A comparação requer bootstrap pareado por ε, seguido do rank estrito entre
30 placebos (>95%, isto é, 29/30), com equivalência em ε=0 por IC95%
estritamente dentro de (−1,+1) mês. Conclusão positiva ou negativa exige
camadas 0/1/2 completas e todos os gates aplicáveis.

O [protocolo aprovado](docs/protocol-decisions.md), o
[plano global](docs/superpowers/plans/headd-l0-global.md) e a
[nota de fontes Gao](docs/gao-source-preparation.md) detalham o desenho.
O perfil sintético não estima a epidemiologia do Pará nem reproduz exatamente
trajetórias upstream. Mobilidade, GNNs e SEIRS+ não são entregas desta etapa.
A [migração CDADE](MIGRATION.md) registra paridades, correções e exclusões;
[AGENTS.md](AGENTS.md) reúne os contratos de desenvolvimento.
