# Entrega L0 — evidências locais

Estado: preparação; G3 pendente, E0*/FAR reprovados e RQ1′ inconclusiva.
`interpretation_allowed=false`. Arquivos em `results/` não são versionados.

## Reprodução do painel

`results/l0-panel-reproduction-v1/manifest.json` registra a comparação feita
com o código do commit `2eeab70`: as matrizes de positivos e totais de testes
coincidem nas 13 regiões × 132 meses, com zero células diferentes. O hash
canônico de ambas é
`693f5fe4c57e388bd1c99e37b94f4a5d2ceb47fd4e11d4be0d1d7b1a5ccfa265`.
A canonicalização identifica nomes, meses e duas matrizes int64 little-endian;
a comparação não afirma identidade dos CSVs brutos nem reexecuta E0*.

A [auditoria por categorias](../../research/2026-10-28-auditoria-integrated-2009-2019.md)
encontrou igualdade de contagens em 7.592 grupos observados e 143 pares
município–região. Bonito, código `150160`, não apareceu no recorte de
notificação PA do arquivo integrado; isso não significa ausência de casos
em outras fontes. O artigo original associa `syn21555930` ao dataset e
`syn21555933` ao dicionário ([Baroni et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7271548/));
a identidade dos bytes locais com versão oficial não foi verificada.

## Pendências

- Obter tabela e documentação do Censo IBGE 2010; acesso automático ao SIDRA
  falhou por resolução de DNS. Exportação com população segue pendente.
- Apresentação atualizada, piloto e demonstração SIR ainda não concluídos.

## Cópia preliminar dos slides

`results/l0-delivery-slides-v1/HEADD-Series-L0-atualizada.pptx` é uma cópia
preliminar, não entrega concluída. O original permanece intacto (SHA-256
`fa35e777d89a9f55cb30a4caa66427e115035e077ea700670d3268bf1d818fef`);
a cópia tem SHA-256
`cba7f91c8ae5dbca077ea2033aa3b80712bc91fd708067c7f12018de5fda1848`.
Foram alterados textos nos slides 4, 5, 7, 9 e 11 para identificar P4,
D-COST, as etapas PA/E0* e o alcance. O pacote ZIP passou verificação de
integridade, mas não havia renderizador disponível para revisão visual.
Faltam verificação de layout, distinção explícita do orçamento histórico,
grafo candidato, fontes e eventuais resultados exploratórios; preservar esta
versão e gerar nova identidade ao completá-la.

A cópia posterior `results/l0-delivery-slides-v2/HEADD-Series-L0-atualizada.pptx`
(SHA-256 `fdebea58a45ee9416630c2ec4ebd885f0e3da495b6332e1228b186aeb4358252`)
inclui a diferença P4/candidata e o orçamento histórico no texto. É igualmente
preliminar: não foi renderizada e ainda não incorpora o grafo com população ou
a execução exploratória. Sua integridade ZIP foi verificada; a v1 foi mantida.

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
população total solicitada. Aguardamos a seleção Total; não imputar zero.
A direção dos arcos representa índices de W, não fluxo de pessoas.

## Piloto SIR

`results/l0-sir-pilot-20261028-v1/manifest.json` (SHA-256
`b7559c78a67e500d8148e03dc457d146ae3ebe4f591992f66c47b8508ff4735f`)
registra `pilot_failed`, com `interpretation_allowed=false` e D-COST pendente.
O primeiro painel (white, ε=0, T, endereço piloto 0) não passou no ajuste
NB2: reprodução diagnóstica com a mesma seed apontou 10 dos 14 ajustes sem
convergência; não houve ajuste do pool de detectores. Não há medição completa
por braço ou projeção de custo e a bancada exploratória não foi executada.
Não alterar sementes ou parâmetros para transformar esse resultado em sucesso.
A reprodução diagnóstica não modifica a evidência histórica E0*/FAR.

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

Na consulta enviada, o texto visível do link menciona `k/239831783`, enquanto
o destino é [k/1136872706](https://apisidra.ibge.gov.br/values/k/1136872706).
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
