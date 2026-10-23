# Desenvolvimento e reprodução

## Relatório preliminar — 23/10/2026

[Status científico HEADD L0 e motivos da conclusão inconclusiva](evidence/2026-10-23-preliminary/README.md).

## Evidência P5/G4 — 22/10/2026

O [pacote para revisão científica](evidence/2026-10-22-p5-g4/README.md) registra
bytes oficiais Gao verificados, seis pares de medianas arquivadas reproduzidos,
384 realizações mensais completas e replay exato, no perfil/seeds fixos.
76 testes determinísticos e a suíte padrão (466 testes, 1 excluído) passaram;
clipping e denominadores estão publicados. G4 permanece pendente de revisão
científica explícita, `interpretation_allowed=false`; E0*/FAR seguem reprovados
e camadas obrigatórias incompletas. Os diretórios locais de cache/resultados
não são versionados.

O repositório dispõe dos componentes da baseline B1*, da preparação da
camada 0, do grafo regional P4 e das features P6, implementados e validados
tecnicamente. Simulador P5, runner reduzido D-COST e exportador descritivo
foram entregues no PR #3; camada 1 e seu runner não estão implementados.
Bancada de 82–105 h não executada; E0*/FAR reprovados, G4 pendente.
D-RATIFY-2026-10-21 ratifica regras/perfil, sem alterar gates ou manifests.
Conclusão positiva ou negativa exige camadas 0/1/2 completas e todos os gates;
falha/incompletude implica inconclusivo. Ver [plano global](superpowers/plans/headd-l0-global.md).
As decisões científicas vigentes estão em [protocol-decisions.md](protocol-decisions.md).
Os resumos portáteis e hashes dos artefatos preservados pelo PR #2 estão em
[`docs/evidence/pr-2/`](evidence/pr-2/README.md).
O [diagnóstico somente leitura de 21/10](evidence/2026-10-21-e0-diagnostics/README.md)
reproduz os 13 pares regionais, a perda média de AP e as três falhas FAR,
com hashes e auditoria causal histórica/atual. Não estabelece defeito independente
da baseline; E0*/FAR seguem reprovados, G4 pendente, bancada não executada
e interpretação bloqueada.

## Ambiente e comandos

Python ≥ 3.12, dependências geridas por uv e fixadas em `uv.lock`. A validação
usa pytest e Ruff; nenhuma instalação do CDADE legado é necessária para rodar
os testes com fixtures versionadas.

Execute da raiz do projeto, com `hybrid-theory` ao lado ou com `raw_dir`
ajustado nos TOMLs:

```bash
cd ~/projects/net-sci-epi
uv sync --locked
uv run python -m headd_l0.data configs/data.toml
uv run pytest -o addopts='' -q
uv run ruff check .
uv run ruff format --check .
uv build
```

A preparação SIVEP escreve `data/processed/sivep/` e
`results/data/manifest.json`; raw é somente leitura. O build escreve sdist e
wheel em `dist/`. Esses diretórios gerados são ignorados pelo Git.
`-o addopts=''` inclui os testes que a seleção rápida padrão exclui.

## Configuração

TOML é lido com `tomllib` para dataclasses congeladas, sem biblioteca adicional.
`configs/e0_star.toml` exige `run_id`, `root_seed`, `raw_dir` e `output_dir`.

| Campo | Contrato |
| --- | --- |
| `run_id` | Nome simples de diretório, não vazio; uma execução existente não é sobrescrita |
| `root_seed` | Inteiro não negativo; strings, floats e booleanos são rejeitados |
| `raw_dir`, `output_dir` | Caminhos não vazios, normalizados para `Path`; relativos ao diretório de execução |
| `baseline_id`, `reference_sha` | Identidade do protocolo aprovado; valores divergentes são rejeitados |

O runner E0 expande `~`. As configurações distribuídas usam
`../hybrid-theory/data/raw`; altere o TOML se os dados estiverem em outro local.
`E0Config.__post_init__` valida também a construção direta em Python.
`load_config` rejeita campos obrigatórios ausentes e nomes desconhecidos.

Os manifests registram configuração, seed, timestamp e proveniência Git do
código executado, independentemente do diretório corrente do chamador.
Imports de produção ficam no topo; Ruff aplica `PLC0415`, com exceção restrita
a testes que usam imports locais para fixtures e referências opcionais.

## Preparação da camada 0 e limite científico

```bash
uv run python -m headd_l0.run configs/e0_star.toml
```

Esse comando prepara a injeção e os diagnósticos; ainda não executa a comparação
B1*/z-score com calibração FAR. Os artefatos ficam em
`results/<run_id>/{injection.npz,events.parquet,tasks.parquet,pa_diagnostics.json,manifest.json}`.

Na seed 42, as 13 regiões têm ambas as classes nos meses 60–131; PA tem 72
positivos e 0 negativos pela união. D-E0*-R1 (28/09) aplica a condição de
classes somente às regiões. O pré-gate revisado retorna **exit 2**,
`E0_star.status = "pending"`, motivos vazios e `interpretation_allowed = false`.
Componentes e baseline trivial continuam `not_evaluated`; E0 permanece
**inconclusivo**. As 110 células negativas e 2 onsets ajustados da injeção
original permanecem, sem clipping nem novo sorteio.

`tasks.parquet` retém as 14 tarefas com prevalência, denominador 72, janela e
papel no gate. `pa_diagnostics.json` registra cobertura da união e coerência de
contagens/rótulos, sem reivindicar discriminação de PA. O manifest fixa revisão,
commit da decisão e versão da regra; resultados históricos nunca são sobrescritos.
Para repetir, use uma cópia do TOML com novo `run_id` e mantenha seed e protocolo.
O pré-gate histórico falhou em `single_class:PA`; a revisão técnica não aprova
E0* nem libera interpretação de E1′.

A execução real revisada em **2026-09-29T09:08:03Z** usou o commit limpo
`fb854f2d56c409f79cc0bd97df1d420d78afad7b` e uma cópia temporária do
TOML com `run_id = "second-execution-regional-preflight"` e
`raw_dir = "/home/vinvs/projects/hybrid-theory/data/raw"`; seed 42, baseline,
referência e `output_dir = "results"` permaneceram. Comando:
`uv run --locked python -m headd_l0.run /tmp/second-execution-regional-preflight.toml`.
Exit 2, E0 inconclusivo, E0* pendente, motivos vazios, interpretação bloqueada.
As regiões tiveram 14–29 positivos e 43–58 negativos; PA 72/0. O manifest
registra 110 células negativas, 2 onsets ajustados, revisão D-E0*-R1 e commit
da decisão `50f8b3f29bacc4747329addf80cee6719fe3c7fc`. Não houve scoring.

## Grafo regional P4

```bash
uv run python -m headd_l0.graph configs/l0_graph.toml
```

O TOML fixa `year=2013`, `simplified=false`, micro regiões de PA, seed 42 e
30 placebos antes da aquisição. A fonte é DataSUS via geobr 2.1.1. A resolução
original mantém o processamento upstream do leitor, que une municípios e
remove anéis internos. Não há reparo geométrico local nem troca de ano,
resolução ou Queen para obter conectividade. Código/nome original e nome
canônico ficam no manifest; exige-se correspondência exata com a tabela de
13 pares código–nome DataSUS/PA de 2013 (`datasus-pa-2013-v1`). Códigos
desconhecidos ou associados ao nome de outra região bloqueiam a aquisição.

A execução real única em **2026-09-29T16:35:04Z**, commit limpo
`7208531475b658ab34ff33d823455a4a12121509`, retornou 13 regiões válidas,
EPSG:4674, sem geometrias vazias. A Queen é conexa, com 25 arestas e graus na
ordem canônica `[3,3,3,5,4,4,3,4,5,1,2,7,6]`. W tem soma 1 por linha. Os
30 placebos são distintos, diferentes de A, conexos e preservam os graus de
cada região. Foram 30 candidatos e 22.616 tentativas para 250 trocas aceitas
por candidato. Distâncias por diferença simétrica de arestas: 16–34 para A
e 18–38 entre draws. Isso não demonstra amostragem uniforme nem aprova
G3/E1; o manifest mantém `interpretation_allowed=false`.

Esse run antecede o validador exato de código↔nome de `61dd0cb`: os 13 pares
registrados no manifest coincidem com o mapeamento canônico em conferência
_post hoc_, mas `name_mapping_version` não foi gravado. A evidência portátil
expõe essa limitação; uma nova aquisição deve passar também pelo validador e
pelo SHA-256 obrigatório da fonte antes de receber status `ready`.

Artefatos em `data/processed/graph/`: fonte e geometrias canônicas, mapas,
`adjacency.npy`, `W.npy`, `S.npy`, `placebos.npy`, centralidades e GEXFs
separados de S/A/30 placebos. O manifest também fica em
`results/l0-graph-2013-original/manifest.json`, com 43 hashes de artefatos,
configuração, seed, versão/hash do código, Git, timestamp e custo. A aquisição
mediu 11,986 s de parede, 4,474 s CPU usuário, 1,110 s CPU sistema e pico RSS
1.176.524 KiB; os artefatos antes dos manifests ocupam 121.715.743 bytes.

O catálogo aponta para o
[GeoParquet 2013](https://github.com/ipea/geobr_prep_data/releases/download/v2.0.0/healthregions_2013.parquet),
SHA256 `42de74c7506a5ce52b46ba4d5abdde6b321eebf649b09c08f641fc2e56d8918e`.
O cache temporário do geobr foi preservado em processed junto ao catálogo.
O leitor pode usar seu espelho IPEA para o mesmo arquivo; o endpoint efetivo
não é exposto pela biblioteca e não é reivindicado no manifest.

O comando recusa diretórios de execução/cache existentes. Para nova aquisição,
use uma cópia do TOML com novos `run_id` e `processed_dir`; não sobrescreva a
evidência. `adjacency()` lê o cache canônico padrão, verifica origem, nomes,
hash e invariantes antes de devolver A. Falhas de aquisição, cardinalidade,
geometria ou conectividade produzem diagnósticos e exit 2, sem cache aprovado.

## Preparação de fonte P5

A [nota científica](gao-source-preparation.md) registra fonte, hashes,
equações, distribuições predecessoras, mediana das tabelas congeladas e
comando de extração reproduzível sem executar o simulador. As tabelas
oficiais rotulam 6000 T e 6000 N por ruído; para branco, CV mediano T
`0.7695323012078741` é menor que N `0.8337873367675575`. A
[D-RATIFY-2026-10-21](protocol-decisions.md#d-ratify-2026-10-21--ratificação-científica-prospectiva)
ratifica equações Gao 1–3 e perfil sintético fixo `P5-IMPL-2026-10-19-v1`.
Manifesto e fixture `gao_single.npz` existem. Caracterização da fonte: AR1(T)>AR1(N)
nos três ruídos; CV(T)<CV(N) em white e > em env/dem, seis pares/hashes a
`1e-12`. Bytes oficiais ausentes: `source_archive_verification=pending`.
A fixture verifica álgebra, não separação. Diagnósticos mensais fixos: 64 T/64 N
por ruído, AR1/CV, janelas válidas, clipping, conservação, θ=0/1 e onsets;
sem impor sinais CV da fonte ou ajustar perfil/seeds. G4 exige ainda checks
de fonte/equações, testes determinísticos e revisão científica; permanece pendente.

## Próximas etapas

1. Diagnosticar E0*/FAR em leitura: nova execução só após defeito independente
   reproduzido por teste falhando e corrigido em plano separado. Manter B1*,
   com versão de código/perfil, seed e run ID distintos; preservar 30/09.
2. Verificar bytes oficiais, executar diagnósticos fixos e revisar G4;
   ratificação das regras não é resultado de gate.
3. Projetar camada 1 separadamente: R0 ~ Uniform[1.2,1.8], k∈{1,3,6},
   100 T/célula ruído/ε/k (27 células, 2.700 surtos antes de scoring),
   200 N calibração + 200 N avaliação por região disjuntos. Fixar precisão,
   custo, seeds e reuso entre células antes de scoring; não há garantia de poder.
4. Só após pré-requisitos, completar camadas 0/1/2. Camada 2 mantém D-COST:
   200 T/200 N + 200 N de calibração/célula; rank em T0000–T0099 (100 T).
   Em ε=0 exigir IC percentil 95% pareado (10.000 draws) estritamente em
   (−1,+1) mês por ruído e por k na camada 1; 29/30 passa rank, 28/30 falha.
   Calibração/avaliação disjuntas e FAR comparável são obrigatórias.
5. `configs/e1_bench.toml` existe; sua existência não autoriza executar a
   bancada. O exportador descritivo usa
   `uv run python -m headd_l0.e1_report results/task6-execution-20261020`
   (exit 2 esperado). Não verifica ainda
   o critério conjunto das três camadas; nenhuma inferência é autorizada.

## Documentação de referência

- [README](../README.md): problema, desenho experimental e descrição do projeto.
- [AGENTS](../AGENTS.md): regras de desenvolvimento e contratos dos componentes.
- [Protocolo](protocol-decisions.md): decisões aprovadas e questões científicas pendentes.
- [Preparação Gao](gao-source-preparation.md): fontes verificadas e escolhas pendentes do simulador.
- [Migração](../MIGRATION.md): métodos portados, diferenças e testes de paridade.
- [Proveniência](reference-provenance.md): busca D-G0a, evidências e hardware D-COST.
- [Arquitetura](superpowers/specs/headd-l0-architecture.md) e
  [plano global](superpowers/plans/headd-l0-global.md): especificação e etapas de implementação.

Os importadores transitórios foram aposentados. Fixtures e hashes permanecem
em `tests/reference/`; o procedimento para recuperar o exportador histórico
está no registro de migração. O histórico de commits substitui inventários
intermediários de tarefas, versões de ferramentas e contagens de testes.

## Scoring E0* (Task 6, 30/09/2026)

```bash
uv run python -m headd_l0.run --score-e0 configs/e0_star_scoring.toml
```

O comando preserva a preparação original, recusa sobrescrita e exige que
D-E0*-R1 seja ancestral do código. Ajusta NB2/MinT/pool somente no treino,
usa 200 nulos de calibração e 200 de avaliação com streams disjuntos e
registra AP/prevalência das regiões; PA fica descritivo. O manifesto registra
os defaults efetivos, seeds, convergência, evidência executada dos componentes,
FAR e bootstrap regional de 10.000 amostras. `components.log` contém a suíte
executada para o SHA e hash do código. Os artefatos `.npz` preservam os nulos
e scores; `far.parquet` separa FAR calibrada da observada.

Falha de ajuste D5 impede MinT e AP e deixa manifesto explícito. Pela
D-RATIFY-2026-10-21, NB2 inválido/não convergente falha fechado: região/gate
indisponível, sem fallback em blocos no protocolo de 23/10. A implementação
dessa regra deve ser verificada em plano próprio; esta emenda não muda runtime. Exit 2 e
`interpretation_allowed=false` continuam esperados, qualquer que seja o
resultado E0*/FAR. Para worktrees aninhadas, use cópia temporária do TOML com
`raw_dir` absoluto; preserve a configuração portátil versionada.


### Resultado real E0* (30/09/2026)

`results/e0-star-scoring-20260930` foi produzido pelo commit limpo
`017bd1a0d6cd3ecf1e8d8efe55a4826c234b3132`, seed 42, com 200 nulos de
calibração e 200 de avaliação. Os 14 ajustes NB2 convergiram; a suíte interna
executada no mesmo SHA passou (122 testes). O caminho convergente está
`implementado` e `validado tecnicamente`; isso não aprova os gates.

| Gate/condição | Resultado preservado |
| --- | --- |
| E0 | `inconclusive` |
| E0* | `failed`: somente `trivial_baseline`; componentes e 13 tarefas válidos |
| Limite inferior IC95% ΔAP(B1* − zscore) | `-0.20186060618499926` |
| FAR | `failed`: ARAGUAIA/B1*, XINGU/B1*, RIO CAETES/zscore |
| PA | Descritivo, prevalência 1, AP indefinida, fora do bootstrap regional |
| Interpretação | `interpretation_allowed=false` |
| Fallback D-GT3 | `pending_specification_not_used`; Task 0/Task 6 integral permanece parcial |

Não houve ajuste de pool, parâmetros, seed ou gates para resgatar o resultado.
A correção posterior de proveniência passa a registrar `FeatureBatch.names`
(`residual`, `residual_lag1`, `residual_change`) em `settings.feature_names`
nas novas execuções; o run de `017bd1a` permanece intacto e não foi repetido.
Sua evidência usa SHA limpo e digest de módulos/testes Python, pyproject e
uv.lock; o digest não cobre fixtures/arquivos auxiliares. Planos anteriores e
pré-gates acima permanecem como histórico, não como estado do scoring atual.
