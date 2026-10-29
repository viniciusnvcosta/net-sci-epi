# Testes diagnósticos do perfil NB2

Critérios, sementes e tamanhos registrados no
[plano](../../superpowers/plans/2026-10-29-testes-perfil-nb2.md), antes do
lote. O [harness](nb2_profile_harness.py) é diagnóstico e isolado; não altera
o previsor nem o runner. Resultados por réplica estão em
`results/l0-nb2-profile-monte-carlo-20261029-v1.json`, SHA-256
`a0c318ee14b4906a03e16a27e0c84b3dee111803c9dfbe9ca472603cb86d92e7`.
O JSON identifica a versão das bibliotecas e o hash do harness.

| Grupo | Válidos / total | Fronteira / total | Critério |
| --- | ---: | ---: | --- |
| Poisson, média 50 | 40/40 | 22/40 | Passou: 10–30 fronteiras. |
| Binomial, média 50 | 40/40 | 40/40 | Passou: ao menos 36 fronteiras. |
| NB2, média 50, α=0,1 | 30/30 | 0/30 | Passou: 30 interiores; cobertura 28/30; viés −0,001898, EP Monte Carlo 0,001148. |
| NB2, média 3300, α=0,0005 | 20/30 | 0/30 válidos | **Falhou:** 10/30 avaliações encontraram IRLS sem convergência; apenas 20 interiores válidos, abaixo do mínimo de 27. Cobertura 18/30 contando falhas no denominador, abaixo de 24. |

O viés no grupo de média alta foi −0,00001550 sobre as 20 réplicas válidas,
com EP Monte Carlo 0,00001017. O viés isoladamente ficou dentro do limite,
mas a exclusão dos dez ajustes inválidos impede concluir desempenho geral.
A cobertura conta intervalo de Wald em α, usando curvatura perfilada e 1,96;
falhas não entram no numerador. A mensagem de IRLS não informa se o erro
ocorreu na busca ou na grade de verificação: não se deve apresentar as dez
falhas como dez máximos finais não convergentes.

Nenhum ponto da grade superou Poisson nos casos classificados fronteira.
Em 16 Poisson e 24 binomiais a grade superou numericamente o resultado da
busca limitada, mas ambos estavam abaixo de Poisson: a comparação relevante
para a fronteira permanece com Poisson, e o fenômeno fica registrado no JSON.
Uma grade finita não comprova máximo global e os limites em α são numéricos.

Os ensaios anteriores para Marajó I, Marajó II e Xingu registraram máximos
interiores e sucesso do otimizador limitado; não são confirmação de que o
harness novo funcione em todos os perfis. A comparação pré-registrada das
14 séries reais passou para todos os parâmetros (<0,001 EP), conforme
[evidência anterior](perfil-validacao-20261029.md). Os respectivos arquivos
de saída têm SHA-256 `c81aa98087f44c23a83fcc1ecd27584c8afaa0023811aa77f0343e7d0371bb25`
e `12eed2e693f5dd0bd6423dd9f899c83ca7b946d246a851542ae1574de28a1193`.

Conclusão: os testes solicitados foram executados; o grupo de média alta não
passou e impede considerar o estimador validado. A decisão de integração,
nova regra do protocolo e piloto corrigido permanecem pendentes. Não repetir
ou escolher tolerâncias para apagar a falha; investigar o ponto de IRLS sob
novo diagnóstico separado e preservar este lote.
