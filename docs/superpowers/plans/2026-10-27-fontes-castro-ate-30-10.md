# Plano de execução: fontes de dados e adoção Castro até 30/10

> **Atualização de 28/10:** D0–D3 abaixo registram a etapa de fontes já
> executada; o complemento prioritário de geografia e seus limites estão em
> [plano de continuidade](2026-10-28-geografia-l0-ate-30-10.md). D1 permanece
> não aprovado e D2 OD suspenso. A auditoria posterior da série não altera
> retroativamente esses estados.

> **Para execução:** usar `superpowers:executing-plans` em modo nativo;
> itens usam caixas de seleção. Qualquer código novo requer ciclo TDD.

**Objetivo:** entregar até 30/10/2026 um inventário auditável, uma avaliação
de viabilidade de OD 2009–2013 e uma proposta de protocolo baseada nas fontes.

**Arquitetura:** auditoria em etapas sobre fontes fixadas, começando por
metadados e um ano de microdados; comparar o crosswalk e as contagens sem
alterar o pipeline L0. Se os requisitos falharem, entregar a decisão e os
motivos; a criação de F ou um novo braço permanece objeto de desenho separado.

**Stack:** Python ≥3.12 e `uv`, pandas/pyarrow/geopandas existentes, pytest e
ruff apenas se houver código; Markdown para evidências, SHA-256 e MD5 de origem.
**Spec:** [desenho e ressalva](../specs/2026-10-27-castro-adoption-design.md).
**Fontes:** [inventário e requisitos](../../research/2026-10-27-requisitos-fontes-dados.md).

## Restrições globais e custo

- Prazo interpretado como **30/10/2026, fim do dia, America/Fortaleza**;
  estimativa indicativa 8–12 horas de trabalho, sem garantia de rede/acesso.
- Treino histórico janeiro/2009–dezembro/2013; avaliação 2014–2019. Separar
  tempo de evento, data de publicação e data efetiva de disponibilidade.
- Não alterar `data/raw`, resultados históricos, seeds, gates ou perfil P5.
  Novos dados em `/tmp` durante inspeção ou armazenamento local apropriado
  fora de `data/raw`; não commitar microdados nem registros individuais.
- Nenhuma execução de M, hhh4, GANF, gate E0\* ou bancada científica é
  autorizada por este plano. Isso depende de escopo e protocolo próprios.
- Desenvolver sequencialmente; manter download máximo inicial em ~21 MB para
  `sivep_malaria_2013.parquet`, mais metadados. Os cinco anos 2009–2013
  somam ~121,2 MB pelo catálogo, somente se a triagem justificar.
- Dados descritos por 2026 sustentam retrospectiva com dados finais; evidência
  operacional de época requer vintages de disponibilidade que não temos.

## Critérios de revisão

| Risco                                         | Verificação que o trata                                 |
| --------------------------------------------- | ------------------------------------------------------- |
| Ano ou campo ausente                          | Triagem de esquema por ano e falha fechada no contrato  |
| Município externo ou desconhecido excluído    | Partições e conservação por destino; fixture abaixo     |
| Mapeamento ambíguo ou território de outro ano | Validação de unicidade e vigência no crosswalk          |
| Célula vazia confundida com zero              | Teste de cobertura observada e reporte de desconhecidos |
| Contaminação temporal por dados posteriores   | Teste de filtro e declaração do vintage em cada fonte   |

## Calendário e tarefas

### 27/10 — D0: requisitos e desenho (2–3 h)

**Arquivos:** manter `docs/research/2026-10-27-requisitos-fontes-dados.md` e
o adendo à spec; criar `docs/research/2026-10-27-adocao-castro-proveniencia.md`
na execução.

- [x] Registrar lista de fontes, acesso indicado, hipótese de uso e limites.
- [x] Identificar o depósito Zenodo v2, sua data, DOI e comparação temporal
      com REGIC. A consulta aos metadados não substitui validação dos dados.
- [x] Na execução, inventariar hashes/colunas/linhas dos dois CSVs locais e
      suas cópias configuradas; transcrever fatos e lacunas no dossiê.
- [x] No dossiê, registrar `A2` como rótulo histórico sem equivalência
      comprovada; não criar novo braço. Conferir com protocolos vigentes.

**Aceite D0:** inventário aponta as fontes, datas, acesso e incertezas; os
hashes e colunas do dossiê reproduzem os arquivos locais.

### 28/10 — D1: triagem de fonte e crosswalk (3–4 h)

**Entrada:** Zenodo [v2](https://zenodo.org/records/20706957), dicionário,
metadados e `sivep_malaria_2013.parquet` (20,8 MB; MD5 anunciado
`c34baeded21ba5f7b378961acfecbd7b`); geometria 2013 documentada no projeto.
**Saída:** seção D1 no dossiê, com URLs, data, MD5 anunciado/medido, SHA-256,
tamanho e esquema. Sem amostras de registros individuais no relatório.

- [x] Baixar somente a metodologia, dicionário, metadados e o Parquet 2013;
      verificar MD5 publicado e calcular SHA-256. Se download ou hash falhar,
      registrar causa, marcar fonte indisponível e seguir para fallback.
- [x] Examinar nomes/tipos e dicionário: identificar campos reais de data,
      município de notificação e de infecção, resultado/espécie e código de UF;
      apontar dúvidas de identificação/deduplicação. Não supor nomes de coluna.
- [x] Levantar tabelas candidatas de município→região de 2013 e fonte de
      vigência para 2009–2019. Comparar códigos com as 13 regiões canônicas,
      marcar duplicidades, ausências e divergências. A API atual isolada não
      comprova histórico; registrar se apenas geometria está disponível.
- [x] Conferir se arquivos públicos de REGIC são acessíveis, o tipo de ligação
      e o ano de publicação. Documentar resultados sem incorporá-los a L0.

**Aceite D1:** campos essenciais e natureza de cada código identificados,
ou falha explícita. Crosswalk só é utilizável no ano com fonte identificada,
1 município→1 região e ausência de ambiguidade para códigos de PA.

### 29/10 — D2: elegibilidade e reconciliação (2–4 h)

- [x] Se D1 passar, baixar os Parquet 2009–2012 da mesma versão, conferir
      hashes publicados e compatibilidade de esquema 2009–2013; caso contrário,
      parar a triagem OD e documentar motivo.
- [ ] Para PA como destino de notificação e universo positivo explicitado,
      reportar por ano totais e partições mutuamente exclusivas de origem:
      desconhecida/inválida, externa a PA, interna à região e entre regiões.
      Reportar também destino inválido e seus denominadores; não inferir zeros
      a partir de ausências nem expor linhas individuais.
- [ ] Comparar totais por mês/região com a série L0 **apenas se** filtros,
      unidade e crosswalk estiverem documentados; registrar diferenças e sua
      denominação, sem exigir igualdade quando as definições divergem.
- [x] Publicar estado `elegível para estudo retrospectivo` ou `indisponível`,
      fundamentado em campos, vigência, cobertura, conservação e limitações.
      Relatar percentuais ausentes para decisão científica; não inventar corte
      numérico de qualidade após ver os resultados.

**Aceite D2:** cada partição reconcilia com seu denominador; falhas de
correspondência, disponibilidade ou semântica impedem afirmar elegibilidade.
Elegibilidade não equivale a aprovação de F nem do experimento.

### 30/10 — D3: entrega e revisão (1–2 h)

- [x] Finalizar dossiê com inventário, matriz de lacunas, contrato OD e
      resultados D1/D2, inclusive evidência de falhas e arquivos não obtidos.
- [x] Formular proposta separada de estudo retrospectivo, caso elegível:
      hipótese, observável, direção, período, normalização, tratamento de
      entradas externas/diagonal/regiões sem entrada, controles e validação.
      Nenhuma opção é ratificada pela elaboração do relatório.
- [x] Conferir links locais, hashes citados, escopo de alterações e ausência
      de arquivos individuais; revisar o diff e resumir limitações. Registrar
      commit local somente dos arquivos desta entrega, sem incluir trabalho alheio.
- [x] Entregar estado por fonte, decisão de fallback e próximos passos com
      custos e impedimentos, distinguindo planejamento, implementação e inferência.

**Aceite D3:** relatório reproduzível com resultado verificável ou bloqueio
documentado; se OD ou crosswalk forem insuficientes, prosseguir apenas com o
relato do grafo A já existente e não declarar nova comparação executada.

## SDD+TDD de baixo custo para a fase posterior

Primeiro congelar uma spec curta de F e controles, depois um plano próprio;
só iniciar implementação se ela for autorizada explicitamente no contexto
de M, que está fora de L0. Evitar infraestrutura ou dependências novas.
Para uma eventual função pura de agregação, propor fixtures pequenas que
comprovem: (1) duas origens municipais na mesma região somam exatamente;
(2) importação municipal intrarregional permanece na diagonal; (3) origem
externa e origem desconhecida são contabilizadas separadamente; (4) código
de PA sem crosswalk ou com mapeamento duplicado falha fechado; (5) 2014 não
entra no treino 2009–2013; (6) mês ausente não vira zero sem cobertura.
Escrever cada teste antes da implementação, observar falha relevante, aplicar
a mudança mínima e executar novamente os testes focados; depois executar ruff
e a suíte exigida pelo projeto. Esses testes não provam qualidade da fonte,
causalidade ou aprovação científica. A assinatura e os arquivos de código
serão fixados na spec própria, quando dados e decisão de escopo existirem.

## Registro de execução — 27/10/2026

D0 concluído. D1 executado e não aprovado: falta crosswalk histórico
administrativo. D2 suspenso; itens de partição e comparação não foram
executados por dependerem de D1. D3: relatório e fallback documentados;
a proposta de F é condicional e não foi formulada porque F não é elegível.
A confirmação de revisão e o commit são registrados no histórico da branch.
Ver [dossiê de evidências](../../research/2026-10-27-adocao-castro-proveniencia.md).
