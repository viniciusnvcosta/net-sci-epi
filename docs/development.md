# Desenvolvimento e reprodução

O repositório dispõe dos componentes da baseline B1* e da preparação da
camada 0. Grafo, simulador acoplado, features relacionais e runner completo de
experimentos seguem os [planos de implementação](superpowers/plans/headd-l0-global.md).
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
`results/<run_id>/{injection.npz,events.parquet,tasks.parquet,pa_diagnostics.json,manifest.json}`.

Na seed 42, as 13 regiões têm ambas as classes nos meses 60–131; PA tem 72
positivos e 0 negativos pela união. D-E0*-R1 (28/09) aplica a condição de
classes somente às regiões. O pré-gate revisado retorna **exit 2**,
`E0_star.status = "pending"`, motivos vazios e `interpretation_allowed = false`.
Componentes e baseline trivial continuam `not_evaluated`; E0 permanece
**inconclusivo**. As 110 células negativas e 2 onsets ajustados da injeção
original permanecem, sem clipping nem novo sorteio.

`tasks.parquet` retém as 14 tarefas com prevalência, denominador 72, janela e
papel no gate. `pa_diagnostics.json` registra cobertura da união e coerência de
contagens/rótulos, sem reivindicar discriminação de PA. O manifest fixa revisão,
commit da decisão e versão da regra; resultados históricos nunca são sobrescritos.
Para repetir, use uma cópia do TOML com novo `run_id` e mantenha seed e protocolo.
O pré-gate histórico falhou em `single_class:PA`; a revisão técnica não aprova
E0* nem libera interpretação de E1′.

A execução real revisada em **2026-09-29T09:08:03Z** usou o commit limpo
`fb854f2d56c409f79cc0bd97df1d420d78afad7b` e uma cópia temporária do
TOML com `run_id = "second-execution-regional-preflight"` e
`raw_dir = "/home/vinvs/projects/hybrid-theory/data/raw"`; seed 42, baseline,
referência e `output_dir = "results"` permaneceram. Comando:
`uv run --locked python -m headd_l0.run /tmp/second-execution-regional-preflight.toml`.
Exit 2, E0 inconclusivo, E0* pendente, motivos vazios, interpretação bloqueada.
As regiões tiveram 14–29 positivos e 43–58 negativos; PA 72/0. O manifest
registra 110 células negativas, 2 onsets ajustados, revisão D-E0*-R1 e commit
da decisão `50f8b3f29bacc4747329addf80cee6719fe3c7fc`. Não houve scoring.

## Próximas etapas

1. Construir A/W e placebos em P4 e implementar features locais
   e relacionais em P6.
2. Preparar P5; definir o perfil científico pendente e validar uma região antes
   de acoplar.
3. Antes do scoring da Task 0, confirmar a tabela regional de classes e
   contraste sem cutoff escolhido por scores, além de features locais P6.
   P1–P3 e a revisão regional do pré-gate foram validados tecnicamente.
4. Integrar os componentes ao gate E0* e respeitar os demais gates antes de
   interpretar resultados. `configs/e1_bench.toml` ainda não está disponível.

## Documentação de referência

- [README](../README.md): problema, desenho experimental e descrição do projeto.
- [AGENTS](../AGENTS.md): regras de desenvolvimento e contratos dos componentes.
- [Protocolo](protocol-decisions.md): decisões aprovadas e questões científicas pendentes.
- [Migração](../MIGRATION.md): métodos portados, diferenças e testes de paridade.
- [Proveniência](reference-provenance.md): busca D-G0a, evidências e hardware D-COST.
- [Arquitetura](superpowers/specs/headd-l0-architecture.md) e
  [plano global](superpowers/plans/headd-l0-global.md): especificação e etapas de implementação.

Os importadores transitórios foram aposentados. Fixtures e hashes permanecem
em `tests/reference/`; o procedimento para recuperar o exportador histórico
está no registro de migração. O histórico de commits substitui inventários
intermediários de tarefas, versões de ferramentas e contagens de testes.
