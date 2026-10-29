# Simulação epidêmica em grafos: revisão dirigida para HEADD L0

Consulta: **26/10/2026**. Revisão narrativa dirigida, com 20 trabalhos no núcleo
e um preprint adicional para acompanhamento. Não é revisão sistemática PRISMA:
não houve busca exaustiva em bases bibliométricas, deduplicação formal ou
reprodução computacional dos artigos.

**Conclusão:** os antecedentes mais próximos do HEADD combinam modelos
metapopulacionais, indicadores espaciais e problemas inversos mecanísticos.
GANF é uma referência para detecção por densidade, mas Li et al. (2026),
NIPA e os estudos de identificabilidade são mais próximos da proposta de
aprender um grafo associado ao SIR. A proximidade e as recomendações abaixo
são avaliações desta revisão, não resultados dos artigos sobre o HEADD.

## Pergunta e método de seleção

O contexto usado foi o desenho atual do [README](../../README.md): 13 regiões
de saúde, 132 meses, incidência observada, acoplamento
`C = (1−ε)I + εW`, detecção causal e comparação sob FAR semelhante.
As [decisões aprovadas](../protocol-decisions.md) continuam vigentes; esta
revisão não aprova experimentos, modifica o perfil ou reabre E0\*/FAR.

As buscas combinaram termos como `metapopulation SIR network simulation`,
`spatial early warning epidemic`, `epidemic network reconstruction surveillance`,
`graph topology epidemic encoder decoder`, `GANF` e `fixed degree graph sampling`.
Também foram seguidas referências dos trabalhos encontrados e das fontes Gao.
Priorizaram-se artigos originais, textos dos editores e manuscritos dos autores.
Revisões gerais, previsões GNN sem reconstrução ou simulação pertinente e
inferência apenas da origem de um surto não foram tratadas como evidência de
recuperação da topologia.

Os itens do núcleo tiveram texto integral consultado pelo editor ou versão
autoral, exceto Wesolowski et al., cuja avaliação aqui se limita ao resumo e
metadados verificados. Versões autorais podem diferir da edição final;
essa distinção está registrada quando material. O item adicional Looker foi
verificado por resumo/metadados: acesso ao integral bloqueado nesta consulta.

## Mapa de proximidade

| Necessidade do HEADD                 | Referências prioritárias                           | O que não transferir automaticamente                                               |
| ------------------------------------ | -------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Simular populações conectadas        | Colizza e Vespignani; Brockmann e Helbing          | Mobilidade explícita e mistura da força de infecção são mecanismos diferentes      |
| Usar sinais multirregionais          | Ghadami et al.; MacLaren et al.; Brett et al.      | Tendência de indicador ou ROC-AUC não estabelece ganho de lead time a FAR fixa     |
| Aprender rede de incidência regional | Wan et al.; NIPA; Li et al.                        | Bom ajuste ou previsão não comprova recuperação da rede real                       |
| Saber se a rede é recuperável        | Prasse e Van Mieghem; Beaufort et al.; Kiss et al. | Identificabilidade teórica não garante estimabilidade com amostra pequena          |
| Comparar rede conhecida e aprendida  | NRI; Li et al.; Braunstein et al.                  | Estados individuais, casos completos e observações mensais não são intercambiáveis |
| Detector neural com grafo aprendido  | GANF                                               | Grafo de dependências DAG não é automaticamente matriz de transmissão SIR          |
| Justificar controles topológicos     | Fosdick et al.                                     | Preservar graus e conectividade não prova mistura ou uniformidade finita           |

## Bibliografia comentada: simulação e propagação entre populações

**1. Colizza, V.; Vespignani, A. (2008). _Epidemic modeling in metapopulation
systems with heterogeneous coupling pattern: Theory and simulations_. Journal
of Theoretical Biology 251, 450–467.**

Deriva dinâmica de invasão entre subpopulações com conectividade e mobilidade
heterogêneas, validada por Monte Carlo. Distingue o limiar epidêmico local do
limiar global de invasão. É fundamento para interpretar alcance entre regiões.
O transporte explícito de indivíduos não é idêntico à mistura de pressão
infecciosa do HEADD; tampouco o artigo avalia detectores ou FAR.
[DOI e edição publicada](https://doi.org/10.1016/j.jtbi.2007.11.028);
[manuscrito integral](https://arxiv.org/pdf/0706.3647).

**2. Brockmann, D.; Helbing, D. (2013). _The hidden geometry of complex,
network-driven contagion phenomena_. Science 342, 1337–1342.**

Mostra como distância efetiva derivada dos fluxos da rede organiza tempos de
chegada e origem de epidemias, com simulação e aplicações SARS/H1N1.
Ajuda a distinguir fronteira geográfica, conectividade funcional e ordem de
chegada. Serve como referência para diagnósticos de propagação, não como
prova de antecedência de detecção ou justificativa para substituir A sem
novo experimento.
[DOI](https://doi.org/10.1126/science.1245200);
[texto integral](https://pdodds.w3.uvm.edu/research/papers/others/2013/brockmann2013a.pdf).

**3. Pandey, A.; Zhong, L.; Rennert, L. (2026). _Mobility-informed metapopulation
models predict the spatio-temporal spread of respiratory epidemics across
scales_. BMC Global and Public Health 4, 61. Publicado em 18/06/2026.**

Compara distância efetiva baseada em deslocamentos, aviação e modelo de
radiação, em simulações e dados regionais de COVID-19, influenza e RSV.
Avalia ordenação dos onsets. Ressalva decisiva: parte da validação empírica
estima onset retrospectivamente usando o pico e suavização da série.
Esse alvo não constitui alarme prospectivo sem look-ahead. É antecedente
para comparar representações de conectividade em estudo futuro.
[Artigo e métodos](https://doi.org/10.1186/s44263-026-00293-8).

**4. Wesolowski, A.; Eagle, N.; Tatem, A. J.; Smith, D. L.; Noor, A. M.;
Snow, R. W.; Buckee, C. O. (2012). _Quantifying the impact of human mobility
on malaria_. Science 338, 267–270.**

Combina padrões de mobilidade por telefonia e informação espacial sobre
malária para estudar dispersão parasitária no Quênia. É contexto aplicado
relevante à doença do HEADD, mas não valida SIR mensal no Pará nem Queen
como rede transmissora. A revisão não fez auditoria integral de suas
simulações; este item é contextual, baseado em resumo e metadados.
[Registro com resumo e DOI](https://pubmed.ncbi.nlm.nih.gov/23066082/).

## Bibliografia comentada: sinais precoces e simulação com ruído

**5. Gao, S.; Chakraborty, A. K.; Greiner, R.; Lewis, M. A.; Wang, H. (2025).
_Early detection of disease outbreaks and non-outbreaks using incidence data:
A framework using feature-based time series classification and machine
learning_. PLOS Computational Biology 21, e1012782.**

Fonte direta dos cenários T/N com ruídos white/env/dem. Compara atributos
de séries e classificadores, com testes externos. O gerador é de mistura
homogênea, sem grafo regional. Apesar do título, a variável simulada inclui
o estado I; transportar atributos para incidência mensal observada exige
validação própria. AUC e treinamento por janela não equivalem ao detector
congelado do HEADD sob FAR fixa.
[Texto e suplementos](https://doi.org/10.1371/journal.pcbi.1012782).

**6. Chakraborty, A. K.; Gao, S.; Miry, R.; Ramazi, P.; Greiner, R.; Lewis,
M. A.; Wang, H. (2024). _An early warning indicator trained on stochastic
disease-spreading models with different noises_. Journal of the Royal
Society Interface 21, 20240199.**

Predecessor de Gao: deep learning treinado em SIR estocástico com três
ruídos, comparado a autocorrelação e variância, com testes SEIR e Edmonton.
O contraste entre desempenho simulado e empírico, dependente da janela,
é especialmente relevante para transferência. Não testa contribuição de
arestas nem identifica um grafo. A leitura conjunta com Gao ajuda a separar
fonte algébrica, escolhas de implementação e capacidade de generalização.
[DOI](https://doi.org/10.1098/rsif.2024.0199);
[PDF dos autores](https://www.math.ualberta.ca/~hwang/rsif-2024-0199.pdf).

**7. Ghadami, A.; O’Dea, E. B.; Drake, J. M.; Rohani, P.; Epureanu, B. I.
(2023). _Anticipating epidemic transitions in metapopulations with multivariate
spectral similarity_. Nonlinear Dynamics 111, 17605–17615.**

Um dos antecedentes mais próximos: SIR em patches acoplados, ruído e
similaridade espectral entre séries; inclui notificações mensais de coqueluche
de 49 unidades continentais dos EUA. A demonstração central é aproximação
à eliminação, não detecção de surto propagado sob FAR igualada. A aproximação
linear perde precisão muito perto da transição. Não citar quantidade única
de patches sem conferir suplemento: o texto alterna descrições de oito e dez.
[Texto integral](https://doi.org/10.1007/s11071-023-08727-w).

**8. MacLaren, N. G.; Aihara, K.; Masuda, N. (2025). _Applicability of spatial
early warning signals to complex network dynamics_. Journal of the Royal
Society Interface 22, 20240696.**

Compara seis indicadores espaciais em 35 redes e quatro dinâmicas, incluindo
SIS. O desempenho depende de topologia e tipo de transição; CV e assimetria
espaciais são alternativas importantes. Avalia Kendall τ e comportamento
dos sinais, não lead time operacional a FAR fixa. No SIS, o estado de nó
não é uma contagem mensal regional. A versão autoral v2 contém seis
indicadores; a v1 tinha quatro.
[Metadados publicados](https://pubmed.ncbi.nlm.nih.gov/40328300/);
[texto v2](https://arxiv.org/html/2410.04303v2);
[DOI](https://doi.org/10.1098/rsif.2024.0696).

**9. Phillips, B.; Anand, M.; Bauch, C. T. (2020). _Spatial early warning
signals of social and epidemiological tipping points in a coupled
behaviour-disease network_. Scientific Reports 10, 7611.**

Simula contatos e opinião vacinal em duas camadas de rede, com SIRV.
Compara informação mútua, Moran, Geary e join counts. Seu lead time mede
distância no parâmetro de risco vacinal, usando mudanças nas médias das
realizações; não são meses de antecedência numa trajetória online.
Fundamenta investigar indicadores espaciais, mas não autoriza importar
o ranking deles para resíduos mensais de 13 regiões.
[Artigo integral](https://doi.org/10.1038/s41598-020-63849-0).

**10. Brett, T.; Ajelli, M.; Liu, Q.-H.; Krauland, M. G.; Grefenstette, J. J.;
van Panhuis, W. G.; Vespignani, A.; Drake, J. M.; Rohani, P. (2020).
_Detecting critical slowing down in high-dimensional epidemiological
systems_. PLOS Computational Biology 16, e1007679.**

Compara sinais precoces em cinco níveis de complexidade, do SEIR homogêneo
a redes multiplex e modelo individual FRED. Usa realizações estocásticas e
ROC-AUC para avaliar reemergência induzida por queda na vacinação.
Justifica testar robustez estrutural do indicador, em vez de depender só
do gerador simples. Não isola ganho de vizinhança regional com controle
placebo ou FAR pareada.
[Texto integral](https://doi.org/10.1371/journal.pcbi.1007679).

## Bibliografia comentada: recuperar rede e parâmetros epidêmicos

**11. Wan, X.; Liu, J.; Cheung, W. K.; Tong, T. (2014). _Inferring Epidemic
Network Topology from Surveillance Data_. PLOS ONE 9, e100661.**

Infere rede dirigida entre áreas a partir de casos novos diários de H1N1
em Hong Kong, com processos de Poisson, modelo linear generalizado e busca
genética. É próximo da observação regional, sem contatos individuais.
Validação usa ajuste/verossimilhança e critérios de informação; a rede
verdadeira não está disponível para conferir arestas. Os autores reconhecem
que ajuste melhor não verifica diretamente a reconstrução.
[Texto integral](https://doi.org/10.1371/journal.pone.0100661).

**12. Prasse, B.; Achterberg, M. A.; Ma, L.; Van Mieghem, P. (2020).
_Network-inference-based prediction of the COVID-19 epidemic outbreak in
the Chinese province Hubei_. Applied Network Science 5, 35.**

NIPA ajusta uma matriz de infecção dirigida com regularização LASSO para
prever epidemias em 16 cidades, usando modelo SIR e dados diários.
É uma alternativa mecanística relativamente simples à aprendizagem neural.
O próprio artigo separa precisão de previsão e precisão de reconstrução.
Episódio curto com parâmetros constantes não equivale a onze anos de
incidência mensal; casos notificados e prevalência infecciosa exigem
correspondência explícita.
[Texto integral](https://doi.org/10.1007/s41109-020-00274-2).

**13. Prasse, B.; Van Mieghem, P. (2020). _Network Reconstruction and
Prediction of Epidemic Outbreaks for General Group-Based Compartmental
Epidemic Models_. IEEE Transactions on Network Science and Engineering
7, 2755–2764.**

Estuda reconstrução em modelos compartimentais de grupos e mostra
mal-condicionamento severo: previsão pode ser excelente sem recuperar
numericamente a rede verdadeira. O resultado depende das observações e
modelo assumidos, não sendo impossibilidade universal. Para o HEADD,
fundamenta reportar previsão e recuperação de pesos como desfechos
separados, sobretudo com observação mensal parcial.
[DOI](https://doi.org/10.1109/TNSE.2020.2987771);
[registro dos autores](https://research.tudelft.nl/en/publications/network-reconstruction-and-prediction-of-epidemic-outbreaks-for-g/).

**14. Beaufort, L.-B.; Massé, P.-Y.; Reboulet, A.; Oudre, L. (2022).
_Network reconstruction problem for an epidemic reaction–diffusion system_.
Journal of Complex Networks 10, cnac047.**

Analisa identificabilidade e reconstrução de matriz de difusão, com
coeficientes epidemiológicos, condições iniciais e trajetórias S/I/R
observados. Difusão mais rápida pode homogeneizar trajetórias e dificultar
reconstrução; maior frequência de amostragem pode ajudar. O HEADD observa
menos informação e usa outro mecanismo de acoplamento. A contribuição
transferível é diagnosticar posto, condicionamento e simetrias antes de
interpretar pesos estimados.
[Edição publicada](https://doi.org/10.1093/comnet/cnac047);
[manuscrito integral anterior](https://arxiv.org/pdf/2109.11334).

**15. Kiss, I. Z.; Berthouze, L.; KhudaBukhsh, W. R. (2024; online em
08/12/2023). _Towards Inferring Network Properties from Epidemic Data_.
Bulletin of Mathematical Biology 86, 6.**

Estima parâmetros da doença e propriedades de redes de contatos por
modelos pairwise SIR, com simulações e aplicações empíricas. Mostra
dependência entre parâmetros e sensibilidade à observação, tamanho
populacional e subnotificação. Estimar grau de uma rede de indivíduos não
é reconstruir uma adjacência de regiões. Serve para discutir confundimento
entre conectividade e transmissibilidade, sem transferir o significado dos
parâmetros entre escalas.
[Texto integral](https://doi.org/10.1007/s11538-023-01235-3).

**16. Li, X.; Cohen, J.; Pilosof, S.; Puzis, R. (2026). _Learning graph
topology from metapopulation epidemic encoder-decoder_. arXiv:2603.02349v1,
submetido em 02/03/2026. PREPRINT; sem publicação revisada identificada.**

Combina encoder neural e decoder SIR mecanístico para inferir topologia e
parâmetros a partir de novas infecções regionais diárias. Testa epidemias
simuladas em grafos aleatórios e empíricos, inclusive contiguidade e
mobilidade. Múltiplos patógenos compartilham um grafo estático; avalia PR-AUC
de arestas, Jaccard, correlação e similaridade espectral. Não demonstra
recuperação em séries reais de notificação. O benchmark diário, parâmetros
constantes e mecanismo diferem do HEADD; as espécies de malária não podem
ser assumidas automaticamente como patógenos independentes do experimento.
[Texto integral v1](https://arxiv.org/html/2603.02349v1);
[DOI arXiv](https://doi.org/10.48550/arXiv.2603.02349).

## Bibliografia comentada: aprendizagem relacional e controles

**17. Braunstein, A.; Ingrosso, A.; Muntoni, A. P. (2019). _Network
reconstruction from infection cascades_. Journal of the Royal Society
Interface 16, 20180844.**

Reconstrói relações de transmissão de cascatas SIR estocásticas com belief
propagation e otimização de verossimilhança aproximada, incluindo observações
esparsas ou snapshots. Permite ciclos na rede física. A observação é de
estados individuais em múltiplas cascatas, diferente de incidência agregada
mensal. Mostra por que repetir epidemias independentes pode informar a rede;
não permite tratar janelas sobrepostas como novas cascatas independentes.
[DOI](https://doi.org/10.1098/rsif.2018.0844);
[manuscrito dos autores](https://arxiv.org/abs/1609.00432).

**18. Dai, E.; Chen, J. (2022). _Graph-Augmented Normalizing Flows for
Anomaly Detection of Multiple Time Series_. ICLR 2022.**

GANF aprende uma fatoração de densidade com DAG e normalizing flows,
usando restrição diferenciável de aciclicidade. Testa sistemas elétricos,
tratamento de água e tráfego; não apresenta benchmark SIR. É candidato
a detector exploratório. A estrutura aprendida organiza dependências;
interpretá-la como transmissão requer validação adicional. Reciprocidade
e ciclos do acoplamento epidêmico não cabem diretamente no DAG espacial.
[Texto integral](https://arxiv.org/html/2202.07857);
[código oficial](https://github.com/EnyanDai/GANF).

**19. Kipf, T.; Fetaya, E.; Wang, K.-C.; Welling, M.; Zemel, R. (2018).
_Neural Relational Inference for Interacting Systems_. ICML, PMLR 80,
2688–2697.**

NRI usa autoencoder variacional, arestas latentes e decoder de dinâmica.
Os benchmarks físicos incluem molas, partículas carregadas e Kuramoto,
não SIR. A contribuição transferível é avaliar separadamente recuperação
das relações e previsão em trajetórias independentes. O volume de treino
simulado é muito maior que um único segmento de 60 meses. O modelo não
impõe a restrição espacial DAG do GANF.
[Proceedings e PDF](https://proceedings.mlr.press/v80/kipf18a.html);
[código oficial](https://github.com/ethanfetaya/NRI).

**20. Fosdick, B. K.; Larremore, D. B.; Nishimura, J.; Ugander, J. (2018).
_Configuring Random Graph Models with Fixed Degree Sequences_. SIAM Review
60, 315–355.**

Referência metodológica para definir espaço amostral e distribuição dos
controles por trocas de arestas. Discute cadeias de Markov, restrições de
conectividade e mistura. Uma distribuição estacionária uniforme, quando
justificada para a cadeia, não garante amostras finitas uniformes e
independentes. No HEADD, é necessário distinguir a cadeia de propostas
da observação apenas de trocas aceitas. Não altera retrospectivamente
os controles existentes.
[DOI](https://doi.org/10.1137/16M1087175);
[texto autoral](https://arxiv.org/html/1608.00607v2).

**Acompanhamento adicional — Looker, J.; Rock, K. S.; Dyson, L. (2026).
_The covariance matrix of metapopulation disease models and applications
to early warning signals_. medRxiv, publicado em 12/05/2026. PREPRINT.**

Tema muito próximo: covariância não estacionária de modelos metapopulacionais
e sinais precoces. Resumo e metadados foram verificados; o texto integral
retornou bloqueio de acesso. Não extraímos conclusões quantitativas nem
o tratamos como evidência revisada. Há código e arquivo Zenodo indicados
pelos autores, ainda não auditados nesta revisão.
[Preprint](https://doi.org/10.64898/2026.05.08.26352721);
[código declarado](https://github.com/joshlooks/covariance-matrix).

## Síntese crítica para o HEADD

**Há quatro problemas científicos diferentes.** Simular propagação, antecipar
uma transição, prever incidência e recuperar a rede exigem validações distintas.
Ghadami e MacLaren contribuem para indicadores; NIPA para previsão; Beaufort,
Prasse e Li para reconstrução. GANF oferece detecção por densidade.
Nenhum resultado desses trabalhos, isoladamente, resolve a comparação do HEADD.

**O tipo de observação determina o que pode ser aprendido.** Uma trajetória
completa de S/I/R contém informação indisponível em notificações mensais.
Mudanças de escala, agregação, processo de observação, parâmetros e ruído
precisam aparecer no benchmark de transferência. Essa é nossa implicação
metodológica dos itens 5–8 e 11–17, não um teste já realizado no projeto.

**Boa previsão não confirma uma aresta transmissora.** Os itens 12–15
justificam separar desempenho preditivo, recuperação estrutural e incerteza.
No HEADD, 13 regiões produzem 78 pares não direcionados ou 156 dirigidos
sem autoarestas; os 132 meses são observações temporais multivariadas, não
132 epidemias independentes. Se o suporte de 25 arestas for mantido,
o problema é menor, mas os pesos ainda podem ser difíceis de identificar.

**Não há demonstração direta do critério conjunto do HEADD neste corpus.**
Entre os trabalhos examinados, não identificamos a combinação de grafo
regional geográfico versus placebos de grau, incidência mensal, detector
causal e ganho de antecedência sob FAR igualada. Isso delimita uma possível
contribuição; não é prova de originalidade bibliográfica universal nem
evidência de que a hipótese esteja correta.

**Moran não deve receber privilégio por convenção.** Os itens 8–10 justificam
avaliar mais de um indicador em desenho prospectivo. Contudo, acrescentar
features após examinar resultados altera o experimento. A literatura não
autoriza usar novos atributos para reverter o resultado histórico.

## O que esta revisão recomenda investigar

Estas são propostas de pesquisa, não uma spec aprovada ou autorização de execução.

1. **Reconstrução sob o gerador atual antes da aplicação real.** Criar um
   estudo separado com A/W conhecidos e o mesmo processo de observação
   mensal. Comparar estimação mecanística restrita, método inspirado em
   NIPA e encoder com decoder mecanístico inspirado em Li. Preservar
   parâmetros/perfil históricos; mudanças recebem desenho próprio.
2. **Avaliação em três eixos.** Medir recuperação de arestas e pesos,
   previsão em realizações independentes e ganho de detecção sob FAR
   comparável. PR-AUC de arestas não é a AP temporal de surtos. Similaridade
   espectral do grafo não é a similaridade espectral das séries de Ghadami.
3. **Identificabilidade e observação.** Variar prospectivamente frequência
   temporal, observação parcial e número de epidemias independentes.
   Em ε=0, W desaparece da dinâmica; recuperar suas arestas a partir desses
   surtos não é uma expectativa válida. Sincronização também merece diagnóstico.
4. **Comparação justa de gerador e detector.** Congelar o grafo gerador e
   treinar a rede candidata em dados separados da avaliação. Não selecionar
   a topologia geradora pelo maior ganho de B2 e depois usá-la como prova.
5. **GANF em pergunta própria.** Estudar se um grafo de dependências melhora
   detecção, preservando o detector e o orçamento adequados ao contraste.
   Trocar simultaneamente o grafo e todo o detector exige ablações para
   atribuir o ganho. Validar orientação, aciclicidade e tratamento de nós
   sem pais antes de qualquer conversão para acoplamento SIR.
6. **Nulo topológico definido antes da análise.** Usar Fosdick para
   explicitar rótulos, pesos, conectividade, distribuição-alvo, algoritmo,
   mistura e independência aproximada. Um grafo dirigido/ponderado aprendido
   exige controles compatíveis; os placebos binários atuais não se transferem
   automaticamente.

## Ordem de leitura e uso no texto científico

1. **Ghadami 2023 → MacLaren 2025:** entender sinais multivariados e dependência
   da topologia, preservando a diferença entre eliminação e emergência.
2. **Prasse e Van Mieghem 2020 → Beaufort 2022:** estabelecer os limites do
   problema inverso antes de escolher arquitetura.
3. **NIPA 2020 → Li 2026:** comparar alternativa mecanística simples com
   aprendizagem neural acoplada ao SIR; assinalar o caráter de preprint de Li.
4. **Gao 2025 → Chakraborty 2024 → Brett 2020:** relacionar fonte do gerador,
   ruído, janela e transferência entre níveis de complexidade.
5. **Fosdick 2018 → GANF 2022 → NRI 2018:** definir controles e só então
   delimitar o papel de grafos aprendidos na extensão de pesquisa.

Uma formulação sustentada por esta revisão seria: “Investigamos o valor
incremental da informação geográfica para detecção causal de surtos sob FAR
comparável; em estudo separado, avaliamos se relações estimadas sob restrições
mecanísticas são recuperáveis e úteis fora dos dados de ajuste.” Não se deve
afirmar que um grafo aprendido é a rede causal de transmissão sem validação
estrutural e de observação correspondente.
