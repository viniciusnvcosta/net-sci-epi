# Proveniência da referência CDADE e hardware

Registro da busca D-G0a ([registro de decisões](protocol-decisions.md)) e do hardware exigido pela D-COST. Tudo foi feito **somente em leitura** sobre `/home/vinvs/projects/hybrid-theory`: git com `GIT_OPTIONAL_LOCKS=0`, bancos SQLite abertos com `mode=ro&immutable=1`, PDFs lidos com `mutool draw -F txt` para um diretório temporário. `git status --short` do original é idêntico antes e depois da busca; HEAD continua em `fbfa609bba6cb0b0f2a9e8d73be18022aec319b7`.

## D-G0a — resultados apresentados do CDADE v1 (27/09/2026)

**Alvo:** tabela de AUC-PR por tarefa em 18 tarefas, média 0,597.

**Resultado: nenhuma proveniência encontrada.** Nenhum artefato inspecionado contém a tabela de 18 tarefas, o valor 0,597 ou qualquer AUC-PR agregado por região/tarefa.

### Rastreamento MLflow

| Armazenamento                                                                              | SHA-256                                                            | Execuções | Achado                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | --------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `results/mlruns.db` (experimentos `cdade_evaluation`, `cdade_baselines`, `cdade_ablation`) | `59447090ace909dc476abf9ed5c96d2cf091b197f42ba471471199c586cb3443` |       200 | Métricas por **dataset** (`sivep`, `tycho`, `uci_501`, `uci_394`), nunca por região. As 296 entradas `*auc_pr` ficam em [0,992; 1,000]. Toda avaliação SIVEP tem `n_test = 26` e AUC-PR = 1,0. |
| `mlflow.db` (experimento `Default`)                                                        | `788ce2004323608f01a1dfe3ac97c2cba1b602780fb1df4b0a6875279e288a86` |        91 | Execuções com `cdade_auc_pr = 0,371` e `n_test = 10`, sem tag de commit nas avaliações: compatível com a suíte de testes, não com dados SIVEP.                                                 |
| `mlruns/0/224a965cf525460093c112388ec1f37a/artifacts/metrics.json`                         | `4fc4a8a55702ce25072cc8d1d5f1a726d8b7594972b0a454ea71730aff5387b4` |         1 | Mesmo padrão (`cdade` 0,371), sem tarefas.                                                                                                                                                     |

Tags `mlflow.source.git.commit` presentes em `results/mlruns.db`: `46f6d06`, `9a1888a`, `9d14421`, `9f21849`, `a7fc1bc`, `aa160fd`, `c8b4e92`, `d79505a`, `ea76919`, `ec7556e`, `edd87e8`. Nenhuma execução com qualquer desses commits registra métricas por tarefa. Nenhum valor de métrica em nenhum dos dois bancos cai em [0,5965; 0,5975].

### Git

- Branches: `main` (`d1df8d6`, ancestral de `fbfa609`), `feat/dataset-autonomy` e `feat/experiment-reports` (ambas em `fbfa609`), `origin/main` (`d1df8d6`). Sem tags e sem stashes.
- `git grep -E "0[.,]597"` sobre os 100 commits de `git rev-list --all`: nenhuma ocorrência.

### Arquivos do working tree

| Caminho                                                            | SHA-256                                                            | Achado                                              |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | --------------------------------------------------- |
| `results/metrics.json`                                             | `e7b9a1417e0dfda3fc428440cb78e5165129bd684de8829ae2b46802e98b97a3` | por dataset                                         |
| `results/metrics/sivep/metrics.json`                               | `c4a1da269a6bd3f2553b8eddfa8a13ecea485d3db698a873cac629e1c181b66e` | 9 métodos, AUC-PR 1,0 (exceto `b2` 0,99999…)        |
| `results/metrics/tycho/metrics.json`                               | `6291c1cfd243d56115446a1126879670e9d055b48947e6f201d3ec1d55f42ecd` | por dataset                                         |
| `results/metrics/uci_394/metrics.json`                             | `d6b28b745f3b639afe255586e9d241bf357bba0b41163bf72392ebdec6682a34` | por dataset                                         |
| `results/metrics/uci_501/metrics.json`                             | `4266e0ea7094de7fff3be4dbc354b0ef0a965b210e7cab90c8d81affb6f4a449` | por dataset                                         |
| `results/stats/summary.csv`                                        | `267b376ffde06a0007f3f3b2f69ce70be2223fbf9a0e97fbfa4431973d52fb4d` | DM e Cliff por par de métodos, sem tarefas          |
| `results/ablation/summary.csv`                                     | `cbc6ea474e6f33783ebea62fddbe70d470c7953cf62b5cd72a1603abc9527bef` | por dataset e variante; SIVEP 1,0 em todas          |
| `reports/experiments/mostra26/tables/metrics_table.csv`            | `09c2873a412a84da442c7c35be47c0ed616f9dbf9c9f17825bd3ca318cfa5c90` | 9 métodos, AUC-PR 1,0                               |
| `reports/rendered_reports/CDADE-—-Consolidated-Project-Report.pdf` | `daef9f12166234aa1fbed4f018238732ec6389cc0a5e21522248e82c126d1dca` | código e figuras por dataset; sem tabela por tarefa |
| `reports/experiments/mostra26/report.pdf`                          | `ce1b8de0f10f0b059a05e1a360d0978779d72c47465c189e65de770a904498fe` | sem tabela por tarefa                               |

`reports/02-results.qmd` descreve uma execução de dois datasets (SIVEP e Tycho) com Friedman `stat = 3,0`, `p = 0,558`. Os arquivos rastreados de `reports/` são idênticos entre o working tree e `fbfa609`. Não há notebooks `.ipynb` no repositório original; `eze_notebook.py` existe no commit e foi apagado no working tree, sem ocorrência de 0,597.

### Fora do repositório original

Busca de texto por `0[.,]597` em `/home/vinvs/projects` (excluindo ambientes virtuais): apenas CSVs brutos de qualidade do ar (UCI Beijing), um notebook e um `uv.lock` de projetos não relacionados, e o próprio registro de decisões. `ppe/mostra-26` é um projeto separado de qualidade do ar, sem menção a CDADE ou AUC-PR em código e relatórios.

### Conclusão

Os números apresentados do CDADE v1 (18 tarefas, média 0,597) **ficam sem proveniência verificável** nos artefatos disponíveis. Além disso, nenhum commit registrado no MLflow produziu métricas por região; a maior granularidade observada é o dataset, e 18 não corresponde a nenhuma combinação de datasets ativos (máximo de 4). Conforme a D-G0a, isso muda apenas a descrição do E0 e pode exigir errata no material do mestrado; não altera a autorização de B1\* nem o cronograma. Uma fonte externa (apresentação, planilha ou máquina diferente) só entra por nova decisão datada.

## Hardware (D-COST, registrado em 27/09/2026)

| Item               | Valor                                                             |
| ------------------ | ----------------------------------------------------------------- |
| CPU                | AMD Ryzen 9 9900X (12 núcleos no host)                            |
| Visível no WSL     | 8 CPUs lógicas: 4 núcleos × 2 threads, 1 socket                   |
| RAM visível no WSL | 25 GiB                                                            |
| GPU                | NVIDIA GeForce RTX 4080, 16 GiB (não usada pelo pipeline)         |
| Sistema            | WSL 2.5.9.0, kernel 6.6.87.2-microsoft-standard-WSL2, WSLg 1.0.66 |
| Disco              | 1007 GB, 686 GB livres em `/`                                     |

As projeções da D-COST (48 h e 96 h) usam este perfil, com 8 CPUs lógicas, que é o limite atual do WSL e não o do host. Uma mudança em `.wslconfig` antes do piloto deve ser registrada aqui.

## D-COST e execução condicionada — 20/10/2026

**Estado:** custo decidido antes de abrir efeitos; D-REACH aferido; bancada
**não executada** porque o runner não representa o degrau (a). A decisão e
os gates estão no [registro do protocolo](protocol-decisions.md#d-costd-reach--execução-condicionada-de-20102026).
Não houve inspeção de valores de lead time, ganhos, AP ou comparações E1,
estatística, tuning ou mudança de seed. Todos os cálculos usaram o SHA limpo
`bcfa9eefb3a0c3b3ec308ecec3bb9c12daa7b034`, antes desta atualização documental.

### Hardware e método

`lscpu` confirmou AMD Ryzen 9 9900X, 8 CPUs lógicas, 4 núcleos × 2 threads
e 1 socket. `/proc/version` confirmou
`6.6.87.2-microsoft-standard-WSL2`. RAM visível: 27.315.625.984 bytes
(25,4397 GiB), compatível com os 25 GiB arredondados no registro anterior;
swap de 8 GiB, sem uso. Disco disponível: 732.617.760.768 bytes.
Não foi detectada divergência de CPU, topologia, RAM ou kernel. A versão do
pacote WSL 2.5.9.0/WSLg e a GPU permanecem como registro histórico, sem nova
sondagem; GPU não foi usada. Não houve mudança do orçamento de 48 h/96 h.

GNU `/usr/bin/time -v` mediu parede e pico RSS de cada processo completo;
wrappers temporários com `perf_counter` mediram simulação, scoring e
componentes, sem examinar seus scores. O `uv run` inicial falhou antes da
execução porque o cache global era somente leitura. O log foi preservado;
usou-se depois `UV_CACHE_DIR` em `/tmp`, `uv run --offline --no-sync` e o
ambiente existente, sem instalação. Python e versões das dependências,
comandos, scripts, configs temporários e logs estão no
[envelope local](../results/task6-execution-20261020/manifest.json).

| Medição | Parede externa | Pico RSS (KiB) | Trabalho |
| --- | ---: | ---: | --- |
| Smoke, três detectores | 33,46 s | 471.148 | 12 réplicas, 33 braços, 7 ajustes NB2 válidos |
| Probe, seis detectores | 66,13 s | 423.020 | Primeira réplica fixa `white:0:calibration:N:0000`, 33 braços |

O smoke preserva `configs/e1_smoke.toml`, exceto pelo novo `run_id`
`e1-cost-smoke-20261020`. O probe usa a mesma réplica e grafo sintético,
com o pool de seis detectores e `selection_k=5` da bancada. Não houve busca
de réplica válida. As cinco falhas NB2 do smoke não entram como economia na
projeção. O probe ajustou 337 pools distintos; o máximo sem reuso de features
é 33 × 13 = 429 por réplica. Mediu 0,023871 s de simulação,
0,020661 s de previsão/MinT compartilhados e 0,191711 s por pool/seleção,
equivalente a 2,492237 s por braço-réplica com 13 regiões sem reuso.
Esta última medida é uma normalização, não um cronômetro individual por braço.

### Projeção congelada antes de efeitos

A [decisão de custo](../results/task6-execution-20261020/cost-decision.json)
foi gravada em **2026-10-20T18:32:09.299278Z**. Para cada cenário:
tempo = réplicas × (simulação + previsão/MinT) + pools × custo por pool.
São nove células e 200 nulos de calibração/célula em todos os cenários.

| Cenário | Réplicas incluindo calibração | Braços-réplicas | Pools máximos | Horas, reuso como smoke → sem reuso |
| --- | ---: | ---: | ---: | ---: |
| Completo: 500 T + 500 N | 10.800 | 356.400 | 4.633.200 | 193,95 → 246,87 |
| (a): placebos em 100 T | 10.800 | 248.400 | 3.229.200 | 135,22 → 172,10 |
| (a)+(b): 200 T + 200 N | 5.400 | 151.200 | 1.965.600 | 82,29 → 104,74 |

Aplicados (a), depois (b); T `0000`–`0099` por célula ficam fixadas para os
30 placebos e a comparação pareada de B2. N e calibração permanecem completos
no tamanho do degrau escolhido. Não há opcionais configurados para o degrau
(c); L0 permanece obrigatório. O intervalo é entre hipóteses de reuso,
**não** IC nem garantia de duração. O cenário sem reuso ainda supera 96 h.
O probe único usa white/ciclo sintético, não Queen calibrada/env/dem; custos
de materialização, escrita, calibração endêmica e D-REACH ficam fora da
projeção. Não se divide o tempo por oito: o runner é sequencial, e os pilotos
usaram aproximadamente uma CPU.

Somente os arrays densos de scores do desenho completo ocupariam
2.668.723.200 bytes; isto não estima o pico da bancada. Arrays compartilhados,
dicionários, tabelas de outcomes/comparações e runtime somam memória. O pico
do smoke não certifica viabilidade de RAM para a execução completa.

### Calibração, alcance e auditoria

As calibrações fixas white/env/dem concluíram com `ready`, seed 42,
128 réplicas/candidato, meses 0–59, bracket `[0,1/7]` e tolerância
`max(1,0.1*mediana)`, satisfeita nas 13 regiões por ruído. Tempos:
4,15/4,16/4,61 s; picos RSS: 181.212/181.468/181.060 KiB. Os CSVs de
`/home/vinvs/projects/hybrid-theory/data/raw` foram somente lidos; hashes
antes/depois iguais e idênticos à cópia de `data/raw/sivep` do checkout
principal. Derivados em `data/processed/endemic-{white,env,dem}` e manifests
em `results/endemic-calibration-{white,env,dem}-task6-20261020`.

O [passe D-REACH](../results/e1-reach-20261020/manifest.json) executou
1.800 T, sem braços, em 59,81 s e pico RSS 349.236 KiB. Usou Queen, hazards
calibrados, endereços canônicos de seed do runner e índices `0000`–`0199`
por célula; não alterou parâmetros para atingir alcance.

| Ruído | ε = 0 | ε = 0,05 | ε = 0,20 |
| --- | ---: | ---: | ---: |
| white | 0/200 (0%) | 163/200 (81,5%) | 165/200 (82,5%) |
| env | 0/200 (0%) | 112/200 (56%) | 132/200 (66%) |
| dem | 0/200 (0%) | 148/200 (74%) | 153/200 (76,5%) |

Cada valor conta T com onset em ao menos um vizinho da semente. O mínimo
de 50% em ε=0,20 passa separadamente nos três ruídos. Em todas as 600 T de
ε=0, nenhum onset fora da semente e contagens não-semente iguais às gêmeas.
Queen e seus 30 placebos novos são conexos e distintos; graus canônicos
preservados: `[3,3,3,5,4,4,3,4,5,1,2,7,6]`.

A [auditoria do smoke](../results/task6-execution-20261020/smoke-audit.json),
posterior à decisão de custo, verificou 3.432 linhas de métricas, mesmos oito
IDs de avaliação nos 33 braços, denominadores de onset iguais e 72 meses
elegíveis. Seeds de calibração/avaliação são disjuntas. Falhas de ajuste não
foram descartadas nem contadas como censura; censura por braço está no JSON.
FAR passa em **28/858** pares ruído/ε/braço/região; só 429 pares têm calibração
e avaliação completas, com 144 meses em cada partição. FAR por braço,
denominadores incompletos e as cinco falhas D5 foram preservados.
Os 30 placebos do ciclo também preservam graus/conectividade/distinção.
Nenhum valor de lead ou ganho foi lido; `comparisons.parquet` foi apenas
verificado por hash. Esta auditoria técnica não substitui a da bancada.

### Identidade e preservação

Os diretórios anteriores não foram sobrescritos. Novos runs e o envelope
ficam preservados, com inventário SHA-256, configs, seeds, versões e gates
explícitos. São artefatos locais gitignored; somente documentação é commitada.
Não existe `metrics.parquet` de bancada nesta Task 6.

| Artefato | SHA-256 |
| --- | --- |
| Envelope `task6-execution-20261020/manifest.json` | `a4032b87322911dfef7504dbc640f7d3f29d97d38db06dc8bd69b527a5b20b8f` |
| Decisão `cost-decision.json` | `146066d5d7de6c7a54c42980ac68d9a24b9becf9e7a910b351408f9abac4a166` |
| Smoke `e1-cost-smoke-20261020/manifest.json` | `77694f04a2d682bea049d2476aa252d297f11dba7eb6012fe9bd3df1bc3fa93d` |
| Smoke `metrics.parquet` | `387b9a9da2b5fed862c9491d844f47590efa6015cda9fffe5c9eddf1f6e7b0ba` |
| Reach `e1-reach-20261020/manifest.json` | `b762abc6ea3e2466c177e7deedb65376f548bba179929b8a37a538165ddd8828` |
