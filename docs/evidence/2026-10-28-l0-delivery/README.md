# Entrega L0 — evidências locais

Estado: preparação; G3 pendente, E0\*/FAR reprovados e RQ1′ inconclusiva.
`interpretation_allowed=false`. Arquivos em `results/` não são versionados.

## Situação em relação ao plano

| Tarefa                    | Situação                                                            | Evidência e justificativa                                                                                                                                                         |
| ------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 — grafo e população     | Concluída tecnicamente; aprovação científica pendente               | GraphML com 13 regiões, população e 52 arcos validado. G3, acesso independente à consulta e condições de redistribuição permanecem pendentes.                                     |
| 2 — painel                | Concluída tecnicamente                                              | Positivos e testes coincidem em 13 × 132 células; a igualdade não comprova a identidade dos bytes com a fonte oficial.                                                            |
| 3 — apresentação e dossiê | Parcial                                                             | Índice e cópia PPTX v2 disponíveis; faltam revisão visual e inclusão do grafo com população. A integridade ZIP não comprova abertura ou layout corretos.                          |
| 4 — protocolo e SIR       | Protocolo e runner preparados; piloto falhou; bancada pendente      | No primeiro painel do piloto, 10 de 14 ajustes NB2 retornaram parâmetros não finitos. O piloto não mediu o custo completo; D-COST e o orçamento prospectivo permanecem pendentes. |
| 5 — GANF e revisão        | Desenho futuro e revisão técnica disponíveis; revisão final parcial | Sem treino de GANF, como previsto; faltam fechamento da apresentação e revisão científica de G3. A revisão técnica não substitui essa decisão.                                    |

A suíte registrada após as alterações teve 537 testes aprovados e um
desselecionado; Ruff e verificação de formatação passaram. A falha do piloto
não autoriza alterar sementes ou parâmetros para obter um resultado favorável.
As falhas históricas de E0\*/FAR e as camadas incompletas mantêm RQ1′
inconclusiva; a aprovação G4 limita-se ao perfil sintético P5 fixado.

## Correção sobre a FAR histórica

A ressalva do item 6 das respostas de entrega sobre 72 meses e probabilidade
de aprovação de aproximadamente 36% está retirada: a avaliação agregou 200
réplicas nulas × 72 meses, ou seja, 14.400 observações por região e braço.
As três FAR observadas fora da banda ficaram abaixo do limite inferior:
ARAGUAIA/B1* 0,012986; XINGU/B1* 0,012778; RIO CAETES/zscore 0,011389.
Isso registra falha de calibração observada no teste, sem atribuir sua causa.
O texto original das respostas é um anexo de entrada e não foi alterado.

## Reprodução do painel

`results/l0-panel-reproduction-v1/manifest.json` registra a comparação feita
com o código do commit `2eeab70`: as matrizes de positivos e totais de testes
coincidem nas 13 regiões × 132 meses, com zero células diferentes. O hash
canônico de ambas é
`693f5fe4c57e388bd1c99e37b94f4a5d2ceb47fd4e11d4be0d1d7b1a5ccfa265`.
A canonicalização identifica nomes, meses e duas matrizes int64 little-endian;
a comparação não afirma identidade dos CSVs brutos nem reexecuta E0\*.

A [auditoria por categorias](../../research/2026-10-28-auditoria-integrated-2009-2019.md)
encontrou igualdade de contagens em 7.592 grupos observados e 143 pares
município–região. Bonito, código `150160`, não apareceu no recorte de
notificação PA do arquivo integrado; isso não significa ausência de casos
em outras fontes. O artigo original associa `syn21555930` ao dataset e
`syn21555933` ao dicionário ([Baroni et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7271548/));
a identidade dos bytes locais com versão oficial não foi verificada.

## Pendências

- Confirmar licença e condições de redistribuição do Censo; a tabela total foi
  fornecida e o grafo com população foi gerado, como registrado adiante.
- Apresentação atualizada, piloto e demonstração SIR ainda não concluídos.

## Cópia preliminar dos slides

`results/l0-delivery-slides-v1/HEADD-Series-L0-atualizada.pptx` é uma cópia
preliminar, não entrega concluída. O original permanece intacto (SHA-256
`fa35e777d89a9f55cb30a4caa66427e115035e077ea700670d3268bf1d818fef`);
a cópia tem SHA-256
`cba7f91c8ae5dbca077ea2033aa3b80712bc91fd708067c7f12018de5fda1848`.
Foram alterados textos nos slides 4, 5, 7, 9 e 11 para identificar P4,
D-COST, as etapas PA/E0\* e o alcance. O pacote ZIP passou verificação de
integridade, mas não havia renderizador disponível para revisão visual.
Faltam verificação de layout, distinção explícita do orçamento histórico,
grafo candidato, fontes e eventuais resultados exploratórios; preservar esta
versão e gerar nova identidade ao completá-la.

A cópia posterior `results/l0-delivery-slides-v2/HEADD-Series-L0-atualizada.pptx`
(SHA-256 `fdebea58a45ee9416630c2ec4ebd885f0e3da495b6332e1228b186aeb4358252`)
inclui a diferença P4/candidata e o orçamento histórico no texto. É igualmente
preliminar: ainda não incorpora o grafo com população ou
a execução exploratória. Sua integridade ZIP foi verificada; a v1 foi mantida.

Atualização de 29/10: o usuário renderizou a v2 com DM Sans e PT Serif e
informou que o layout está íntegro; sobreposições anteriores decorriam de
substituição de fontes. Permanecem ajustes de conteúdo: custo histórico no
slide 12, novo slide da candidata e população, falha do piloto, referências,
data do slide 1 e margem do card no slide 7. O slide 8 permanece oculto; caso
seja reexibido, diferenciar os ajustes sobre dados reais do piloto sintético.
Esta inspeção é relato do usuário, não uma renderização realizada pelo agente.

O usuário forneceu `results/l0-delivery-slides-v2/HEADD-Series-L0-atualizada-v3.pptx`
(SHA-256 `d2d27b61dc88d7fbeee055a76ae13e792889bbd587e220700ebcd57a023d2fa5`).
O arquivo contém 14 slides, incluindo o mapa da candidata após o P4, as
referências Baroni e IBGE, a estimativa histórica e o piloto; o slide do plano
global continua oculto. A nota inicial foi atualizada para 29/10. O mapa
embutido identifica Tailândia e as regiões; seu recorte é uma nova imagem,
não os bytes originais do PNG. A integridade ZIP passou. A inspeção visual
anterior relatada pelo usuário refere-se à v2, não comprova o layout da v3.

Após o diagnóstico NB2, foi criada a cópia
`results/l0-delivery-slides-v4/HEADD-Series-L0-atualizada-v4.pptx`
(SHA-256 `3ca0d435669735f6dcad4d69fdc9adc73fa040b422d6b9960d57746ec02fe466`),
que altera apenas o texto e a nota do slide de próximos passos: dez ajustes
inválidos com parâmetros não finitos, em lugar de afirmar que o otimizador não
convergiu. A v3 foi preservada. A v4 requer abertura e inspeção visual no
ambiente com as fontes corretas; seu manifesto é local e não versionado.

A revisão técnica identificou que v1 calculava os hashes das referências após
carregá-las. A execução v2, com código do commit `d206a2d`, verifica os hashes
antes e depois da leitura e preserva v1. O manifesto v2 tem SHA-256
`fc38f1c6094f605ee75342343d699553bcdd5785e52ef0efade2ffbd14458740`;
os dois painéis novamente concordam em todas as células e têm o mesmo hash
canônico informado acima. Essa conferência não prova proveniência oficial dos
bytes integrados.

## Grafo candidato parcial

`results/l0-delivery-graph-partial-v1/candidate.graphml` contém 13 nós e 52
arcos direcionados, com código, nome, tipo Queen e os pesos W verificados contra
as matrizes do pacote. SHA-256:
`061420b84c8bc0b97dc56efb9978a5156f04880194341b5ca8fe78e04cd7f59b`.
Seu manifesto SHA-256
`776250d4cbe10a4fa298dade3222da50dee7a9d6ac1cf32cf195add54d04e32f`
registra `partial_population_pending`. Não há atributo de população:
`tabela1378.csv` recebido tem situação do domicílio Urbana, inadequada para a
população total solicitada. Posteriormente, a tabela Total foi fornecida e
utilizada no grafo completo documentado abaixo; o parcial permanece histórico.
A direção dos arcos representa índices de W, não fluxo de pessoas.

## Piloto SIR

`results/l0-sir-pilot-20261028-v1/manifest.json` (SHA-256
`b7559c78a67e500d8148e03dc457d146ae3ebe4f591992f66c47b8508ff4735f`)
registra `pilot_failed`, com `interpretation_allowed=false` e D-COST pendente.
O primeiro painel (white, ε=0, T, endereço piloto 0) não passou no ajuste
NB2: reprodução diagnóstica com a mesma seed apontou 10 dos 14 ajustes com
parâmetros não finitos; não houve ajuste do pool de detectores. Não há medição completa
por braço ou projeção de custo e a bancada exploratória não foi executada.
Não alterar sementes ou parâmetros para transformar esse resultado em sucesso.
A reprodução diagnóstica não modifica a evidência histórica E0\*/FAR.
O [diagnóstico de dispersão](diagnostico-nb2.md) encontrou parâmetros não
finitos em dez ajustes; há evidência parcial de subdispersão, insuficiente para
decidir por Poisson como substituto geral.
Uma [investigação posterior](investigacao-newton-20261029.md) confirmou passos
de Newton para α negativo e falsa indicação de convergência, além de testar
BFGS e comparar a fixture real. A correção e a regra de fronteira ainda não
foram validadas; o protocolo original permanece em vigor. O
[ensaio de perfil](perfil-validacao-20261029.md) recuperou os três casos
interiores e passou na comparação de parâmetros das 14 séries reais, mas ainda
não implementa nem valida um estimador para uso no piloto.
Os [testes de Monte Carlo](testes-perfil-20261029.md) passaram em Poisson,
binomial e NB2 com média 50; o grupo NB2 com média 3300 falhou em 10/30
avaliações por IRLS não convergente. O perfil continua sem validação para o
runner e o piloto corrigido não foi executado.
O [diagnóstico IRLS posterior](diagnostico-irls-20261029.md) localizou as dez
falhas na grade de α pequeno. Um início com parâmetros Poisson passou no lote
independente 804, mas falhou na regressão do lote 204; não foi integrado.

Em 29/10 o piloto foi repetido com a mesma seed e o contrato NB2 inalterado,
após o teste independente Poisson e os testes do runner (11 aprovados). O novo
manifesto `results/l0-sir-pilot-20261029-repeat-v1/manifest.json` tem SHA-256
`46d619e82f753b4bd1eb52d0c85df59f2f10fa5b8566ea3a6e28c22de0c028ee` e
registra novamente `pilot_failed`, sem registros completos, projeção de custo
ou autorização de interpretação. Essa repetição não aplicou Poisson como
fallback: o teste reproduziu uma falha, mas não comprovou α na fronteira para
as séries inválidas. O piloto original permanece preservado.

## Grafo com população do Censo 2010

`results/l0-delivery-graph-v1/candidate.graphml` contém 13 nós, 52 arcos,
códigos, nomes, pesos W e população total por região, com `interpretation_allowed=false`.
Seu SHA-256 é
`6c6e9d639b1b93b430b40b298cd110c053904134fd39c1ba8721e3b5445e8e42`;
o manifesto tem SHA-256
`d87333ae691a4a462860ec61153489cf4cc976817e2c7568f7158be7dd684e92`.
As matrizes, pesos e hashes foram conferidos; população total agregada:
7.581.051 habitantes. O exportador é identificado pelo commit `8b04176` e
pelos hashes de código no manifesto. A candidata permanece sem aprovação de G3.

Fonte: **IBGE, Censo Demográfico 2010, Tabela SIDRA 1378**, variável população
residente, situação do domicílio total, sexo total, idade total e condição no
domicílio total, em pessoas. O CSV fornecido `tabela1378.csv` tem SHA-256
`f1a3248dec235571ff9c6984daf2f904082eaec91a76d387f3e3482723e50b54`.
As duas notas presentes no próprio arquivo são:

1. Dados do Universo.
2. A categoria Pessoa responsável inclui as pessoas Sem declaração de
   compartilhamento de responsabilidade pelo domicílio.

Consulta correta, confirmada pelo usuário:
[API SIDRA, k/1136872706](https://apisidra.ibge.gov.br/values/k/1136872706).
O texto `k/239831783` registrado no manifesto histórico corresponde apenas ao
rótulo exibido anteriormente; não é a consulta correta. O manifesto é
preservado como evidência da execução original.
O ambiente não acessou a API para confirmar a consulta; os filtros e notas foram
conferidos no CSV, e não há verificação independente de checksum oficial.
A licença e condições de redistribuição ainda devem ser confirmadas.

O Censo lista 143 municípios do Pará em 2010; a candidata lista 144. A única
diferença de códigos é Mojuí dos Campos (`150475`), instalado em 2013 após
desmembramento de Santarém (`150680`), segundo o
[IBGE](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15761-areas-dos-municipios.html?edicao=30133&t=downloads).
Ambos pertencem à região `15002` na composição fixa; a população de Santarém
em 2010 foi contada uma vez nessa região. Isso não estima a população separada
de Mojuí em 2010 nem a população por região em outros anos.

Os mapas associados estão no worktree irmão, em
`results/l0-geography-review-20261028-v1/`: `mapa-regioes.png` SHA-256
`7cbb79bc1488e58f9ecd277f299e30529c2892b45268a2e9bcd8ad304aac32cb` e
`comparacao-arestas.png` SHA-256
`806e53195c71d414c1b97a3d467db2449357ef254924e43a7cd3a7eb56066b43`.
Sua [proveniência e os limites](../2026-10-28-geography-review/README.md)
permanecem independentes do novo manifesto do GraphML.
