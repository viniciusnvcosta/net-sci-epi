# Construção técnica da geografia candidata

Em 28/10/2026, o usuário aprovou a seleção da composição fixa com Tailândia
em Lago para a análise retrospectiva e a construção técnica SDD+TDD. Essa
seleção não é aprovação de uso experimental, revisão científica ou gate G3.
O [parecer de decisão](2026-10-28-parecer-decisao-geografia-l0.md) distingue
essas etapas e os limites da evidência.

## Artefatos e verificações

O comando abaixo foi executado no worktree, usando o ambiente já instalado no
checkout principal e explicitando `PYTHONPATH=src` para usar o código do worktree:

```bash
UV_PROJECT_ENVIRONMENT=/home/vinvs/projects/net-sci-epi/.venv UV_CACHE_DIR=/tmp/headd-uv MPLCONFIGDIR=/tmp/headd-mpl PYTHONPATH=src uv run --no-sync python -m headd_l0.fixed_geography configs/l0_fixed_geography.toml
```

`results/l0-fixed-geography-candidate-v2/manifest.json` tem SHA-256
`7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0` e
identifica o commit `5308a65ea197e7efd25521539ed5f5d851d2a6ae`, insumos,
SHA-256 de código e saídas, configuração, versões, seed 42, orçamento e
comparação. Os arquivos estão em `results/`, fora do versionamento. O
manifesto registra `source_git_status=[]`, `topology_check=expected`,
`status=candidate_only` e `interpretation_allowed=false`.

A candidata possui 26 arestas, P4 possui 25 e a única adição é
Lago de Tucuruí–Metropolitana II. A inspeção posterior encontrou 30 placebos
distintos, não iguais à candidata, todos conexos e com graus rotulados
preservados; as linhas de W somam 1 e os hashes de saídas e código coincidem
com o manifesto. Não se afirma amostragem uniforme de placebos.

O primeiro pacote, `results/l0-fixed-geography-candidate-v1/`, foi preservado.
Seu manifesto tem SHA-256
`68153cae9b61eef40e2d399885666e5ecebbf98b4a4d5fe3a2bdc9b9f87ced5d`;
a revisão técnica identificou que não registrava hashes de código nem
sinalização explícita da comparação topológica. A correção foi testada e
gerou v2 com a mesma seed, sem sobrescrever v1; os arrays são idênticos entre
as duas execuções. A revisão técnica de implementação não substitui revisão
científica independente do pacote.

A suíte completa no mesmo ambiente, após estabilizar o commit do código,
terminou com **487 testes aprovados e um desmarcado**, em 186 segundos;
`ruff check .` e `ruff format --check .` também passaram. Uma execução anterior
da suíte ocorreu em paralelo a commits e teve falhas; uma comparação de
manifestos capturou commits diferentes e o outro teste falho passou isolado.
O resultado definitivo acima foi obtido sem commits durante a execução.

## Limites e próximos passos

O grafo é alinhado à série fixa, não prova regionalização administrativa
vigente em cada mês ou causalidade de transmissão. D1 permanece não aprovado,
D2 OD suspenso, G3 pendente e E0*/FAR históricos preservados; G4 continua
restrito ao perfil fixo ratificado. Nenhuma bancada, detector ou comparação de
lead time foi executada. Encaminhar o manifesto, entradas, esta evidência e o
parecer à revisão científica independente; uma decisão prospectiva posterior
é necessária antes do uso experimental e não equivale a inferência de RQ1′.
