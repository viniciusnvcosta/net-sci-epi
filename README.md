# HEADD-Series L0 — Estrutura Relacional do Grafo

> Vinícius Nunes · <vnvc@ecomp.poli.br>

Estuda se estruturas relacionais além da árvore de agregação hierárquica (adjacência geográfica, mobilidade inter-regional e multiplex de fenótipo) melhoram a detecção precoce de anomalias em vigilância epidemiológica.

---

## 1 · Objetivo e contexto

A vigilância epidemiológica organiza contagens em hierarquias — geografia (`município → região → estado → país`), classificação diagnóstica (CID-10: `subcategoria → categoria → bloco → capítulo`) e tempo (`dia → semana ISO → mês`). Um surto raramente se anuncia no topo dessas hierarquias: ele emerge em folhas esparsas e ruidosas, e cabe ao operador decidir se sinais fracos e dispersos constituem uma alta real.

A **HEADD-Series** (_Hierarchical Early Anomaly Dynamic Detection for Time Series_) endereça esse problema com um pipeline de cinco camadas (L0–L5). Este pré-projeto de disciplina isola e aprofunda **L0 — o construtor de estrutura relacional** — como estudo de caso de Ciência das Redes, tratando as camadas L1–L5 (detecção, reconciliação, seleção de ensemble, decisão sequencial e fenótipo) como fora de escopo desta entrega.

Uma árvore de agregação é o caso trivial de um grafo. O movimento metodológico central deste projeto é generalizar essa árvore para um grafo relacional mais rico — que carrega mecanismo epidemiológico, não apenas soma — e testar, em forma hipótese, se essa generalização produz ganho mensurável.

## 2 · Pergunta de pesquisa (RQ1)

> **A estrutura relacional adicional ao grafo de agregação (adjacência geográfica, mobilidade inter-regional e multiplex de fenótipo) melhora o _lead time_ de detecção precoce de anomalias em vigilância epidemiológica hierárquica, em comparação ao baseline que usa apenas a árvore de soma (CDADE v1)?**

A pergunta é desenhada para ser **refutável**: o protocolo experimental (§4) define de antemão o critério que a confirma ou a rejeita, e o projeto se compromete a reportar rejeição como resultado negativo — sem expandir o grafo até encontrar significância.

## 3 · Estratégia de coleta de dados

Quatro fontes de dados abertos sustentam a construção do grafo L0 e a validação do protocolo experimental. Nenhuma exige acesso restrito a dados sensíveis identificáveis.

| Fonte                                                                                                                        | Uso no L0                                                                | Formato / acesso                                                                                                                   | Granularidade                | Licença                                                           | Risco conhecido                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **IBGE REGIC 2018** (Regiões de Influência das Cidades) — bases "Ligações entre Cidades" e "Matriz de regiões de influência" | Camada **M** (mobilidade/influência inter-regional)                      | xlsx/ods via `geoftp.ibge.gov.br`; ~71 mil ligações intermunicipais, 5.503 municípios pesquisados                                  | Municipal                    | Dados abertos do governo federal                                  | Mede _influência/atração_, não deslocamento físico contínuo — é uma proxy de mobilidade             |
| **Malhas geográficas do IBGE** (municípios, regiões) via `geobr`                                                             | Camada **A** (adjacência geográfica de contiguidade)                     | GeoPackage/shapefile, pacote Python `geobr`                                                                                        | Municipal                    | Dados abertos do governo federal                                  | Paridade da API Python do `geobr` pode ser menor que a da versão em R — validar funções disponíveis |
| **SIVEP-Malária (Pará), 2009–2019** — corpus usado por Eze et al. (2023)                                                     | Série temporal alvo (contagens de testes/positivos/negativos por região) | Microdados não têm disseminação pública ampla; via pedido **LAI/Fala.BR** ao Ministério da Saúde, ou depósitos derivados no Zenodo | 13 regiões de saúde do Pará  | Não documentada no artigo-fonte — tratar como acesso condicionado | **Caminho crítico**: abrir o pedido LAI o quanto antes; prazo de resposta pode levar semanas        |
| **Project Tycho v2.0**                                                                                                       | Segundo corpus de validação (séries semanais padronizadas)               | API com autenticação (conta + API key), `tycho.pitt.edu`                                                                           | Semanal, por condição/região | CC BY 4.0                                                         | Requer cadastro prévio — contabilizar no cronograma                                                 |

**Fallback previsto para a camada M:** se a fração de peso das ligações REGIC corretamente mapeadas das ~71 mil ligações municipais para as 13 regiões SIVEP do Pará ficar abaixo de um limiar pré-definido (ex.: <90% do peso total preservado), a camada M é descartada e o experimento recorre ao braço A2 (apenas contiguidade), reportando a limitação explicitamente em vez de forçar um mapeamento ruim.

## 4 · Desenho experimental do grafo (protocolo E1)

O L0 constrói quatro estruturas relacionais sobre as mesmas unidades geográficas:

| Estrutura | Descrição                                                                                  |
| --------- | ------------------------------------------------------------------------------------------ |
| **S**     | Matriz de soma — árvore de agregação hierárquica (`município → região → estado → país`)    |
| **A**     | Adjacência geográfica de contiguidade entre regiões                                        |
| **M**     | Mobilidade inter-regional ponderada (fluxos REGIC agregados)                               |
| **Φ**     | Multiplex de fenótipo — acoplamento CID-10 (`subcategoria → categoria → bloco → capítulo`) |

O protocolo **E1 (Relational lift ablation)** é um design fatorial de 5 braços que adiciona complexidade relacional progressivamente, mantendo fixas as demais camadas do pipeline:

| Braço  | Estrutura                               | Nota                           |
| ------ | --------------------------------------- | ------------------------------ |
| **A0** | séries independentes                    | sem coerência — piso (_floor_) |
| **A1** | apenas **S**                            | baseline CDADE v1 (incumbente) |
| **A2** | **S** + **A**                           | apenas contiguidade            |
| **A3** | **S** + **M**                           | ponderado por mobilidade       |
| **A4** | **S** + **A** + **M** + **Φ**-multiplex | relacional completo            |

**Critério de validação:** A4 deve superar A1 em _lead time_ de detecção, com intervalo de confiança de 95% excluindo zero, sob reamostragem corrigida hierarquia-aware. Se A2, A3 e A4 forem indistinguíveis de A1, a hipótese relacional (RQ1) é considerada **refutada** para esses corpora e reportada como resultado negativo, o grafo não será expandido até que apareça significância. Essa metodologia evita o _p-hacking_.

## 5 · Ambiente e dependências

Ambiente gerenciado com uv (Python ≥3.12). Dependências já presentes no pyproject.toml (matplotlib, numpy, pandas, pmdarima, scikit-learn, seaborn, statsmodels) cobrem a análise estatística geral; para a construção e visualização do grafo L0, este pré-projeto adiciona:

```toml
[project]
dependencies = [
# ... dependências existentes ...
"networkx>=3.4", # construção e features do grafo L0 (S, A, M, Φ)
"geopandas", # geometrias e operações espaciais (camada A)
"libpysal", # contiguidade espacial (queen/rook)
"geobr", # download das malhas oficiais do IBGE
"openpyxl", # leitura das tabelas REGIC (.xlsx)
]

[dependency-groups]
dev = [
"ipykernel>=7.3.0",
"jupyter>=1.1.1",
"python-igraph", # opcional — validação cruzada de métricas de grafo
"pymnet", # opcional — métricas específicas de multicamada (Φ)
]
```

Ferramentas externas:

- **NetworkX** + `scipy.sparse`: construção e engenharia de features do L0 (graus, centralidades, modularidade). Escolha primária: suficiente e mais produtiva na escala de dezenas de regiões; a lentidão do NetworkX puro-Python só importa em grafos muito maiores.
- **Gephi**: visualização exploratória e geração das figuras dos slides (import via nx.write_gexf, layout ForceAtlas2, coloração por modularidade).
- **Cytoscape** + `py4cytoscape`: alternativa para um workflow de visualização 100% automatizado via código (import via GraphML), caso se deseje reprodutibilidade total da figura.
