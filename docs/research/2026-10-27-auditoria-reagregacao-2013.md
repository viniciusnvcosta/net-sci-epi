# Auditoria descritiva: Tailândia e série regional em 2013

Data: 27/10/2026. Complemento ao [estudo de geografia L0 e GANF](2026-10-27-geografia-l0-kernel-ganf.md).
Esta verificação usa arquivos já baixados; **não é a etapa D2 de OD**, não
gera F, não testa um detector e não muda gates ou o protocolo. Ela compara
apenas a agregação de registros por município de **notificação** em 2013.

## Resultado

A atribuição de Tailândia a Lago de Tucuruí no crosswalk DATASUS de 2023
reproduz os totais regionais L0 observados em 2013 sob os filtros abaixo.
A atribuição a Tocantins no GeoParquet P4 não reproduz as duas séries
envolvidas. É evidência direta de **compatibilidade observacional para esse
ano e essa fonte**; não comprova que o crosswalk de 2023 foi usado no
processamento original, que ele foi vigente nos demais anos ou que o Zenodo
tenha a mesma linhagem que o CSV local.

| Comparação | Municípios de PA mapeados | Positivos: região × mês | Todas as categorias: região × mês × resultado |
| --- | ---: | ---: | ---: |
| DATASUS 2023, Tailândia→Lago | 144/144 | 156/156 células idênticas | 1.560/1.560 células idênticas |
| Geografia P4, Tailândia→Tocantins | 144/144 | 132/156 células idênticas | 1.502/1.560 células idênticas |

No Zenodo, 2013 contém 327.982 notificações de PA com resultado nas dez
categorias presentes no recorte: 29.806 positivos e 298.176 negativos.
Todos os códigos municipais de notificação dessas linhas foram mapeados nas
duas tabelas. Tailândia contém 1.144 registros: 88 positivos e 1.056
negativos. Com P4, o delta absoluto soma 176 nas células positivas e 2.288
considerando todos os resultados, porque cada registro transferido é contado
como menos um em Lago e mais um em Tocantins. O total estadual é igual nos
dois cenários. Cada um dos 12 meses tem positivos de Tailândia, produzindo
diferenças nas 24 células positivas das duas regiões.

## Método e limites

- Fonte de 2013: [Zenodo SIVEP v2](https://zenodo.org/records/20706957),
  Parquet SHA-256 `e14f03dcc996432103481dae6abd3d1122fd8d916deec8cf5685426b9bec07bf`.
  Contar linhas por `dt_notif_year=2013`, `uf_notif_code=15`, mês de
  notificação, município de notificação e resultado; cada linha conta uma vez.
- Crosswalk P4: GeoParquet arquivado SHA-256
  `42de74c7506a5ce52b46ba4d5abdde6b321eebf649b09c08f641fc2e56d8918e`.
  Usar `code_muni6` e `code_health_region`; o crosswalk da base territorial
  DATASUS 2023 SHA-256 `798be2f62a53dd1af8e335a44a1916154f36ee3a3051a7375864a74ef47c3bc4`
  vem de `rl_municip_regsaud.csv`. Cada tabela tem 144 códigos únicos de PA.
- Referência L0: `data/raw/sivep/PASIVEPDailyPerHr.csv` na raiz principal,
  SHA-256 `ad61c77c8c187713cd47e72bb5f028eda1203e3f5e4962c5970d41abd9ae7188`.
  Cada célula é a soma de `testperhr`; todos os 13×12 pares região/mês
  existem no CSV. Categorias ausentes *dentro desses pares observados* entram
  com zero, como no loader L0. Das 1.560 combinações, 701 têm linha no CSV
  e 859 não têm; esse preenchimento segue a convenção do loader, não prova
  independente de ausência clínica de casos.
- Harmonização explícita dos dez rótulos Zenodo para L0: `Negativo`→`negative`,
  `Vivax`→`vivax`, `Falciparum`→`falciparum`, `Nao falciparum`→`non falciparum`,
  `F+V`→`F+V`, `F+Fg`→`F+FG`, `Fg`→`FG`, `V+Fg`→`V+FG`,
  `Malariae`→`malariae`, `F+M`→`F+M`. Não houve resultado sem mapeamento.
- Grade detalhada é produto das 13 regiões, 12 meses e 10 categorias
  observadas em PA no ano. A comparação positiva usa as nove categorias
  distintas de `negative`. Não se deduzem episódios clínicos deduplicados.

O ensaio controla a divergência de Tailândia porque os dois crosswalks têm
os mesmos 144 municípios e apenas esse par é diferente. Igualdade de totais
não prova que todo registro seja o mesmo ou que não existam outros
processamentos equivalentes. O Zenodo é uma extração publicada em 2026; não
comprova disponibilidade em tempo real em 2013. Os demais anos e os
documentos Synapse necessários à linhagem continuam não verificados.

A análise positiva e a comparação de todas as categorias foram reproduzidas
independentemente. A comparação detalhada pode ser refeita pelo trecho abaixo. As fontes continuam em
`/tmp` e são identificadas por hash; não as copiar para `data/raw`.

## Reprodução

Executar o trecho com `pandas`/`pyarrow` do ambiente existente. O código
escreve apenas resumos numéricos no terminal, sem imprimir registros
individuais. O caminho `root` deve apontar para o checkout principal que
contém o CSV e a fonte P4 arquivada; `/tmp` deve conter as fontes listadas.

```python
import pandas as pd
from pathlib import Path
import zipfile
root=Path('/home/vinvs/projects/net-sci-epi');tmp=Path('/tmp/headd-castro-20261027')
x=pd.read_parquet(tmp/'sivep_malaria_2013.parquet',columns=['dt_notif_year','dt_notif_month','uf_notif_code','mun_noti_code','res_exam']);x=x[(x.uf_notif_code==15)&(x.dt_notif_year==2013)].copy()
res={'Negativo':'negative','Vivax':'vivax','Falciparum':'falciparum','Nao falciparum':'non falciparum','F+V':'F+V','F+Fg':'F+FG','Fg':'FG','V+Fg':'V+FG','Malariae':'malariae','F+M':'F+M'}
x['result']=x.res_exam.map(res);assert x.result.notna().all();x['mun']=x.mun_noti_code.astype('Int64').astype(str)
g=pd.read_parquet(root/'.worktrees/_archive/2026-10-23/second-execution/data/processed/graph/healthregions_2013.parquet',columns=['code_muni6','code_health_region','abbrev_state']);g=g[g.abbrev_state=='PA'].copy();g['mun']=g.code_muni6.astype(int).astype(str);g['p4']=g.code_health_region.astype(int)
with zipfile.ZipFile(tmp/'base_territorial_2023.zip') as z:r=pd.read_csv(z.open('rl_municip_regsaud.csv'),dtype=str,encoding='latin1')
r=r[r.CO_MUNICIP.str.startswith('15')].copy();r['cib']=r.CO_REGSAUD.astype(int)
x=x.merge(g[['mun','p4']],how='left',on='mun',validate='many_to_one').merge(r[['CO_MUNICIP','cib']],left_on='mun',right_on='CO_MUNICIP',how='left',validate='many_to_one')
codes={15001:'ARAGUAIA',15002:'BAIXO AMAZONAS',15003:'CARAJAS',15004:'LAGO DE TUCURUI',15006:'METROPOLITANA I',15007:'METROPOLITANA II',15008:'METROPOLITANA III',15009:'RIO CAETES',15010:'TAPAJOS',15011:'TOCANTINS',15012:'XINGU',15013:'MARAJO I',15014:'MARAJO II'}
o=pd.read_csv(root/'data/raw/sivep/PASIVEPDailyPerHr.csv');o=o[o['notification.year']==2013];assert len(o.groupby(['notification.hr','notification.month'])) == 156;assert set(o['exam.result']) == set(res.values());assert x[['p4','cib']].notna().all().all();k=sorted(res.values()); grid=pd.MultiIndex.from_product([list(codes.values()),range(1,13),k]);old=o.groupby(['notification.hr','notification.month','exam.result']).testperhr.sum().reindex(grid,fill_value=0)
for arm in ['p4','cib']:
 x['region']=x[arm].map(codes); v=x.groupby(['region','dt_notif_month','result']).size().reindex(grid,fill_value=0);delta=v-old
 print(arm,'cells',len(delta),'matches',int((delta==0).sum()),'sum_abs',int(delta.abs().sum()),'PA diff',int(v.sum()-old.sum()),'by category',delta.abs().groupby(level=2).sum().to_dict())
print('all notifications',len(x),'tail all records',sum(x.mun=='150795'),'tail positives',sum((x.mun=='150795')&(x.result!='negative')))
```
