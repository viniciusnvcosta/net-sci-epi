# Auditoria da tabela e do script de integração disponibilizados

Em 27/10/2026, o usuário disponibilizou na raiz deste worktree `rl_municip_regsaud.csv` e `data_integration_process.r`. A análise leu os arquivos sem modificá-los nem executar o código R. Os nomes correspondem aos artefatos [syn21552452 e syn21555551 identificados no artigo de Baroni et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7271548/), mas não foi obtida confirmação independente de versão ou checksum do Synapse para os bytes recebidos.

| Arquivo fornecido | SHA-256 | Observação |
| --- | --- | --- |
| `rl_municip_regsaud.csv` | `9de50c97ec32ab159cf8e7361da7cb7e2cd08692eaa213f06d8f77d19cf45f6f` | 5.658 linhas, sem cabeçalho; separador `;`; município e região. |
| `data_integration_process.r` | `f16801d31eb829548ed5c3830c1c729d7470abe93d70c1a7117a3c5b61c1ea12` | Texto de integração; funções e dados não executados. |
| `tb_regsaud.csv` | `a386f78d581255487bbf047b753d0c7335f471310ab3635a8e6a8926401af77d` | Fornecida posteriormente pelo usuário; 466 linhas, quatro colunas, separador `;`, sem cabeçalho. |
| `integrated-dataset.pdf` | `86f31b9a27a9a79a2aee10f929f6d99c94e4fd49d9f280f26ac60a0d548448e3` | Documentação fornecida pelo usuário, quatro páginas; metadados internos indicam 23/04/2020. |

## Comparação de composição

A tabela fornecida tem códigos municipais únicos. Dos 145 códigos iniciados por `15`, um é o agregado `150000 → 15000`; os outros 144 coincidem exatamente com os municípios de PA e suas regiões na tabela territorial DATASUS de 2023 previamente identificada. **Tailândia `150795 → 15004` (Lago de Tucuruí)**. Associando por código aos 144 registros municipais do GeoParquet P4, todos são encontrados e a única diferença é Tailândia, em P4 `15011` (Tocantins).

Esta é evidência direta da composição da tabela fornecida e reforça a [reagregação das contagens de 2013](2026-10-27-auditoria-reagregacao-2013.md): Lago reproduziu 1.560/1.560 células regionais mensais por resultado. É ainda necessário comprovar que os bytes fornecidos e a versão do processo efetivamente produziram o arquivo regional de Eze/L0; igualdade de totais em 2013 não comprova isso para todos os anos ou para cada registro.

## O que o script especifica

O código renomeia as duas colunas da relação territorial e as quatro da tabela `tb_regsaud`. Faz um `merge` interno de município–região com `tb_regsaud` pelo código da região e seleciona o código do município e o nome regional. Faz então três `merge(..., all.x=TRUE)` pelos códigos `MUN_NOTI`, `MUN_RESI` e `MUN_INFE`, produzindo respectivamente `notification.hr`, `home.hr` e `infection.hr`. O mesmo objeto territorial é usado nas três junções, sem chave de ano ou intervalo de vigência explícitos no trecho. Isso descreve uma atribuição fixa **se os mesmos objetos forem fornecidos à função**, e não prova a organização administrativa vigente em cada ano.

O `merge` com `tb_regsaud` é interno e pode excluir códigos regionais sem correspondência; códigos duplicados em `tb_regsaud` podem multiplicar linhas. Na tabela fornecida posteriormente, todos os 466 códigos regionais são únicos e todos os 5.658 códigos da relação municipal encontram correspondência; a junção não multiplica municípios. Nos 144 municípios de PA, há 144 linhas, com 13 códigos ativos e nomes canônicos; `150795 → 15004 → LAGO DE TUCURUI`. Isso verifica o join das duas tabelas fornecidas, não a cobertura ou unicidade de registros no SIVEP, nem que essas versões tenham produzido o CSV L0. A linha inicial do arquivo chama a função antes de sua definição; o arquivo foi inspecionado como texto e não é uma receita independente comprovadamente executável de ponta a ponta. Também não foi localizado nele o processamento posterior que gerou `PASIVEPDailyPerHr.csv`.

Como diagnóstico auxiliar, a `tb_regsaud.csv` do pacote territorial DATASUS
de 2023, SHA-256 `c79bf2cac0b1608066f1860eb1fabac9b4382777a1c46a600e76e4748dccc8ff`,
contém exatamente uma linha ativa para cada um dos 13 códigos regionais dos
144 municípios de PA na relação fornecida. Uma junção por código com esse
snapshot produz 144 linhas, sem município ausente ou multiplicado. Isso não
verifica a tabela histórica nem os nomes efetivamente usados por Baroni;
a tabela de 2023 tem seis colunas e não pode ser passada diretamente à função
R, que espera quatro. Não executar essa substituição no experimento.

## Documentação do conjunto integrado

O PDF fornecido descreve o pré-processamento do conjunto integrado; seus
metadados de criação são apenas uma pista de versão, não confirmação de
linhagem do CSV Eze/L0. Na p. 1, descreve a remoção de atributos de
identificação e localidades e a limpeza de inconsistências de datas. Nas
pp. 2–3, informa que dia, mês e ano das datas são transformados em atributos
de mês/ano, com omissão do dia por privacidade, e que códigos municipais de
notificação, residência e infecção são mantidos. O script R recebido mantém
as colunas de data no retorno, além de criar mês/ano; a documentação e esse
trecho não demonstram em que etapa, versão ou produto o dia foi omitido.
Não inferir frequência diária efetiva pelo nome `PASIVEPDailyPerHr.csv`.
O próprio CSV L0 contém as colunas `notification.year`, `notification.month`,
`notification.hr`, `exam.result` e `testperhr`: não há coluna de dia. Isso
confirma a granularidade mensal do arquivo usado, mas não esclarece em qual
etapa o dia eventualmente foi omitido dos dados anteriores.

A tabela 2 do PDF, p. 4, informa preenchimento de 100% para região e município
de notificação, 12,62% para região e município de infecção e 12,94% para
região e município de residência. Esses percentuais referem-se ao conjunto
integrado descrito, não foram recalculados por ano, Pará ou resultado de
exame e não comprovam a qualidade dos códigos preenchidos. O artigo de Baroni
observa que informação pessoal só é fornecida para exames positivos: os
campos esparsos podem sofrer seleção por resultado. Comparações de fluxos
exigiriam denominadores, cobertura e mecanismos de ausência específicos antes
de construir qualquer OD; os percentuais não identificam mobilidade observada.
O PDF não documenta a criação do CSV agregado de Eze nem prova quais versões
das tabelas foram usadas nesse arquivo.

## Consequência para L0

O mapa com Tailândia em Lago agora é o **candidato prioritário de alinhamento** com a tabela fornecida e com as contagens de 2013, sujeito à confirmação da linhagem e revisão científica. P4 permanece referência histórica imutável. A análise exploratória anterior aponta uma alteração de 25 para 26 arestas e exige regenerar W e placebos para qualquer novo protocolo; não autoriza sobrescrever artefatos, alterar resultados ou afirmar ganho de desempenho. A divergência de vigência administrativa e a abrangência de 2009–2019 continuam abertas; D1 não passa automaticamente, D2 OD permanece suspenso conforme o plano, e E0*/FAR, G3 e demais gates permanecem inalterados.

Próximas verificações: verificar origem e versão dos três arquivos e cobertura do join no SIVEP; identificar o processamento da série Eze e verificar a relação entre os bytes usados e o CSV L0. Qualquer nova geografia deve receber identificação própria e revisão prospectiva, sem mudar o perfil ou as evidências históricas.

## Reprodução das comparações de PA

O exemplo exige o ZIP DATASUS 2023 previamente identificado na [auditoria geográfica](2026-10-27-geografia-l0-kernel-ganf.md) e o P4 arquivado; não grava arquivos nem imprime microdados.

```python
import pandas as pd
import zipfile

old = pd.read_csv('rl_municip_regsaud.csv', sep=';', header=None,
                  names=['municipio', 'regiao'], dtype=str)
assert len(old) == 5658 and old.municipio.is_unique
assert old.loc[old.municipio.eq('150795'), 'regiao'].item() == '15004'
with zipfile.ZipFile('/tmp/headd-castro-20261027/base_territorial_2023.zip') as z:
    recent = pd.read_csv(z.open('rl_municip_regsaud.csv'), dtype=str)
recent = recent[recent.CO_MUNICIP.str.startswith('15')]
pa = old[old.municipio.str.startswith('15')]
joined = recent.merge(pa, left_on='CO_MUNICIP', right_on='municipio',
                      how='outer', indicator=True, validate='one_to_one')
assert len(recent) == 144 and len(pa) == 145
assert (joined._merge == 'both').sum() == 144
assert (joined.loc[joined._merge.eq('both'), 'CO_REGSAUD'] ==
        joined.loc[joined._merge.eq('both'), 'regiao']).all()
assert joined.loc[joined._merge.eq('right_only'), 'municipio'].tolist() == ['150000']
historic_names = pd.read_csv('tb_regsaud.csv', sep=';', header=None,
                             names=['regiao', 'status', 'nome', 'ordem'], dtype=str,
                             encoding='latin1')
assert len(historic_names) == 466 and historic_names.regiao.is_unique
historic_join = old.merge(historic_names, on='regiao', how='left', validate='many_to_one')
assert len(historic_join) == len(old) == 5658 and historic_join.nome.notna().all()
pa_join = historic_join[historic_join.municipio.str.startswith('15') &
                        historic_join.municipio.ne('150000')]
assert len(pa_join) == 144 and pa_join.municipio.is_unique
assert pa_join.regiao.nunique() == 13 and pa_join.status.eq('ATIVO').all()
assert pa_join.loc[pa_join.municipio.eq('150795'), 'nome'].item() == 'LAGO DE TUCURUI'
print('Tabelas fornecidas: 5658 relações correspondidas; PA 144 linhas')
g = pd.read_parquet('/home/vinvs/projects/net-sci-epi/.worktrees/_archive/2026-10-23/second-execution/data/processed/graph/healthregions_2013.parquet',
                    columns=['code_muni6', 'code_health_region', 'abbrev_state'])
g = g[g.abbrev_state.eq('PA')].copy()
g['municipio'] = g.code_muni6.astype(int).astype(str)
g['p4'] = g.code_health_region.astype(int).astype(str)
c = g.merge(old, on='municipio', how='left', validate='one_to_one')
assert len(c) == 144 and c.regiao.notna().all()
assert c.loc[c.regiao.ne(c.p4), ['municipio', 'regiao', 'p4']].values.tolist() == [['150795', '15004', '15011']]
print('PA: 144 pares concordantes com DATASUS 2023; uma diferença frente a P4')
with zipfile.ZipFile('/tmp/headd-castro-20261027/base_territorial_2023.zip') as z:
    names = pd.read_csv(z.open('tb_regsaud.csv'), dtype=str, encoding='latin1')
municipal = pa[pa.municipio.ne('150000')]
matched_names = names[names.CO_REGSAUD.isin(municipal.regiao)]
assert len(matched_names) == matched_names.CO_REGSAUD.nunique() == 13
assert matched_names.CO_STATUS.eq('ATIVO').all()
joined_names = municipal.merge(matched_names, left_on='regiao', right_on='CO_REGSAUD',
                               how='left', validate='many_to_one')
assert len(joined_names) == 144 and joined_names.CO_REGSAUD.notna().all()
print('Snapshot 2023: 13 códigos únicos ativos; 144 municípios sem multiplicação')
```
