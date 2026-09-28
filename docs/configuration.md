# Configuração de execução

A configuração permanece em TOML, lida com `tomllib` e representada por uma
dataclass congelada. Não há dependência adicional de configuração.

## Campos de E0

`configs/e0_star.toml` deve declarar `run_id`, `root_seed`, `raw_dir` e
`output_dir`. Esses campos não têm defaults no código: omiti-los é erro.

- `run_id`: nome de diretório simples, não vazio, sem caminhos relativos ou absolutos.
- `root_seed`: inteiro não negativo; booleanos, strings e floats são rejeitados.
- `raw_dir` e `output_dir`: caminhos não vazios, normalizados para `Path`.
  No runner E0, `~` é expandido. Caminhos relativos permanecem relativos ao
  diretório de execução, não ao arquivo TOML.
- `baseline_id` e `reference_sha`: identidade do protocolo aprovado. O código
  conserva constantes de validação e rejeita valores divergentes.

A validação está em `E0Config.__post_init__`, valendo tanto para TOML quanto
para construção direta em Python. `load_config` rejeita também campos
obrigatórios ausentes e nomes desconhecidos.

## Caminhos portáveis

Execute os comandos a partir da raiz do projeto:

```bash
cd ~/projects/net-sci-epi
uv sync --locked
uv run python -m headd_l0.data configs/data.toml
```

As duas configurações distribuídas usam `../hybrid-theory/data/raw`, supondo
os repositórios lado a lado. Se seus dados estiverem em outro local, altere
`raw_dir` no TOML, sem editar o Python. Os caminhos de saída também são
configuráveis. A seed 42 permanece fixada para esta execução científica;
a limpeza não muda o protocolo para tentar aprovar E0*.

O pré-gate usa `uv run python -m headd_l0.run configs/e0_star.toml` e continua
com o diagnóstico de PA de classe única. Se o `run_id` já existir, use outra
cópia da configuração com novo identificador, mantendo seed e protocolo.

## Imports e proveniência

Imports de produção ficam no topo do módulo. Ruff verifica isso com `PLC0415`;
a exceção é restrita a `tests/**`, onde imports locais atendem fixtures e
referências opcionais. `uv run ruff check .` executa essa regra.

O manifest de E0 consulta o Git associado ao módulo executado, independentemente
do diretório corrente do chamador. Essa mudança impede atribuir os artefatos
a outro repositório ao chamar `run_preflight` por Python.

A revisão também retirou os imports duplicados de `Path` e as referências
obsoletas a `CLAUDE.md` no README. Scripts históricos da auditoria continuam
aposentados; fixtures, hashes e documentação histórica são preservados.

## Verificação desta limpeza

Na pasta original, após a correção: **155 testes passaram** com
`uv run pytest -o addopts='' -q`; `uv sync --locked`, lint, format e `uv build`
terminaram com exit 0. A CLI de dados foi executada com o caminho relativo.
A CLI E0 foi exercitada com a mesma configuração e saída temporária isolada:
exit 2 esperado, `single_class:PA`, seed 42, 110 células negativas e 2 onsets
ajustados. Os arquivos temporários desse smoke foram removidos automaticamente.

A revisão independente dos arquivos de configuração, runner e testes não
identificou achados acionáveis. Os registros anteriores de 135 testes em
[pipeline-commands.md](pipeline-commands.md) descrevem a verificação anterior.
