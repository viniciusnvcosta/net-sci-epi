# Reconstrução geográfica para L0 e relação entre kernel e GANF

Investigação de 27/10/2026. Complementa a [comparação de atos e grafos](2026-10-27-crosswalk-e-alternativas-a-F.md)
e o [dossiê de dados](2026-10-27-adocao-castro-proveniencia.md). A análise
não substitui fontes, perfis ou resultados históricos.

**Atualização de 28/10:** a [auditoria do conjunto integrado fornecido](2026-10-28-auditoria-integrated-2009-2019.md)
encontrou concordância completa com o CSV L0 nos 7.592 grupos observados de
região × mês × resultado em 2009–2019, além de concordância município–região
com as tabelas fornecidas em todos os registros de notificação de PA. Isso
reforça o candidato Lago para alinhar a geografia à série fixa, sem provar a
vigência administrativa mensal ou a cadeia exata de produção do CSV L0.

**Atualização da evidência, 27/10:** a [reagregação independente de 2013](2026-10-27-auditoria-reagregacao-2013.md)
reproduziu 1.560/1.560 células região × mês × resultado da série L0 com
Tailândia em Lago; com P4, foram 1.502/1.560. O candidato Lago tem, portanto,
melhor suporte de compatibilidade observacional para esse ano e essa extração.
Posteriormente, a [tabela territorial e o script fornecidos pelo usuário](2026-10-27-baroni-tabela-e-script.md)
indicaram Tailândia em Lago e concordância dos 144 pares de PA com o DATASUS
2023; o script descreve uma junção fixa sem chave temporal explícita. Sua
versão e vínculo efetivo com a geração da série L0 ainda não foram provados.
A tabela de nomes posteriormente fornecida produz um único nome por município
nessa junção e confirma `15004 → LAGO DE TUCURUI`.
O [rastreio posterior](2026-10-27-origem-serie-e-tabela-territorial.md)
confirma que o CSV de Eze publicado é idêntico ao CSV local, mas não identifica
a tabela histórica que gerou a série. A verificação posterior de 28/10 amplia
a compatibilidade observacional aos demais anos; ela não autoriza substituir A, alterar gates ou
inferir o desempenho do candidato. A referência P4 é preservada por ser a
usada historicamente; não por ter maior suporte de alinhamento em 2013.

## Decisão recomendada

Para a pergunta L0 existente, a geografia mais adequada é aquela que coincide
com a correspondência municipal efetivamente usada para construir a série
`notification.hr`. **Ela ainda não foi identificada com segurança.** Até
isso ocorrer, manter a A P4 arquivada como referência provisória e preservar
o cenário Tailândia→Lago como sensibilidade documentada. Não declarar nenhuma
delas a reconstrução ótima ou oficial de toda a série 2009–2019.

É uma decisão de continuidade técnica, não aprovação do gate G3. Soma exata
das 13 regiões a PA confirma coerência aritmética, não identifica os
municípios atribuídos a cada série. Resolver a composição é prioritário
porque altera A, W, graus/placebos e possivelmente os próprios dados.

## O que se esclareceu sobre Tailândia

1. A [CIB/PA nº 237/2012](https://ioepa.com.br/pages/2012/08/28/2012.08.28.DOE_50.pdf),
   publicada em 28/08/2012, alterou a CIB 83 para inserir Placas em Baixo
   Amazonas. O anexo lista Tailândia em Lago de Tucuruí. A fonte anterior
   havia sido identificada, mas esta alteração ainda não havia sido examinada.
2. A [CIB/PA nº 90/2013](https://www.ioepa.com.br/diarios/2013/06/21/2013.06.21.DOE_0.pdf),
   com vigência em 21/06, também a lista em Lago. O
   [regimento da CIR Tocantins de julho de 2013](https://ioepa.com.br/pages/2013/2013.07.15.DOE.pdf)
   lista Tailândia em Tocantins. São fontes oficiais de objetos administrativos
   diferentes; não se encontrou ato que resolva conclusivamente o conflito.
3. A [CIB/PA nº 77/2024](https://www.ioepa.com.br/pages/2024/2024.05.23.DOE.pdf)
   determina remanejamento de Lago para Tocantins. Uma [resolução CIR de 14/08/2024,
   publicada em 22/01/2025](https://ioepa.com.br/pages/2025/01/22/2025.01.22.DOE_20.pdf),
   altera seu regimento em referência à CIB 77. Isso não determina a causa
   da classificação na fonte geográfica de 2013 nem os dados usados em L0.

### Contexto da divergência entre CIR e regionalização

A [notícia institucional da CIES Pará de 07/11/2013](https://ciespara.wordpress.com/2013/11/07/organizacao-da-cies-chega-a-regiao-de-saude-tocantins/)
descreve nove municípios como integrantes da região Tocantins e Tailândia
como município de Lago que havia solicitado transferência para aderir à CIR
Tocantins. É uma descrição contemporânea de uma solicitação, não o ato que
decide sua vigência; não basta para explicar ou invalidar o regimento publicado
em julho de 2013. Ela reforça a necessidade de distinguir participação em
instâncias regionais, pedido de transferência e composição pactuada para a
série. A página foi consultada diretamente em 27/10/2026; o arquivo HTML da
listagem de novembro consultado teve SHA-256
`7a8e02bb39dfa97fa346ac2020b68345e3aa20af6d12ad3bd0cfaf35e43b9787`.

O texto da própria CIB 77/2024 também registra um pedido municipal de 2023
e resoluções das CIRs como antecedentes, antes de pactuar a alteração da
CIB 90 e fixar sua entrada em vigor na publicação. Isso é evidência adicional
de que solicitação, manifestação regional e pactuação estadual não devem ser
tratadas como eventos automaticamente equivalentes. A sequência não prova que
nada mais ocorreu entre 2013 e 2024 e não estabelece a versão territorial
usada por Baroni ou Eze. O conflito documental permanece aberto.

### A divergência já está no arquivo de origem geográfica

O `healthregions_2013.parquet` arquivado tem 144 registros municipais de PA.
O registro de Tailândia contém `code_muni=1507953`,
`code_health_region=15011`, `name_health_region=Tocantins`, `year=2013`.
Ao associar os 144 códigos ao [CSV da comparação com o anexo](2026-10-27-comparacao-anexo-cib90-geometria.csv),
todos foram encontrados e as regiões do atributo original concordaram com as
obtidas no teste espacial por pontos. Assim, **a atribuição a Tocantins já
existe nos atributos do GeoParquet**, antes da dissolução e Queen. Isso não
explica por que a fonte tem esse valor nem demonstra defeito no código local.

O [script de preparação geobr na tag v2.0.0](https://github.com/ipea/geobr_prep_data/blob/04a8304cf5bf8c82a1b454bda04908f0c3512246/R/health_region_before_2020.R)
oferece uma hipótese rastreável para essa atribuição: para anos anteriores a
2020, seu código prevê ler `br_regsaud.MAP` do pacote de mapas DATASUS do
ano, obter um ponto de superfície para cada município e fazer uma junção
espacial com as regiões; depois associa o resultado às geometrias municipais
e grava o GeoParquet. A tag aponta para o commit
`04a8304cf5bf8c82a1b454bda04908f0c3512246`; o script consultado tem SHA-256
`169784ac94f93117448ce6ee63673f1a720b0e4e992236cc67007d9bd75c1e4b`.
O código foi lido, não executado. Isso identifica o método previsto nessa
versão, mas não prova, sem reconstrução e conferência dos insumos, que o
arquivo P4 foi gerado exatamente por esse script nem se Tailândia já consta
em Tocantins no mapa DATASUS original ou houve efeito da junção espacial.
É uma atribuição geométrica potencial, não comprovação da tabela usada para
agregar notificações.

O [pacote de mapas DATASUS rotulado 2013](ftp://ftp.datasus.gov.br/territorio/mapas/br_mapas_2013.zip)
foi obtido em 27/10/2026, SHA-256
`23de96702b70b264ed8ebe4f0a0c79872e13a91fc1e2a8ce471e5c1e83abc886`.
Ele contém `br_regsaud.MAP` e `br_regsaude.MAP`, ambos com data interna ZIP
15/04/2025; o script seleciona o primeiro. Esses metadados não provam quais
bytes foram utilizados na construção do artefato P4 nem a vigência do mapa.

Uma decodificação exploratória independente de `br_regsaud.MAP`, SHA-256
`9177f36d8f1b9225d3942fd950addeec158d326789d59b12b337349d5fda6d98`,
encontrou o ponto de superfície de Tailândia no polígono `15011` Tocantins.
Os 144 pontos da malha municipal 2013 de PA tiveram uma região única e
concordaram com os 144 atributos de P4. A malha municipal ZIP usada tem
SHA-256 `db318af3a1bbf52cff3df64706e69a606fe85689666e0f35d0132b518c4c065e`.
O [script exploratório](2026-10-27-verificar-mapa-datasus.py) está registrado
para reprodução com esses arquivos em `/tmp/headd-castro-20261027` e o
GeoParquet P4 arquivado. Ele interpreta o formato conforme o leitor geobr,
trata anéis como polígonos independentes e usa `covers` com `make_valid`;
não é uma reprodução bit a bit de DuckSpatial ou da limpeza geobr. O
resultado apoia a origem da atribuição no mapa consultado, mas não prova
que essa versão do `.MAP` foi o insumo do P4, nem a validade normativa ou
a correspondência com a série de notificações.

Na mesma leitura exploratória, a interseção do polígono municipal de
Tailândia com o polígono DATASUS de Tocantins cobre aproximadamente **99,41%**
da área municipal; com Lago de Tucuruí, **0%**. A área foi calculada após
projeção EPSG:5880, com `make_valid` e união dos anéis interpretados como
polígonos independentes. As malhas são distintas e esse leitor não preserva
eventuais buracos; a diferença residual não identifica, por si, erro de
limites. Esse resultado oferece suporte espacial além do ponto representativo,
mas mantém as mesmas limitações de versão, vigência e linhagem acima.

**Divergência dentro do próprio pacote DATASUS:** o segundo arquivo,
`br_regsaude.MAP`, SHA-256
`e0e2d67afef7cf6f881c662025539885534cbd76391a84bb5e78f41e741fcab9`,
foi submetido à mesma leitura exploratória e aos mesmos 144 pontos. Nele,
todos têm correspondência única, mas Tailândia é a única divergência em
relação a P4: o ponto está em Lago (`15004`), enquanto no primeiro mapa está
em Tocantins (`15011`). O polígono municipal sobrepõe aproximadamente
99,10% de Lago e 0,31% de Tocantins nesse segundo mapa, com as mesmas
ressalvas sobre projeção, anéis e diferenças de malhas. Os dois arquivos
estão no mesmo ZIP e não constituem fontes independentes. Ainda não sabemos
por que há dois mapas, sua finalidade específica ou qual deles teria
vigência para o estudo. O script geobr da tag examinada seleciona
`br_regsaud.MAP`, não `br_regsaude.MAP`.

Para reproduzir a comparação, executar o script exploratório com argumento
`br_regsaud.MAP` e novamente com `br_regsaude.MAP`; o argumento ausente usa
o primeiro. Essa divergência cartográfica explica uma possibilidade concreta
para as representações opostas, mas não demonstra que qualquer mapa produziu
os dados de Eze nem resolve o conflito normativo.

**Outro pacote territorial com data interna anterior:** o catálogo público
DATASUS também lista [mrno_mapas_2013.zip](ftp://ftp.datasus.gov.br/territorio/mapas/mrno_mapas_2013.zip),
SHA-256 `f0037099633c6aec3d79efc1a617b4667889eefcfda565b2c2f6c65690785085`,
cujo membro `mrno_regsaud.MAP` tem data interna ZIP 27/05/2016 14:12 e
SHA-256 `2a47a5ab51bfc35136b09be30cb88e35b71fa1d393a0fb562c88cd3d91c35b33`.
Na mesma leitura exploratória dos 144 pontos, o mapa Norte diverge do P4
somente em Tailândia, atribuída a Lago. As sobreposições aproximadas da área
municipal são 99,74% com Lago e 0,09% com Tocantins, sujeitas às limitações
do leitor e das malhas já expostas. A comparação pode ser reproduzida com
o argumento `mrno_regsaud.MAP` no script. A data interna e a data da listagem
não provam que esses bytes existiam em 2016 nem a vigência jurídica do mapa;
trata-se de nova evidência cartográfica coerente com Lago, não da tabela de
agregação de Baroni/Eze e não de prova para toda a série 2009–2019.

Fonte P4: `healthregions_2013.parquet`, SHA-256
`42de74c7506a5ce52b46ba4d5abdde6b321eebf649b09c08f641fc2e56d8918e`;
13 regiões agregadas, 25 arestas. Fonte/código e processamento em
[development.md](../development.md#grafo-regional-p4).

### Tabela territorial DATASUS de 2023

Em 27/10, a listagem pública `ftp://ftp.datasus.gov.br/territorio/tabelas/`
mostrou diretórios 2023, 2024, 2025 e 2026; essa consulta não demonstrou
arquivos de 2009–2013 no catálogo listado. Foi obtido
`ftp://ftp.datasus.gov.br/territorio/tabelas/2023/base_territorial_2023.zip`,
SHA-256 `798be2f62a53dd1af8e335a44a1916154f36ee3a3051a7375864a74ef47c3bc4`.
Sua `rl_municip_regsaud.csv` contém 144 códigos PA únicos e classifica
`150795` em `15004` (Lago). Em comparação por código com o GeoParquet P4,
**143/144 concordam e só Tailândia difere**. Com o anexo CIB 90 extraído e
o mapeamento de nomes/códigos P4, **144/144 concordam**, sujeito à revisão
manual do anexo já indicada no relatório anterior.

A tabela é um snapshot de 2023, não prova que o DATASUS usou essa mesma
classificação para os registros 2009–2019 ou para a base Baroni de 2020.
O arquivo `tb_regsaud.csv` inclui códigos repetidos; associação deve usar
critérios de status/versão verificados, não uma junção supostamente única.
Nesta comparação dos 144 pares, os códigos regionais foram traduzidos pela
tabela canônica `PA_HEALTH_REGIONS_2013` do projeto.

O resultado pode ser refeito com os arquivos identificados acima, a partir da
raiz do worktree e com o Python do projeto. O ZIP baixado reside em `/tmp`;
deve ser novamente obtido e conferido pelo hash caso desapareça.

```python
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from headd_l0.graph_io import PA_HEALTH_REGIONS_2013

root = Path('/home/vinvs/projects/net-sci-epi')
geo = root / '.worktrees/_archive/2026-10-23/second-execution/data/processed/graph/healthregions_2013.parquet'
g = pd.read_parquet(geo, columns=['code_muni6', 'code_health_region', 'abbrev_state'])
g = g[g.abbrev_state == 'PA'].copy()
g['mun6'] = g.code_muni6.astype(int).astype(str)
g['regiao_p4'] = g.code_health_region.astype(int)
with ZipFile('/tmp/headd-castro-20261027/base_territorial_2023.zip') as z:
    r = pd.read_csv(z.open('rl_municip_regsaud.csv'), dtype=str, encoding='latin1')
r = r[r.CO_MUNICIP.str.startswith('15')].copy()
c = pd.read_csv('docs/research/2026-10-27-comparacao-anexo-cib90-geometria.csv',
                dtype={'codigo_ibge_2013': str})
c['mun6'] = c.codigo_ibge_2013.str[:6]
j = c.merge(g, on='mun6', validate='one_to_one', how='outer', indicator=True)
assert len(j) == 144 and j['_merge'].eq('both').all()
j = j.drop(columns='_merge').merge(r, left_on='mun6', right_on='CO_MUNICIP',
                                    validate='one_to_one', how='outer', indicator=True)
assert len(j) == 144 and j['_merge'].eq('both').all()
j['regiao_2023'] = j.CO_REGSAUD.astype(int).map(PA_HEALTH_REGIONS_2013)
assert j.regiao_2023.notna().all()
print('anexo CIB90 versus DATASUS 2023 divergências:',
      (j.regiao_cib90_2013 != j.regiao_2023).sum())
print('P4 versus DATASUS 2023 divergências:',
      (j.regiao_p4 != j.CO_REGSAUD.astype(int)).sum())
print(j.loc[j.regiao_p4 != j.CO_REGSAUD.astype(int),
            ['codigo_ibge_2013', 'regiao_p4', 'CO_REGSAUD']].to_string(index=False))
```

## A pista mais direta para a série L0: Baroni et al.

**Atualização:** a relação, o script e a tabela de nomes foram fornecidos pelo usuário e
examinados na [auditoria dos arquivos](2026-10-27-baroni-tabela-e-script.md).
Os registros de HTTP 403 abaixo descrevem a consulta anônima anterior, não a
disponibilidade dos arquivos agora recebidos. As tabelas foram comparadas; o
vínculo exato das versões com a série ainda não foi verificado.

O README do repositório CDADE original atribui sua série SIVEP a Baroni et
al., mas não comprova os bytes e processamento que geraram o CSV local.
O [artigo de Baroni et al. (2020)](https://link.springer.com/article/10.1186/s13104-020-05109-y)
descreve explicitamente o enriquecimento de `notification.hr`, `infection.hr`
e `home.hr` por `rl_municip_regsaud` e `tb_regsaud` do DATASUS. Identifica
como artefatos:

| Artefato Synapse | ID | Metadados acessados anonimamente em 27/10 | Conteúdo |
| --- | --- | --- | --- |
| relação município–região | `syn21552452` | versão 1; criado 28/01/2020 | download anônimo HTTP 403 |
| regiões | `syn21552453` | versão 1; criado 28/01/2020 | download anônimo HTTP 403 |
| script de integração R | `syn21555551` | versão 4; modificado 17/04/2020 | download anônimo HTTP 403 |
| documentação integrada | `syn21585580` | versão 4; modificado 23/04/2020 | download anônimo HTTP 403 |

A API de metadados respondeu HTTP 200, mas a rota de download retornou
`Anonymous users have only READ access permission`. O artigo descreve os
dados como abertos; nesta consulta não houve acesso anônimo ao conteúdo.
Não foi feita tentativa de usar credenciais ou executar o script de terceiros.
Os links de cada artefato estão na [tabela do artigo](https://pmc.ncbi.nlm.nih.gov/articles/PMC7271548/).

Se for possível obter as duas pequenas tabelas e o script por acesso regular,
registrar versão, hash e licença, ler o script sem executá-lo, extrair a
regra de join e comparar os 144 códigos com o anexo, DATASUS 2023 e P4.
Verificar Tailândia especificamente e se existe variável de vigência. Se a
tabela usada por Baroni for fixa, ela identifica o agrupamento do *dataset*
integrado, não a regionalização vigente em cada mês. Ainda será necessário
estabelecer que a mesma versão e os mesmos filtros produziram os CSVs L0;
comparar 13×132 totais é evidência adicional, não garantia isolada de linhagem.

## Estratégia de reconstrução com os dados atuais

| Cenário | Ação e interpretação | Condição |
| --- | --- | --- |
| Correspondência Baroni comprovadamente igual a P4 | Manter A P4, comparar à norma como limitação e registrar vigência fixa dos dados | Provar versão, join, universo e vínculo com os CSVs L0. |
| Correspondência Baroni igual à CIB 90/2023, inclusive Tailândia em Lago | Preparar candidato A pela composição correspondente, comparar com P4 e revisar antes de eventual nova execução | Verificar 144 pares, fonte, limites e atribuições conflitantes; exige novos artefatos e decisão científica. |
| Correspondência Baroni diferente das duas ou desconhecida | Não declarar alinhamento. Preservar P4 e resultados; concluir diagnóstico descritivo | Aguardar evidência adicional ou desenhar estudo próprio. |
| Geografia administrativa variável no tempo | Reconstruir séries municipais por vigência, mudança territorial e data; gerar S/A por período | Dados municipais e protocolo novos. Não se consegue redistribuir município a partir de 13 totais agregados. |

Se a resolução CIB 90 for escolhida como referência retrospectiva para um
**novo estudo**, os 144 pares triados e o snapshot 2023 fornecem duas fontes
convergentes, mas a transcrição, o conflito CIR e a linhagem da série ainda
exigem revisão. Selecionar CIB 90 por conformidade normativa não demonstra
que as contagens existentes foram agregadas com esse mapa.

Alterar Tailândia muda, no cálculo exploratório anterior, A de 25 para 26
arestas (+ Lago de Tucuruí–Metropolitana II). Os graus passam de 5 para 6
em Lago e de 4 para 5 em Metropolitana II; mudam as linhas correspondentes
de W normalizada.
Há que regenerar placebos com os novos graus, verificar topologia, atualizar
features e distinguir a A de geração da A de detecção. Um novo gerador exige
novos nulos e calibração; não há evidência de alteração em FAR ou lead time.
Não editar cache/manifest histórico nem presumir que a validação G4 aprova
qualquer perfil alterado. Falhas E0*/FAR, G3 pendente e camadas incompletas
continuam regendo a interpretação.

## Otimizar um kernel é GANF?

**Existe uma semelhança de objetivo geral:** ambos podem aprender uma estrutura
relacional a partir de dados. O que é otimizado e o significado da matriz,
porém, dependem do modelo e da função de perda escolhidos.

### Kernel topológico ajustado

Com A conexa e `d(i,j)` igual à distância em número de arestas em A, uma família seria

\[
K_{ij}(\alpha)=\frac{d(i,j)^{-\alpha}}
 {\sum_{k\ne i}d(i,k)^{-\alpha}},\quad i\ne j;\qquad K_{ii}=0,\quad\alpha>0.
\]

`α` pode ser fixado antecipadamente ou ajustado **somente dentro do treino**
por um critério previamente escolhido, por exemplo verossimilhança preditiva
de contagens em validação temporal interna. Isso estima um parâmetro de uma
família restrita, não uma matriz livre. Se o objetivo for detecção de surtos,
ótimo em previsão não equivale automaticamente a maior lead time nem a FAR
adequada; calibração e avaliação permanecem separadas.

`K` é um peso relativo de vizinhos com linha somando 1; não é uma densidade
de probabilidade dos dados e não é F observada. Uma transformação `α·A`
seguida de normalização por linha não ajusta nada para `α>0`: o fator cancela.
Por sua vez, a família de distâncias muda pesos relativos e alcance. Ela é
densa num grafo conexo; A→K altera simultaneamente alcance e pesos.

### GANF

O [GANF de Dai e Chen (2022)](https://arxiv.org/html/2202.07857) aprende
conjuntamente uma matriz de dependência dirigida `B` e parâmetros `θ` de um
normalizing flow, maximizando verossimilhança das séries com restrição de
aciclidade. O score de anomalia deriva da densidade estimada. Sua restrição
teórica é `tr(exp(B ∘ B)) − n = 0`; o algoritmo numérico pode terminar com
tolerância finita. O código usa uma RNN, agregação por grafo e flow condicional.
Não otimiza diretamente β, ε, R0, recuperação de arestas SIR ou lead time.

Em especial, o kernel sobre A é simétrico antes da normalização e representa
interação recíproca; como um grafo com ambas as direções contém ciclos de
comprimento dois, **não é diretamente um DAG GANF**. Em geral uma matriz
não negativa com diagonal zero, linhas todas somando 1 e número finito de
nós contém um ciclo dirigido: portanto, impor ao mesmo tempo esse contrato W
e DAG seria incompatível. Ciclos espaciais com defasagens podem ser
representados em um grafo expandido no tempo; isso é outro desenho, não a
equivalência automática do GANF original ao SIR.
Após normalização, o suporte permanece recíproco, mas `K_ij` e `K_ji` podem
ter valores diferentes por causa dos denominadores das linhas.

Os pais GANF podem incluir observações contemporâneas até t: um score em t
é possível se as entradas exigidas estiverem disponíveis em t; prever x(t)
antes de observá-las é outra tarefa. A convenção de índices do artigo e a
[implementação](https://raw.githubusercontent.com/EnyanDai/GANF/main/models/GANF.py)
precisam ser explicitadas ao comparar arestas: o código soma `h_k A_kj`
para o receptor j. Não interpretar direção ou intensidade aprendida como
transmissão identificada. O código calcula média das log-densidades por nó
e tempo, enquanto o artigo escreve soma; para janelas de tamanho diferente,
a escala dos scores não é diretamente a mesma.

### Viabilidade e comparação justa

Com 13 regiões, uma matriz dirigida sem diagonal tem 156 candidatos; um DAG
simples admite no máximo 78 arestas, além de todos os parâmetros neurais.
Com 60 meses de treino, janelas mensais inclusivas de comprimento L produzem
no máximo `61−L` janelas sobrepostas, não amostras independentes. Para L=12,
são 49 janelas. O [artigo](https://arxiv.org/html/2202.07857) usa sinais de
alta frequência e não demonstra desempenho nesse regime. A limitação aumenta
o risco de instabilidade, mas não prova impossibilidade.

O [loader oficial](https://raw.githubusercontent.com/EnyanDai/GANF/main/dataset.py)
padroniza antes da divisão e, no exemplo de tráfego, sobrepõe validação e
teste. São propriedades do código consultado, não requisitos do método;
uma avaliação L0 teria de ajustar escala apenas no treino e manter divisões
temporais e streams de calibração/avaliação separados.

Se o usuário decidir estudar GANF futuramente, pré-registrar o objetivo e
comparar, com mesmo universo e cortes, ao menos: detector sem relação;
mesmo detector com A e com K fixo/ajustado; e GANF como **baseline de modelo
diferente**. Um possível GANF com grafo fixado e um com DAG aprendido podem
ser ablações internas, respeitando a DAG e indicando o tratamento dos nós
sem pais. Para usar A como DAG fixo seria necessário escolher uma orientação
acíclica, que descarta a reciprocidade e não é ablação fiel de A simétrica.
Definir também como o flow contínuo trata contagens discretas e como se
comparam seus scores. Controlar sementes, seleção no treino, custo, orientação, score e
limiares a FAR igual. Nenhuma ablação transforma a dependência estimada em
ground truth SIR. Uma comparação entre GANF e CDADE altera modelo e grafo,
portanto não isola o efeito da informação relacional.

Kernel ajustado e GANF/GNN não foram implementados ou executados nesta
investigação. O GANF permanece fora do escopo de implementação L0 sem pedido
explícito, conforme [AGENTS.md](../../AGENTS.md); a pergunta sobre sua
relação conceitual não altera essa restrição.
