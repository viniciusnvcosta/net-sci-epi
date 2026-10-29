# Ensaio prospectivo: convergência IRLS por parâmetros

O lote anterior e a tentativa com início Poisson foram congelados no commit
`f4897d1`. A inspeção da réplica 2 da seed 204 confirma estabilização dos
coeficientes e oscilação da deviance com α `exp(log(1e-6))` e 600 meses.

## Regra e testes fixados antes da execução

- Copiar o harness diagnóstico original para um arquivo novo, sem modificá-lo.
  Única mudança: `tol_criterion="params"`, tolerância absoluta de 10⁻¹⁰,
  tolerância relativa padrão zero e demais parâmetros, grade e verificações
  inalterados. Não aplicar ao código de produção ou runner.
- Validar a trajetória da réplica 2/204 em α igual a `exp(log(1e-6))`:
  relatar séries de deviance e máximas variações em β; verificar que a nova
  regra termina antes de 100 iterações e retorna β finito.
- Registrar sementes **204 e 804** como regressão; para validação usar apenas
  **904**, nunca utilizada nesta comparação. Cada lote: 30 séries NB2, média
  3300, α=0,0005, 600 meses. Cada lote deve ter ≥27 válidos interiores,
  cobertura ≥24/30 e |viés| ≤3 EP Monte Carlo; falhas entram no denominador.
- Preservar lote original, candidata Poisson e todos os resultados negativos.
  Publicar por arquivo novo sem substituição, com hashes e valores por réplica.
- Reportar grade e limites, não inferir máximo global apenas do escore. Se
  algum lote falhar, não retunar e manter o piloto bloqueado. Se passar, é
  evidência diagnóstica, ainda sem autorização científica para alterar gates
  nem para executar bancada; revisar testes Poisson/binomial e 14 séries reais
  antes de qualquer integração futura.
