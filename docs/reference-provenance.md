# Proveniência da referência CDADE e hardware

Registro da busca D-G0a ([registro de decisões](protocol-decisions.md)) e do hardware exigido pela D-COST. Tudo foi feito **somente em leitura** sobre `/home/vinvs/projects/hybrid-theory`: git com `GIT_OPTIONAL_LOCKS=0`, bancos SQLite abertos com `mode=ro&immutable=1`, PDFs lidos com `mutool draw -F txt` para um diretório temporário. `git status --short` do original é idêntico antes e depois da busca; HEAD continua em `fbfa609bba6cb0b0f2a9e8d73be18022aec319b7`.

## D-G0a — resultados apresentados do CDADE v1 (27/09/2026)

**Alvo:** tabela de AUC-PR por tarefa em 18 tarefas, média 0,597.

**Resultado: nenhuma proveniência encontrada.** Nenhum artefato inspecionado contém a tabela de 18 tarefas, o valor 0,597 ou qualquer AUC-PR agregado por região/tarefa.

### Rastreamento MLflow

| Armazenamento | SHA-256 | Execuções | Achado |
|---|---|---:|---|
| `results/mlruns.db` (experimentos `cdade_evaluation`, `cdade_baselines`, `cdade_ablation`) | `59447090ace909dc476abf9ed5c96d2cf091b197f42ba471471199c586cb3443` | 200 | Métricas por **dataset** (`sivep`, `tycho`, `uci_501`, `uci_394`), nunca por região. As 296 entradas `*auc_pr` ficam em [0,992; 1,000]. Toda avaliação SIVEP tem `n_test = 26` e AUC-PR = 1,0. |
| `mlflow.db` (experimento `Default`) | `788ce2004323608f01a1dfe3ac97c2cba1b602780fb1df4b0a6875279e288a86` | 91 | Execuções com `cdade_auc_pr = 0,371` e `n_test = 10`, sem tag de commit nas avaliações: compatível com a suíte de testes, não com dados SIVEP. |
| `mlruns/0/224a965cf525460093c112388ec1f37a/artifacts/metrics.json` | `4fc4a8a55702ce25072cc8d1d5f1a726d8b7594972b0a454ea71730aff5387b4` | 1 | Mesmo padrão (`cdade` 0,371), sem tarefas. |

Tags `mlflow.source.git.commit` presentes em `results/mlruns.db`: `46f6d06`, `9a1888a`, `9d14421`, `9f21849`, `a7fc1bc`, `aa160fd`, `c8b4e92`, `d79505a`, `ea76919`, `ec7556e`, `edd87e8`. Nenhuma execução com qualquer desses commits registra métricas por tarefa. Nenhum valor de métrica em nenhum dos dois bancos cai em [0,5965; 0,5975].

### Git

- Branches: `main` (`d1df8d6`, ancestral de `fbfa609`), `feat/dataset-autonomy` e `feat/experiment-reports` (ambas em `fbfa609`), `origin/main` (`d1df8d6`). Sem tags e sem stashes.
- `git grep -E "0[.,]597"` sobre os 100 commits de `git rev-list --all`: nenhuma ocorrência.

### Arquivos do working tree

| Caminho | SHA-256 | Achado |
|---|---|---|
| `results/metrics.json` | `e7b9a1417e0dfda3fc428440cb78e5165129bd684de8829ae2b46802e98b97a3` | por dataset |
| `results/metrics/sivep/metrics.json` | `c4a1da269a6bd3f2553b8eddfa8a13ecea485d3db698a873cac629e1c181b66e` | 9 métodos, AUC-PR 1,0 (exceto `b2` 0,99999…) |
| `results/metrics/tycho/metrics.json` | `6291c1cfd243d56115446a1126879670e9d055b48947e6f201d3ec1d55f42ecd` | por dataset |
| `results/metrics/uci_394/metrics.json` | `d6b28b745f3b639afe255586e9d241bf357bba0b41163bf72392ebdec6682a34` | por dataset |
| `results/metrics/uci_501/metrics.json` | `4266e0ea7094de7fff3be4dbc354b0ef0a965b210e7cab90c8d81affb6f4a449` | por dataset |
| `results/stats/summary.csv` | `267b376ffde06a0007f3f3b2f69ce70be2223fbf9a0e97fbfa4431973d52fb4d` | DM e Cliff por par de métodos, sem tarefas |
| `results/ablation/summary.csv` | `cbc6ea474e6f33783ebea62fddbe70d470c7953cf62b5cd72a1603abc9527bef` | por dataset e variante; SIVEP 1,0 em todas |
| `reports/experiments/mostra26/tables/metrics_table.csv` | `09c2873a412a84da442c7c35be47c0ed616f9dbf9c9f17825bd3ca318cfa5c90` | 9 métodos, AUC-PR 1,0 |
| `reports/rendered_reports/CDADE-—-Consolidated-Project-Report.pdf` | `daef9f12166234aa1fbed4f018238732ec6389cc0a5e21522248e82c126d1dca` | código e figuras por dataset; sem tabela por tarefa |
| `reports/experiments/mostra26/report.pdf` | `ce1b8de0f10f0b059a05e1a360d0978779d72c47465c189e65de770a904498fe` | sem tabela por tarefa |

`reports/02-results.qmd` descreve uma execução de dois datasets (SIVEP e Tycho) com Friedman `stat = 3,0`, `p = 0,558`. Os arquivos rastreados de `reports/` são idênticos entre o working tree e `fbfa609`. Não há notebooks `.ipynb` no repositório original; `eze_notebook.py` existe no commit e foi apagado no working tree, sem ocorrência de 0,597.

### Fora do repositório original

Busca de texto por `0[.,]597` em `/home/vinvs/projects` (excluindo ambientes virtuais): apenas CSVs brutos de qualidade do ar (UCI Beijing), um notebook e um `uv.lock` de projetos não relacionados, e o próprio registro de decisões. `ppe/mostra-26` é um projeto separado de qualidade do ar, sem menção a CDADE ou AUC-PR em código e relatórios.

### Conclusão

Os números apresentados do CDADE v1 (18 tarefas, média 0,597) **ficam sem proveniência verificável** nos artefatos disponíveis. Além disso, nenhum commit registrado no MLflow produziu métricas por região; a maior granularidade observada é o dataset, e 18 não corresponde a nenhuma combinação de datasets ativos (máximo de 4). Conforme a D-G0a, isso muda apenas a descrição do E0 e pode exigir errata no material do mestrado; não altera a autorização de B1\* nem o cronograma. Uma fonte externa (apresentação, planilha ou máquina diferente) só entra por nova decisão datada.

## Hardware (D-COST, registrado em 27/09/2026)

| Item | Valor |
|---|---|
| CPU | AMD Ryzen 9 9900X (12 núcleos no host) |
| Visível no WSL | 8 CPUs lógicas: 4 núcleos × 2 threads, 1 socket |
| RAM visível no WSL | 25 GiB |
| GPU | NVIDIA GeForce RTX 4080, 16 GiB (não usada pelo pipeline) |
| Sistema | WSL 2.5.9.0, kernel 6.6.87.2-microsoft-standard-WSL2, WSLg 1.0.66 |
| Disco | 1007 GB, 686 GB livres em `/` |

As projeções da D-COST (48 h e 96 h) usam este perfil, com 8 CPUs lógicas, que é o limite atual do WSL e não o do host. Uma mudança em `.wslconfig` antes do piloto deve ser registrada aqui.
