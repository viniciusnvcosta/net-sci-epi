# Fontes e requisitos para HEADD: revisão de 27/10/2026

Este inventário complementa a [auditoria Castro](2026-10-27-castro-malaria-mobilidade.md).
O objetivo é preparar decisões sobre dados até 30/10, não alterar o protocolo
L0. **Aberto** abaixo significa que a fonte se apresenta com acesso público;
não significa que seus arquivos foram baixados, validados ou estejam livres
de limitações de uso. Consulta web em 27/10/2026.
O catálogo do Zenodo foi acessível, mas as prévias da metodologia e dos
metadados retornaram HTTP 429 e a prévia do dicionário expirou; seu conteúdo
e a integridade dos Parquet permaneciam pendentes de verificação direta.
**Atualização:** os downloads diretos dos metadados, dicionário e Parquet
2013 foram posteriormente conferidos; ver [dossiê](2026-10-27-adocao-castro-proveniencia.md).

## Fontes candidatas

| Fonte                                                                                                                                                                                                      | Uso e requisitos                                                                               | Granularidade/período                                                           | Acesso e situação                                                                                                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SIVEP local `PASIVEPDailyPerHr.csv` e `PA.csv`                                                                                                              | Série existente L0, continuidade e comparação                                                  | 13 regiões × mês; 2009–2019                                                     | Arquivos ignorados disponíveis na raiz principal; o caminho relativo do TOML não resolve no worktree. Origens upstream e licença ainda a confirmar; ver dossiê.                                                                                                                                                  |
| [SIVEP histórico, Zenodo v2](https://zenodo.org/records/20706957)                                                                                                                                          | Candidato principal para verificar OD infecção→notificação, classificação e série reconstruída | Notificações anuais 2004–2024; campos geográficos e datas descritos no depósito | Aberto, [CC BY 4.0 segundo o depositante](https://rfsaldanha.github.io/data-projects/sivep-malaria.html); obtido por LAI, com dicionário, manifesto e arquivos anuais. Campos de 2013 conferidos; qualidade histórica e anos 2009–2012 pendentes.                                                                                     |
| [SIVEP oficial](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/m/malaria/notificacao)                                                                                                              | Definições, regras e eventual acesso institucional ou LAI                                      | Notificação individual e processo de vigilância                                 | O sistema é [descrito pelo Ministério como de acesso restrito](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/m/malaria/situacao-epidemiologica-da-malaria/indicadores/indicadores-de-eliminacao-consolidado); essa página redirecionou a login nesta consulta. O depósito aberto acima é uma via separada. |
| [Regiões de saúde 2013, DataSUS/geobr](https://github.com/ipea/geobr)                                                                                                                                      | Geometrias e A Queen 13×13                                                                     | Regional, referência 2013                                                       | Fonte acessível; o [guia do projeto](../development.md#grafo-regional-p4) identifica o arquivo e o manifesto. Licença/termos específicos devem ser registrados.                                                                                                                                                     |
| [Malhas municipais IBGE](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html) e [códigos IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php) | Correspondência município→região e controle territorial                                        | Municipal, ano de referência compatível                                         | Dados públicos; baixar versão específica, registrar fonte/termos e verificar vigência e códigos.                                                                                                                                                                                                                    |
| [Regiões de Saúde, OpenDataSUS](https://dadosabertos.saude.gov.br/dataset/macrorregiao-de-saude/resource/3ef05b19-e31f-41fc-b7e1-6e80b8e2d788)                                                             | Candidato a crosswalk administrativo                                                           | Município→região; referência temporal a verificar                               | API pública listada; dados de 2024 não comprovam composição 2009–2019. Comparar com fonte histórica e limites 2013.                                                                                                                                                                                                 |
| [REGIC 2018, IBGE](https://www.ibge.gov.br/geociencias/cartas-e-mapas/redes-geograficas/15798-regioes-de-)                                                                                                 | Proxy de conexões urbanas/atendimento para eventual M                                          | Ligações, cidades/municípios; XLSX/ODS                                          | Catálogo público anuncia tabelas. Disponibilidade específica e licença devem ser verificadas no download. Trata relações da rede urbana, não contagem direta de pessoas nem transmissão de malária.                                                                                                                 |
| [População municipal, IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html)                                                                                     | Denominadores populacionais se exigidos por um protocolo de taxas ou modelo                    | Município/ano                                                                   | Fonte pública; selecionar edição, referência territorial e vintage. Não substituir contagens existentes por proporções.                                                                                                                                                                                             |
| [Castro: redes municipais](https://github.com/mcastrolab/-Brazil-Malaria-Networks-) e [mobilidade](https://github.com/mcastrolab/Mobility-Expanded-Brazil)                                                 | Referência metodológica e conferência descritiva                                               | Rotas agregadas sem data, marginais municipais mensais; mock individual         | Acesso público aos repositórios; dados de exemplo e marginais não são OD mensal. Licença de uso de cada material requer verificação.                                                                                                                                                                                |
| [Project Tycho v2](https://www.tycho.pitt.edu/data/version.php)                                                                                                                                            | Validação externa opcional, fora do escopo L0 atual                                            | Séries por doença/localidade e período; frequência depende do conjunto          | Portal público; [artigo de v2 informa CC BY 4.0](https://academic.oup.com/jamia/article/25/12/1608/5132125). Necessidade atual de cadastro/download e série adequada não foram verificadas; não é pré-requisito de 30/10.                                                                                           |
| Dados simulados internos                                                                                                                                                                                   | Ground truth de A/C e testes de recuperação                                                    | Região × mês, parâmetros e seeds                                                | Gerados localmente; fonte/perfil/seeds e manifests exigidos. O perfil P5 fixo não é estimativa epidemiológica do Pará.                                                                                                                                                                                              |

Para replicação operacional ideal também seriam necessários vintages de
vigilância, data de disponibilidade/revisão, histórico territorial e, para
validar alarmes, eventos independentes ou protocolo prospectivo de rótulos.
Essas fontes não foram identificadas como abertas nesta consulta. Metadados
de extração de 2026 não comprovam o que estava disponível em 2013.

## Requisitos mínimos e decisões temporais

- **Alvo:** explicitar exame positivo versus episódio; resultado/espécie,
  mês e região de notificação; deduplicação e comparabilidade entre séries.
  Reconstruir contagens para comparação não substitui a série histórica L0.
- **F candidata:** para cada notificação, município provável de infecção,
  município de notificação, data e resultado; ou tabela agregada real
  `origem,destino,ano,mes,n` produzida com filtros documentados. Confirmar
  esquema por ano, códigos, proporção de ausentes/inválidos, diagnóstico,
  deduplicação e denominação dos registros. Agregar por notificação e
  conservar origens fora do Pará como categoria própria. O dado do local
  provável de infecção é observacional e pode conter erro.
- **Crosswalk:** cada município de PA mapeia a uma região canônica para o
  ano aplicável, com código IBGE, fonte e intervalo de vigência; auditar
  códigos 6/7 dígitos, alterações e agregados urbanos. Sem correspondência
  inequívoca, reportar cobertura e suspender o uso como grafo regional.
- **Conservação:** publicar denominadores, contagens de origem desconhecida,
  externa, intrarregional, inter-regional e fora de escopo; somas por destino
  devem reconciliar com o mesmo universo de registros. Toda escolha de exclusão
  deve ser contada. Células desconhecidas não são zeros observados.
- **Sem vazamento:** a configuração atual reserva janeiro/2009–dezembro/2013
  para treino e janeiro/2014–dezembro/2019 para avaliação. F de treino usa
  apenas registros com data até 2013, mas o depósito de 2026 pode conter
  revisões posteriores; denominar análise retrospectiva com dados finais.
  Um teste que afirma disponibilidade em tempo real exige vintages reais.
- **REGIC:** resultados de deslocamento para saúde foram divulgados em
  [2020](https://agenciadenoticias.ibge.gov.br/media/com_mediaibge/arquivos/9329c127e50825491a23f679e6469a61.pdf).
  Assim REGIC 2018 não estava disponível no corte de 2013, nem no período
  de teste 2014–2019. Pode servir como proxy em estudo retrospectivo novo,
  não como covariável historicamente disponível para o protocolo atual.
- **Interpretação:** A mede contiguidade; F reflete o sistema de vigilância;
  M REGIC representa ligações urbanas. Nenhuma das três, por si, é a matriz
  causal de transmissão do SIR ou ground truth de arestas.

## Decisão de contingência para 30/10

Se OD, crosswalk ou proveniência não puderem ser validados até 29/10, produzir
o relatório com A existente e limitações; não chamar a alternativa de braço
novo executado. O fallback originalmente descrito como **A2** precisa ser
traduzido aos nomes atuais B1\*/B2/B2-placebo antes de qualquer execução: a
equivalência não foi verificada. REGIC também não é fallback causal para o
período histórico. Na ausência de um evento independente para avaliar alarmes,
as conclusões ficam descritivas e os gates atuais não mudam.
