# Adoção dos trabalhos de Castro: primeira etapa

Data: 27/10/2026. **Status: proposta para aprovação do autor.**

## Intenção e abordagem

O autor solicitou iniciar a adoção recomendada após a revisão dos trabalhos
de Castro e colaboradores. A recomendação é começar pela proveniência e pela
definição do observável, antes de construir redes ou comparar modelos.
Este documento delimita essa primeira etapa; não registra aprovação antecipada
de implementação ou de um novo protocolo científico.

Foram consideradas três entradas:

| Entrada | Ganho e dependência | Encaminhamento proposto |
| --- | --- | --- |
| Proveniência e contrato de dados | Usa os arquivos existentes e explicita o que falta | Primeira etapa recomendada; este desenho |
| Construção de F infecção→notificação | Permite estudar fluxos observados; exige OD real datada e correspondência territorial | Etapa posterior condicionada aos dados |
| Baseline hhh4 e aprendizagem de grafo | Permite avaliar modelos adicionais; exige objetivo, validação e escopo próprios | Desenho separado posterior |

A solicitação de iniciar a recomendação é entendida como autorização para
preparar esta adoção gradual. O recorte documental e os critérios abaixo são
propostas do assistente, sujeitos à aprovação deste desenho.

## Evidência local reconferida

Em 27/10, leitura dos CSVs e SHA-256 confirmou que as cópias locais são
idênticas às fontes apontadas por `configs/data.toml`, em
`../hybrid-theory/data/raw`:

| Arquivo | Linhas | SHA-256 |
| --- | --- | --- |
| `PA.csv` | 132 | `ba437eff83a537addcdda93aca09401d5033804b83a0b767baa55788267041f5` |
| `PASIVEPDailyPerHr.csv` | 7.592 | `ad61c77c8c187713cd47e72bb5f028eda1203e3f5e4962c5970d41abd9ae7188` |

O CSV regional contém somente `notification.year`, `notification.month`,
`notification.hr`, `exam.result` e `testperhr`. O loader em
`src/headd_l0/data.py` agrega os resultados distintos de `negative`.
Isso estabelece a operação sobre contagens de exames positivos; não comprova
deduplicação por pessoa/episódio, município de infecção ou transformação
municipal que produziu `notification.hr`. Igualdade de bytes não resolve
essas lacunas semânticas.

Os achados externos já estão registrados na
[revisão Castro](../../research/2026-10-27-castro-malaria-mobilidade.md),
com fontes fixadas e limitações de acesso. A primeira etapa utilizará essa
auditoria como evidência datada, sem alegar nova reprodução dos estudos.

## Entrega proposta

Um único dossiê em `docs/research/2026-10-27-adocao-castro-proveniencia.md`,
com três partes:

1. Inventário dos dados existentes: caminho, fonte, hash, granularidade,
   campos, unidade observada e distinção entre verificado e desconhecido.
2. Matriz de lacunas: deduplicação, significado dos resultados diagnósticos,
   derivação de região, fronteiras municipais/regionais e suas vigências,
   datas de disponibilidade/revisão, documentação e autorização de uso.
   Cada item deve apontar evidência presente ou documento ainda necessário.
3. Contrato para uma futura tabela OD e checklist de elegibilidade para F.
   Preparar os requisitos não implica obter ou fabricar a tabela.

O contrato deve exigir `municipio_infeccao`, `municipio_notificacao`,
`ano`, `mes` e `n`, com definição da data de referência. Deve documentar
espécies/resultados incluídos, contagem de exames ou episódios, tratamento
de desconhecidos, duplicatas, completude, extração e disponibilidade temporal.
Ausência de vintage permite análise retrospectiva delimitada, mas não
comprova disponibilidade operacional no mês estudado.

A correspondência municipal→regional precisa explicitar códigos, fonte e
vigência. Devem permanecer identificáveis fluxos externos ao Pará e fluxos
intrarregionais. Valores ausentes não serão convertidos em zero sem evidência.

## Critérios de conclusão e limites

- Toda afirmação sobre dados locais aponta para arquivo/campo ou código;
  desconhecidos permanecem explicitamente desconhecidos.
- Fontes externas distinguem dados sintéticos, marginais derivadas e OD;
  marginais não são apresentadas como pares observados.
- O checklist termina com uma decisão de elegibilidade sustentada pela
  evidência. Concluir que F ainda é indisponível é um resultado válido.
- Não há requisito de obter dados externos para concluir o dossiê. Eventual
  contato com autores exige instrução explícita; nenhum contato será feito
  nesta etapa.
- Validação documental: conferir caminhos e links locais, hashes e campos
  contra os CSVs e ausência de alterações em dados, código e resultados.
  Não se exige executar experimentos ou a suíte completa para esta entrega.

A, F observada pela vigilância e acoplamento latente SIR permanecem objetos
distintos. Este trabalho não modifica `graph.py`, o simulador, configs,
dependências ou decisões de protocolo. Não implementa M, hhh4 ou GANF.
Preserva os resultados históricos e os limites de interpretação definidos em
[protocol-decisions.md](../../protocol-decisions.md).

Após aprovação deste desenho, o próximo passo é um plano de execução da
entrega documental. Construir F, escolher sua normalização, definir controles
dirigidos/ponderados ou iniciar comparação de modelos exige desenho próprio.
