# Rastreio da série regional e da tabela territorial

Data: 27/10/2026. Investigação descritiva, sem alteração do protocolo ou dos dados brutos.

## Série publicada por Eze e colaboradores

O artigo de Eze e colaboradores referencia o [repositório público da análise](https://github.com/KingPeter2014/Anomaly_in_malaria_surveillance_data). Na revisão `8fd4067bba3f4491bded0948a67d14b08fabfe33`, o [CSV regional](https://github.com/KingPeter2014/Anomaly_in_malaria_surveillance_data/blob/8fd4067bba3f4491bded0948a67d14b08fabfe33/PASIVEPDailyPerHr.csv) tem SHA-256 `ad61c77c8c187713cd47e72bb5f028eda1203e3f5e4962c5970d41abd9ae7188`, idêntico ao de `data/raw/sivep/PASIVEPDailyPerHr.csv` no projeto. Isso identifica a mesma versão dos bytes publicados, mas não prova por si só toda a cadeia anterior de processamento.

O [caderno](https://github.com/KingPeter2014/Anomaly_in_malaria_surveillance_data/blob/8fd4067bba3f4491bded0948a67d14b08fabfe33/BrazillianDatasetByStateHrCounty.ipynb) examina `notification.county` e `notification.hr` e lê o CSV regional. O trecho que salvaria `testbkdownbyhr` está comentado; a leitura de `integratedDataset` também está comentada e a construção de `testbkdownbyhr` não aparece nas células examinadas. Portanto esse caderno, isoladamente, não reproduz a criação do CSV nem comprova qual tabela município–região foi usada. O [módulo auxiliar](https://github.com/KingPeter2014/Anomaly_in_malaria_surveillance_data/blob/8fd4067bba3f4491bded0948a67d14b08fabfe33/functions/amazonmalariadata.py) referencia `integrated_datasetfull.csv`, filtra por estado e campos presentes, e não documenta nesse carregamento a versão da relação territorial.

Hashes dos arquivos inspecionados: caderno `aa61599af73e0dc61b77dc7e41cb30c1b9f9f11051e7bf7d624af52d2fdcc50e`; módulo `37fa17bd3e8020038ad08f3d374858003d8ca05230ace37c066c8f0b0edf74f8`. O código externo foi lido, não executado.

## Dois formatos no pacote territorial de 2023

No [pacote territorial DATASUS de 2023](ftp://ftp.datasus.gov.br/territorio/tabelas/2023/base_territorial_2023.zip), SHA-256 `798be2f62a53dd1af8e335a44a1916154f36ee3a3051a7375864a74ef47c3bc4`, há:

| Membro | Data interna ZIP | SHA-256 |
| --- | --- | --- |
| `rl_municip_regsaud.csv` | 29/08/2023 16:25:46 | `ac2ce1781d8df06da6e8ad202b2754c60c0080aaee2009b15bd571583e9515df` |
| `rl_municip_regsaud.txt` | 18/02/2020 17:39:58 | `2818042ecd7f547e9e30f4eaeb25886727b462ff2ae0fc59f01a82e8265f4065` |
| `rl_municip_regsaud_layout.txt` | 19/01/2015 15:47:26 | `707375ba21067a0228b1c8aa694cbb5ca73cbdcbc8b7e5a0997a0d9a67189b32` |

O layout descreve seis caracteres de município e cinco de região. Para os 144 códigos municipais do Pará presentes no CSV, o TXT contém exatamente a mesma relação, incluindo Tailândia `150795 → 15004` (Lago de Tucuruí). O TXT também contém `150000 → 15000`, código agregado não tratado como município nessa comparação. A data interna do ZIP é apenas metadado: não comprova que esses bytes existiam em 2020, que foram usados por Baroni ou por Eze, nem a vigência da relação em 2013.

Reprodução com o pacote previamente obtido, sem escrever dados derivados:

```python
import csv
import io
from zipfile import ZipFile

with ZipFile('/tmp/headd-castro-20261027/base_territorial_2023.zip') as z:
    rows = csv.DictReader(io.StringIO(z.read('rl_municip_regsaud.csv').decode('latin1')))
    pa = [(r['CO_MUNICIP'], r['CO_REGSAUD']) for r in rows if r['CO_MUNICIP'].startswith('15')]
    lines = z.read('rl_municip_regsaud.txt').decode('latin1').splitlines()
    txt = [(line[:6], line[6:11]) for line in lines if line.startswith('15')]
assert len(pa) == len(dict(pa)) == 144
assert len(txt) == len(dict(txt)) == 145
assert all(dict(txt).get(m) == region for m, region in pa)
assert dict(txt)['150795'] == dict(pa)['150795'] == '15004'
assert dict(txt)['150000'] == '15000' and '150000' not in dict(pa)
```

## Consequência e pendência

A compatibilidade dos totais de 2013 com a atribuição a Lago, descrita na [auditoria de reagregação](2026-10-27-auditoria-reagregacao-2013.md), continua sendo evidência observacional, não prova do processamento histórico nem dos demais anos. A mesma atribuição no TXT acrescenta uma pista, não uma fonte histórica independente: ambos os formatos foram obtidos do mesmo pacote de 2023.

A consulta anônima de metadados do arquivo histórico [Synapse syn21552452](https://www.synapse.org/Synapse:syn21552452), pelo endpoint `entity/syn21552452/filehandles`, retornou HTTP 403; não foi possível comparar o checksum ou o conteúdo da tabela de Baroni. A análise da [reconstrução geográfica e do GANF](2026-10-27-geografia-l0-kernel-ganf.md) permanece válida: manter P4 como histórico provisório, tratar o mapa alinhado à série como candidato de sensibilidade e não reinterpretar os resultados nem alterar os gates. O próximo passo decisivo é obter legitimamente a tabela e o script históricos identificados na auditoria anterior e verificar versão, relações e regras de agregação; isso não autoriza construir a camada OD suspensa pelo plano.
