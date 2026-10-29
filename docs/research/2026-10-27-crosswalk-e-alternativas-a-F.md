# Regiões de saúde históricas e alternativas à rede F

Pesquisa e diagnóstico descritivo em 27/10/2026, na branch
`docs/castro-data-provenance`. Complementa o
[dossiê de proveniência](2026-10-27-adocao-castro-proveniencia.md). A
pesquisa encontrou uma fonte primária para a composição de 2013 e uma
divergência que muda uma aresta em um cenário geométrico de sensibilidade.
Ela não autoriza mudar o grafo histórico ou executar um novo protocolo.

## 1. O que significa comprovar o mapeamento

Há três perguntas distintas:

1. **Administrativa:** qual região abrangia cada município na data relevante?
   É necessária a norma estadual, seu anexo e eventuais alterações, com
   vigência por data e identificadores IBGE, não apenas nomes de regiões.
2. **Geográfica:** a atribuição municipal é consistente com as geometrias de
   DataSUS/geobr escolhidas? O teste de um ponto por município é um indício,
   não prova de cobertura integral ou de que o polígono é homologado.
3. **Série L0:** a agregação que gerou `notification.hr` usou qual versão do
   crosswalk, e aplicou-a retrospectivamente ou na data da notificação?
   Mesmo uma fonte normativa perfeita não responde a essa pergunta upstream.

O [CSV comparativo](2026-10-27-comparacao-anexo-cib90-geometria.csv) contém
os 144 nomes do anexo 2013 associados a códigos municipais 2013 e à região
do ponto representativo da malha IBGE no polígono regional P4. É **triagem
provisória**, não crosswalk administrativo homologado. SHA-256 do CSV:
`e5d618826c7ca58438c6c5f17a478a7e12a653b80973918cca9a9ab10893933b`.

## 2. Atos oficiais encontrados

| Fonte primária | Conteúdo e alcance | Limite |
| --- | --- | --- |
| [CIB/PA nº 83/2012, DOE de 20/04/2012](https://www.ioepa.com.br/pages/2012/2012.04.20.DOE.pdf), PDF p. 70 em diante | Regionalização e anexo de municípios; vigência na publicação | Há alteração posterior nº 237/2012 a examinar; não representa todo 2012 nem 2009–2011. |
| [CIB/PA nº 90/2013, DOE de 21/06/2013](https://www.ioepa.com.br/diarios/2013/06/21/2013.06.21.DOE_0.pdf), PDF pp. 36–37 | Anexo por município e região; vigência na publicação; revoga 83 e 237/2012; menciona instalação de Mojuí dos Campos em 01/01/2013 | O ato traz o lapso textual `13 (doze)`; comparar com as 13 seções do anexo. Não prova validade antes de 21/06 nem ausência de mudança posterior. |
| [Regimento da CIR Tocantins, DOE 15/07/2013](https://ioepa.com.br/pages/2013/2013.07.15.DOE.pdf) | Lista Tailândia entre os municípios da CIR Tocantins | Conflita com o anexo CIB 90; verificar natureza, autoridade, eventual retificação e vigência. |
| [CIB/PA nº 77/2024, DOE 23/05/2024](https://www.ioepa.com.br/pages/2024/2024.05.23.DOE.pdf), PDF p. 32 | Determina remanejamento de Tailândia de Lago de Tucuruí para Tocantins | Não prova a causa da geometria 2013 nem resolve automaticamente conflitos de 2013. |
| [DOE 21/10/2011](https://www.ioepa.com.br/pages/2011/2011.10.21.DOE.pdf) | Referencia a CIB 215/2010 e 23 regiões | Ainda falta localizar o anexo e os atos necessários para 2009–2011. |

O próprio ato de 2013 demonstra que mudanças ocorreram dentro do treino.
Não é defensável atribuir o desenho de 2013 a todos os meses como se fosse a
regionalização administrativa de cada mês. Isso não impede, em princípio,
uma **retabulação retrospectiva para uma geografia fixa**: trata-se de outra
estimanda, que exige dizer qual mapa foi escolhido e como foram tratados os
municípios alterados. A concordância com a série L0 ainda é desconhecida.

### Divergência de Tailândia

Na comparação automatizada, **143/144 municípios** receberam a mesma região
na extração do anexo da CIB 90 e no ponto representativo sobre P4; Tailândia
(`1507953`) aparece em **Lago de Tucuruí** no anexo e em **Tocantins** na
geometria P4. Compararam-se nomes normalizados por acentos/pontuação e duas
equivalências explícitas: `Eldorado dos Carajás` → `Eldorado do Carajás` e
`Santa Isabel do Pará` → `Santa Izabel do Pará`. Sem correspondência restante
ou duplicidade entre os 144 nomes extraídos. A transcrição automatizada ainda
precisa de conferência independente linha a linha com o PDF original.

O DOE de julho de 2013 citado acima lista Tailândia em Tocantins; uma
[resolução de financiamento de novembro de 2013](https://www.ioepa.com.br/pages/2013/2013.11.22.DOE.pdf)
volta a referi-la em Lago. Essa divergência impede escolher a versão correta
por mera suposição. Região de saúde e centro regional administrativo CRS
são conceitos distintos.

### Sensibilidade do grafo, não correção homologada

Com a malha municipal [IBGE 2013](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2013/PA/pa_municipios.zip)
e a geometria regional P4 arquivada, ambos EPSG:4674, associaram-se pontos
representativos por `within`, dissolveram-se os 144 polígonos por região e
calculou-se Queen com `libpysal`. O cenário que preserva a atribuição espacial
P4 reproduziu exatamente as **25 arestas** da `adjacency.npy` arquivada.
Alterando apenas a atribuição de Tailândia para Lago, antes da dissolução,
o cenário teve **26 arestas**: acrescentou Lago de Tucuruí–Metropolitana II,
sem remover arestas. Os 144 polígonos municipais e os 13 dissolvidos foram
válidos na execução. Uma revisão independente reexecutou o cálculo.

Este resultado mostra que a escolha territorial pode afetar A; não prova que
o contrafactual seja a geometria oficialmente correta, nem estima impacto em
lead time, FAR ou gates. A reconstrução usou a malha municipal IBGE e não
reproduziu todos os passos de preparação das fontes P4. Não foram gerados
novos placebos nem alterados artefatos oficiais.

Identificação das fontes lidas em `/tmp/headd-castro-20261027`: PDF original
CIB 90 SHA-256 `043db6ec47ba7283c3e5fe918bd923616efde05c9f4789c779e86a884c979cf7`;
malha IBGE ZIP `db318af3a1bbf52cff3df64706e69a606fe85689666e0f35d0132b518c4c065e`;
`source_regions.parquet` P4 `23a7351587d7ba40c45f05a40b221b9cac17fb62d358a507f2428ad24d7c342a`.
O texto do anexo foi obtido pela extração de texto do buscador e conferido
na fonte para a linha divergente; o PDF foi baixado e seu texto extraído com
`mutool draw -F txt ... 36-37`. Os scripts temporários de comparação e
sensibilidade estão em `/tmp/headd-castro-20261027/compare_annex.py` e
`graph_sensitivity.py`; `/tmp` é transitório. O CSV preserva o resultado
intermediário, não substitui a conferência dos atos.

Para reproduzir a sensibilidade enquanto os arquivos identificados estiverem
disponíveis, executar o trecho a seguir a partir do worktree no ambiente
Python do projeto. Ele constrói os cenários a partir das geometrias, lê o CSV
apenas para resumir a comparação e não grava nenhum artefato:

```python
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from libpysal.weights import Queen
from headd_l0.data import LEAVES
from headd_l0.graph_io import PA_HEALTH_REGIONS_2013

root = Path('/home/vinvs/projects/net-sci-epi')
archive = root / '.worktrees/_archive/2026-10-23/second-execution/data/processed/graph'
municipios = gpd.read_file('zip:///tmp/headd-castro-20261027/pa_municipios_2013.zip')
regioes = gpd.read_parquet(archive / 'source_regions.parquet')
assert municipios.crs.to_epsg() == regioes.crs.to_epsg() == 4674
pontos = municipios.copy()
pontos.geometry = pontos.geometry.representative_point()
join = gpd.sjoin(pontos, regioes[['code_health_region', 'geometry']],
                 how='left', predicate='within')
assert len(join) == 144 and not join.index.duplicated().any()
assert join.code_health_region.notna().all() and municipios.geometry.is_valid.all()
municipios['region'] = join.code_health_region.astype(int)
order = [next(code for code, name in PA_HEALTH_REGIONS_2013.items() if name == label)
         for label in LEAVES]

def queen(frame):
    dissolved = frame.dissolve(by='region').loc[order]
    assert len(dissolved) == 13 and dissolved.geometry.is_valid.all()
    return Queen.from_dataframe(dissolved, use_index=True, silence_warnings=True).full()[0]

base = queen(municipios)
assert np.array_equal(base, np.load(archive / 'adjacency.npy', allow_pickle=False))
municipios.loc[municipios.CD_GEOCMU == '1507953', 'region'] = 15004
candidate = queen(municipios)
print('arestas base/candidato:', int(base.sum() // 2), int(candidate.sum() // 2))
print('arestas acrescentadas:', [(LEAVES[i], LEAVES[j])
      for i in range(13) for j in range(i + 1, 13)
      if candidate[i, j] and not base[i, j]])
print('arestas removidas:', [(LEAVES[i], LEAVES[j])
      for i in range(13) for j in range(i + 1, 13)
      if base[i, j] and not candidate[i, j]])
comparison = pd.read_csv('docs/research/2026-10-27-comparacao-anexo-cib90-geometria.csv')
print('comparação:', len(comparison), comparison.concorda.value_counts().to_dict())
```

## 3. Fontes para os dados e o que elas realmente resolvem

| Fonte | Aberta e função | Lacuna |
| --- | --- | --- |
| [Zenodo SIVEP v2, 2004–2024](https://zenodo.org/records/20706957) | CC BY 4.0; Parquet 2013 com códigos de infecção/notificação e data conferidos | Anos 2009–2012, completude, deduplicação, vintage e comparação com L0 ainda requerem auditoria. |
| [Mendeley v2, 2003–2022](https://data.mendeley.com/datasets/9n6b97fsbd/2) | CC BY 4.0; série municipal diária para confrontar marginais | [Descrição dos autores](https://link.springer.com/article/10.1186/s12879-025-11193-x) apresenta município de notificação, resultado e contagem, não par OD. Sem prova de disponibilidade operacional em 2013. |
| [Arisco/Peterka/Castro 2024](https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0003452) | Descreve como construir redes mensais com registros SIVEP/SINAN desidentificados | Seus filtros e universo diferem do L0; os dados públicos dos repositórios auditados não fornecem a OD mensal completa. |
| [IBGE e DataSUS/geobr](https://github.com/ipea/geobr) | Geometrias e códigos para correspondência; fonte geobr lista regiões 2005 e 2013 | Não substituem atos por vigência nem esclarecem upstream. |
| [OpenDataSUS regiões de saúde](https://dadosabertos.saude.gov.br/dataset/macrorregiao-de-saude/resource/3ef05b19-e31f-41fc-b7e1-6e80b8e2d788) | API pública, candidato a conferência administrativa | Metadados de 2024 não demonstram snapshots de 2009–2013. |
| [CNES/TabNet](https://wiki.saude.gov.br/cnes/index.php/Portal_CNES) | Série por competência pode ajudar como evidência suplementar | Competência histórica não prova versão histórica da dimensão regional; download de base citado no portal começa em 06/2017. |
| [REGIC](https://geoftp.ibge.gov.br/organizacao_do_territorio/divisao_regional/regioes_de_influencia_das_cidades/Regioes_de_influencia_das_cidades_2018_Resultados_definitivos/base_tabular/) | Tabelas públicas de ligações urbanas e serviços | Publicação posterior à avaliação 2014–2019; não é fluxo SIVEP nem disponível operacionalmente então. |

Os dados das duas publicações SIVEP derivam da vigilância e não constituem
validação independente da transmissão. Uma reconstrução da série e outra de
F podem compartilhar erros de cobertura e revisões. Vintages preservados,
datas de processamento e alterações territoriais seriam necessários para
afirmar uma avaliação operacional da época.

## 4. Como concluir a comprovação

1. **Até 28/10:** transcrever o anexo da CIB 90 por código IBGE, revisar os
   144 pares contra o PDF e localizar texto/retificações da CIB 237/2012,
   CIB 215/2010 e demais atos de 2009–2013. Criar tabela de intervalos
   `[início, fim)` com fonte, vigência, município, região e conflitos.
2. Investigar o regimento CIR de julho e a CIB 77/2024, confirmando autoridade
   e eventual retificação em fonte primária. Enquanto permanecer conflito,
   manter Tailândia como ambígua; fazer sensibilidade documentada.
3. Comparar a tabela normativa com a geometria, testar municípios sem
   correspondência ou duplicados e auditar fronteiras e geometrias completas.
   Comparar os dois grafos, graus, conectividade, W e novos placebos sob
   protocolo separado; não substituir o A histórico no lugar.
4. Rastrear a transformação upstream dos CSVs para saber se o mapeamento é
   dinâmico ou fixo. Se isso não for obtido, produzir comparação de totais
   com diferenças e limites, não afirmar que a série foi reconstruída.
5. Se a decisão for um novo estudo retrospectivo com geografia fixa, fixar
   prospectivamente a geografia, as regras para municípios criados/mudados,
   resultado e deduplicação; então auditar os arquivos 2009–2012, incluindo
   município de origem/destino, valores ausentes e conservação dos fluxos.
   A nova hipótese não prova disponibilidade operacional histórica.

O prazo de 30/10 favorece evidência documental e uma decisão de escopo,
não promessa de resolver conflitos administrativos ou executar a bancada.
Pedidos a SESPA/DATASUS ou autores poderiam esclarecer lacunas, mas nenhum
contato foi feito.

## 5. Alternativa de complexidade equivalente sem F

**Recomendação para estudo separado: kernel de distância topológica sobre A.**
Para regiões distintas, calcule a distância mínima em arestas `d_A(i,j)` e
use `K_ij ∝ d_A(i,j)^(-α)`, `K_ii=0`, normalizando cada linha. Para pesos
decrescentes, fixar prospectivamente um expoente finito `α > 0`; A é conexo,
mas uma implementação deve
rejeitar nós sem caminho ou linha sem massa. A família de pesos por ordem
de vizinhança tem antecedente explícito em
[Meyer e Held (2014)](https://arxiv.org/abs/1308.5115).

Usa as 13 séries, A e o simulador já existentes, e permite estudar o alcance
de dependências, inclusive além dos vizinhos imediatos. **K não é uma rede
de deslocamentos, F observada, nem recuperação da matriz causal SIR.** Em
termos científicos, mantém uma hipótese espacial e uma comparação com
placebos; em termos de dados e parâmetros é mais simples que estimar F ou
uma matriz livre. Portanto não há equivalência de informação empírica.

Para A conexo, K atribui peso positivo a todos os pares distintos: K é denso.
A comparação A versus K altera ao mesmo tempo o alcance e os pesos; não
identifica isoladamente qual dessas escolhas produz uma eventual diferença.

Estudo proposto, não executado: definir separadamente cenários em que o
gerador usa A ou K e detectores recebem A, K ou seus placebos transformados
da mesma maneira; usar réplicas pareadas e explicitar condições oráculo em
que gerador e detector compartilham o grafo. Gerar/calibrar nulos para cada
cenário, congelar limiares e comparar apenas com FAR equivalente e avaliação
separada; medir lead time restrito, cobertura de onset e incerteza. Placebos
preservam graus e conectividade do grafo-base, não distribuição de distância
geográfica nem amostragem uniforme; os graus esparsos são preservados apenas
no grafo-base, pois K torna os placebos densos. Tempo, seeds, número de réplicas e
critérios precisariam ser pré-fixados em novo desenho; smoke não é evidência
de desempenho. A adjudicação da divergência de Tailândia deve preceder a
escolha do A de referência ou entrar como sensibilidade pré-especificada.

Outras opções respondem a perguntas diferentes:

- **hhh4 espacial:** decomposição endêmica, autorregressiva e espacial para
  previsão de contagens, com posterior calibração de alarmes. O modelo
  completo está fora de L0 e precisaria de nova autorização e protocolo;
  não estima automaticamente fluxo ou transmissão individual. [Held et al.](https://doi.org/10.1191/1471082X05st098oa).
- **Rede de dependência regularizada:** inferir dependências defasadas ou
  condicionais no treino e congelar antes da avaliação. Com 13 regiões e
  60 meses, uma matriz VAR de uma defasagem tem 169 coeficientes antes de
  sazonalidade e interceptos; regularização, teste de estabilidade e
  validação cronológica são essenciais. Dependência não equivale a fluxo ou
  transmissão; sinais negativos não são automaticamente pesos SIR válidos.
  [Graphical lasso](https://pmc.ncbi.nlm.nih.gov/articles/PMC3019769/).
- **Recuperação mecanística em simulação:** estimar ε ou outro parâmetro
  sob hipóteses fixas, verificando viés, cobertura e falhas entre réplicas.
  É estudo de identificabilidade, não baseline de detecção; não supor que
  boa previsão implica recuperar a rede ou parâmetros reais. [Tuncer e Le](https://pubmed.ncbi.nlm.nih.gov/29477671/).

O perfil P5/G4, falhas E0*/FAR, requisitos das camadas e estado inconclusivo
de RQ1′ permanecem os documentados no [protocolo](../protocol-decisions.md).
O estudo com K não está ratificado por G4 e não substitui F na hipótese sobre
mobilidade empírica. Não foi solicitada nem feita implementação de M, hhh4,
GANF ou novo experimento nesta pesquisa.
