# Pacote local de revisão científica da geografia fixa

Este dossiê prepara a revisão da adequação da composição retrospectiva à série
L0; não constitui parecer, ratificação dos critérios, aprovação de G3 nem
permissão de uso experimental. `interpretation_allowed=false` e RQ1′ segue
inconclusiva. O revisor deve ser independente da implementação e competente
em geografia e epidemiologia. Seu acesso e parecer estão pendentes.

## Identificação dos artefatos

Caminhos relativos à raiz do worktree `castro-data-provenance`; `results/` e
os dados baixados são locais e não versionados. Os arquivos precisam estar
acessíveis ao revisor para que ele próprio confira os hashes.

| Artefato | SHA-256 |
| --- | --- |
| `results/l0-fixed-geography-candidate-v2/manifest.json` | `7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0` |
| `results/l0-geography-review-20261028-v1/manifest.json` | `af20146ebe932026d1f33cefe94ebda6ad3474403bf7cd1278b41165efd3b429` |
| `results/l0-geography-review-20261028-v1/mapa-regioes.png` | `7cbb79bc1488e58f9ecd277f299e30529c2892b45268a2e9bcd8ad304aac32cb` |
| `results/l0-geography-review-20261028-v1/comparacao-arestas.png` | `806e53195c71d414c1b97a3d467db2449357ef254924e43a7cd3a7eb56066b43` |

A v2 contém `adjacency.npy`, `W.npy`, `placebos.npy`, hashes das fontes e
código, seed 42, 30 placebos e orçamento do método. O manifesto de revisão
registra os hashes das imagens, entradas, matrizes, configuração, código de
visualização e commit `53b1541`; o grafo reconstruído foi comparado exatamente
à matriz v2 antes da publicação. As linhas da figura de arestas são
**esquemáticas** entre pontos representativos, não trajetos ou limites.

Fontes de construção: `rl_municip_regsaud.csv`, `tb_regsaud.csv`, geometria
municipal e matriz P4 nos caminhos identificados por
`configs/l0_fixed_geography.toml` e pelos manifests. Esses caminhos incluem
uma área arquivada local e podem não existir em outra máquina. Os arquivos
`integrated_dataset.csv`, `data_integration_process.r`, `integrated-dataset.pdf`
e `exploratory-analysis.pdf` apoiam a auditoria de proveniência; sua
redistribuição e licenças permanecem por confirmar. Não há autorização de
compartilhamento de microdados nem de contato externo.

## Comparação P4 e candidata

P4 tem 25 arestas; a candidata tem 26. Foi adicionada
**Lago de Tucuruí–Metropolitana II**; não há aresta removida. As demais
regiões mantêm grau e linha de W. As duas linhas alteradas, com valores exatos
expressos como frações da normalização por grau, são:

| Linha | Grau P4 → candidata | Colunas existentes alteradas | Coluna adicionada |
| --- | --- | --- | --- |
| LAGO DE TUCURUI | 5 → 6 | ARAGUAIA, CARAJAS, METROPOLITANA III, TOCANTINS, XINGU: cada uma 1/5 → 1/6 | METROPOLITANA II: 0 → 1/6 |
| METROPOLITANA II | 4 → 5 | MARAJO I, METROPOLITANA I, METROPOLITANA III, TOCANTINS: cada uma 1/4 → 1/5 | LAGO DE TUCURUI: 0 → 1/5 |

## Evidência e limites

A [auditoria de 2009–2019](../../research/2026-10-28-auditoria-integrated-2009-2019.md)
identificou igualdade em 7.592 de 7.592 grupos observados de região × mês ×
resultado e concordância de 143 pares município–região observados; a tabela
contém 144 municípios de PA. A compatibilidade observada não prova a linhagem
histórica exata dos dados nem a vigência administrativa em cada mês.
Tailândia foi associada a Lago de Tucuruí na composição fixa candidata.

Consultar [conflito territorial](../../research/2026-10-27-geografia-l0-kernel-ganf.md),
[execução técnica](../../research/2026-10-28-execucao-geografia-candidata.md),
[parecer preparatório](../../research/2026-10-28-parecer-decisao-geografia-l0.md)
e [desenho da revisão](../../superpowers/specs/2026-10-28-revisao-geografia-g3-design.md).
Esses documentos e o [formulário](review-form.md) não substituem julgamento
científico independente. A distribuição dos placebos não é alegada uniforme.

Critérios de G3 são propostos prospectivamente e ainda requerem ratificação
pelo responsável científico, após a revisão. Mesmo um eventual G3 favorável
não altera os demais gates: E0*/FAR históricos reprovados, D1 não aprovado, D2
suspenso e G4 restrito ao perfil sintético fixo; camadas incompletas mantêm
RQ1′ inconclusiva. Nenhum teste foi ajustado para reverter resultado anterior.
