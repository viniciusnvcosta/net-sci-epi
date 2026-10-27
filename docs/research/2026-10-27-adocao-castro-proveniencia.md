# Dossiê de fontes: adoção Castro e viabilidade de OD

Auditoria de 27/10/2026 na branch `docs/castro-data-provenance`. Escopo e
critérios: [plano aprovado](../superpowers/plans/2026-10-27-fontes-castro-ate-30-10.md)
e [inventário de fontes](2026-10-27-requisitos-fontes-dados.md). Este é um
relato descritivo; não houve construção de F nem execução de experimento.

## Resultado da decisão

**F para o treino completo 2009–2013: indisponível para uso neste momento.**
O Zenodo disponibiliza dados reais e o arquivo 2013 foi conferido, mas não
foi demonstrado o mapeamento administrativo de cada ano para as 13 regiões,
nem a semântica que tornaria comparáveis os agregados SIVEP e a série L0.
São limites de validação, não prova de que os dados necessários inexistam.
Conforme o plano, não foram baixados 2009–2012 ou produzidas partições OD
para o treino completo. O fallback é a documentação da A já existente.

**D1 não aprovado:** o crosswalk histórico não foi demonstrado. **D2
suspenso** pela condição do plano. A [evidência P4](../development.md#grafo-regional-p4)
documenta A Queen com 13 regiões, 25 arestas e 30 placebos conexos que
preservam graus; G3 não está aprovado e não há alegação de amostragem
uniforme. Isso não representa uma nova execução ou comparação.

## D0 — dados locais e proveniência

Em `/home/vinvs/projects/net-sci-epi/data/raw/sivep` e
`/home/vinvs/projects/hybrid-theory/data/raw`, as cópias têm os seguintes
conteúdos e SHA-256 idênticos; contagem exclui cabeçalho:

| Arquivo | Linhas | Colunas | SHA-256 |
| --- | ---: | --- | --- |
| `PA.csv` | 132 | `Date`, `notification.year`, `notification.month`, `monthlyPrevalence`, `negatives`, `positives`, `totalTests` | `ba437eff83a537addcdda93aca09401d5033804b83a0b767baa55788267041f5` |
| `PASIVEPDailyPerHr.csv` | 7.592 | `notification.year`, `notification.month`, `notification.hr`, `exam.result`, `testperhr` | `ad61c77c8c187713cd47e72bb5f028eda1203e3f5e4962c5970d41abd9ae7188` |

[Loader](../../src/headd_l0/data.py): contagens regionais são soma de
`testperhr` com `exam.result != negative`; `tests` inclui negativos e PA é
validado contra a soma regional. Não há identificador, par municipal ou data
individual nesses CSVs. A equivalência com casos clínicos deduplicados e a
regra upstream de `notification.hr` não foram demonstradas.

O TOML `configs/data.toml` usa `../hybrid-theory/data/raw` relativo ao
diretório de execução. Esse caminho existe na raiz principal, mas **não**
na raiz deste worktree, pois resolveria para `.worktrees/hybrid-theory`.
Os CSVs locais também são ignorados e não foram copiados para o worktree.
A auditoria leu as origens por caminhos absolutos; não alterou o TOML.
Para reprodução futura é necessário ajustar uma cópia da configuração ao
caminho correto, mantendo os arquivos brutos somente leitura.

O fallback histórico designado `A2` não foi associado de forma comprovada
a um braço atual. O [README](../../README.md) descreve B1*, B2 e B2-placebo;
não se criou nem executou um novo braço chamado A2.

## D1 — fonte SIVEP e metadados

Fonte: [Zenodo v2, DOI 10.5281/zenodo.20706957](https://zenodo.org/records/20706957),
publicada em 15/06/2026; dados de processo LAI `25072.030306202615`.
Download em `/tmp/headd-castro-20261027`, sem copiar microdados ao repositório.
A primeira tentativa no sandbox falhou por DNS; a tentativa com acesso de rede
permitido obteve os arquivos. MD5 calculado coincide com o catálogo em todos
os quatro casos. SHA-256 calculado:

| Arquivo | MD5 publicado e confirmado | SHA-256 |
| --- | --- | --- |
| `sivep_malaria_2013.parquet` | `c34baeded21ba5f7b378961acfecbd7b` | `e14f03dcc996432103481dae6abd3d1122fd8d916deec8cf5685426b9bec07bf` |
| `sivep_malaria_full_methodology_description.md` | `20affbc91f0bc4d2d98fc99ac9319bb2` | `c7965886143ffe5b90c976d06a34d547d5f72aa35d2628b4e62fcbad6bbecad1` |
| `sivep_malaria_metadata_csv.zip` | `8904b47470b900cf7841f4fc2909e723` | `a2ff1d3f0d42d9ac8739894ca5238568fea68c64a098a4dffc87a377cd3dfbaa` |
| `DICIONÁRIO DE DADOS DO ARQUIVO NOTIFICAÇÃO v3.pdf` | `e0fc37eca9fd92007c26a7f0e7ce187f` | `90532251097d6217df3b073161909d3c733801ece55b46fbf80eaea916dcbc31` |

Tamanhos medidos em bytes, na ordem da tabela: 20.766.436, 3.667, 8.734 e
263.528. O esquema completo é consultável no Parquet; a lista abaixo contém
somente os campos essenciais à triagem, não todas as 66 colunas.

O dicionário PDF foi obtido e verificado, mas não foi extraído: `pdftotext`
não está instalado. O codebook CSV dentro do ZIP de metadados foi lido; ele
descreve `DT_NOTIF` como data de notificação e `RES_EXAM` como resultado.
O manifesto de 2013 registra 2.058.686 linhas, 66 colunas processadas,
42 colunas fonte e nenhuma coluna conhecida ausente. O Parquet confirmou
2.058.686 linhas e 66 colunas. O pipeline documenta que campos ausentes em
outros anos podem ser preenchidos como missing, devendo-se verificar cada ano.

Campos conferidos diretamente no Parquet: `dt_notif` (date32),
`dt_notif_year`/`dt_notif_month` (int32), `res_exam` (string),
`uf_notif_code`/`mun_noti_code` (int32), `uf_infec_code`/`mun_infe_code`
(int32). Os códigos preservam a geografia da fonte conforme o codebook.
Os códigos municipais preenchidos na amostra de positivos de PA têm seis
dígitos; o IBGE usa sete. Associar os seis primeiros dígitos exige validar
unicidade e códigos especiais, não apenas completar um dígito por suposição.
O campo `id_pacie` é descrito no codebook como idade do paciente; não é
um identificador de pessoa. Não foi encontrado identificador adequado para
comprovar deduplicação. Nenhum valor individual é exposto.

Como triagem, entre **327.982 registros** de UF de notificação PA em 2013,
**29.806** têm resultado preenchido diferente de `Negativo`. Destes, 532
(1,78%) não têm código de município de infecção; os mesmos 532 não têm UF
de infecção. Nos restantes, 28.892 têm UF de infecção codificada como PA e
382 têm outra UF preenchida. São contagens de registros por esses filtros,
não episódios deduplicados ou partições territoriais validadas. Não se
examinaram códigos inválidos por crosswalk administrativo, nem se inferiu que
origens desconhecidas equivalham a zero. Este recorte 2013 não é o treino
completo nem prova equivalência com o loader L0.

O depósito descreve licença CC BY 4.0 para dados; seu
[repositório de processamento](https://github.com/rfsaldanha/sivep_malaria)
declara GPL-3.0 para código. Uma extração em 2026 pode incorporar revisões:
não demonstra o conteúdo disponível operacionalmente em 2013.

## D1 — território e REGIC

Malha de municípios de PA: [IBGE 2013](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2013/PA/pa_municipios.zip),
SHA-256 `db318af3a1bbf52cff3df64706e69a606fe85689666e0f35d0132b518c4c065e`.
O [leia-me IBGE](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2013/1_Leia-me_Malha_2013_jul2015.pdf)
declara referência territorial em 01/07/2013. A geometria das 13 regiões é
o `source_regions.parquet` arquivado do P4, derivado de DataSUS/geobr 2013;
SHA-256 `23a7351587d7ba40c45f05a40b221b9cac17fb62d358a507f2428ad24d7c342a`;
ver [proveniência e hashes P4](../development.md#grafo-regional-p4).

Usando ponto representativo de cada polígono municipal, houve **144/144**
associações espaciais, nenhuma ausente ou duplicada; os 144 códigos do IBGE
são únicos tanto em sete dígitos como nos seis primeiros. Esta checagem é
um candidato geométrico para 2013, não uma tabela administrativa homologada
nem verificação de vigência 2009–2012. Não foram testadas alterações
territoriais ou eventuais inconsistências com `notification.hr` upstream.
A API atual [OpenDataSUS](https://dadosabertos.saude.gov.br/dataset/macrorregiao-de-saude/resource/3ef05b19-e31f-41fc-b7e1-6e80b8e2d788)
é fonte candidata adicional, mas sua página de metadados de 2024 não comprova
a composição histórica. A ligação espacial não estabelece por si só a
correspondência usada para gerar os CSVs L0.

Foi baixada a [tabela de ligações REGIC 2018](https://geoftp.ibge.gov.br/organizacao_do_territorio/divisao_regional/regioes_de_influencia_das_cidades/Regioes_de_influencia_das_cidades_2018_Resultados_definitivos/base_tabular/REGIC2018_Ligacoes_entre_Cidades.xlsx),
SHA-256 `be5644287ac0ad5c6772b342e2d574acbbd33eb2d34f8c8a8dc59ac4bf72a4eb`.
Seu dicionário define origem/destino como município ou núcleo de arranjo
populacional; `quest_3` e `quest_4` classificam ordem de ligação para saúde
de baixa/média e alta complexidade. Não são contagens de pacientes de malária.
O diretório IBGE a lista em 25/06/2020; não era disponível na avaliação
2014–2019. Documentar direitos específicos antes de redistribuir.

## Lacunas e contrato para uma futura F

| Requisito | Evidência disponível | Falta para avançar |
| --- | --- | --- |
| OD mensal | Campos 2013 presentes; dicionário/manifesto | Checar 2009–2012 e sua completude e códigos; definir universo e unidade |
| Municípios→13 regiões | 144 pontos associados espacialmente em 2013 | Fonte administrativa/histórica, vigência anual, comparação à agregação L0 |
| Resultado/espécie | `res_exam` e labels no codebook | Harmonizar mistos e categorias; fixar inclusão antes de comparar |
| Duplicação e unidade | Codebook descreve `id_pacie` como idade | Identificador adequado e regras de episódio/exame; não assumir deduplicação |
| Ausentes/externos | 532 sem origem e 382 com outra UF em positivos PA 2013 | Validar códigos, causas e denominadores por ano/categoria |
| Disponibilidade temporal | Dados e metadados foram publicados em 2026 | Vintages anteriores se houver afirmação de uso operacional em 2013 |
| Direitos e redistribuição | Zenodo indica dados CC BY 4.0 | Verificar termos específicos das demais fontes e forma de publicação |

Contrato candidato por mês de notificação: `municipio_infeccao`,
`municipio_notificacao`, `ano`, `mes`, `n`, incluindo unidades, dicionário,
filtros, versão e hash de origem, cobertura, desconhecidos e data de extração.
Incluir explicitamente entradas de fora de PA e diagonal intrarregional;
verificar conservação de totais por destino sobre o mesmo universo. Não
transformar ausência de informação em zero.

**Checklist:** [x] fonte 2013 e hashes; [x] campos candidatos 2013;
[ ] anos 2009–2012; [ ] crosswalk histórico validado; [ ] semântica e
deduplicação; [ ] partições e conservação do treino; [ ] comparação com L0
sob filtros comparáveis. Sem esses itens, não declarar F elegível.

## Continuidade

Buscar composição administrativa histórica das regiões e esclarecer a
origem de `notification.hr`. Se isso for resolvido, repetir D1 e executar D2
para 2009–2013, registrando diferenças e cobertura antes de propor grafo.
Se não for possível, entregar A e limites descritivos. A elegibilidade de
dados não é aprovação de protocolo; E0*/FAR e as camadas incompletas mantêm
RQ1′ inconclusiva conforme [decisões](../protocol-decisions.md).

## Reprodução da triagem

Com os seis arquivos indicados acima em `/tmp/headd-castro-20261027` e a
geometria arquivada identificada por hash, execute o trecho abaixo com a
Python do ambiente do projeto. Não imprime registros individuais. O arquivo
`source_regions.parquet` está em `.worktrees/_archive/2026-10-23/second-execution/data/processed/graph/`
relativo à raiz principal. O predicado usa pontos representativos em
EPSG:4674; não testa área de interseção integral dos polígonos.

```python
from pathlib import Path
import geopandas as gpd
import pandas as pd
import pyarrow.parquet as pq

base = Path('/tmp/headd-castro-20261027')
p = base / 'sivep_malaria_2013.parquet'
f = pq.ParquetFile(p)
print('linhas, colunas:', f.metadata.num_rows, len(f.schema_arrow))
print('esquema completo:', f.schema_arrow)
d = pd.read_parquet(p, columns=['uf_notif_code', 'uf_infec_code',
                               'mun_infe_code', 'res_exam'])
pa = d[d.uf_notif_code.eq(15)]
pos = pa[pa.res_exam.notna() & pa.res_exam.ne('Negativo')]
print('PA, positivos:', len(pa), len(pos))
print('origem municipal ausente:', pos.mun_infe_code.isna().sum())
print('UF origem ausente, PA, outra:', pos.uf_infec_code.isna().sum(),
      pos.uf_infec_code.eq(15).sum(),
      (pos.uf_infec_code.notna() & pos.uf_infec_code.ne(15)).sum())
m = gpd.read_file('zip://' + str(base / 'pa_municipios_2013.zip'))
region_path = Path('/home/vinvs/projects/net-sci-epi/.worktrees/_archive/'
                   '2026-10-23/second-execution/data/processed/graph/source_regions.parquet')
h = gpd.read_parquet(region_path)
assert m.crs.to_epsg() == h.crs.to_epsg() == 4674
points = m.copy()
points.geometry = points.geometry.representative_point()
j = gpd.sjoin(points, h[['code_health_region', 'geometry']],
              how='left', predicate='within')
print('municipios, ausentes, duplicados:', len(j),
      j.index_right.isna().sum(), j.index.duplicated().sum())
print('codigos unicos 6/7:', m.CD_GEOCMU.str[:6].nunique(),
      m.CD_GEOCMU.nunique())
```

Conferir os hashes antes da execução; `/tmp` é temporário e os endereços das
fontes e hashes acima permitem baixar novamente os arquivos.
