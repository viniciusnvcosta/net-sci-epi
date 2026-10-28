# Protocolo prospectivo da demonstração SIR L0

Estado: configuração prospectiva, não executada. Esta demonstração não substitui
E0*, D-COST ou G3 e não autoriza interpretação de RQ1′. O contrato em
`configs/l0_exploratory.toml` fixa o perfil P5 existente, ruído white, 13
regiões, 132 meses, ε de 0 e 0,20 e seed independente 20261028.

Para cada célula T/N, o gerador usa W da candidata v2; detector recebe A, P4
(sem Lago–Metropolitana II) ou os placebos candidatos prefixados 00–02. B1*
não recebe grafo; z-score causal usa janela 12. Os braços compartilham a mesma
realização de contagens; o gerador não muda com o grafo do detector. Os três
placebos não constituem rank dos 30 e a condição A é oracular em relação ao
gerador sintético. Comparações não indicam causalidade nem desempenho real.

Janelas de treino 0–59 e avaliação 60–131. Onsets e gêmea seguem o contrato
`simulate.py` do perfil P5; métricas lead time restrito, detecção e FAR devem
usar os contratos de `evaluate.py` com denominadores e indisponibilidades.
Calibrar por braço em 200 N independentes e avaliar em outros 200 N por
célula. Alvo por região-mês 1/60, tolerância 1/300; sem nulos suficientes,
relatar somente diagnósticos, sem alegar comparação a FAR fixa.

A seed raiz usa filhos de `SeedSequence` distintos para piloto, geração,
calibração, avaliação e detectores, com endereço estável por célula, rótulo e
índice. O piloto usa uma T e uma N por célula, mede tempo/memória e não
contribui às métricas finais. Antes dos resultados, uma decisão identificada
fixará T, número e IDs de placebos por prefixo 00,01,02 e o orçamento; a escolha
depende exclusivamente de custo e prazo, nunca de desempenho. Se 200 N de
cada partição não couberem, não substituir por alegação de FAR comparável.

A execução só pode ocorrer após teste do runner separado, validação por hash
do manifesto v2 e arrays (incluindo os 30 placebos e a ordem dos nomes),
revisão de custo e publicação sem sobrescrita. Qualquer ajuste NB2 inválido
falha fechado. Registrar seeds, código, tempos, inputs, hashes, falhas e
`interpretation_allowed=false`. Nenhuma significância confirmatória.

Para esta demonstração, os hazards são os 13 valores da calibração white
`endemic-white` já produzida sob P5; manifesto SHA-256
`6cce8698b56d7b9ec4774e6ed0645bd6ab0ed78d08cbce51d2fc15605a9abbc0`
e NPZ SHA-256
`1f2a99787ce9e4cdd858fb6fe5a6c0931ed40d3d41d80a748380372aa0c47c3e`.
O arquivo local está no worktree arquivado `second-execution`, sob
`data/processed/endemic-white/`. Validar hashes, status `ready`, perfil, ruído,
ordem e valores antes do uso. Essa calibração sintética não é estimativa de
transmissão regional. Pool fixo PCA, LOF, KNN, HBOS, IF, MCD; seleção K=5.

O piloto será limitado a 1.800 segundos de relógio por processo. Um timeout
não constitui piloto concluído nem autoriza orçamento ou execução final. As
medições por braço repetem ajustes compartilhados e são estimativas de custo,
não ganho científico. A projeção D-COST extrapola os quatro painéis white e
apresenta suas suposições; D-COST continua pendente até conferência formal.
