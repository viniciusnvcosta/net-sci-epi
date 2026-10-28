# Inventário dos arquivos locais da investigação

Este inventário organiza os materiais preservados no worktree
`castro-data-provenance`. Os arquivos abaixo são locais, não versionados e não
foram movidos: configurações e manifests existentes referenciam seus caminhos.
Sua presença não autoriza redistribuição; verificar licenças e acesso antes de
compartilhá-los.

| Local, relativo ao worktree | Papel |
| --- | --- |
| `rl_municip_regsaud.csv` | Relação município–região usada na construção candidata. |
| `tb_regsaud.csv` | Nomes de regiões usados na construção candidata. |
| `integrated_dataset.csv` | Base integrada de auditoria, aproximadamente 4,1 GiB. |
| `data_integration_process.r` | Script da fonte examinado na auditoria. |
| `integrated-dataset.pdf` | Documentação da base integrada. |
| `exploratory-analysis.pdf` | Documentação de análise exploratória. |
| `results/l0-fixed-geography-candidate-v1/` e `results/l0-fixed-geography-candidate-v2/` | Candidatas e manifests históricos; preservar ambas. |
| `results/l0-geography-review-20261028-v1/` | Figuras e manifesto do pacote de revisão. |
| `.superpowers/sdd/` | Ledgers e artefatos locais de execução dos planos. |

Os caminhos externos e hashes das fontes efetivamente utilizadas estão em
`configs/l0_fixed_geography.toml` e no manifesto v2. O [índice da revisão](README.md)
identifica hashes e limitações. A geometria e P4 residem em um worktree
arquivado, fora deste diretório; também não foram movidos.

Há quatro documentos rastreados com alterações locais anteriores à integração.
Essas alterações permanecem no worktree original, sem inclusão automática no
merge; uma delas altera notação matemática e precisa de revisão antes de ser
versionada. O checkout principal também contém alterações próprias preservadas.
