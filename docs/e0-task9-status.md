# Task 9 e preparação L0 — 28/09/2026

A Task 9 entrega a injeção finita coerente, o z-score causal, a função do gate
E0* e a preparação executável. A integração de scores e calibração FAR de
B1*/zscore pertence à Task 4 do plano de experimentos.

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python -m headd_l0.run configs/e0_star.toml
```

O último comando retorna **2**, gerando `results/e0-star-preflight/` com
`injection.npz`, `events.parquet`, `tasks.parquet` e `manifest.json`. Não
sobrescreve runs existentes: para outra execução, use outro `run_id` em uma
cópia da configuração. Não troque a seed para buscar aprovação científica.

Resultado observado com seed42: as13regiões têm ambas as classes, mas PA
tem72meses positivos e nenhum negativo. O gate falha na condição de14tarefas
com ambas as classes. Há110células negativas e2onsets ajustados; sem clipping.
E0 segue inconclusivo; a comparação com z-score não foi executada. Nenhum
resultado E1′ está autorizado para interpretação.

## Próximas etapas

1. Construir A/W e placebos conforme o plano de grafo/simulação.
2. Definir o perfil científico pendente e validar uma região antes de acoplar.
3. Implementar features causais e o runner completo de experimentos, com
   calibração/avaliação nulas independentes.
4. Resolver por decisão explícita a inviabilidade de duas classes em PA neste
   protocolo antes de interpretar E1′; não ajustar o baseline pelos resultados.

O ambiente tem uv0.12.19 e Ruff0.16.9. Os importadores transitórios foram
retirados; fixtures e proveniência continuam versionadas. O código histórico
dos importadores pode ser recuperado do commit98187ee em diretório temporário.
Raw e artefatos de outros agentes não foram removidos.
