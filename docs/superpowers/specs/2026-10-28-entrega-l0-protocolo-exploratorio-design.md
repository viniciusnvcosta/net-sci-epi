# Entrega L0 de 30/10: grafo e protocolo exploratório

**Data:** 28/10/2026. **Estado:** desenho para aprovação; não autoriza por si só
execução experimental, ratificação de G3, alteração de gates ou interpretação de
RQ1′. Prazo: 30/10/2026, fim do dia, America/Fortaleza.

## Objetivo e alternativas

Entregar à turma de mestrado e ao orientador um grafo candidato rastreável,
mapas e apresentação no padrão do PPT existente. Preparar uma demonstração
SIR exploratória se o piloto e o prazo permitirem; seu resultado pode ser
positivo, negativo ou inconclusivo. Desenhar GANF e comparações futuras, sem
implementá-los ou executá-los até 30/10.

O usuário escolheu **grafo e evidência primeiro, demonstração condicionada ao
piloto**, em vez de priorizar a execução SIR antes dos artefatos. O desenho
futuro de GANF não bloqueia a entrega. Não desenvolver M/OD nem alegar que se
recuperou a estrutura de transmissão real.

## Geografia, dados e artefatos

A fonte candidata é o manifesto v2 de SHA-256
`7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0`, com
A, W e 30 placebos. Confirmar hashes dos arquivos e dos insumos antes de usar;
nenhuma gravação altera v1/v2, P4, dados brutos ou resultados históricos.
Os arquivos locais e seus limites estão em
[arquivos locais](../../evidence/2026-10-28-geography-review/arquivos-locais.md).

Exportar GraphML direcionado: cada contato Queen de A gera dois arcos, cada
um com tipo `queen` e o peso de W da linha de origem. Cada nó terá nome,
código regional e população municipal do Censo IBGE 2010 agregada pelos 144
municípios da composição fixa candidata. Identificar fonte, ano, download,
licença, unidade, códigos, hashes e método; não substituir a população
sintética do simulador. Se população verificável não estiver disponível,
declarar o atributo ausente como pendência, sem fabricar valor ou chamar a
exportação completa.

O pacote inclui A, W, mapa e comparação P4, referenciados por hashes; P4 tem
25 arestas, candidata 26, com adição Lago de Tucuruí–Metropolitana II. Na
geometria candidata Tailândia não intersecta o restante de Lago e intersecta
Metropolitana II: o contato Queen pode decorrer desse componente não contíguo.
Descrever a consequência sem alegar erro ou causalidade epidemiológica.
Publicar sob identidade nova com manifesto e sem sobrescrever destinos.

A auditoria da série encontrou 7.592/7.592 contagens agregadas concordantes
nos grupos observados, 143 pares município–região compatíveis e 24.629
registros de Tailândia em Lago. Bonito (`150160`) não foi observado no recorte
PA; não inferir ausência de casos. Isso não prova bytes ou linhagem exatos.
Reproduzir o painel 13×132 a partir da fonte integrada e compará-lo ao painel
L0 após normalizar chaves, categorias, tipos, ordem e tratamento de ausências;
verificar igualdade semântica antes de comparar hashes de uma serialização
canônica explicitamente definida. Um hash diferente de CSVs com mesma tabela
não prova diferença de conteúdo. A fonte de Baroni identifica
`syn21555930` como dataset e `syn21555933` como dicionário; distinguir
identificador publicado e verificação dos bytes obtidos. Não reexecutar E0*
como consequência desta reprodução.

## Demonstração SIR: desenho prospectivo

A simulação gera sobre **A candidata**; para cada realização, os detectores
recebem respectivamente A, placebos da candidata e a variante A sem a aresta
Lago–Metropolitana II. A remoção corresponde a P4 neste par de matrizes, mas
é uma sensibilidade do grafo do detector, não do gerador. Nunca substituir
placebos da candidata pelos de P4. O runner atual não consome diretamente os
artefatos v2: o plano deverá estabelecer entrada explícita verificada por hash,
sem modificar o caminho histórico nem alegar que a capacidade já existe.

- Cenários exploratórios `ε ∈ {0, 0,20}`; A como gerador nos dois.
- Comparar B1*, B2 e z-score causal; B2 com A, com placebos escolhidos e com
  a variante sem aresta. A identidade de cada placebo é fixada antes dos
  resultados; não se infere rank dos 30 a partir de uma amostra.
- Contraste B2–B1* avalia o acréscimo relacional ao ensemble, não isola a
  geografia; A versus placebo compara alternativas no cenário gerado por A.
  Como A é conhecida pelo detector, a condição é de conhecimento da estrutura
  geradora, não recuperação de rede ou efeito no mundo real.
- Fixar antes do piloto métricas, pareamento, nulos, streams, FAR alvo,
  janelas, onsets, parâmetros, regra para sementes e procedimento de seleção
  de placebos no plano de implementação. Definir o teste de custo sem olhar
  métricas de desempenho e registrar tempo, memória, CPU, SO, dependências e
  GPU reais, sem dados pessoais desnecessários.
- Após o piloto e antes da demonstração, fixar numa decisão identificada o
  número de replicados, número e IDs de placebos e orçamento, em função apenas
  do custo e tempo disponíveis. Não alterar seeds, protocolo ou orçamento para
  reverter resultados. Não reaproveitar dados do piloto para resultados finais.
- Separar nulos de calibração e avaliação e aferir FAR por braço. Com orçamento
  insuficiente para FAR comparável e seus denominadores, resultados são apenas
  diagnósticos descritivos, sem afirmar ganho em lead time a FAR fixa. Reportar
  custo, amostra, incerteza e falhas; não declarar significância confirmatória.

As regras acima são desenho aprovado em conversa, não um protocolo executável
completo: o plano deve preencher explicitamente os campos restantes e prever
verificação antes de qualquer execução. O piloto deve levantar também os insumos exigidos para D-COST, incluindo
registro de hardware em `docs/reference-provenance.md`, custo por braço,
memória e projeção da bancada completa, com estimativas declaradas para
componentes faltantes. O plano verificará se os requisitos formais de D-COST
foram atendidos; enquanto faltarem evidências, ele permanece pendente. O
dimensionamento da demonstração é decisão própria e não modifica os números
do protocolo vigente. As
comparações SIR são demonstrações do pipeline e não validam RQ1′.

## GANF e outros estudos futuros

Desenhar, sem implementação nesta entrega, três condições: grafo geográfico
fixo, grafo aprendido e baseline sem informação relacional, com mesma divisão
cronológica. Formalizar arquitetura, direção da matriz, perda, mascaramento e
escala após revisar fontes originais e viabilidade: não presumir que qualquer
GANF aprende automaticamente o grafo SIR ótimo. Ajustar pré-processamento,
grafo e hiperparâmetros exclusivamente no treino; definir validação e teste
posteriores, impedir look-ahead e registrar seed e versões. Comparar detecção
sob calibração apropriada e analisar estabilidade do grafo separadamente.
Grafo aprendido representa dependência do modelo, não necessariamente
mobilidade, causalidade ou geografia epidemiológica. Comparações entre classes
precisam explicitar capacidade e custo; placebo/topologia são controles quando
adequados. Outras abordagens relacionais ficam como ideias futuras, sem
implementar GNN, mobilidade ou GANF nesta entrega.

## Apresentação, gates e critérios de entrega

Preservar PPT original e preparar cópia no mesmo padrão. Diferenciar orçamento
histórico de 500 T + 500 N e 9.000 simulações do D-COST vigente da camada 2:
200 T, 200 N de avaliação e 200 N de calibração por célula, com os 100 T
fixados para placebos. Não misturar esse orçamento com o piloto exploratório.
Trocar alegação de poder por propagação no cenário, usar “testar” em vez de
prometer ganho e indicar grafo candidato, hipótese de enclave e limites.

Mostrar separadamente: pré-gate histórico `single_class:PA`; regra posterior
com PA descritivo; E0* de 30/09 reprovado em `trivial_baseline` e FAR em três
pares; camadas incompletas e RQ1′ inconclusiva. A hipótese binomial de 72 meses
é somente ilustração com independência e probabilidade constantes. Não
inventar parecer do orientador, ratificar G3 ou alterar protocolo de E0*;
`interpretation_allowed=false` permanece para a hipótese.

A entrega é verificável quando arquivos, códigos, versões, comparações e
hashes estão identificados, os artefatos locais estão disponíveis e os slides
reproduzem corretamente as limitações. Se fonte, custo, implementação ou tempo
não permitirem a demonstração, relatar pendência e entregar grafo e
apresentação disponíveis sem transformar ausência de execução em sucesso.
Nenhum envio externo ou publicação está autorizado por este desenho.
