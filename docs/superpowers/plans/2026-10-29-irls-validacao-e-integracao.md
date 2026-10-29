# Diagnóstico IRLS e preparação da integração

**Objetivo:** preservar a falha, testar uma alteração isolada com sementes
independentes e preparar, sem executar, a integração a `develop` em `origin`.

## Experimento

1. Reproduzir as dez réplicas inválidas de seed 204 com a implementação
   original, registrar α, fase e iterações; não modificar o lote original.
2. Avaliar uma única alteração no harness isolado: iniciar todos os GLM NB2
   com os parâmetros do GLM Poisson da mesma série. Manter intervalo, tolerância,
   grade, maxiter e critérios. O harness antigo e seus hashes são imutáveis.
3. Congelar seed independente **804**, 30 réplicas NB2 de média 3300,
   α=0,0005 e 600 meses; exigir ≥27 ajustes interiores válidos, cobertura
   ≥24/30, viés em até três EP Monte Carlo; falhas no denominador. Comparar
   separadamente com as mesmas 30 réplicas históricas seed 204, apenas
   regressão. Ambos os resultados em destinos novos sem sobrescrever.
4. Se falhar, parar sem alterar seed/critério e registrar todas as falhas;
   se passar, informar escopo diagnóstico, com regra de fronteira ainda sem
   prova global e sem integração ao piloto nem mudança dos gates.

## Integração posterior — requer autorização após o ciclo

1. Inventariar alterações rastreadas e ignoradas das worktrees, identificar
   dados do usuário, licenças, fontes e hashes; não apagar nem adicionar fontes
   brutas ou resultados ignorados indiscriminadamente.
2. Preparar commits convencionais separados: protocolo/plano, instrumentação
   e testes, evidência negativa e diagnóstico/correção, síntese de entrega.
   Como os planos anteriores já foram executados antes do commit, o Git não
   pode provar retrospectivamente sua anterioridade: registrar essa limitação
   e preservar hashes, carimbos e artefatos existentes sem fabricar histórico.
3. `docs/castro-data-provenance` e `develop` apontam ao mesmo commit local;
   verificar ancestralidade, modificações e remoto antes de qualquer integração.
   Integrar `docs/l0-delivery-protocol` em branch de PR baseada no `develop`
   remoto após fetch/verificação, sem tocar `main` e sem force-push.
   A informação de `origin/develop` pode estar desatualizada; reconciliar
   divergências e rever o escopo completo de commits antes de abrir PR.
4. Executar Ruff, formatação e suíte completa na árvore estável e integrada;
   revisar links, reprodutibilidade e artefatos locais não versionados. Não
   apresentar o menu de finalização enquanto testes falharem.
5. Preparar descrição de PR para `develop`, com escopo, resultados negativos,
   diagnóstico, limitações e validações. Depois do ciclo, pedir autorização
   específica para commits, push e criação do PR; preservar worktrees.
   Rascunho: `docs/evidence/2026-10-28-l0-delivery/rascunho-pr-develop.md`.
