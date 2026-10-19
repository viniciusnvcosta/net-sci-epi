# Evidência portátil do PR #2

Este diretório versiona somente resumos pequenos dos artefatos locais e seus
SHA-256. Os resultados completos continuam nos diretórios ignorados
`results/e0-star-scoring-20260930/` e `data/processed/graph/`; eles não são
duplicados no Git.

- `e0-star-summary.json`: identidade da execução, gates e hashes do scoring
  regional E0*.
- `graph-summary.json`: invariantes e hashes da aquisição P4.

Os resumos não alteram o estado científico: E0 permanece inconclusivo, E0* e
FAR falharam, e `interpretation_allowed=false`. O grafo e as features estão
validados tecnicamente, mas isso não aprova G3/G5 nem autoriza E1′.

O run P4 preservado foi produzido em `7208531`, antes do validador exato de
código↔nome de `61dd0cb`. Seus 13 pares registrados foram conferidos _post hoc_
e coincidem com o mapeamento canônico, mas o run não contém
`name_mapping_version`; o resumo registra essa limitação sem atribuir ao run um
teste que ele não executou.
