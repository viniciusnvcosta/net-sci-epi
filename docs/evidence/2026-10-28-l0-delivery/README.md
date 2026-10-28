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
