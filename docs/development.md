# Desenvolvimento e reprodução

O repositório dispõe dos componentes da baseline B1* e da preparação da
camada 0. Grafo, simulador acoplado, features relacionais e runner completo de
experimentos seguem os [planos de implementação](superpowers/plans/2026-09-26-headd-l0-global.md).
As decisões científicas vigentes estão em [protocol-decisions.md](protocol-decisions.md).

## Ambiente e comandos

Python ≥ 3.12, dependências geridas por uv e fixadas em `uv.lock`. A validação
usa pytest e Ruff; nenhuma instalação do CDADE legado é necessária para rodar
os testes com fixtures versionadas.

Execute da raiz do projeto, com `hybrid-theory` ao lado ou com `raw_dir`
ajustado nos TOMLs:

```bash
cd ~/projects/net-sci-epi
uv sync --locked
uv run python -m headd_l0.data configs/data.toml
uv run pytest -o addopts='' -q
uv run ruff check .
uv run ruff format --check .
uv build
```

A preparação SIVEP escreve `data/processed/sivep/` e
`results/data/manifest.json`; raw é somente leitura. O build escreve sdist e
wheel em `dist/`. Esses diretórios gerados são ignorados pelo Git.
`-o addopts=''` inclui os testes que a seleção rápida padrão exclui.

## Configuração

TOML é lido com `tomllib` para dataclasses congeladas, sem biblioteca adicional.
`configs/e0_star.toml` exige `run_id`, `root_seed`, `raw_dir` e `output_dir`.

| Campo | Contrato |
| --- | --- |
| `run_id` | Nome simples de diretório, não vazio; uma execução existente não é sobrescrita |
| `root_seed` | Inteiro não negativo; strings, floats e booleanos são rejeitados |
| `raw_dir`, `output_dir` | Caminhos não vazios, normalizados para `Path`; relativos ao diretório de execução |
| `baseline_id`, `reference_sha` | Identidade do protocolo aprovado; valores divergentes são rejeitados |

O runner E0 expande `~`. As configurações distribuídas usam
`../hybrid-theory/data/raw`; altere o TOML se os dados estiverem em outro local.
`E0Config.__post_init__` valida também a construção direta em Python.
`load_config` rejeita campos obrigatórios ausentes e nomes desconhecidos.

Os manifests registram configuração, seed, timestamp e proveniência Git do
código executado, independentemente do diretório corrente do chamador.
Imports de produção ficam no topo; Ruff aplica `PLC0415`, com exceção restrita
a testes que usam imports locais para fixtures e referências opcionais.

## Preparação da camada 0 e limite científico

```bash
uv run python -m headd_l0.run configs/e0_star.toml
```

Esse comando prepara a injeção e os diagnósticos; ainda não executa a comparação
B1*/z-score com calibração FAR. Os artefatos ficam em
`results/<run_id>/{injection.npz,events.parquet,tasks.parquet,manifest.json}`.

Com a seed 42 fixada, as 13 regiões têm ambas as classes, mas a união regional
rotula todos os 72 meses de teste de PA como positivos. O pré-gate retorna
**exit 2**, `E0_star.status = "failed"`, motivo `single_class:PA`, e
`interpretation_allowed = false`. E0 permanece **inconclusivo**. Foram observadas
110 células negativas e 2 onsets ajustados; não houve clipping nem novo sorteio.

Para repetir uma execução existente, use uma cópia do TOML com outro `run_id`,
mantendo seed e protocolo. Não escolha seeds ou ajuste o baseline para obter
aprovação. O bloqueio em PA exige decisão científica explícita antes de
interpretar E1′; a implementação dos componentes seguintes pode prosseguir.

## Próximas etapas

1. Construir A/W e placebos conforme o plano de grafo/simulação.
2. Definir o perfil científico pendente e validar uma região antes de acoplar.
3. Implementar features causais e o runner de experimentos, com conjuntos
   independentes de calibração e avaliação nulas.
4. Integrar os componentes ao gate E0* e respeitar os demais gates antes de
   interpretar resultados. `configs/e1_bench.toml` ainda não está disponível.

## Documentação de referência

- [README](../README.md): problema, desenho experimental e descrição do projeto.
- [AGENTS](../AGENTS.md): regras de desenvolvimento e contratos dos componentes.
- [Protocolo](protocol-decisions.md): decisões aprovadas e questões científicas pendentes.
- [Migração](../MIGRATION.md): métodos portados, diferenças e testes de paridade.
- [Proveniência](reference-provenance.md): busca D-G0a, evidências e hardware D-COST.
- [Arquitetura](superpowers/specs/2026-09-26-headd-l0-architecture.md) e
  [plano global](superpowers/plans/2026-09-26-headd-l0-global.md): especificação e etapas de implementação.

Os importadores transitórios foram aposentados. Fixtures e hashes permanecem
em `tests/reference/`; o procedimento para recuperar o exportador histórico
está no registro de migração. O histórico de commits substitui inventários
intermediários de tarefas, versões de ferramentas e contagens de testes.
