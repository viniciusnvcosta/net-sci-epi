## Entregas

- aplica D-E0*-R1 e executa o scoring regional E0* com NB2 convergente;
- preserva a falha de E0*/FAR sem ajuste pós-resultado;
- constrói A/W para 13 regiões e 30 placebos conexos que preservam grau;
- adiciona features causais locais e relacionais;
- registra preparação científica P5 e o conflito ainda pendente no perfil Gao;
- adiciona CI para Ruff, suíte completa e build;
- versiona resumos pequenos com hashes da evidência local.

## Resultado atual

- E0: inconclusivo;
- E0*: falhou em `trivial_baseline` (limite inferior IC95% ΔAP = -0.20186060618499926);
- FAR: 23/26 pares dentro da tolerância; três falhas conservadoras;
- P4/P6: implementados e validados tecnicamente;
- P5: bloqueado pela decisão científica sobre paridade/perfil;
- interpretação de E1′: não autorizada.

## Verificação pré-merge

```text
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest -o addopts='' -q
uv build
```

O prazo dos resultados preliminares foi reprogramado de 16/10/2026 para
23/10/2026. A execução posterior segue o plano de continuidade versionado no
PR e só começa após revisão explícita.
