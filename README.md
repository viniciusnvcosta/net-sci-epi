# HEADD-Series L0 — Estrutura Relacional do Grafo

> Vinícius Nunes · <vnvc@ecomp.poli.br>

Estuda se a adjacência geográfica entre regiões de saúde, usada como informação relacional sobre a árvore de agregação hierárquica, antecipa a detecção de surtos em vigilância epidemiológica — e se esse ganho desaparece quando o grafo real é trocado por um grafo placebo.

---

## 1 · Objetivo e contexto

A vigilância epidemiológica organiza contagens em hierarquias — geografia (`município → região → estado`), diagnóstico (espécie do parasita, CID-10) e tempo (`semana → mês`). Um surto raramente se anuncia no topo dessas hierarquias: ele emerge em folhas esparsas e ruidosas, e cabe ao operador decidir se sinais fracos e dispersos constituem uma alta real.

A **HEADD-Series** (_Hierarchical Early Anomaly Dynamic Detection for Time Series_) endereça esse problema com um pipeline de camadas L0–L5. Este projeto de disciplina isola **L0 — o construtor de estrutura relacional** — como estudo de caso de Ciência das Redes. O baseline é o **CDADE v1** (_Coherent Drift-Aware Dynamic Ensemble_), que usa apenas a árvore de soma **S**.

Uma árvore de agregação é o caso trivial de um grafo. O movimento metodológico central é generalizar essa árvore para um grafo que carregue mecanismo epidemiológico — quem é vizinho de quem — e testar, de forma refutável, se essa generalização produz ganho mensurável.

### Mudanças em relação à Entrega 1

A proposta foi aprovada com duas ressalvas, que redefiniram o escopo:

| Ressalva                                                                                                      | Resposta nesta versão                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prazo para adquirir e estruturar **M** (mobilidade) e **A** (adjacência)                                      | Escopo reduzido a **S + A**. A sai do `geobr` em horas. **M** passa para o mestrado. **Φ** entra como exploratório, porque os dados já trazem a espécie do parasita.             |
| Comparação com o CDADE possivelmente falha, porque pool e seleção dinâmica operam sobre representação tabular | O grafo entra como **informação** (features de vizinhança) dentro do mesmo pipeline, não como modelo concorrente. A comparação vira uma ablação com uma única variável alterada. |

Um terceiro problema, identificado na revisão: o ground truth do CDADE v1 (spikes, level shifts e drifts injetados de forma independente em cada série) **não tem propagação**. Por construção, nenhuma estrutura relacional pode ajudar a detectá-lo. Por isso este projeto introduz uma bancada sintética em que o surto se propaga pelo grafo (§5).

## 2 · Pergunta de pesquisa (RQ1′)

> **Quando surtos se propagam entre as 13 regiões de saúde do Pará por acoplamento geográfico, informar o CDADE com a adjacência A antecipa a detecção (_lead time_), com taxa de falso alarme fixa, em relação ao CDADE só com S? O ganho desaparece quando A é substituída por um grafo aleatório de mesma sequência de graus?**

A hipótese prevê um padrão de dose-resposta: nenhum ganho sem acoplamento entre regiões (ε = 0), e ganho crescente com o acoplamento. O critério de validação (§5.4) é fixado antes de qualquer execução, e uma rejeição é reportada como resultado negativo — sem expandir o grafo até encontrar significância.

## 3 · Dados

### 3.1 SIVEP-Malária, Pará, 2009–2019 (em mãos)

Os dois arquivos vêm do repositório público de Eze et al. (2023), `github.com/KingPeter2014/Anomaly_in_malaria_surveillance_data`. A licença do repositório não foi verificada; cite o artigo-fonte, publicado sob CC BY.

| Arquivo                 | Conteúdo                                                                                                    | Dimensão                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| `PA.csv`                | agregado estadual mensal: testes, positivos, negativos, prevalência                                         | 132 meses (jan/2009–dez/2019)        |
| `PASIVEPDailyPerHr.csv` | região de saúde × mês × resultado do exame (`negative`, `vivax`, `falciparum`, mistas, `malariae`, `ovale`) | 7.592 linhas; 13 regiões × 132 meses |

Propriedades verificadas:

- **As 13 unidades são as regiões de saúde da SESPA**: Araguaia, Baixo Amazonas, Carajás, Lago de Tucuruí, Marajó I, Marajó II, Metropolitana I, II e III, Rio Caetés, Tapajós, Tocantins e Xingu. Não são os Centros Regionais de Saúde (CRS), então a camada A pode vir diretamente das malhas de regiões de saúde.
- **A hierarquia S é exata.** A soma das 13 regiões coincide com `PA.csv` em positivos e em total de testes, com diferença zero nos 132 meses.
- **Há um eixo de fenótipo.** Dos positivos, 86,1% são vivax, 12,3% falciparum e 1,5% infecções mistas; malariae e ovale são residuais.
- **A escala é muito heterogênea.** A mediana mensal de positivos vai de 1.453 (Marajó II) a 5 (Metropolitana II e Rio Caetés, com 14% de meses sem casos).
- **A sincronia entre regiões é fraca.** A correlação média entre as variações mensais (log) das regiões é 0,16. Os dados reais podem ter pouco sinal relacional detectável, o que justifica a bancada sintética.

### 3.2 Malhas de regiões de saúde (IBGE/DataSUS, via `geobr`)

Base da camada **A**. A construção prevista é `read_health_region(code_state="PA", geometry_level="micro")`, seguida de contiguidade _queen_ com `libpysal`. É preciso tratar Marajó I/II, que pode ficar isolado ou mal ligado por causa de rios e baías; a variante documentada é vizinhança por _k_-NN de centróides.

### 3.3 Dados sintéticos (gerados neste projeto)

Bancada metapopulacional descrita em §5.1. Os dados são regenerados de forma determinística a partir das sementes e não são versionados.

### 3.4 Fora do escopo desta etapa

REGIC 2018 e a rede infecção→notificação do SIVEP (camada **M**), o Project Tycho v2.0 e o multiplex CID-10 completo ficam para o mestrado.

## 4 · Estruturas do L0

| Estrutura     | Construção                                                                               | Papel nesta etapa             |
| ------------- | ---------------------------------------------------------------------------------------- | ----------------------------- |
| **S**         | matriz de soma 13 → 1 (Wickramasuriya et al., 2019)                                      | baseline (CDADE v1)           |
| **A**         | contiguidade _queen_ entre regiões de saúde, normalizada por linha em **W**              | hipótese                      |
| **A**-placebo | 30 grafos por troca de arestas com preservação de grau (Maslov & Sneppen, 2002), conexos | controle                      |
| **Φ**         | camadas por espécie (vivax, falciparum, mista) em cada região                            | exploratório (só dados reais) |
| **M**         | mobilidade inter-regional                                                                | adiado (mestrado)             |

## 5 · Protocolo experimental E1′

### 5.1 Bancada sintética: metapopulação sobre as 13 regiões

O ponto de partida é o SIR estocástico de Gao et al. (2025), com três fontes de ruído: branco, ambiental multiplicativo e demográfico. Nesse modelo, a classe "surto" (T) tem β(t) crescendo lentamente até R0 cruzar 1 (bifurcação transcrítica), e a classe nula (N) mantém R0 < 1. As adaptações deste projeto são:

1. **Acoplamento.** A força de infecção na região _i_ é λᵢ = βᵢ(t) · Σⱼ Cᵢⱼ Iⱼ / Nⱼ, com C = (1 − ε)·I + ε·W. O acoplamento ε assume três níveis: 0, baixo e alto.
2. **Surto.** Só a região-semente (sorteada) tem β crescente, como em Gao. As demais têm R0 local < 1, então o surto só chega a elas pelo grafo.
3. **Fundo endêmico.** Um termo de importação constante νᵢ, calibrado pelas medianas reais de cada região, no espírito do componente endêmico do hhh4 (Held et al., 2005). Soma-se sazonalidade anual.
4. **Variante SEIRS (robustez).** Compartimento E (latência) e perda de imunidade R → S, estruturas motivadas pelo SEIRS+ (§6).
5. **Observação.** Integração Euler–Maruyama em passo semanal, agregada em contagens mensais (132 meses). A notificação é modelada por subnotificação binomial com taxa de testagem θ.
6. **Ground truth.** Uso números aleatórios comuns: cada réplica T tem uma gêmea sem surto, com a mesma semente. O onset da região-semente é o mês em que R0 cruza 1 (Gao). O onset de cada outra região é o primeiro mês em que o excesso em relação à gêmea passa de 2 desvios-padrão.
7. **Volume.** 3 ruídos × 3 níveis de ε × (500 T + 500 N) = 9.000 simulações de 13 × 132.

O nível ε = 0 é um controle interno de falsificação. Sem propagação, A não pode ajudar; qualquer ganho nesse nível indica vazamento no pipeline.

**Validação do simulador (antes de acoplar):** com uma única região, reproduzir a separação T/N dos indicadores AR1 e CV reportada no suplementar de Gao et al. (Figs. F–H).

### 5.2 Bancada semi-real: ground truth em camadas

- **Camada 0 — anomalias locais.** Usa injeções finitas de spikes, level shifts e drifts (D-GT1), com treino intacto e PA recalculado. Não é evidência de propagação. A não-inferioridade B2−B1* exige limite inferior do IC95% ≥ −0,02, bootstrap pareado sobre as13regiões e PA separado. E0 permanece inconclusivo; E0* é o gate substituto. O pré-gate atual falha porque PA tem uma só classe na janela de teste.
- **Camada 1 — injeção epidêmica.** Substitui o pulso ad hoc por casos adicionais gerados pelo componente de surto de `simulate.py`, com fundo endêmico desligado e propagação por `C=(1−ε)I+εW`. Somar a uma cópia das contagens reais e recalcular PA; não criar um segundo simulador. Níveis propostos k=(1,3,6) vezes a mediana mensal de treino da semente; introdução uniforme em 72–118, θ igual à bancada e faixa R0 pré-registrada. Domínio do tamanho e demais parâmetros ainda precisam ser fixados.
- **Camada 2 — bancada inteiramente sintética.** Mantém o mecanismo e os onsets da §5.1; dimensionamento pode seguir somente a escada de custo pré-registrada.
- **Camada 3 — eventos documentados.** Checagem qualitativa no notebook 02, com fontes verificadas, sem critério formal.

Na camada 1, onset da semente é a introdução; nas demais regiões, o primeiro mês com caso importado observado≥1, ou −1 se não chegar. Na camada 2 permanecem cruzamento R0/2SD. Nas camadas 1/2 o gerador usa A: B2 é um oráculo; as comparações relevantes incluem os placebos e o padrão em ε. A soma de casos supõe ausência de interação do surto com a dinâmica endêmica, incluindo depleção de suscetíveis compartilhados; essa é uma aproximação na escala mensal.

A camada 1 tem prioridade sobre B-Gao, Φ/B3 e SEIRS; a camada 0 não é cortada. Decisões e pendências: [registro do protocolo](docs/protocol-decisions.md).

### 5.3 Braços

| Braço             | Descrição                                                                                                                                                |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **B0**            | séries independentes, sem S (piso)                                                                                                                       |
| **B1\***           | Baseline corrigido estilo CDADE: S + pool + reconciliação MinT + seleção dinâmica + limiar EVT/GPD                                                                              |
| **B2**            | B1\* + features de vizinhança em W: W·xₜ, W·xₜ₋₁, diferença entre a região e a média dos vizinhos, e I de Moran local em janela móvel                      |
| **B2-placebo**    | B2 com cada um dos 30 grafos placebo                                                                                                                     |
| B-Gao (opcional)  | classificador GBM sobre os 5 indicadores de alerta precoce (SD, CV, AR1, assimetria, curtose), treinado na bancada e aplicado por região em janela móvel |
| B3 (exploratório) | B2 + camadas de espécie Φ (só dados reais)                                                                                                               |

Entre B1* e B2 muda uma única coisa: a informação relacional disponível. Pool, reconciliação, seleção e limiar ficam idênticos.

### 5.4 Métricas e critério de validação

**Calibração.** FAR alvo=1/60 por região-mês em todos os braços. Nos dados reais, a proposta é ajustar uma binomial negativa com harmônicos sazonais e tendência somente nos 60 meses de treino de cada região e gerar 200 séries nulas por região. Calibração e avaliação usam realizações e seeds independentes; PA é soma das folhas. Tolerância proposta da FAR observada=1/300. Bootstrap em blocos do treino fica como diagnóstico secundário. Especificação do nulo e tamanho da avaliação devem ser registrados antes da execução; adequação ao modelo não prova ausência de surtos naturais.

**Métricas.** Lead time, probabilidade de detecção, FAR observada, AUC T/N, AUC-PR, F1 e NAB. Registrar atraso=`alarme−onset` e lead=`onset−alarme`, para que ganho B2−baseline positivo signifique detecção mais cedo; censura e equivalência ε=0 dependem das convenções pré-registradas.

**Alcance.** Antes de executar os braços, reportar por ε/célula a fração de T com onset em ao menos um vizinho da semente. Mínimo proposto≥50% em ε=.20. Célula abaixo do mínimo é sem poder, não evidência negativa; não ajustar parâmetros olhando avaliação para passar o gate.

**Inferência principal, camadas 1/2.** Bootstrap pareado do ganho por réplica, estratificado por ε, seguido da posição de B2 nos 30 placebos. Sustentar RQ1′ exige conjuntamente IC95% do ganho>0 nos níveis ε>0, equivalência pré-registrada em ε=0 e rank estrito>.95 nos placebos. Com redução de custo, B2 e placebos são comparados no mesmo subconjunto fixo de réplicas; registrar dimensão efetiva.

**Camada 0.** E0 inconclusivo e não-inferioridade são análises distintas. A regra aprovada D-GT1 usa o limite inferior do IC95% de ΔAUC-PR(B2−B1*) e reamostra as13regiões; PA é reportado à parte. Piora é custo do método, não refutação isolada de RQ1′.

**Protocolo secundário real.** Manter Friedman→Wilcoxon/Bonferroni→Diebold-Mariano/HAC→Cliff/IC95%, interrompendo os testes seguintes se Friedman p>.05; não substituir por ele os critérios principais da camada 1.

**Gates e conclusão.** D-G0 autorizou B1* corrigido com E0 inconclusivo. E0* e os outros gates continuam obrigatórios; seu estado executável está em [Task 9](docs/e0-task9-status.md). Critério científico não satisfeito com gates válidos é resultado negativo para a bancada; gate inválido ou alcance insuficiente é inconclusivo. Não expandir o grafo nem ajustar a baseline para resgatar a hipótese.

### 5.5 Análise de rede complementar

Correlação de Spearman entre a centralidade de cada região em A (grau, intermediação, autovetor) e a ordem em que ela detecta o surto, na linha da literatura de sentinelas em redes (Christakis & Fowler, 2010; Colman et al., 2019).

## 6 · Escolha do simulador: Gao et al. vs. SEIRS+ (Liu et al.)

Liu et al. (2026) geraram um conjunto sintético com o modelo agent-based SEIRS+ (McGee): 20 infectados introduzidos numa rede de 20 mil agentes, com parâmetros padrão do pacote. As curvas resultantes foram sobrepostas, em posições aleatórias, a ruído gaussiano calibrado nos dados reais. Avaliei o SEIRS+ contra as limitações já identificadas:

| Limitação                 | SEIRS+ atende?                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Mistura homogênea do SIR  | **Sim**, em nível de indivíduos: rede de contatos com parâmetro de interações globais _p_. Mas a estrutura de interesse aqui é entre **regiões**; só uma rede em 13 blocos com ligações entre blocos proporcionais a A a reproduziria.                                                                                                                                          |
| Ausência de latência      | **Sim** (compartimento E). Na escala mensal o efeito é pequeno, porque a incubação da malária é de ~1–2 semanas.                                                                                                                                                                                                                                                                |
| Endemicidade e reinfecção | **Parcial**: SEIRS (R → S) permite reinfecção, mas não modela recaída do _P. vivax_ (hipnozoítos).                                                                                                                                                                                                                                                                              |
| Processo de notificação   | **Sim**: parâmetros de testagem e detecção geram séries de casos detectados, análogas à notificação.                                                                                                                                                                                                                                                                            |
| Vetor (_Anopheles_)       | **Não.**                                                                                                                                                                                                                                                                                                                                                                        |
| Propagação entre regiões  | **Não nativamente.** O conjunto de Liu et al. tem um único surto por segmento, sobreposto a ruído, sem propagação espacial — a mesma limitação das injeções do CDADE v1.                                                                                                                                                                                                        |
| Onset verificável         | **Sim**: o evento de introdução é observável.                                                                                                                                                                                                                                                                                                                                   |
| Manutenção e custo        | **Fraco.** Última versão no PyPI é a 1.0.9 (ago/2020). `SEIRSNetworkModel` falha com networkx ≥ 3 (usa `nx.adj_matrix`, removido); só roda com um shim de compatibilidade, e a correção nesse caso não foi verificada. Em teste local, 2 mil agentes por 1 ano levaram ~4 s; 20 mil agentes não completaram 1 ano em 5 min. As 9.000 réplicas de 11 anos da §5.1 são inviáveis. |

**Decisão.** O simulador principal é a metapopulação própria em numpy (§5.1), que roda milhares de réplicas em minutos. Do SEIRS+ incorporamos as ideias (compartimento E, perda de imunidade, observação por testagem) como variante de robustez. Uma rodada SEIRS+ em 13 blocos, com poucas réplicas, fica como verificação de realismo no mestrado.

## 7 · Repositório e reprodução

```bash
.
├── data/
│   ├── raw/sivep/          # PA.csv, PASIVEPDailyPerHr.csv (imutáveis)
│   └── processed/          # tabela longa região × mês × espécie (regenerável)
├── configs/                # um .toml por experimento (bancada, semi-real)
├── src/headd_l0/           # ver AGENTS.md para o mapa de módulos
├── tests/                  # espelha src/
├── results/                # parquet + manifesto JSON por execução
├── README.md
└── AGENTS.md
```

```bash
uv sync
uv run pytest
uv run python -m headd_l0.run configs/e0_star.toml  # pré-gate; exit 2 esperado
```

Comandos executados com resultados: [pipeline verificada](docs/pipeline-commands.md).
Configuração, caminhos e validação: [configuração de execução](docs/configuration.md).

Estado executável e próximos passos: [Task 9 e ambiente L0](docs/e0-task9-status.md).
O runner de bancada E1′ ainda pertence às próximas etapas; o pré-gate atual
não autoriza interpretação científica.

## 8 · Ambiente e dependências

Ambiente gerenciado com `uv` (Python ≥ 3.12). Às dependências existentes (matplotlib, numpy, pandas, pmdarima, scikit-learn, seaborn, statsmodels), este projeto adiciona:

```toml
[project]
dependencies = [
    # ... dependências existentes ...
    "networkx>=3.4",   # grafo L0, placebos, centralidades
    "scipy",           # matrizes esparsas, EVT/GPD
    "geopandas",       # malhas de regiões de saúde (camada A)
    "libpysal",        # contiguidade queen
    "geobr",           # download das malhas oficiais
    "pyarrow",         # parquet
]

[dependency-groups]
dev = ["ipykernel>=7.3.0", "jupyter>=1.1.1", "pytest", "ruff"]
```

Ferramentas externas: **Gephi** para as figuras do grafo (exportação via `nx.write_gexf`, uma camada por arquivo).

## 9 · Cronograma até 16/10/2026

| Período     | Entrega                                                                                                                                    |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 25/09–01/10 | Contrato de dados e teste de coerência de S; construção de A e mapa; simulador de uma região validado contra Gao; extensão para 13 regiões |
| 02/10–08/10 | Porte do baseline CDADE (ver `AGENTS.md`); features de vizinhança; placebos; calibração nas réplicas nulas; execução de B0–B2-placebo      |
| 09/10–13/10 | Bancada semi-real no SIVEP; bootstrap e análise de centralidade; B-Gao e B3 se houver tempo                                                |
| 14/10–16/10 | Redação de Metodologia e Resultados Preliminares                                                                                           |

## 10 · Limitações

- SIR e SEIRS não modelam o vetor nem as recaídas do _P. vivax_. A bancada testa "surtos que se propagam por acoplamento", não a biologia da malária.
- Na bancada, o grafo de simulação é A. B2 funciona, portanto, como oráculo, e a evidência relevante é B2 vs. placebo e o padrão em ε. Simular com um grafo diferente de A (por exemplo, gravitacional) fica como teste de má especificação no mestrado.
- A contiguidade é uma aproximação fraca da conectividade real na Amazônia, onde o transporte é fluvial.
- Com correlação média de 0,16 entre regiões, um efeito pequeno pode ser indetectável nos dados reais. A bancada sintética é o que separa "o método não aproveita a rede" de "os dados não têm sinal relacional".

## 11 · Referências

- Weaver, W. (1948). Science and Complexity. _American Scientist_, 36(4), 536–544.
- Hidalgo, C. A. (2016). Disconnected, fragmented, or united? A trans-disciplinary review of network science. _Applied Network Science_, 1, 6.
- Eze, P. U., Geard, N., Mueller, I., & Chadès, I. (2023). Anomaly Detection in Endemic Disease Surveillance Data Using Machine Learning Techniques. _Healthcare_, 11(13), 1896.
- Gao, S., Chakraborty, A. K., Greiner, R., Lewis, M. A., & Wang, H. (2025). Early detection of disease outbreaks and non-outbreaks using incidence data: A framework using feature-based time series classification and machine learning. _PLOS Computational Biology_, 21(2), e1012782.
- Chakraborty, A. K., Gao, S., Miry, R., Ramazi, P., Greiner, R., Lewis, M. A., & Wang, H. (2024). An early warning indicator trained on stochastic disease-spreading models with different noises. _Journal of the Royal Society Interface_, 21(217), 20240199.
- Liu, Y., Wang, X., Cao, Z., Luo, T., Yang, P., & Wang, Q. (2026). A framework using large time series model for early warning of infectious diseases. _Infectious Disease Modelling_, 11(1), 107–120. <https://doi.org/10.1016/j.idm.2025.08.006>
- McGee, R. S. SEIRS+ (`seirsplus`), software. <https://github.com/ryansmcgee/seirsplus>
- Wickramasuriya, S. L., Athanasopoulos, G., & Hyndman, R. J. (2019). Optimal Forecast Reconciliation for Hierarchical and Grouped Time Series through Trace Minimization. _Journal of the American Statistical Association_, 114(526), 804–819.
- Kulldorff, M. (1997). A spatial scan statistic. _Communications in Statistics — Theory and Methods_, 26(6), 1481–1496.
- Held, L., Höhle, M., & Hofmann, M. (2005). A statistical framework for the analysis of multivariate infectious disease surveillance counts. _Statistical Modelling_, 5(3), 187–199.
- Colizza, V., & Vespignani, A. (2007). Invasion threshold in heterogeneous metapopulation networks. _Physical Review Letters_, 99, 148701.
- Maslov, S., & Sneppen, K. (2002). Specificity and stability in topology of protein networks. _Science_, 296(5569), 910–913.
- Christakis, N. A., & Fowler, J. H. (2010). Social network sensors for early detection of contagious outbreaks. _PLoS ONE_, 5(9), e12948.
- Colman, E., Holme, P., Sayama, H., & Gershenson, C. (2019). Efficient sentinel surveillance strategies for preventing epidemics on networks. _PLOS Computational Biology_, 15(11), e1007517.
- Lubba, C. H., et al. (2019). catch22: CAnonical Time-series CHaracteristics. _Data Mining and Knowledge Discovery_, 33(6), 1821–1852.
