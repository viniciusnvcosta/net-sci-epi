# Proposta: geografia alinhada à série fixa L0

Data: 28/10/2026. **Estado: proposta para revisão científica; não ratifica
protocolo, grafo, execução ou interpretação.**

## Objetivo e evidência

Preparar uma candidata de adjacência entre as 13 regiões da série fixa de
notificações, atribuindo Tailândia a Lago de Tucuruí, e compará-la com o P4
histórico. A escolha busca compatibilidade com o agrupamento observado da
série, não reconstrução comprovada da regionalização administrativa de cada mês.

A [auditoria integrada](../../research/2026-10-28-auditoria-integrated-2009-2019.md)
encontrou igualdade dos 7.592 grupos observados de região × mês × resultado
em 2009–2019 e 143 pares município–região observados concordantes com as
tabelas fornecidas. A tabela abrange 144 municípios de PA: o município não
observado não foi validado por registros. Essa comparação não prova identidade
dos registros ou da cadeia de produção. O conflito entre atos CIR/CIB e os
mapas DATASUS permanece [documentado](../../research/2026-10-27-geografia-l0-kernel-ganf.md).

## Entradas propostas

Os caminhos a seguir são locais e podem exigir restauração; conferir SHA-256
antes de uso. Os arquivos recebidos não devem ser incluídos no Git.

| Entrada | Caminho a partir do worktree ou absoluto | SHA-256 | Limite de acesso e proveniência |
| --- | --- | --- | --- |
| Relação municipal | `rl_municip_regsaud.csv` | `9de50c97ec32ab159cf8e7361da7cb7e2cd08692eaa213f06d8f77d19cf45f6f` | Fornecida pelo usuário; nome coincide com artefato Synapse, versão e checksum oficial não confirmados. |
| Nomes regionais | `tb_regsaud.csv` | `a386f78d581255487bbf047b753d0c7335f471310ab3635a8e6a8926401af77d` | Fornecida pelo usuário; não presumir códigos únicos sem o filtro auditado. |
| Geometria municipal P4 | `/home/vinvs/projects/net-sci-epi/.worktrees/_archive/2026-10-23/second-execution/data/processed/graph/healthregions_2013.parquet` | `42de74c7506a5ce52b46ba4d5abdde6b321eebf649b09c08f641fc2e56d8918e` | GeoParquet arquivado, distribuição e linhagem discutidas na análise geográfica; sua atribuição regional não é a candidata. |
| Série regional L0 | `/home/vinvs/projects/net-sci-epi/data/raw/sivep/PASIVEPDailyPerHr.csv` | `ad61c77c8c187713cd47e72bb5f028eda1203e3f5e4962c5970d41abd9ae7188` | Referência para observáveis e ordem temporal; não fornece composição municipal. |
| Integrado fornecido | `integrated_dataset.csv` | `0a82aaecb02c5854149e22235a9e460abd82780d824c54ae5bd0fbd17902d05e` | Evidência auditada; checksum oficial não confirmado; não é entrada necessária para gerar A. |

Os dois CSVs territoriais foram recebidos por acesso do usuário após resposta
403 ao download anônimo. Licença e direito de redistribuição dos bytes
específicos permanecem a confirmar; acesso ao artigo ou a metadados não prova
download anônimo nem autorização para republicação. A auditoria registra o hash
do conjunto integrado; ele não foi recalculado para esta spec.

## Composição e construção propostas

1. Ler a relação nacional com separador `;` e sem cabeçalho. Selecionar PA,
   registrar e excluir exclusivamente o agregado `150000 → 15000`, que não é
   município; não confundir as linhas nacionais externas com entradas inválidas
   da seleção de PA. Associar os códigos municipais de seis dígitos da tabela
   aos sete dígitos IBGE da geometria, removendo apenas o dígito verificador;
   validar formatos e verificar exatamente 144 códigos distintos em cada
   fonte e uma correspondência um-para-um, sem descartar ou multiplicar linhas.
2. Associar a cada município um único código de região da tabela; exigir os
   13 códigos e nomes canônicos de `PA_HEALTH_REGIONS_2013` e
   `hierarchy().leaves`. Para esta composição fixa, município `150795`
   pertence a `15004` Lago de Tucuruí. Duplicidade, ausência, código externo
   ou discrepância de nome bloqueia a construção.
3. Usar as geometrias municipais fornecidas, sem reparos silenciosos, dissolver
   por região e calcular contiguidade Queen na ordem canônica. Aplicar os
   contratos existentes `build_adjacency(regions, names)` e `row_normalize(A)`:
   simetria, diagonal nula, conectividade e ausência de ilhas são obrigatórias.
4. Comparar pares de arestas, graus por região e linhas de W com P4, mantendo
   ambos identificados. O cálculo exploratório indicou 26 versus 25 arestas e
   uma aresta adicional Lago–Metropolitana II; repetir o cálculo com insumos
   verificados. Divergência deve ser investigada, não corrigida por ajuste.

O recorte temporal é a série fixa 2009–2019, e não uma afirmação de que o
mapa é juridicamente vigente nesse intervalo. Para uma análise com geografia
administrativa variável seriam necessários dados municipais, atos de vigência
e regras de mudanças territoriais por período, além de desenho separado.

## Artefatos e verificação prospectivos

Após decisão científica e plano TDD próprios, gerar artefatos em diretório novo
que falhe se já existir; nunca alterar os dados brutos ou os artefatos P4.
O manifesto deve identificar versão da regra, hashes de cada entrada e saída,
commit, parâmetros, ordem das regiões, lista de arestas e graus, seed e estado
de construção. Exigir 30 placebos distintos, conexos e com graus rotulados
iguais aos da candidata; registrar seed e orçamento. Se não for possível
obtê-los, falhar explicitamente e não declarar sucesso.

O plano TDD deve cobrir município ausente, duplicado e externo; região/nome
não canônico; geometria vazia, ausente ou inválida; A desconexa, assimétrica
ou com diagonal; destino já existente; ordem e atribuição de Tailândia; Queen,
normalização e propriedades dos placebos. Fixtures pequenas não comprovam
proveniência; a comparação com fontes reais exige hashes verificados.

## Decisão e limites

Revisão deve decidir se a candidata é adequada como representação da série
fixa, se P4 é comparador de sensibilidade e quais controles, custos e gates
valem para eventual execução. Comparar apenas grafos não mede lead time ou FAR.
Uma bancada posterior deve especificar separadamente o grafo gerador e o de
detecção, nulos, calibração FAR, sementes e revisão independente.

D1 administrativo continua não aprovado e D2 OD suspenso. Esta proposta não
aprova G3, não amplia G4 além do perfil fixo, não apaga falhas E0*/FAR e não
autoriza conclusão sobre RQ1′. Não inclui M, GANF nem otimização de kernel.
