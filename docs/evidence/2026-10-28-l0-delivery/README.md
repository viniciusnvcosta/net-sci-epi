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
