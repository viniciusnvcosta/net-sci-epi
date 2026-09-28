# HEADD-Series L0 — registro de decisões do protocolo

Este registro distingue **decisões tomadas** de **escolhas ainda pendentes**. Cada decisão vale a partir da data registrada e precede qualquer execução que dependa dela. Mudanças posteriores entram como nova linha datada, sem apagar a anterior. Ver [arquitetura §7](superpowers/specs/2026-09-26-headd-l0-architecture.md#7-decisões-experimentais-propostas-para-revisão) e [plano global](superpowers/plans/2026-09-26-headd-l0-global.md).

**Evidência de base:** auditoria da Tarefa 1 (exit 2) sobre o SHA `fbfa609bba6cb0b0f2a9e8d73be18022aec319b7`, registrada em `MIGRATION.md` e `tests/reference/manifest.json`. O original produz uma única tarefa (`sivep`) com os 26 meses de teste rotulados como anômalos (AUC-PR = 1,0 para todos os métodos). Só 3 dos 6 detectores executam. MinT falha por dimensão, PCA tem orientação invertida, o ajuste EVT levanta erro, a seleção usa dados futuros e DM/Cliff rodam após um Friedman não significativo.

## Resumo

| ID      | Status (27/09/2026)                                    | Decisão em uma linha                                                                            |
| ------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| D-G0    | **Decidido**                                           | Saída (i): E0 inconclusivo; B1\* corrigido autorizado como baseline do E1′                      |
| D-G0a   | **Em execução** (prazo 29/09)                          | Busca documentada da proveniência dos resultados apresentados do CDADE v1                       |
| D-E0\*  | **Decidido**                                           | Gate substituto de sanidade para B1\*, pré-registrado                                           |
| D2      | **Decidido**                                           | MinT(Shrink) de Wickramasuriya et al. (2019): alvo diagonal, λ de Schäfer–Strimmer              |
| D3      | **Decidido**                                           | Seis detectores corrigidos; critério de comportamento, sem paridade                             |
| D5      | **Decidido**                                           | Reconciliar previsões de contagem um passo à frente; detectores consomem resíduos reconciliados |
| D6      | **Decidido**                                           | Seleção causal conforme E0 Tarefa 6                                                             |
| D-GT1   | **Decidido**                                           | Camada 0 com anomalias de duração finita; não-inferioridade pelo limite inferior do IC          |
| D-GT2   | **Decidido**, com pendência de parâmetros do simulador | Injeção epidêmica com proveniência explícita de casos importados                                |
| D-GT3   | **Decidido**                                           | Nulo paramétrico NB2 com tendência e dois pares de harmônicos                                   |
| D-GT4   | **Decidido**, com pendência da faixa de R0             | Tamanho, truncamento e onsets definidos                                                         |
| D-COST  | **Decidido**, com pendência do hardware                | Gatilhos de 48 h e 96 h para a escada de redução                                                |
| D-REACH | **Decidido**                                           | ≥ 50% em ε = 0,20, por tipo de ruído                                                            |
| D-L3    | **Pendente**                                           | Seleção e verificação dos eventos reais                                                         |
| D-OPS   | **Decidido**                                           | Worktree persistente e disciplina de commits                                                    |

Responsável por todas as decisões: autor do projeto. Fonte das recomendações: revisão metodológica de 27/09/2026 sobre a auditoria da Tarefa 1.

---

## D-G0 — Saída do gate G0

**Decisão:** saída (i). O E0 fica registrado como **inconclusivo**: a referência fixada não produz o objeto que o E0 compara (14 tarefas com rótulos das duas classes). Um baseline corrigido, **B1\***, é autorizado como baseline do E1′.

**Justificativa:** a RQ1′ compara B2 com B1\* dentro do mesmo pipeline, com uma única variável alterada; essa comparação interna não depende de paridade com o original. Reproduzir o original fielmente significaria reproduzir look-ahead, PCA invertido, EVT quebrado e metade do pool inoperante.

**Consequências obrigatórias:**

- Todo artefato, tabela, figura e texto usa o rótulo `B1*`, nunca `B1` ou "CDADE v1".
- A alegação permitida é "B2 melhora um baseline estilo CDADE corrigido (B1\*)". A alegação "B2 melhora o CDADE v1" fica proibida.
- O SHA de referência não muda silenciosamente. D5 foi resolvido abaixo; o E0 continua inconclusivo mesmo com B1\*.
- A saída (ii), bloqueio total do E1′, foi rejeitada.

## D-G0a — Proveniência dos resultados apresentados do CDADE v1

Os resultados apresentados do CDADE v1 (AUC-PR por tarefa em 18 tarefas, média 0,597) **não podem ter sido gerados** pelo SHA fixado, que avalia uma tarefa única com AUC-PR = 1,0.

**Ação (somente leitura sobre o repo original, prazo 29/09):**

1. Inspecionar `mlruns/`: a tag `mlflow.source.git.commit`, parâmetros e métricas das execuções com métricas por tarefa.
2. Inspecionar outras branches, tags, stashes, `results/` e notebooks que contenham a tabela de 18 tarefas.
3. Registrar em `docs/reference-provenance.md`: o que foi encontrado, com hashes e caminhos, ou a ausência de proveniência.

**Efeito:** o resultado desta busca muda apenas **como o E0 é descrito** e se é preciso uma errata no material do mestrado. **Não altera** a autorização de B1\* nem o cronograma.

- Se um commit produtor for encontrado, ele pode ser auditado como referência descritiva adicional, por nova decisão datada.
- Se não for encontrado, os números apresentados ficam sem proveniência verificável, e isso é registrado.

## D-E0\* — Gate substituto de sanidade para B1\*

O E1′ só é interpretado se B1\* passar nas quatro condições, todas avaliadas antes de qualquer resultado do E1′:

1. **Componentes:** todos os testes de comportamento passam: orientação dos scores dos seis detectores, ajuste EVT, invariância de prefixo da seleção e parada do protocolo secundário após Friedman com p > 0,05.
2. **Tarefas:** B1\* executa as 14 tarefas (13 regiões + PA) sob a injeção da camada 0 (D-GT1), com as duas classes presentes em cada tarefa.
3. **Sanidade contra um detector trivial:** B1\* supera um **z-score móvel causal** (janela de 12 meses, por região, alarme por calibração FAR idêntica) em AUC-PR média nas 13 regiões, com limite inferior do IC 95% da diferença pareada > 0 (bootstrap sobre regiões, 10.000 reamostras).
4. **Descritivo:** os números do original (3 detectores, bottom-up) são reportados apenas como descrição, nunca como alvo.

Falha em 1–3 torna o E1′ **inconclusivo** e abre diagnóstico. Não se ajusta B1\* olhando o resultado de 3.

## D2 — Qual MinT

**Decisão:** MinT(Shrink) conforme Wickramasuriya, Athanasopoulos & Hyndman (2019):

- Ŵ = λ̂·diag(Ŵ₁) + (1 − λ̂)·Ŵ₁, onde Ŵ₁ é a covariância amostral dos erros um passo à frente no treino e o alvo de encolhimento é **a sua diagonal**.
- λ̂ pelo estimador de Schäfer & Strimmer (2005) aplicado à matriz de correlação.
- Piso na diagonal de `1e-8 · max(trace(Ŵ)/14, 1)`. Projeção P = S (SᵀŴ⁻¹S)⁻¹ SᵀŴ⁻¹ calculada com `solve`, sem inversões explícitas e sem clipping.

O Ledoit–Wolf do sklearn (alvo identidade escalada) **não** é usado. S tem dimensão 14 × 13 (linha PA + identidade das 13 folhas).

## D3 — Detectores

**Decisão:**

- **LOF, KNN, HBOS:** PyOD sem o argumento `random_state` (são determinísticos).
- **IForest:** PyOD com semente derivada de `SeedSequence`.
- **PCA:** score de reconstrução do PyOD, com orientação "maior = mais anômalo" verificada por teste.
- **MCD:** FAST-MCD próprio, conforme E0 Tarefa 4; `MinCovDet` apenas em testes.

Paridade com o original só nas primitivas que o original executa sem erro; o critério dos seis detectores é comportamental.

## D5 — O que o MinT reconcilia

**Decisão:** reconciliar **previsões de contagem um passo à frente**, nunca scores de anomalia (scores não são aditivos).

- **Previsor base:** o mesmo modelo NB2 da D-GT3, ajustado por série (14 séries) apenas nos meses 0–59, produzindo μ̂ₜ para os meses 60–131. É estático após o treino e, portanto, causal.
- **Ŵ₁:** covariância dos resíduos in-sample um passo à frente do treino (meses 0–59).
- **Entrada dos detectores:** resíduos reconciliados eₜ = yₜ − P·μ̂ₜ, padronizados pelo desvio-padrão de treino de cada série. Como yₜ é coerente (S exata) e P·μ̂ₜ também é, os resíduos são coerentes por construção.
- **Reuso:** previsões e reconciliação são calculadas uma vez por réplica e compartilhadas por todos os braços.

**Braços resultantes (uma variável por braço):**

| Braço      | Entrada                                                                        |
| ---------- | ------------------------------------------------------------------------------ |
| B0         | resíduos base eₜ = yₜ − μ̂ₜ, sem reconciliação                                  |
| B1\*       | resíduos reconciliados por MinT(Shrink)                                        |
| B2         | B1\* + features de vizinhança em W (13 folhas; linha PA com zeros relacionais) |
| B2-placebo | B2 com W de cada placebo                                                       |

**Impacto nos planos:** E0 Tarefa 3 (interfaces de `reconcile`), grafo/simulação Tarefa 4 (as features passam a operar sobre resíduos) e Experimentos Tarefa 1 (`ArmSpec`). O ajuste NB2 fica num módulo `forecast.py`, justificado por ter dois chamadores (reconciliação e nulos da D-GT3).

## D6 — Seleção causal

**Decisão:** aprovar a E0 Tarefa 6 como escrita: competência calculada só na janela anterior a t; pseudo-rótulos por cutoff aprendido no treino; reset de competência por drift apenas para decisões futuras; teste de invariância de prefixo obrigatório. A auditoria confirmou que o original viola essa invariância nos meses 80–84, 87 e 89.

## D-GT1 — Camada 0: anomalias locais e não-inferioridade

**Injeção:** `inject_original_bounded`, com os mesmos tipos (spike, level shift, drift), magnitudes e ordem de consumo aleatório do original, mais duas mudanças:

- Level shifts e drifts têm **duração finita** entre 3 e 6 meses (inteiro uniforme). Spikes duram 1 mês.
- O onset fica restrito à janela de teste (meses 60–131), de modo que a anomalia termine até o mês 131.

O `inject_original` literal permanece apenas como fixture de caracterização do defeito, em `tests/`.

**Critério de não-inferioridade:** limite inferior do IC 95% da média de ΔAUC-PR(B2 − B1\*) ≥ −0,02. O IC vem de bootstrap pareado (10.000 reamostras) com unidade de reamostragem **as 13 regiões**. O PA é soma das regiões, então é reportado à parte e fica fora do bootstrap. Uma piora é reportada como custo do método, não como refutação da RQ1′.

## D-GT2 — Camada 1: injeção epidêmica

Substitui o pulso ad hoc, sem análise de sensibilidade paralela.

- **Motor:** os casos são produzidos pelo componente de surto de `simulate.py` com ν = 0 e acoplamento C = (1 − ε)·I + ε·W, e somados a uma cópia das contagens reais. PA é recalculado como soma das 13 folhas. Não se cria outro simulador.
- **Proveniência:** o motor mantém, por região, dois fluxos de infecção separados: **local** (transmissão interna) e **importado** (termo de acoplamento). A observação binomial é aplicada uma única vez ao total, e a parcela importada observada é registrada.
- **Onsets:** o da semente é o mês de introdução. O de cada região não-semente é o primeiro mês com caso importado observado ≥ 1, ou −1 se não ocorrer. Com ε = 0, nenhuma infecção pode surgir fora da semente.
- **Oráculo:** o grafo gerador é A, então B2 é oráculo nesta camada e na camada 2. A evidência relevante é B2 vs. placebo e o padrão em ε.

**Pendência:** o perfil completo do simulador (parâmetros aprovados na grafo/simulação Tarefa 2, após a validação de uma região).

## D-GT3 — Nulo paramétrico para calibrar a FAR nos dados reais

- **Modelo por série**, ajustado só nos meses 0–59, com t em meses:

  log μₜ = β₀ + β₁·t + Σₖ₌₁² [aₖ·sen(2πkt/12) + bₖ·cos(2πkt/12)]

  Binomial negativa NB2 com dispersão estimada por máxima verossimilhança (statsmodels).

- **Conjuntos:** 200 séries de calibração + 200 séries de avaliação por região, disjuntas, simuladas para os meses 60–131.
- **Alvo e tolerância:** FAR alvo 1/60 por região-mês; tolerância observada 1/300.
- **Falha de ajuste:** se o ajuste de uma região não convergir, a falha é registrada, a região é calibrada pelo bootstrap em blocos do treino e marcada em todos os artefatos.
- **Papel do bootstrap em blocos:** nas demais regiões, é apenas diagnóstico.
- **Limitação:** o nulo é um proxy ajustado ao treino e não prova ausência de surtos naturais.

## D-GT4 — Escala, forma e onsets da camada 1

- **Tamanho:** casos observados em excesso na **região-semente**. O alvo esperado é k × max(mediana mensal de treino, 1), com k ∈ {1, 3, 6}. O tamanho realizado é sempre reportado junto do alvo.
- **Introdução:** mês uniforme em 72–118, inclusive. θ igual ao da bancada sintética.
- **Truncamento:** surtos cortados no mês 131 são permitidos e contados; a fração truncada é reportada por célula.
- **R0:** sorteado de uma faixa fixa, declarada como escolha de desenho e não como estimativa epidemiológica.

**Pendência:** o valor numérico da faixa de R0, a fixar junto com o perfil do simulador (D-GT2), antes de qualquer execução da camada 1. Não inferir do resultado.

## D-COST — Piloto de custo e escada de redução

- **Quando:** piloto em ~02/10, após detectores e simulador acoplado. Medir tempo e RAM por réplica e por braço; o custo de componentes ainda inexistentes é estimado e declarado.
- **Gatilhos (projeção da execução completa no hardware registrado):**
  - acima de 48 h → degrau (a): os 30 placebos são avaliados num subconjunto fixo de 100 réplicas T por célula, com B2 avaliado nas mesmas T; calibração e avaliação N ficam completas;
  - acima de 96 h → degrau (b): 500 T + 500 N → 200 T + 200 N por célula;
  - se ainda insuficiente → degrau (c): cortar opcionais.
- **Restrições:** a escada é aplicada antes de ver qualquer efeito. Nenhuma redução corta a camada 0 nem altera a ordem de porte.

**Pendência:** registrar o hardware (CPU, núcleos, RAM, SO/WSL) em `docs/reference-provenance.md` antes do piloto.

## D-REACH — Alcance mínimo da propagação

Antes de rodar os braços, reportar por célula (tipo de ruído × ε) a fração de réplicas T com onset em pelo menos um vizinho da semente.

- **Mínimo:** ≥ 50% em ε = 0,20, avaliado **separadamente para cada tipo de ruído**.
- **Abaixo do mínimo:** a célula é reportada como de **poder insuficiente**, não como evidência negativa.
- O gerador não é ajustado para atingir a meta.

## D-L3 — Camada 3: eventos reais

Leitura qualitativa no notebook `02_e1_results.ipynb`, sem critério formal. Prioridade: camada 0 obrigatória; camada 1 antes de B-Gao, Φ/B3 e SEIRS.

**Pendência:** escolher os eventos (candidato: a alta sustentada de 2016 apontada por Eze et al., 2023) e verificar as fontes antes de descrevê-los como observados.

## D-OPS — Operação

- Mover a worktree de `/tmp` para um caminho persistente (`git worktree move`).
- O script auxiliar `scripts/_reference_primitives.py` e a exclusão de `*.md` no ruff format são aceitos e registrados no `MIGRATION.md`.
- A renomeação `net-sci` → `net-sci-epi` no commit da Tarefa 1 fica como está. Daqui em diante, mudanças não commitadas do usuário não entram em commits de tarefa.
- Commits locais convencionais; sem push.

---

## Gates preservados

G0–G7 continuam condicionais.

- **G0:** resolvido pela saída (i); o **E0 é registrado como inconclusivo**, jamais como paridade aprovada. O gate que libera o E1′ passa a ser o **E0\***.
- **Falhas:** uma falha de E0\*, de FAR ou de outro gate torna o E1′ inconclusivo.
- **Análise principal da camada 2:** bootstrap pareado → rank dos 30 placebos → critério conjunto.
- **Camada 1:** usa o mesmo critério, depois que D-GT2 e D-GT4 estiverem sem pendências.
- **Camada 0:** usa o critério de não-inferioridade da D-GT1.
- Não comparar braços em FAR diferentes.

## Critérios do adaptador epidêmico

- Remover o pulso, sem sensibilidade paralela.
- Reutilizar o motor com ν = 0 e casos observados não negativos, sem aplicar θ duas vezes.
- Testar:
  - isolamento com ε = 0;
  - meses 0–59 intactos;
  - tamanho relativo à mediana de treino;
  - onsets e censura;
  - PA recomputado;
  - entrada não mutada;
  - determinismo;
  - proveniência local/importado.
- O ruído não pode criar casos espontâneos fora da semente no controle ε = 0.
- A soma supõe ausência de interação com o fundo endêmico, inclusive depleção de suscetíveis compartilhados.

## Referências das decisões

- Wickramasuriya, S. L., Athanasopoulos, G., & Hyndman, R. J. (2019). Optimal forecast reconciliation for hierarchical and grouped time series through trace minimization. _JASA_, 114(526), 804–819.
- Schäfer, J., & Strimmer, K. (2005). A shrinkage approach to large-scale covariance matrix estimation and implications for functional genomics. _Statistical Applications in Genetics and Molecular Biology_, 4(1), Art. 32.
- Eze, P. U., Geard, N., Mueller, I., & Chadès, I. (2023). Anomaly detection in endemic disease surveillance data using machine learning techniques. _Healthcare_, 11(13), 1896.

## Confirmação operacional — Task 9 (28/09/2026)

O autor confirmou seguir D5/D-GT1: duração completa de 3–6 meses, sem
truncamento, e PA recalculado como soma das 13 regiões. Para preservar a
ordem de consumo aleatório, sorteiam-se os onsets propostos em 60–131;
onsets tardios são deslocados para `min(onset, 132 − duração)`, sem novo
sorteio. Registrar onset proposto e realizado. Isso concentra eventos tardios
no último início admissível; não se alega uniformidade dos onsets realizados.
A máscara de PA é a união das máscaras regionais. Sobreposições não são
removidas e não há resampling para garantir duas classes.

Com seed 42, PA tem 72 meses positivos na janela de teste. A condição de duas
classes em todas as 14 tarefas falha; E0* não libera interpretação de E1′.
Não alterar seed, rótulos ou baseline para obter aprovação. A implementação
das etapas L0 pode prosseguir, mas a interpretação permanece bloqueada.
O escopo confirmado é preparar as próximas etapas, sem antecipar o simulador
ou escolher seus parâmetros científicos pendentes.

## Pendência PA — registro documental de 28/09/2026

**Status:** pendente; nenhuma alternativa científica aprovada por esta atualização.
**Responsável pela decisão futura:** autor do projeto, Vinícius Costa.
A aprovação das revisões dos planos autoriza documentação e verificações técnicas,
não altera D-E0*, D-GT1 nem o resultado oficial da seed 42.

Enquanto D-E0* não for revisado, a comparação B1* × `rolling_zscore` nas 13 regiões
fica selada, inclusive como diagnóstico. Só verificações técnicas P1–P3 e classes
no fluxo E0; P4/P6 e preparação condicionada de P5 podem avançar. Escolher o gate
regional depois de conhecer sua aprovação repetiria o problema de selecionar seeds.

A decisão deve responder, independentemente de scores: PA como união é um alvo
com sentido epidemiológico ou artefato da agregação? RQ1′ exige discriminação
agregada ou coerência? Qual alternativa preserva melhor a comparabilidade com E0?
As quatro alternativas, seus custos e atividades permitidas estão no
[plano E0](superpowers/plans/2026-09-26-headd-l0-e0.md#decisão-pendente-sobre-pa--comparação-regional-selada).
Nenhuma foi escolhida: manter o protocolo; gate regional/PA descritivo; redesenhar
injeção; redefinir rótulo PA (esta última altera D-GT1 confirmado em 28/09).

A caracterização de máscaras em muitas seeds está **somente planejada**, sem
execução nesta entrega; nenhuma seed substitui a 42. Frequência amostral zero não
prova impossibilidade. Toda AP futura acompanha prevalência, janela e denominador;
contraste suficiente não se resume à existência de duas classes.

A decisão futura será acrescentada com data, responsável e justificativa; seu
commit deve preceder o primeiro commit de integração do scoring E0*. Este registro
de pendência não satisfaz essa precedência. E0 continua inconclusivo, E0* failed
(`single_class:PA`) e a interpretação de E1′ permanece bloqueada.
