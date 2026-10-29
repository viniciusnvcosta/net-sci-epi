# Rascunho de PR para `develop`

**Título proposto:** `feat: prepare traceable L0 candidate and exploratory evidence`

## Descrição proposta

A entrega L0 precisava de um grafo regional rastreável, reprodução da série e
um retrato consistente das pendências antes da apresentação. Este conjunto
prepara a candidata Queen de 13 regiões com população do Censo 2010, compara o
painel agregado com a fonte integrada e documenta a apresentação, o protocolo
SIR isolado e o desenho de investigação futura com GANF.

O piloto SIR parou no primeiro painel por dez ajustes NB2 com parâmetros não
finitos. A investigação identificou passos de Newton para α negativo e
localizou dez falhas do ensaio posterior na grade de verificação IRLS. A
inicialização por Poisson passou nos limiares do lote independente (27/30
válidos, cobertura 26/30), mas a regressão histórica ainda falhou (22/30
válidos, cobertura 20/30). A alteração é apenas diagnóstica e não foi
integrada ao previsor ou ao piloto.

G3 permanece pendente; E0*/FAR históricos falharam; G4 está restrito ao perfil
sintético fixo; D-COST e a bancada continuam pendentes. RQ1′ permanece
inconclusiva e `interpretation_allowed=false`. Fontes e resultados locais
ignorados precisam estar disponíveis no ambiente para reprodução; não se
incluem microdados brutos nem dados com termos de redistribuição não verificados.

**Validação na branch antes da integração:** 540 testes aprovados, um
desselecionado; Ruff, formatação e `git diff --check` aprovados. Executar
novamente na árvore efetivamente proposta ao PR, inclusive após eventual
rebase ou merge; confirmar remoto, CI e revisão antes de afirmar integração.

## Pendências antes da publicação

- Conferir escopo completo de `origin/develop..HEAD`: a referência remota local
  estava 37 commits atrás de `develop` local; isso não confirma o remoto atual.
- Inventariar as modificações e arquivos não versionados das worktrees; não
  transferir automaticamente os arquivos de entrada do usuário ou resultados.
- Versionar primeiro planos e protocolos e, em commits separados, códigos,
  testes e evidências. Não alegar que commits posteriores provam que planos
  anteriores aos resultados já estavam sob controle de versão.
- Decidir como disponibilizar evidências em `results/`, hoje ignoradas, sem
  exceder os termos de uso; os links e hashes locais não garantem acesso externo.
- Verificar o PPTX escolhido visualmente e documentar seus limites de edição.
- Consultar a situação do remoto e preparar o PR apenas após autorização
  explícita para a execução do plano; não tocar `main` nem fazer force-push.
