# Castro e colaboradores: malária, mobilidade e implicações para o HEADD

Consulta: **27/10/2026**. Complemento à [revisão de simulação em grafos](2026-10-26-simulacao-epidemica-grafos-literatura.md).
Foram examinados os artigos indicados, o texto anexado pelo usuário, os dois
repositórios e os campos efetivamente usados pelo loader local. O anexo foi
tratado como material para conferência, não como autorização para implementar
mobilidade, hhh4 ou novos experimentos.

**Atualização posterior em 27/10:** identificou-se um depósito aberto de
microdados SIVEP 2004–2024 com geografia de infecção e notificação descrita
nos metadados. Ele é candidato a OD histórica; campos e qualidade ainda não
foram auditados. Ver [fontes e requisitos](2026-10-27-requisitos-fontes-dados.md).
As conclusões abaixo sobre os dois repositórios Castro e os arquivos locais
permanecem válidas, mas não devem ser generalizadas a todas as fontes públicas.

**Resultado principal:** esses trabalhos acrescentam uma referência brasileira
direta sobre fluxos de casos de malária. Entretanto, os dados públicos
inspecionados não fornecem uma tabela real completa de pares municipais
origem–destino por mês que permita construir, exclusivamente no treino,
uma matriz de 13 regiões. Dados locais do HEADD também não contêm esses pares.

## Artigos e status de publicação

**Arisco, N. J.; Peterka, C.; Castro, M. C. (2024). _Spatiotemporal analysis
of within-country imported malaria in Brazilian municipalities, 2004–2022_.
PLOS Global Public Health 4(7), e0003452. Publicado em 15/07/2024.**

É o artigo correspondente a PMC11249269. Agrega registros SIVEP/SINAN em
redes municipais mensais: origem é o provável município de infecção;
destino é o de notificação; peso é o número de casos na rota. Não usa residência
nessa definição. Fundamenta comparar geografias de aquisição e diagnóstico,
mas a ligação administrativa não identifica quem infectou quem nem toda a
mobilidade humana. Autodeclaração, procura de atendimento e cobertura da
vigilância condicionam a observação. O uso de séries completas e clusters
retrospectivos não constitui avaliação de alarme online.
[Texto integral](https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0003452).

**Castro, M. C.; Arisco, N. J.; Diniz, C. G.; Ponmattam, J.; Peterka, C.;
Basta, P. C.; Ferreira, M. U. (2025). _Mining and malaria in the Brazilian
Amazon and in the Yanomami indigenous land_. PLOS Neglected Tropical Diseases
19(11), e0013677. Publicado em 03/11/2025.**

Usa modelagem Bayesiana espaço-temporal com contagens, sobredispersão/zeros,
covariáveis ambientais e estrutura espacial. É análise explicativa e de cenários,
não reconstrução de matriz SIR. A avaliação de 2022 usa também dados de 2023;
não pode ser convertida diretamente em baseline causal daquele ano. O texto
compara 15.033 casos locais reportados a 27.611 estimados: aproximadamente
83,7% a mais que o observado, ou 45,6% do total estimado não reportado.
Essa distinção de denominador evita interpretar a expressão “83% de
subnotificação” como ausência de 83% de todos os casos estimados.
[Artigo e métodos](https://journals.plos.org/plosntds/article?id=10.1371/journal.pntd.0013677).

**Arisco, N. J.; Fontoura, P. S.; Peterka, C.; Castro, M. C. (2026).
_Mobility hinders malaria elimination goals in the Brazilian Amazon_.
PLOS Computational Biology 22(10), e1014843. Publicado em 06/10/2026.**

O trabalho já está publicado, não apenas disponível como manuscrito.
O resumo descreve análise de 2003–2023, trajetórias de importação e regras
por espécie para reintrodução e restabelecimento. Autoria, data e resumo
foram verificados no PubMed; publisher e PMC bloquearam o texto integral
nesta consulta. Detalhes do código abaixo são achados do repositório, não
uma verificação integral da correspondência com os métodos publicados.
[Registro bibliográfico](https://pubmed.ncbi.nlm.nih.gov/42837383/);
[DOI](https://doi.org/10.1371/journal.pcbi.1014843).

## O que os repositórios realmente disponibilizam

A auditoria fez download/leitura em `/tmp`, incluindo os ZIPs suplementares,
sem executar R ou R Markdown de terceiros. Commits inspecionados:

| Repositório               | Commit                                     |
| ------------------------- | ------------------------------------------ |
| Mobility-Expanded-Brazil  | `e0f85cb531e94dc1ec9891f6adfe945a5606c6f7` |
| -Brazil-Malaria-Networks- | `a37c408033d5c94f6b0f50abcd0b1af4616662dd` |

### Mobility-Expanded-Brazil

O [README fixado](https://github.com/mcastrolab/Mobility-Expanded-Brazil/blob/e0f85cb531e94dc1ec9891f6adfe945a5606c6f7/README.md)
identifica `data/Arisco_etal_mockdata.csv` e `data/locality_final.csv` como
sintéticos. O primeiro contém 3.013 registros com
`RES_EXAM,MUN_NOTI,MUN_INFE,LOC_INFE,date_notif`; não fornece microdados reais
para reconstruir a rede do artigo. Importação depende da diferença entre
municípios, não do resultado `RES_EXAM`, que participa do filtro por espécie.

**Nem todo o repositório é mock.** O
[script de análise de sequências](https://github.com/mcastrolab/Mobility-Expanded-Brazil/blob/e0f85cb531e94dc1ec9891f6adfe945a5606c6f7/Sequence%20Analysis/Code/Sequence_Analysis_Figure_1.R#L59-L78)
apresenta quatro tabelas municipais derivadas do SIVEP em `Sequence Analysis/Data`:

| Arquivo                        | Conteúdo                                                   | Recupera pares OD mensais? |
| ------------------------------ | ---------------------------------------------------------- | -------------------------- |
| `API_Monthly_For_Sequence.csv` | Casos, população e API por município de infecção e mês     | Não                        |
| `base_network_data_ym.csv`     | Casos locais/importados por município de notificação e mês | Não                        |
| `Typology_SINK_monthly.csv`    | Força/grau de entrada e tipologia por município/mês        | Não                        |
| `Typology_SOURCE_monthly.csv`  | Força/grau de saída e tipologia por município/mês          | Não                        |

O período nominal é 2003–2023. No recorte 2009–2013, as duas primeiras
tabelas têm respectivamente 4.826 e 5.518 registros de 142 municípios do Pará;
não são painéis completos explicitamente observados. O script expande uma
grade com municípios de 2022 e preenche lacunas com categorias zero/sem casos.
Esse preenchimento não prova ausência epidemiológica original e exige
auditoria territorial antes de agregação às regiões.

As sequências e seu clustering são calculados conjuntamente para o histórico
completo. Usar suas classes como atributos disponíveis em 2013 introduziria
informação futura. Não foram encontrados vintages que comprovem quando cada
registro ficou disponível para uma vigilância operacional.

### -Brazil-Malaria-Networks-

O repositório ligado ao artigo de 2024 contém marginais de rede e uma
exceção importante com pares municipais:

| Material auditado        | Informação disponível                                                                | Limitação                                                 |
| ------------------------ | ------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| Supplemental Table 2     | Rotas `município->município` e `count`                                               | Sem ano/mês; período exato não documentado no próprio CSV |
| Supplemental Table 4.zip | Forças/graus município-mês e classificações                                          | Não contém os dois municípios de cada ligação             |
| Supplemental Table 5.zip | Painel mensal de 2004–2022, 497.388 linhas, importação/exportação, casos e população | Marginais por município                                   |
| Supplemental Table 6.zip | Painel reutilizado e resumos municipais                                              | Sem OD mensal                                             |
| Supplemental Figures.zip | Painéis, figuras e sazonalidade estadual                                             | Sem OD mensal                                             |

Fontes fixadas: [Tabela 2](https://github.com/mcastrolab/-Brazil-Malaria-Networks-/tree/a37c408033d5c94f6b0f50abcd0b1af4616662dd/Supplemental%20Table%202),
[Tabela 4](https://github.com/mcastrolab/-Brazil-Malaria-Networks-/blob/a37c408033d5c94f6b0f50abcd0b1af4616662dd/Supplemental%20Table%204.zip),
[Tabela 5](https://github.com/mcastrolab/-Brazil-Malaria-Networks-/blob/a37c408033d5c94f6b0f50abcd0b1af4616662dd/Supplemental%20Table%205.zip),
[Tabela 6](https://github.com/mcastrolab/-Brazil-Malaria-Networks-/blob/a37c408033d5c94f6b0f50abcd0b1af4616662dd/Supplemental%20Table%206.zip),
[figuras](https://github.com/mcastrolab/-Brazil-Malaria-Networks-/blob/a37c408033d5c94f6b0f50abcd0b1af4616662dd/Supplemental%20Figures.zip).

Marginais não determinam as arestas: matrizes OD diferentes podem produzir
as mesmas forças de entrada e saída. Tampouco é possível separar 2009–2013
de contagens de rota sem data. Estimar uma matriz a partir dessas marginais
seria outro modelo, não recuperar uma rede observada. Rotas agregadas podem
informar uma comparação descritiva histórica, desde que a abrangência seja
documentada, mas não servir como W ajustada só no treino.

SHA-256 dos ZIPs inspecionados, para identificar a evidência desta leitura:

```text
ST4  38e31d38d65d769c399ae9411e3fbba4e38e2d3d7e43a8a8b98b9622774db401
ST5  9522f5cf7b5ce60ef7c744d5447ac3e7c254745abd9d41ca3fff1456171b9170
ST6  c3ca68d7c8ce81e41ca82dfc3b82ff526723dfe465d4b3bf67fa65cd4fe3d5a1
Figs e494acd6819bda6a7e45212ff43bf017d972d65f932e5d3178939cc8ea58c777
```

## Reintrodução, eventos e limites do código

As [funções de classificação](https://github.com/mcastrolab/Mobility-Expanded-Brazil/blob/e0f85cb531e94dc1ec9891f6adfe945a5606c6f7/scripts/reintroduction_functions.R)
usam a data de notificação. O baseline parametrizado é de 1.095 dias sem
casos locais antes da importação. No Pf, exige ausência local até +30 dias
e procura casos locais entre +31 e +75; no Pv, os intervalos são até +24
e entre +25 e +69. O fim da janela é contado desde a importação.

O código não exige que todos os 1.095 dias anteriores estejam observados:
aceita histórico truncado no início da base. O marcador F1/F2 não demonstra
parentesco de transmissão individual. Períodos ainda ativos no fim da série
são exportados sem indicador explícito de censura. São aspectos a validar
antes de usar esses outputs como ground truth independente.

Não é correto classificar automaticamente todo evento como vazamento de
futuro: um caso elegível pode ser marcado quando sua notificação ocorre.
Já a duração final, a escolha de municípios por eventos ocorridos em todo
o histórico e as classes de sequências completas são retrospectivas.
A base mock não contém datas de disponibilidade/revisão para testar uma
reprodução operacional. Nenhuma regra foi executada nesta auditoria.

## O que o HEADD observa hoje

O [loader](../../src/headd_l0/data.py) usa `notification.year`,
`notification.month` e `notification.hr` (linhas 79–92). Portanto, a unidade
operacional é região/mês de notificação, conforme a nomenclatura disponível.
Não existe dicionário ou transformação upstream local que permita conferir
a derivação municipal de `notification.hr`.

O CSV regional `PASIVEPDailyPerHr.csv` contém cinco
colunas e 7.592 linhas agregadas. O CSV estadual `PA.csv`
contém 132 meses. Não têm os campos `MUN_INFE`, `MUN_NOTI`, residência,
identificador individual ou datas individuais. O loader soma resultados
diferentes de `negative`; a equivalência desses exames positivos a episódios
clínicos deduplicados não é estabelecida pelos arquivos inspecionados.

Logo, não é possível separar os positivos atuais em locais/importados ou
recuperar fluxos municipais com esses CSVs. Espécie/resultado existe, mas os
rótulos incluem misturas e categorias diagnósticas; exigem harmonização.
O grafo é de 2013 e as contagens são de 2009–2019: nomes iguais não
comprovam estabilidade territorial ou agregação municipal consistente.

## Três grafos que precisam permanecer distintos

| Objeto                 | Interpretação                                                    | Validação pertinente                                         |
| ---------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------ |
| A geográfica           | Fronteiras entre regiões                                         | Fonte cartográfica, identidade, topologia                    |
| F infecção→notificação | Fluxos de casos capturados pela vigilância                       | Pares/data, completude, processo de atendimento              |
| W aprendido            | Dependência preditiva ou acoplamento estimado, conforme o modelo | Generalização, identificabilidade e recuperação em simulação |

F é uma referência empírica complementar, não ground truth da matriz C do
SIR. Se F e as séries vêm da mesma vigilância, seus erros podem ser
compartilhados. Separar períodos reduz reutilização dos mesmos registros,
mas não elimina esses vieses nem prova estabilidade da rede.

Para um estudo futuro, definindo F com origem nas linhas e destino nas
colunas, a agregação por uma matriz regional H seria `F_reg = H F_mun Hᵀ`.
Um W receptor por linha usaria a orientação transposta, se essa fosse a
hipótese escolhida. Converter fluxos de notificação em força de infecção,
porém, exige hipóteses adicionais; não é uma normalização automática.

Também seria necessário preservar: fluxos intrarregionais que viram diagonal,
importações externas ao Pará, regiões sem entrada e incerteza no local
provável de infecção. Um caso importado entre municípios pode ser interno
à mesma região. Excluir fluxos externos e renormalizar muda o objeto estudado.

## A lacuna hhh4 e o que ela acrescenta

**Held, L.; Höhle, M.; Hofmann, M. (2005). _A statistical framework for the
analysis of multivariate infectious disease surveillance counts_. Statistical
Modelling 5, 187–199.** Fundamenta decomposição endêmica/epidêmica de
contagens, com dependência espaço-temporal e extensões para sazonalidade
e sobredispersão. [Resumo do editor](https://doi.org/10.1191/1471082X05st098oa).

**Meyer, S.; Held, L. (2014). _Power-law models for infectious disease spread_.
Annals of Applied Statistics 8, 1612–1639.** Estima decaimento espacial,
incluindo pesos por ordem de vizinhança em contagens regionais. É uma
alternativa parcimoniosa a uma matriz livre de arestas: estima parâmetros
sob estrutura, não identifica automaticamente toda a rede transmissora.
[Texto integral](https://arxiv.org/pdf/1308.5115);
[DOI](https://doi.org/10.1214/14-AOAS743).

**Meyer, S.; Held, L.; Höhle, M. (2017). _Spatio-Temporal Analysis of Epidemic
Phenomena Using the R Package surveillance_. JSS 77(11).** A seção hhh4
formaliza contagens condicionais binomiais negativas com média:

\[
\mu*{it}=e*{it}\nu*{it}+\lambda*{it}Y*{i,t-1}
+\phi*{it}\sum*{j\ne i}w*{ji}Y\_{j,t-1}.
\]

Os termos representam contribuição endêmica, autorregressiva e de outras
regiões. **Não equivalem a uma classificação individual observada de casos
locais e importados.** A defasagem mensal tampouco é automaticamente um
intervalo de geração. [Artigo](https://doi.org/10.18637/jss.v077.i11);
[manuscrito integral](https://arxiv.org/pdf/1411.0416).

Minha avaliação: para explicar e prever os dados agregados atuais, essa
família é um antecedente mais próximo que GANF. Para recuperar acoplamento
do simulador SIR, continuam relevantes métodos mecanísticos e estudos de
identificabilidade. As duas perguntas não devem ser confundidas.

## Continuidade recomendada

1. Incorporar estes trabalhos à fundamentação brasileira e explicitar a
   geografia de notificação da resposta observada.
2. Documentar a origem e deduplicação dos agregados atuais e o crosswalk
   municipal/regional no tempo.
3. Para uma futura F de treino, obter uma tabela autorizada contendo
   `município_infecção,município_notificação,ano,mês,n`, com dados reais e
   documentação da extração. As marginais públicas não a substituem.
4. Definir separadamente um estudo descritivo A versus F e um estudo
   prospectivo de previsão/detecção com pesos geográficos ou derivados de F.
   Redes dirigidas/ponderadas exigem controles compatíveis.
5. Avaliar hhh4 como alternativa estatística de contagens e GANF como
   alternativa de detecção, com ablações para atribuir eventual ganho.
6. Separar no simulador a propagação latente da redistribuição de observações
   entre local de aquisição e de notificação, se essa extensão for escolhida.

Esses são encaminhamentos de pesquisa. [AGENTS.md](../../AGENTS.md) mantém
mobilidade M, hhh4 completo e GNN/GANF fora da implementação L0 sem pedido
explícito; esta revisão não altera gates, perfil ou resultados históricos.
