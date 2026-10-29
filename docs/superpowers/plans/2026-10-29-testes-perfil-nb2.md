# Testes diagnósticos do perfil NB2

> **Execução:** SDD e TDD de baixo custo; resultados negativos ficam registrados.

**Objetivo:** avaliar a regra proposta e o perfil numérico sem alterar o runner.
**Arquitetura:** harness diagnóstico isolado em `docs/evidence/2026-10-28-l0-delivery/`,
saída JSON com cada réplica e parâmetros; testes de sanidade em `tests/`.
**Ferramentas:** numpy, scipy, statsmodels e pytest existentes.
**Contexto:** `docs/evidence/2026-10-28-l0-delivery/perfil-validacao-20261029.md`.

## Critérios fixados antes da execução

- Sementes 201, 202, 203 e 204, respectivamente Poisson, binomial e dois NB2.
- Desenho harmônico do projeto; 40 séries Poisson(50) e 40 binomiais(100, 0,5),
  com 120 meses; 30 séries NB2 de média 50 e α=0,1 e 30 com média 3300 e
  α=0,0005, cada uma com 600 meses. Réplicas independentes.
- GLM de Poisson e NB2 com IRLS `tol=1e-10`, `maxiter=100`; perfil em
  log α no intervalo [log(10⁻⁶), log(10)], otimização limitada `xatol=1e-8`.
  Avaliar também uma grade de 17 pontos e Poisson; registrar se a grade
  supera a solução limitada ou a regra de escore. Critério pelo sinal do
  escore é provisório e local: não alegar máximo global pelo sinal.
- Poisson: 10–30 das 40 séries classificadas na fronteira; binomial: pelo
  menos 36/40. Falhas de ajuste e de perfil contam no denominador e falham.
- NB2: cada grupo deve ter pelo menos 27/30 ajustes interiores válidos;
  erro médio de α deve ficar em até três erros-padrão Monte Carlo empíricos;
  IC aproximado de 95% por curvatura perfilada deve cobrir o valor real em
  ao menos 24/30 séries. Esses limites são verificações de fumaça, não prova
  de calibragem estatística; qualquer curvatura inválida conta como falha.
- Os três casos do piloto e as 14 séries reais usam ensaios anteriores
  identificados, com verificação independente dos arquivos e números; a
  tolerância dos reais é 10⁻³ EP por parâmetro e foi registrada anteriormente.
- Não alterar `forecast.py`, E0*, sementes históricas ou regras vigentes;
  não executar piloto, não declarar G3/G4/D-COST aprovados.

## Execução

1. Criar teste focado para verificar a regra, limites e detecção de falhas;
   observar RED antes do harness.
2. Implementar harness diagnóstico com falha explícita e resultados por
   réplica; executar o teste focado e Ruff.
3. Executar uma vez a simulação fixada; armazenar JSON em destino novo sem
   sobrescrever; identificar código, bibliotecas, contagens, falhas e critérios.
4. Conferir resultados, artefatos dos três casos e 14 reais, registrar
   limitações, testes, hashes e conclusão; sem promover a regra a protocolo.
