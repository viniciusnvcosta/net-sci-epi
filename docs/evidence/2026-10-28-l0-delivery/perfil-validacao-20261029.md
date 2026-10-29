# Ensaio de perfil NB2 — critérios registrados antes da comparação real

Ensaio diagnóstico, não protocolo do piloto. Fixar para as 14 séries da
fixture real `tests/reference/data.npz`: meses 0–59, desenho harmônico do
projeto, perfil log α no intervalo α ∈ [10⁻⁶, 10], GLM NB2 por IRLS com
tolerância 10⁻¹⁰ e otimização limitada com tolerância em log α de 10⁻⁸.
Comparar β e α da solução perfilada com o ajuste Newton existente, usando
|diferença|/erro-padrão Newton < 10⁻³ para cada parâmetro; erros-padrão devem
ser finitos e positivos. Qualquer falha de ajuste, borda ou EP invalida a
comparação, não autoriza reduzir a exigência. A fonte dos EP é a matriz de
covariância calculada no ajuste Newton sobre a mesma janela.

O escore na fronteira é a derivada unilateral do perfil, não garantia
automática de máximo global. Comparar explicitamente o perfil com Poisson e
não presumir unimodalidade. Este ensaio não autoriza execução de piloto,
não muda contratos de E0*/FAR e não produz nova decisão científica.

## Resultados exploratórios

O [ensaio sintético](perfil-nb2-20261029.txt), reproduzível pelo
[script](perfil-nb2-20261029.py), encontrou escores negativos nas sete séries
apontadas; a otimização delimitada parou perto de 10⁻⁶ e com verossimilhança
inferior à Poisson. Para Marajó I, Marajó II e Xingu, respectivamente,
obteve α ≈ 0,000335915, 0,000445608 e 0,000330332; os ganhos de
log-verossimilhança frente a Poisson foram 0,226, 17,152 e 0,877. O sucesso
do otimizador limitado não substitui verificação do ótimo global ou das bordas.

A comparação real em [perfil-real](perfil-real-20261029.txt), reproduzível
pelo [script](perfil-real-20261029.py), passou no critério das 14 séries;
todos os EP foram finitos e positivos e o maior desvio foi menor que 0,001 EP.
Não prova equivalência de scores ou FAR.

Um teste de diferenças finitas verifica a expressão do escore na fronteira
para médias fixas. Pelo teorema do envelope, aplica-se à derivada do perfil
em condições regulares. Sinal não positivo é condição local para fronteira;
sem prova de unimodalidade não basta, isoladamente, para afirmar máximo global.
Não foram feitos os testes de Monte Carlo de Poisson e binomial nem testes de
recuperação NB2 do estimador proposto. Nenhum dos scripts altera o estimador
do runner. A decisão de produção, integração e novo piloto permanecem abertos.
Posteriormente, os [testes de Monte Carlo](testes-perfil-20261029.md) foram
executados: o grupo NB2 de média alta não atingiu os critérios.

O caminho do piloto usa nulos do simulador e não chama `sample_nb2`; mesmo
assim, `_score` exige α > 0. Seus resíduos são divididos pelo desvio-padrão
empírico do treino (`reconcile.standardize`), não pela variância teórica
Poisson. Eventuais efeitos da subdispersão sobre scores e FAR devem ser
avaliados empiricamente, sem presumir variância residual padronizada inferior
a 1 no treino.
