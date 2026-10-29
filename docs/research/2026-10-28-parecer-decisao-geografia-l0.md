# Parecer para decisão prospectiva sobre a geografia L0

Data: 28/10/2026. **Estado: recomendação para deliberação; não é uma decisão
ratificada nem aprovação de gate.**

## Questão e recomendação

Recomenda-se escolher a composição fixa da tabela fornecida, com Tailândia em
Lago de Tucuruí, como **candidata principal para representar a série de
notificações L0**, sujeita a verificação técnica e revisão independente antes
de uso experimental. Manter P4 como referência histórica e comparação de
sensibilidade, com identidade e evidência próprias. Essa escolha é adequada
para uma pergunta retrospectiva sobre a série fixa; não estabelece qual
regionalização administrativa vigorou em cada mês nem qual grafo causa surtos.

Escolher P4 como principal manteria a continuidade direta com os artefatos
históricos, mas deixaria a diferença de Tailândia em relação à composição da
série observada. Exigir resolução administrativa mensal antes de qualquer
escolha asseguraria uma pergunta diferente, mas os atos e mapas disponíveis
não a resolvem e os totais regionais existentes não permitem redistribuir
municípios. A proposta recomendada aceita essa limitação explicitamente e
não a usa para atribuir vigência histórica.

## Evidência e limites para o decisor

| Evidência | O que apoia | O que não demonstra |
| --- | --- | --- |
| [Auditoria integrada 2009–2019](2026-10-28-auditoria-integrated-2009-2019.md): 7.592/7.592 grupos observados iguais; 143 pares municipais observados concordantes | Compatibilidade da composição fornecida com os totais regionais L0 e os registros observados | Identidade de todos os registros, linhagem exata, município não observado ou vigência mensal. |
| [Tabela e script fornecidos](2026-10-27-baroni-tabela-e-script.md): 144 municípios e Tailândia `150795 → 15004`; join sem chave temporal explícita | Definição operacional fixa da composição candidata | Versão oficial dos bytes e sua utilização na geração da série L0. |
| [Reagregação 2013](2026-10-27-auditoria-reagregacao-2013.md): 1.560/1.560 células com Lago; 1.502/1.560 com P4 | Compatibilidade adicional para 2013 e diferença entre as duas atribuições | Independência plena das fontes ou qualidade de OD. |
| [Atos e mapas conflitantes](2026-10-27-geografia-l0-kernel-ganf.md) | Limite claro da inferência administrativa | Resolução definitiva do conflito ou vigência anual de 2009–2019. |

Em conferência descritiva nesta data, usando os bytes P4 e da relação de
municípios fixados na [spec](../superpowers/specs/2026-10-28-geografia-serie-fixa-design.md),
os 144 polígonos municipais selecionados e as 13 regiões dissolvidas eram
válidos; a candidata teve 26 arestas e P4 25, com a única adição
Lago de Tucuruí–Metropolitana II. Nenhum artefato ou placebo foi gravado.
O primeiro ensaio de junção retornou zero linhas por conversão textual de
códigos numéricos com sufixo decimal; foi corrigido no diagnóstico e reforça
a necessidade de validar tipos e cardinalidade antes de qualquer produção.
Esse resultado reproduz a diferença topológica exploratória usando a geometria
do GeoParquet proposto, mas ainda não é validação independente de produção.

## Sequência de aprovação proposta

1. **Decisão de desenho**, pelo responsável científico: registrar a escolha
   candidata fixa, P4 como sensibilidade e a pergunta retrospectiva; aceitar
   expressamente as limitações acima. Essa decisão permite planejar e construir
   artefatos candidatos, não aprova automaticamente seu uso experimental.
2. **Verificação técnica**, com plano TDD próprio: integridade dos insumos;
   144 associações válidas e 13 regiões; Queen, W e comparação P4; 30 placebos
   novos distintos, conexos e com graus rotulados preservados; manifesto com
   hashes, parâmetros e identidade própria. Ausência ou divergência bloqueia
   a entrega; não alterar dados históricos para atingir o resultado esperado.
3. **Revisão científica independente** do pacote verificável: conferir a
   correspondência da série, fontes e licenças, geometrias, topologia, placebo,
   incerteza administrativa e consequências de usar geografia fixa. Registrar
   revisor, data, evidências, achados, decisão e limitações; um parecer do autor
   do código sozinho não constitui revisão independente.
4. **Decisão prospectiva de uso**, datada e registrada em
   `docs/protocol-decisions.md` somente depois de decisão explícita: identificar
   hashes dos artefatos e escopo, regra de comparação P4, gates aplicáveis e
   o que permanece inconclusivo. Se a evidência falhar ou a revisão não estiver
   disponível, manter candidata sem aprovação e registrar o impedimento.
5. **G3 e experimento são decisões distintas**: a escolha da representação e a
   produção técnica não implicam G3 aprovado. Verificar todos os critérios
   aplicáveis do protocolo, com seus responsáveis, antes de qualquer
   ratificação. Nova bancada exige plano separado para grafos de geração e
   detecção, nulos, FAR, pareamento e sementes; não repetir E0* sem as condições
   específicas vigentes. G4 permanece restrito ao perfil ratificado.

Até essas etapas terminarem, `interpretation_allowed=false` para a nova
evidência sujeita aos gates. P4 e runs históricos permanecem imutáveis; não
se infere desempenho, causalidade ou elegibilidade OD. O prazo de 30/10
justifica priorização, não dispensa evidência ou revisão independente.

## Texto proposto para uma futura decisão — ainda não aprovado

> Para uma análise retrospectiva da série fixa L0, selecionar como candidata
> a composição municipal da relação identificada por SHA-256 na spec, com
> Tailândia em Lago de Tucuruí; preservar P4 como referência histórica e
> sensibilidade. Esta seleção não afirma vigência administrativa mensal nem
> autoriza inferência experimental. O uso da candidata depende da validação
> técnica e revisão independente de artefatos identificados por hash, seguidas
> de decisão prospectiva específica. Falhas históricas e gates permanecem.

O responsável e a data devem ser preenchidos somente quando houver decisão
real. A aprovação deste texto não substitui revisão independente posterior.
