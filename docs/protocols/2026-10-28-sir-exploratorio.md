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
