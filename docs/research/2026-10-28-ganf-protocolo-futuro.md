# GANF: protocolo futuro para a série L0

Estado: desenho exploratório, sem implementação, treinamento ou autorização de
inferência. [Dai e Chen, ICLR 2022](https://arxiv.org/abs/2202.07857)
propõem Graph-Augmented Normalizing Flows para densidade e anomalias em séries
múltiplas; o [repositório dos autores](https://github.com/EnyanDai/GANF) é
referência de implementação. Não se trata de uma GAN generativa adversarial.

O modelo fatoriza a densidade condicional por série e tempo; `A[i,j]` indica
`j` como pai de `i`. Um encoder de dependência usa a matriz e uma rede
recorrente para condicionar normalizing flows. A matriz contínua e os parâmetros
do flow são ajustados por máxima verossimilhança sob restrição diferenciável de
aciclicidade `tr(exp(A ⊙ A)) − n = 0` (artigo, seções 5.1–5.3). O código
original declara PyTorch 1.7.1; reprodução em versões atuais exigirá validação
própria. A verossimilhança é um escore de anomalia, não medida de infecção.

## Obstáculo da comparação com Queen

O GANF original exige um DAG. A adjacência Queen é não direcionada, e sua
representação com dois arcos por aresta cria ciclos de comprimento dois. Logo,
**W candidata não pode ser inserida literalmente como DAG fixo do GANF
original** mantendo sua interpretação probabilística. O desenho de três
condições requer uma decisão metodológica futura, antes de qualquer resultado:

1. Orientar arestas segundo ordem pré-declarada e acíclica, usar pesos
   compatíveis e denominá-la `Queen-orientada`; ela já não equivale à W completa.
2. Tratar Queen como máscara de arestas candidatas durante aprendizagem de um
   DAG, comparando ao DAG livre; isso difere de um grafo fixo.
3. Estudar modelo alternativo que aceite grafo cíclico, sem chamá-lo de GANF
   original nem presumir a fatorização do artigo.

A condição sem relações usa matriz zero e o mesmo modelo/capacidade sempre que
compatível. O protocolo final deve fixar orientação, máscara e eventual matriz
zero antes da avaliação, medir a restrição de aciclicidade e explicitar que o
DAG aprendido não é necessariamente causal, mobilidade ou grafo SIR ótimo.

## Desenho de avaliação proposto

- Preservar séries de contagens 13 × 132, chaves e valores faltantes; decidir
  normalização e janelas só no treino. Para dados reais não existem rótulos de
  surtos de referência independentes automaticamente disponíveis.
- Fixar cortes cronológicos de treino/validação/teste antes de comparar. O
  treino ajusta transformação e parâmetros; a validação escolhe configurações;
  o teste final é intocado. Evitar janelas que atravessam cortes ou incluam
  dados futuros. O tamanho de 132 meses limita precisão e treino neural.
- Comparar Queen-orientada ou máscara geográfica, DAG aprendido sem restrição
  geográfica e matriz zero; distinguir as condições que o código e a teoria
  realmente suportam. Registrar implementação, versões, seed, parâmetros,
  custo e convergência.
- Calibrar limiares em nulos independentes quando disponíveis e comparar FAR
  realizada com denominadores e incerteza. Avaliar AP e lead time apenas com
  rótulos e onsets justificados, sem ponto-ajustamento como métrica isolada.
- Para grafos sintéticos conhecidos, usar gerador separado e partições
  independentes, avaliar detecção e recuperação de estrutura como tarefas
  distintas. Não presumir que um DAG represente uma rede SIR bidirecional.
- Avaliar estabilidade entre seeds e janelas de treino: sobreposição de arestas,
  pesos e direção após limiar pré-declarado; incluir controles topológicos
  compatíveis com o modelo. Estabilidade não demonstra causalidade.

Antes de qualquer experimento, revisão das fontes, viabilidade e escolha da
representação precisam de desenho e aprovação separados. Sem resultados GANF
são afirmados nesta entrega; E0*/FAR e G3 permanecem como registrados.
