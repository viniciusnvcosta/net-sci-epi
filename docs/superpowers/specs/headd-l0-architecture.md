# HEADD-Series L0 — arquitetura e decisões de implementação

Data original: 26/09/2026. Atualização documental: 30/09/2026.
E0 inconclusivo; B1\* autorizado. O pré-gate histórico falhou por
`single_class:PA`. D-E0*-R1 (28/09) revisou a condição 2 para ambas as
classes nas 13 regiões, com PA descritivo. Scoring NB2 convergente executado
no commit limpo `017bd1a` (30/09): E0* falhou em trivial_baseline, limite inferior
−0.20186060618499926; FAR falhou em ARAGUAIA/B1*, XINGU/B1* e
RIO CAETES/zscore. `interpretation_allowed=false`. Task 0 tem caminho
convergente implementado/validado; fallback D-GT3 pendente, não usado.
Detalhes: [execução real](../../development.md#resultado-real-e0-30092026).

## Vocabulário de status

Usar os mesmos quatro rótulos nos planos e na arquitetura: `implementado`
(código/artefato existe), `validado tecnicamente` (checks identificados passaram),
`gate aprovado` (todas as condições daquele gate satisfeitas) e
`interpretação autorizada` (todos os gates/decisões aplicáveis satisfeitos).
Identificar o componente/gate; nenhum rótulo implica automaticamente o seguinte.

## 1. Objetivo, fontes e limites

Construir a bancada E1′ do README §5, com baseline B1\* corrigido sob D-G0/D-E0\* (E0 inconclusivo), S + A, controle ε = 0, FAR de 1/60 por região-mês e 30 placebos. O resultado pode ser negativo. O prazo é 16/10/2026.

Fontes históricas lidas em 26/09 (hashes não representam a revisão atual): `AGENTS.md`, `README.md` e `pyproject.toml`, incluindo suas alterações ainda não commitadas. SHA-256 dessas versões:

| Arquivo        | SHA-256                                                            |
| -------------- | ------------------------------------------------------------------ |
| AGENTS.md      | `c45507dd2c81bec13acaf13e702c3bf5771747f5c86008e1c01242f11f9a15b3` |
| README.md      | `e4b4af6ef16757e971477e6044255bfeae32eef41b3aaa0142eeb18de8d4104e` |
| pyproject.toml | `c4264a205f49cc4287a723cd47a728b4c363a09dd952e954d935c5ce6f1e3a3b` |

Referência CDADE: `/home/vinvs/projects/hybrid-theory`, commit **`fbfa609bba6cb0b0f2a9e8d73be18022aec319b7`**. As leituras de código usaram `git show HEAD:<path>`, não arquivos modificados do working tree. E0 deve fixar esse SHA completo, nunca resolver `HEAD` novamente durante uma execução. Os resultados locais não possuem, por si só, proveniência suficiente para certificar E0.

Estado atual: Python ≥3.12; `src/headd_l0/`, testes e dependências do baseline já existem. P1–P2 estão implementados; P3 prepara injeção/classes; Task 0 integra e executou scoring NB2 convergente, com fallback ainda pendente. P4 grafo e P6 features estão `implementado` e `validado tecnicamente`; seus gates científicos não estão aprovados. P5 tem [preparação de fonte](../../gao-source-preparation.md) parcial, com manifesto/fixture/perfil pendentes; simulador futuro. Comandos atuais: [development](../../development.md).

Não implementar M, REGIC, GNN, GANF/GDN, hhh4 completo, Tycho, L4/L5 ou SEIRS+ agent-based. B-Gao, B3/Φ e variante SEIRS são extensões condicionais, não dependências da entrega principal.

## 2. Alternativas e escolha

1. **Recomendada: pacote plano, funções numéricas e estado explícito.** Portar apenas componentes chamados e executar tudo em memória; TOML, dataclasses congeladas e dicionários locais. Facilita comparação de braços, testes e rastreabilidade.
2. Copiar o pipeline original completo: aproxima sua execução literal, mas reintroduz ferramentas proibidas e problemas identificados abaixo. Usar o original somente como oráculo isolado de caracterização.
3. Reescrever diretamente pelo artigo/protocolo: produz uma implementação científica nova, mas perde a alegação de paridade com CDADE. Exige decisão explícita caso o HEAD torne E0 inviável.

O plano adota 1, com uma auditoria inicial. Corrigir um erro metodológico não equivale a reproduzir o resultado original. Nenhuma correção recebe o rótulo de porte paritário sem o teste correspondente.

## 3. Divergências verificadas por leitura do HEAD

Esta tabela preserva as observações históricas da leitura inicial. A auditoria posterior, o porte e suas evidências estão em MIGRATION e no registro de decisões; não repetir tarefas resolvidas.

| ID  | Evidência no commit de referência                                                                                                                                        | Consequência e condição de desbloqueio                                                                                                            |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | `cdade/detectors/run_detect.py:run_detect` ajusta e pontua a matriz completa; produz um score por mês, não por região e detector.                                        | Não satisfaz causalidade nem as 14 tarefas. Auditoria deve mostrar os eixos e uma reprodução mínima.                                              |
| D2  | `cdade/reconciliation/min_t.py:MinTReconciler` constrói S quadrada 13×13, usa identidade para W e não estima shrinkage. `summing_matrix.py` constrói corretamente 14×13. | MinT científico e saída literal desse código são contratos diferentes. Exigir decisão registrada antes do porte de MinT.                          |
| D3  | `cdade/detectors/mcd.py:MCDDetector.fit` usa um subconjunto aleatório e shrinkage, sem C-steps; PCA devolve `-PyODPCA.decision_function`.                                | FAST-MCD e orientação de score precisam de testes próprios. Mudanças de algoritmo/sinal podem impedir E0.                                         |
| D4  | `cdade/reconciliation/evt.py:fit` desempacota `genpareto.fit` em dois valores; `cdade/baselines/reconciliation_evt.py:_fit_gpd` usa `(shape, loc, scale)` corretamente.  | Caracterizar exceção; aproveitar a rotina funcional chamada por `run_baselines._run_b5`, sem confundir B5 original com B2 deste projeto.          |
| D5  | `run_reconcile.py` reconcilia scores; AGENTS exige contagens.                                                                                                            | Antes de integrar, decidir qual quantidade em unidades de contagem entra em MinT. Não inventar um previsor nem somar scores como se fossem casos. |
| D6  | `run_select.py` trata colunas como detectores e atribui a t uma janela que pode terminar depois de t.                                                                    | O adaptador causal deve usar janelas encerradas em t−1 para selecionar em t; divergência de resultados deve ser registrada.                       |
| D7  | `run_evaluate.py` reduz máscaras e scores com `max(axis=1)` e calcula métricas por dataset. `results/metrics/sivep/metrics.json` local contém métodos, não 14 tarefas.   | Não há evidência inspecionada que certifique a tabela exigida por E0. Recuperar uma tabela verificável ou declarar E0 bloqueado.                  |
| D8  | `evaluation/stats.py` continua DM/Cliff após Friedman não significativo, contém resultados substitutos e fallback HAC sem pesos Bartlett; bootstrap usa RandomState.     | Portar rotinas válidas separadamente; fluxo científico, HAC e Generator requerem testes e registro de desvio.                                     |
| D9  | `evaluation/metrics.py` usa AP como AUC-PR e um NAB simplificado com mediana dos scores avaliados.                                                                       | AP mantém essa definição. NAB legado é apenas caracterização; E1 usa alarmes do limiar calibrado, sem mediana do teste.                           |

**Gate G0:** produzir `reference_audit.json` com reprodução, fontes, exceções e cobertura das 14 tarefas. Manter E0 bloqueado enquanto D1–D7 impedirem satisfazer simultaneamente referência, causalidade e contratos. Não criar um modo legado no pacote de produção para contornar o gate. Deliberar G0/D1–D7 até 29/09/2026. Se o HEAD não sustentar E0, registrar escolha explícita entre E0 inconclusivo com B1\* corrigido e autorizado, ou bloqueio total da interpretação E1′. Decisão de 27/09: saída (i), E0 inconclusivo com B1\* autorizado e gate E0\* ([registro](../../protocol-decisions.md)). B1\* deve aparecer em todos os artefatos e textos; não transforma discrepância em paridade. D5 também foi resolvida em 27/09: MinT sobre previsões NB2 de contagens. A referência histórica não libera E0\*.

## 4. Mapa de código e responsabilidade

O mapa combina contratos atuais de baseline, grafo/features e scoring E0*
com contratos **futuros** de simulador, runner E1 completo e camada 1. Nomes/arquivos ausentes nessas
trilhas são entregas futuras; o exporter indicado é histórico aposentado.

Manter o layout do AGENTS. `tests/test_<module>.py` espelha cada módulo. Não criar serviços, factories, registry global ou camadas de repositório. Cada módulo mira 150–300 linhas e só se divide ao ultrapassar aproximadamente 400.

| Arquivo                                                | Responsabilidade / tipos próprios                                                                                                                                                                 |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/headd_l0/data.py`                                 | Ordem canônica, `Hierarchy`, `DataBundle`, leitura longa e contagens, proveniência dos CSVs.                                                                                                      |
| `src/headd_l0/reconcile.py`                            | Única implementação de S; bottom-up e MinT; covariância estimada apenas de erros de treino fornecidos pelo chamador.                                                                              |
| `src/headd_l0/detectors.py`                            | `DetectorConfig`, cinco wrappers mínimos PyOD e FAST-MCD próprio; `DETECTORS`.                                                                                                                    |
| `src/headd_l0/threshold.py`                            | `TailFit`, `Calibration`, POT/GPD e FAR; nenhuma dependência de rótulos T.                                                                                                                        |
| `src/headd_l0/select.py`                               | `SelectionConfig`, `SelectionResult`, competências, Q e ADWIN; `SELECTORS`.                                                                                                                       |
| `src/headd_l0/evaluate.py`                             | `DetectionOutcome`, AP, ROC-AUC, F1, NAB simplificado explicitamente nomeado, FAR e censura.                                                                                                      |
| `src/headd_l0/stats.py`                                | Bootstrap por réplica/blocos, placebo rank e sequência secundária; `BootstrapResult`, `SecondaryResult`.                                                                                          |
| `src/headd_l0/graph.py`                                | Geometria → A → W, placebos, centralidades, exportação GEXF; importa S de `reconcile`, sem duplicá-la.                                                                                            |
| `src/headd_l0/features.py`                             | `FeatureBatch`, representação local/S/vizinhos e indicadores causais; eixos explícitos.                                                                                                           |
| `src/headd_l0/simulate.py`                             | `SimConfig`, `SimResult`, `EndemicCalibration`, uma região, extensão acoplada/gêmeas e componente de surto reutilizado pela camada 1; proveniência de casos importados observados.                |
| `src/headd_l0/inject.py`                               | `InjectionConfig`, `InjectionResult`; injeção limitada da camada 0. Futuros `EpidemicInjectionConfig`/`EpidemicInjectionResult` e adaptador da camada 1; amostragem NB2 pertence a `forecast.py`. |
| `src/headd_l0/run.py`                                  | Atuais: `E0Config`, preparação, gate, CLI e wrapper `run_e0_scoring`. Futuros: `ExperimentConfig`, `ArmSpec`, `RunResult` e runner E1.                                                                                                      |
| `src/headd_l0/e0_scoring.py` | Integração NB2/MinT/features locais/pool/seleção, 200+200 nulos, evidência de componentes e artefatos E0*. |
| `scripts/export_cdade_reference.py`                    | Histórico aposentado: exporter recuperável por MIGRATION; não recriar nem exigir na validação atual.                                                                                              |
| `tests/reference/`                                     | Pequenas fixtures determinísticas e seus manifests; nenhum resultado fabricado.                                                                                                                   |
| `configs/*.toml`                                       | Atuais: `data`, `e0_star` (preparação), `e0_star_scoring`, `l0_graph`. Futuros: `sim_single`, `e1_bench`, `e1_real`, `e1_local`; extensões só quando priorizadas.                                 |
| `MIGRATION.md`                                         | Criado na primeira tarefa: componente, caminho/SHA original, caminho novo, teste, tolerância, exclusões e divergências.                                                                           |
| `notebooks/01_l0_network.ipynb`, `02_e1_results.ipynb` | Consomem resultados; não reimplementam métricas nem escolhem parâmetros.                                                                                                                          |

`summing_matrix` pertence a `reconcile.py`: resolve a duplicação entre layout de graph e contrato do reconciliador no AGENTS. Expor/reutilizar a mesma função onde necessário.

## 5. Contratos de dados e orientação

- Ordem: PA, ARAGUAIA, BAIXO AMAZONAS, CARAJAS, LAGO DE TUCURUI, MARAJO I, MARAJO II, METROPOLITANA I, METROPOLITANA II, METROPOLITANA III, RIO CAETES, TAPAJOS, TOCANTINS, XINGU. As matrizes regionais excluem PA.
- `Hierarchy(state: str, leaves: tuple[str, ...])`, congelada; `DataBundle(long: pd.DataFrame, counts: np.ndarray, state_counts: np.ndarray, tests: np.ndarray, months: pd.DatetimeIndex, hierarchy: Hierarchy)`, congelada. Arrays congelados por convenção/read-only para impedir mutação entre braços.
- `long`: `region, month, species, count`; preservar rótulos originais. `counts` e `tests`: `[13,132]`; `state_counts`: `[132]`; inteiros não negativos. `tests` inclui negativos; `counts` soma todos os resultados diferentes de `negative`, exatamente como o original.
- S `[14,13]`, primeira linha de uns; A/W `[13,13]`; contagens coerentes `S @ counts`. Amostras de detectores sempre `[n_samples,n_features]`, scores `[n_samples]`.
- `FeatureBatch(values: np.ndarray, months: np.ndarray, names: tuple[str,...])`: values `[n_nodes,n_months,n_features]`. Scores do pool `[n_nodes,n_months,6]`. Jamais reinterpretar regiões como detectores.
- `SimResult(counts, twin_counts, onset, seed_region, label, params)` congelada: counts/twin `[n_regions,132]`, onset `[n_regions]` inteiro; `-1` significa sem onset. Uma região só no gate de validação; produção tem 13. `params` serializável inclui parâmetros efetivos e hash do estado inicial do Generator; o runner associa esse resultado à entropy/spawn_key do manifesto, sem tentar recuperar uma seed a partir do Generator.
- `InjectionResult` é o contrato atual da camada 0: contagens/máscaras `[14,132]`, PA primeiro, onset `[14]`, seed_region e events (`tuple[InjectionEvent, ...]`); a entrada tem 13 folhas. A camada 1 futura usa `EpidemicInjectionResult(counts, mask, onset, seed_region)`, dataclass congelada separada em `inject.py`: entrada e contagens/máscara `[13,132]`, onset `[13]`; o runner recalcula PA por soma/união. O componente reutilizado de `simulate.py` precisa expor casos importados observados por região/mês para derivar onsets; não inferi-los apenas da diferença entre séries. Perfil completo do simulador deve ser referenciado e hasheado, sem defaults escondidos no adaptador.
- Ausência de espécie numa região-mês observada pode virar zero; ausência do mês inteiro ou de uma região é erro. Não interpolar silenciosamente. A tabela contém rótulos adicionais como `FG`, `F+FG`, `non falciparum`; o mapeamento Φ exige uma tabela documentada, não um teste de substring.

Os CSVs foram encontrados no working tree de `hybrid-theory/data/raw/`, não como arquivos rastreados nesse SHA:

| Arquivo               | Linhas | SHA-256                                                            |
| --------------------- | -----: | ------------------------------------------------------------------ |
| PA.csv                |    132 | `ba437eff83a537addcdda93aca09401d5033804b83a0b767baa55788267041f5` |
| PASIVEPDailyPerHr.csv |  7.592 | `ad61c77c8c187713cd47e72bb5f028eda1203e3f5e4962c5970d41abd9ae7188` |

A leitura inicial e os testes atuais do loader verificam 13 regiões e diferenças `(positivos, testes) = (0,0)` nos 132 meses; ver sequência ativa P1 no plano E0. Como `data/raw/` é imutável e está ausente aqui, usar o diretório original em modo leitura na primeira execução. Materialização inicial no novo repositório exige que o usuário disponibilize/autorize a inclusão dos arquivos; nunca sobrescrever dados existentes.

## 6. Composição dos braços e causalidade

```mermaid
flowchart LR
  CSV[CSV e hierarquia] --> COUNT[Contagens canônicas]
  GEO[Malhas] --> A[A e 30 placebos]
  PROFILE[Perfil científico aprovado] --> SINGLE[Uma região validada]
  SINGLE --> SIM
  COUNT --> CAL[Calibração endêmica no treino]
  CAL --> SIM[SIR validado e gêmeas]
  A --> SIM
  COUNT --> INJ[Camada 1: soma de casos epidêmicos]
  SIM --> INJ
  A --> INJ
  COUNT --> NULL[Nulos reais paramétricos ajustados no treino]
  NULL --> NREP[Representação por braço já ajustada]
  NREP --> NPOOL[Mesmo pool já ajustado]
  NPOOL --> NSEL[Mesma seleção causal]
  NSEL -->|scores N independentes para calibrar| FAR
  SIM --> REP[Representação por braço]
  INJ --> REP
  A --> REP
  REP --> POOL[Mesmo pool de seis detectores]
  POOL --> SEL[Seleção causal]
  SEL -->|scores para aplicar limiar| FAR[EVT e calibração em N independentes]
  FAR --> EVAL[Métricas por região e réplica]
  EVAL --> STAT[Bootstrap e placebos]
  G0[Auditoria de referência] --> E0[E0 inconclusivo]
  G0 --> ROUTE[B1* autorizado, D-G0 saída i]
  ROUTE --> PA[D-E0*-R1 registrada, classes/contraste e P6 antes do scoring]
  PA --> E0S[Gate E0*]
  E0S --> STAT
```

Os nulos começam como contagens e passam pela mesma representação, pool e seleção do respectivo braço antes de gerar scores para o limiar. N de calibração e N de avaliação são independentes; esta última mede FAR observada. Posição de MinT ([D5](../../protocol-decisions.md), 27/09): um previsor NB2 com tendência e dois pares de harmônicos, ajustado por série nos meses 0–59, produz previsões de contagem um passo à frente μ̂ₜ; MinT(Shrink) reconcilia μ̂ₜ com Ŵ estimada dos erros de treino; os detectores consomem resíduos y − μ̂ (B0) ou y − P·μ̂ (B1\*, B2), padronizados pelo desvio-padrão de treino. Scores nunca são reconciliados.

A saída B1\* foi autorizada (D-G0, 27/09): `baseline_id="B1*"` e a decisão constam em todos os braços/artefatos, com E0 inconclusivo; a interpretação do E1′ depende do E0\*.

`ArmSpec(name, residuals, graph_id)` define: B0 `("base",None)`, B1\* `("reconciled",None)`, B2 `("reconciled","observed")`, B2-placebo `("reconciled","placebo_00"..."placebo_29")`. O braço se chama `B1*` em identificadores, textos, tabelas e legendas. B0 usa modelos independentes por região. B1\*/B2/placebos compartilham arquitetura, algoritmos, hiperparâmetros, partições e seeds; parâmetros aprendidos e limiares numéricos podem diferir porque as representações diferem. Não exigir o mesmo valor numérico de threshold.

Fit de detector, escalador, covariância e calibração ocorre só em treino/calibração independente. Seleção em t usa exclusivamente scores até t−1 e pseudo-rótulos, nunca onset/máscara; reset atualiza o estado a partir daquele instante, sem revisar o passado. Features contemporâneas `W·x_t` são permitidas pelo contrato ≤t; adicionar teste de invariância a qualquer sufixo futuro.

Representação local: resíduo padronizado em t, t−1 e diferença temporal; a hierarquia entra pela reconciliação (D5). Reconciliação sempre sobre contagens previstas, nunca proporções. Extensão de vizinhança sobre os mesmos resíduos: `W·e_t`, `W·e_(t−1)`, `e_t−W·e_t`, Moran local por mês suavizado por janela causal de 12 meses. B1\* não recebe essas quatro colunas; B2 e placebo têm nomes/dimensões idênticos. Sem vizinhos para PA: suas colunas relacionais recebem zero em todos os braços com S.

## 7. Decisões experimentais propostas para revisão

**D-E0*-R1 (28/09):** condição 2 exige ambas as classes nas 13 tarefas
regionais; PA mantém soma/união coerente, com prevalência, cobertura e coerência
descritivas, sem AUC-PR como critério. Condições 1/3/4 não mudam. A tabela
pré-scoring de positivos/negativos/prevalência e a discussão de contraste estão
no [registro](../../protocol-decisions.md#d-e0-r1--revisão-regional-da-condição-2).
A decisão antecede scores e o primeiro commit de integração E0*. Task 0 requer
features locais P6 antes do scoring; P1–P3 e a regra regional estão
validados tecnicamente. Ver [alternativas históricas no E0](../plans/headd-l0-e0.md#decisão-pendente-sobre-pa--comparação-regional-selada).
Toda AUC-PR futura acompanha prevalência, janela e denominador; nenhuma seed
substitui a 42 e não se escolhe cutoff de contraste olhando scores.

As decisões D-G0, D-E0\*, D2, D3, D5, D6, D-GT1–D-GT4, D-COST e D-REACH (27/09) constam no [registro de decisões](../../protocol-decisions.md). Continuam pendentes a faixa de R0 e o perfil do simulador (D-GT2/D-GT4), os eventos da camada 3 (D-L3) e a construção/tamanho do fallback D-GT3 de E0*. O caminho NB2 convergente foi executado, com E0*/FAR reprovados. Hardware registrado em 27/09; piloto D-COST ainda pendente.

| Camada      | Ground truth / uso                                                                                                                                                                             | Regra                                                                                                                                                                                                              |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0           | `inject_original_bounded`: tipos, magnitudes e ordem aleatória do original; shifts/drifts de 3–6 meses; onset em 60–131. O `inject_original` literal só caracteriza o defeito, em `tests/`     | E0 inconclusivo; E0\* (sanidade de B1\* contra z-score móvel causal) antes de tudo; não-inferioridade: limite inferior do IC 95% da média de ΔAUC-PR(B2 − B1\*) ≥ −0,02, bootstrap sobre as 13 regiões, PA à parte |
| 1           | Componente epidêmico de `simulate.py`, ν=0, somado ao SIVEP; A gera propagação por C                                                                                                           | Evidência semi-real principal: IC>0 em ε>0, equivalência em ε=0, rank>.95; gates próprios                                                                                                                          |
| 2           | Metapopulação totalmente sintética                                                                                                                                                             | Protocolo científico preservado; dimensionamento sujeito somente à escada pré-registrada D-COST                                                                                                                    |
| Nulos reais | NB2 com tendência e dois pares de harmônicos (`forecast.py`, o mesmo modelo das previsões do MinT), ajustado nos meses 0–59; 200 séries de calibração + 200 de avaliação por região, disjuntas | FAR 1/60, tolerância 1/300; ajuste sem convergência → bootstrap em blocos do treino, marcado; nas demais regiões, blocos só diagnóstico                                                                            |
| 3           | Eventos documentados com fonte verificada no notebook 02                                                                                                                                       | Checagem qualitativa, sem critério formal                                                                                                                                                                          |

O pulso de 3SD/atraso1 mês/amplitude0,5 é removido, sem sensibilidade paralela. Nas camadas 1/2 B2 é um oráculo porque o gerador usa A; a evidência central inclui comparação com placebos e padrão em ε. A soma epidêmica supõe ausência de interação com o fundo endêmico, inclusive depleção de suscetíveis compartilhados.

Na camada 1, tamanho-alvo=k×mediana mensal de treino da semente, k proposto=(1,3,6); introdução uniforme72–118 inclusive, θ igual à bancada. Onset semente=introdução; demais=primeiro mês com casos importados observados≥1, ausência=−1. Tamanho = casos observados em excesso na semente, alvo k × max(mediana, 1), com o realizado sempre reportado; truncamento no mês 131 permitido e contado (D-GT4). Pendências bloqueantes: faixa de R0 e perfil SimConfig. Onsets da camada 2 continuam R0/2SD.

Antes de rodar braços, D-REACH mede fraçãoT com onset em ao menos um vizinho por ε/célula; mínimo ≥ 50% em ε = 0,20, por tipo de ruído (D-REACH). Abaixo disso, reportar sem poder, não resultado negativo; não ajustar o gerador olhando avaliação.

Os valores fixados por README/AGENTS são obrigatórios, salvo revisão explícita registrada como D-G0/D-COST. Os seguintes complementos são **propostas**, não valores recuperados do CDADE nem escolhas já pré-registradas. Registrar a aprovação em `docs/protocol-decisions.md` antes de rodar a bancada final.

| Decisão              | Proposta concreta                                                                                                                                                                                                            | Motivo / teste                                                                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Lead time            | Publicar `delay = alarm−onset` e `lead = onset−alarm`; Δ principal é `lead_B2−lead_B1*`.                                                                                                                                     | Resolver a ambiguidade do texto: Δ positivo significa detecção mais cedo.                                                       |
| Janela / censura     | Janela `[onset−12,onset+12]`, limitada à observação; primeiro alarme nela. Sem alarme: `detected=false`, tempo censurado no fim+1; usar esse tempo restrito no bootstrap e publicar probabilidade de detecção separadamente. | Não descartar falhas nem transformar ausência de onset em surto perdido.                                                        |
| ε e janela de treino | ε = `[0.0,0.05,0.20]`; meses 0–59 de treino; monitoramento 60–131; surto sem cruzamento durante treino.                                                                                                                      | Baixo/alto não são numericamente fixados no README. Valores só mudam por revisão prévia, nunca pelo efeito observado.           |
| Amostragem           | Planejamento inicial: 500 T + 500 N de avaliação por ruído×ε = 9.000; **mais** 200 N de calibração por célula = 1.800, com seeds disjuntas.                                                                                  | As gêmeas T não são réplicas N independentes; não reutilizar calibração na estimativa de FAR.                                   |
| Seeds                | raiz 42; subárvores estáveis para dados, calibração, avaliação, placebos, detectores e bootstrap. Registrar entropy, spawn_key e seed inteira quando biblioteca a exigir.                                                    | Reordenar braços não muda dados, gráficos ou bootstrap.                                                                         |
| Bootstrap            | 10.000 reamostragens, IC percentil 95%; unidade = réplica, com suas 13 regiões juntas; estratificar ε e ruído.                                                                                                               | Não tratar 13 regiões correlacionadas como 13 réplicas independentes.                                                           |
| Controle ε = 0       | Reportar IC e teste de equivalência com margem proposta ±1 mês. Sem equivalência, critério de ausência de ganho não foi demonstrado.                                                                                         | Falta de significância não prova ausência de efeito; margem exige revisão científica.                                           |
| Placebo rank         | Fração estrita de placebos superados por B2 na mesma estatística; empates não contam. `29/30 > .95`; `28/30` não.                                                                                                            | É posição descritiva, não chamar essa fração de p-valor.                                                                        |
| FAR                  | Um alarme = um mês-região acima do limiar; sem cooldown implícito. Ajustar por braço/região em N de calibração; alvo 1/60.                                                                                                   | Avaliação N separada: reportar FAR e IC por blocos, incluindo desvio do alvo; bloquear interpretação se comparabilidade falhar. |
| Geografia            | Queen é primária. Se desconexa, falhar e produzir diagnóstico; k-NN simétrico de centróides é variante identificada e exige pré-registro.                                                                                    | Não ligar ilhas arbitrariamente nem chamar grafo corrigido de queen puro.                                                       |

D-COST antecipa o piloto para ~02/10 após detectores+simulador acoplado, sem inverter a ordem de porte. Registrar o hardware antes do piloto; gatilhos sobre a projeção da execução completa: > 48 h → degrau (a), > 96 h → degrau (b). Escada: 30 placebos em 100T fixas/célula (rank compara B2 no mesmo subconjunto e preserva N); depois 200T+200N/célula; depois opcionais. IDs e parâmetros são congelados antes dos efeitos. A seleção existe; declarar custo da integração ainda não medida, sem certificar pipeline completo. Camada1 precede B-Gao/Φ/SEIRS; camada 0 não é cortada.

Definir, no mesmo registro antes da implementação metapopulacional, Nᵢ (populações efetivas, não inferidas só de casos), θ, β₀/β₁, µ/γ, intensidade de cada ruído, sazonalidade e SD usada no onset. Proposta para a SD: desvio-padrão da série observada da gêmea nos 60 meses de treino, congelado; não SD do excesso pré-surto (que pode ser identicamente zero com números comuns). Estimar νᵢ só das medianas de treino, condicionado aos parâmetros fixados; ν e θ não são identificáveis separadamente por essas medianas. Essa definição quantitativa é um gate de desenho, com fonte e teste, não um default escondido no código.

## 8. Grafo, simulação e features

Verificar 13 nomes e códigos de regiões de saúde, não CRS ou municípios; dissolver geometria municipal explicitamente quando necessário, preservar CRS e hash da fonte. Há um relato dos mantenedores de que `geometry_level` podia retornar municípios na implementação Python; o teste deve verificar o resultado, independentemente da versão instalada ([geobr #448](https://github.com/ipea/geobr/issues/448)). Queen: A simétrica/binária/diagonal zero; W normalizada por linha. Conectividade é pré-condição da geração de placebos.

Rewiring com trocas duplas, graus por nó preservados, sem loops/arestas duplicadas, rejeitando desconexão. Rejeitar A original e duplicatas entre os 30 draws; orçamento explícito de tentativas e erro se insuficiente. Gravar A e placebos, hashes, seeds, trocas aceitas e orçamento; não prometer amostragem uniforme das realizações gráficas.

O modelo de uma região precede o acoplamento: verificar SDEs 1–3, escalas temporais e observável I no [suplemento de Gao](https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1012782.s001&type=supplementary). O artigo disponibiliza código/dados no [Zenodo](https://doi.org/10.5281/zenodo.10967222), referência para fixtures. A adaptação a incidência mensal observada é um segundo teste; não somar prevalências semanais e chamar o resultado de novos casos.

Na extensão, aplicar `C=(1−ε)I+εW`, `λ_i=β_i(t)Σ_j C_ij I_j/N_j`; introduzir ν e sazonalidade documentados. Uma semana = 7 dias; integrar o último intervalo parcial e distribuir fluxos aos meses do calendário. Registrar clipping de compartimentos e frequência de projeções; incidência inteira antes da observação binomial, com a regra de discretização pré-registrada.

Números comuns significam as mesmas inovações por `(réplica,semana,região,canal)`, incluindo observação; apenas reutilizar um seed com chamadas condicionais não garante isso. Usar inovações de tamanho fixo e quantis binomiais comuns para estados diferentes. ε=0 deve dar igualdade exata outbreak/twin nas regiões não sementes. Rótulos e onset nunca entram nas features.

SD, CV, AR1, skewness e kurtosis têm janela causal e máscara de validade. Janela sem variância/média: zero determinístico com indicador de validade, documentado; não gerar infinito. Teste de separação T/N usa apenas janelas pré-onset definidas no experimento de validação.

## 9. Artefatos, dependências e verificação

`results/<run_id>/manifest.json`: config resolvida/hash, SHA do projeto e estado dirty, SHA CDADE, versões/lock hash, timestamp UTC, seeds completas, hashes dos dados/grafos, partições, parâmetros científicos, `baseline_id`, status dos gates, caminhos e hashes dos artefatos. `metrics.parquet`: `experiment,layer,baseline_id,arm,graph_id,noise,epsilon,k,replicate,region,metric,value,status`. Manifesto inclui perfil/hash da injeção e do nulo, decisão G0 explícita (`gates.G0.decision`) e status E0 (`gates.E0.status`), nívelD-COST, IDs do subconjunto, tamanho efetivo e diagnósticoD-REACH. `scores.parquet`, `onsets.parquet`, `calibration.parquet`, `statistics.json` preservam auditoria. Toda linha AUC-PR de `metrics.parquet` deve ser acompanhada por `n_positive`, `n_negative` e `prevalence`, identificando tarefa/janela; figuras/tabelas preservam essa informação (também no descritivo original, explicitando ausências). Não sobrescrever run_id existente.

`data/processed/` guarda longa, geometrias, calibração endêmica e cache regenerável. O manifesto do run referencia seus hashes. Componentes numéricos não fazem I/O; o runner é responsável por salvar seus outputs. Isso satisfaz a definição de pronto sem acoplar cada função ao filesystem.

Dependências do baseline já declaradas: scipy/pyarrow, pytest/ruff em dev, PyOD e river. Não repetir instalação/porte; dependências futuras apenas via `uv add`. Não introduzir framework para eliminar essas duas bibliotecas pequenas à custa de paridade. Resolver versões e registrar conflitos com os pisos atuais; não baixar versões silenciosamente. Bibliotecas geográficas/networkx já declaradas são aproveitadas. Não remover openpyxl/pymnet/igraph/pmdarima neste trabalho de planejamento.

Testes rápidos sem rede; integração geográfica/fixtures originais marcada; simulador `slow`; reprodução completa E0 e bancada fora do pytest padrão. Ausência de dados/oráculo pode dar skip só em testes opcionais; comandos de gate devem falhar explicitamente. Checks: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest` e testes científicos da etapa. Commits locais convencionais; sem push.

## 10. Questões que impedem execução automática

1. D-E0*-R1 foi registrada antes da integração; PA é descritivo. E0* e FAR falharam na execução de 30/09, mantendo interpretação bloqueada. A especificação do fallback D-GT3 permanece pendente.
2. Aprovar as convenções da §7 e parâmetros numéricos da simulação antes de E1; documentar se o critério de equivalência é aceito.
3. Preservar D5 já aprovada: MinT sobre previsões de contagem, features sobre resíduos padronizados; P6 independe de P5.
4. Obter malha com 13 regiões e conectividade compatível, ou registrar a variante antes dos placebos.

Esses gates não impedem entregar o plano global, auditar o original, escrever testes dos componentes isolados ou construir S/A. Impedem anunciar baseline paritário; interpretar E1′ exige E0\* aprovado sob o protocolo vigente, além de FAR e todos os demais gates aplicáveis. B1\* já autorizado não basta. Os planos associados descrevem tarefas condicionais com critérios objetivos de entrada/saída.
