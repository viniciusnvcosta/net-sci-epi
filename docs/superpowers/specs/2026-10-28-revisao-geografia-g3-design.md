# Revisão da geografia fixa e critérios prospectivos de G3

Data: 28/10/2026. **Estado: desenho para revisão do usuário.** Este documento
não ratifica critérios, não registra parecer científico e não aprova G3.

## Objetivo e escolhas

Preparar uma decisão auditável sobre a geografia candidata da série L0 e,
separadamente, os critérios prospectivos para avaliar G3. Em conversa, o
usuário escolheu a abordagem em duas etapas, com P4 histórico como referência
e comparação de sensibilidade, mapa como apoio e GEXF opcional. Os critérios
propostos de G3 foram apresentados e aceitos como desenho; sua ratificação e
o resultado do gate são decisões posteriores e distintas.

A primeira etapa é revisão científica da adequação da composição à **série
fixa retrospectiva de notificação**. A segunda define e avalia G3 de forma
prospectiva, após o parecer. Nenhuma etapa estabelece regionalização
administrativa vigente em cada mês, causalidade de transmissão ou desempenho
de detecção. A aprovação do desenho não equivale a parecer independente ou à
aprovação de uso experimental.

## Alternativas consideradas

| Abordagem | Consequência | Decisão da conversa |
| --- | --- | --- |
| Duas etapas: adequação à série fixa, depois critérios/G3 | Separa evidência territorial, gate e eventual uso experimental | Escolhida. |
| G3 apenas técnico | Menor escopo; deixa adequação científica em decisão separada | Não escolhida. |
| G3 integrado a todo o protocolo experimental | Exige antecipar decisões das camadas ainda não desenhadas | Não escolhida. |

Quanto à linhagem, o usuário aceitou considerar a compatibilidade observada
suficiente **em princípio**, para o recorte da série fixa e condicionada ao
juízo do revisor independente; exigir prova completa da linhagem antes de
qualquer revisão não foi escolhido. Não se transforma a ressalva em prova de
linhagem ou vigência administrativa.

## Etapa 1 — pacote e parecer independente

O pacote de revisão deve conter:

1. Referência ao manifesto v2 SHA-256
   `7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0`,
   A, W e 30 placebos; informar que estão em `results/`, não versionados.
   Verificar os hashes e a disponibilidade dos insumos antes da revisão.
2. Comparação P4/candidata: arestas, graus e linhas de W, com a adição
   Lago de Tucuruí–Metropolitana II; registrar as versões por hash.
3. Mapa das 13 regiões candidatas com Tailândia destacada e uma visualização
   das arestas alteradas. Vincular mapa, código, geometria e crosswalk por
   hashes, sem editar o pacote v2. GEXF é opcional e não condiciona G3.
4. Referências à [auditoria 2009–2019](../../research/2026-10-28-auditoria-integrated-2009-2019.md),
   [conflito territorial](../../research/2026-10-27-geografia-l0-kernel-ganf.md),
   [relatório técnico](../../research/2026-10-28-execucao-geografia-candidata.md)
   e [parecer preparatório](../../research/2026-10-28-parecer-decisao-geografia-l0.md).
   Informar 7.592 grupos observados iguais, 143 pares municipais observados,
   144 municípios na tabela e limites de linhagem, licenças e vigência.
5. Formulário de parecer com identidade e independência do revisor, data,
   hashes efetivamente examinados, evidências, achados, ressalvas e decisão
   `favorável com ressalvas`, `complementação necessária` ou `não favorável`.

O revisor deve ser independente do autor da implementação e ter competência
para julgar a adequação geográfica e epidemiológica; revisão automatizada de
código não substitui parecer científico. Sem revisor ou sem dados acessíveis,
registrar impedimento e manter a etapa pendente. A entrega ao revisor não
autoriza compartilhamento de microdados ou contato externo sem instrução
explícita; licenças e direitos de redistribuição seguem por confirmar.

## Etapa 2 — critérios propostos para G3 da candidata

Critérios abaixo são uma **proposta prospectiva**, não uma transcrição de uma
lista histórica de G3. Ratificação dos critérios pelo responsável científico
precede a avaliação formal. Avaliar por evidência, sem alterar parâmetros para
transformar uma falha em aprovação.

| Critério | Evidência necessária para aceite | Estado inicial |
| --- | --- | --- |
| Identidade e proveniência | Hashes de insumos, código, configuração e saídas verificados; seed e versões identificadas; fontes disponíveis para revisão | V2 registra hashes; disponibilidade e revisão independentes pendentes. |
| Composição | 144 municípios de PA associados uma única vez às 13 regiões canônicas; Tailândia em Lago; compatibilidade e limites da série avaliados | Associação validada tecnicamente; juízo científico pendente. |
| Queen e W | Geometrias válidas, A binária, simétrica, diagonal nula e conexa; W normalizada por linha; comparação documentada com P4 | Verificação técnica documentada; revisão independente pendente. |
| Placebos | 30 grafos distintos, não iguais a A, conexos e com graus preservados por região; método, orçamento e limites de mistura documentados | Propriedades técnicas verificadas; não há afirmação de uniformidade. |
| Parecer e decisão | Parecer independente favorável com ressalvas aceitas pelo responsável, seguido de decisão explícita identificando artefatos e escopo | Pendente. |

Para cada critério, registrar `pass`, `fail` ou `pending`, evidência e
responsável: ausência de evidência ou de parecer deixa `pending`; uma violação
comprovada é `fail`. G3 só pode ser aprovado se todos passarem e houver decisão
explícita. Uma eventual complementação recebe identidade própria e é avaliada
prospectivamente; manter versões e falhas históricas. O mapa auxilia o parecer;
não é um critério numérico de aprovação nem altera o grafo.

## Escopo, limites e entregas

O resultado desta etapa é um pacote verificável e, quando existir, um parecer;
a aprovação final de G3 e eventual uso experimental exigem decisões explícitas
separadas, datadas e com hashes, registradas em `docs/protocol-decisions.md`
apenas após ocorrerem. Não representar nomes ou datas de revisor como já
existentes. A preparação do pacote não autoriza execução de bancada.

E0*/FAR históricos seguem reprovados; D1 administrativo segue não aprovado e
D2 OD suspenso. G4 permanece restrito ao perfil sintético ratificado; RQ1′
permanece inconclusiva e `interpretation_allowed=false` enquanto os gates e
camadas aplicáveis não estiverem completos. Não implementar M, OD, GANF ou
kernel ajustado, não modificar `data/raw/`, v1/v2, P4, seeds ou runs históricos.

O plano de execução posterior deve definir exatamente caminhos para pacote,
mapa, visualização de arestas e formulário; verificação dos hashes e links;
reprodução barata do mapa e teste de sua vinculação com os dados. Preserve o
trabalho preexistente e arquivos locais do usuário. O prazo para a entrega
preparatória continua 30/10/2026, fim do dia em America/Fortaleza; revisão
independente não pode ser presumida disponível até esse prazo.
