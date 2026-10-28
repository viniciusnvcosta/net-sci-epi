# Auditoria descritiva do conjunto integrado 2009–2019

Em 28/10/2026 o usuário disponibilizou `integrated_dataset.csv` no worktree. A leitura ocorreu em blocos e produziu apenas totais agregados, sem gravar ou imprimir registros individuais, sem construir OD e sem alterar fontes ou gates. O arquivo tem 4.398.056.867 bytes e SHA-256 `0a82aaecb02c5854149e22235a9e460abd82780d824c54ae5bd0fbd17902d05e`; a integridade e a versão Synapse não foram verificadas independentemente por checksum oficial. O arquivo regional L0 tem SHA-256 `ad61c77c8c187713cd47e72bb5f028eda1203e3f5e4962c5970d41abd9ae7188`.

## Resultado

O conjunto fornecido contém 22.923.977 linhas; 4.015.621 têm estado de notificação PA. Nos seis campos inspecionados (município, região e estado de notificação, resultado, mês e ano) não houve valores ausentes no recorte PA. A junção descritiva desses registros por município com as tabelas territoriais fornecidas, já auditadas em [Baroni, tabela e script](2026-10-27-baroni-tabela-e-script.md), encontrou todos os códigos e **nenhuma divergência município–nome regional**. Foram observados 143 pares município–região distintos nos registros PA; isso não demonstra registros para todos os 144 municípios do crosswalk. Os 24.629 registros de Tailândia presentes têm região de notificação Lago de Tucuruí.

A contagem por ano, mês, região de notificação e resultado coincide exatamente com o CSV L0 em todos os **7.592 grupos observados na união das duas fontes**, totalizando 4.015.621 linhas/contagens em cada. O mês foi normalizado removendo zero à esquerda. Grupos ausentes de uma das fontes foram tratados como zero apenas nesta comparação da união de grupos observados; o resultado não é uma auditoria de cobertura temporal ou ausência clínica.

| Ano | Grupos na união | Iguais |
| --- | ---: | ---: |
| 2009 | 937 | 937 |
| 2010 | 929 | 929 |
| 2011 | 919 | 919 |
| 2012 | 890 | 890 |
| 2013 | 701 | 701 |
| 2014 | 565 | 565 |
| 2015 | 550 | 550 |
| 2016 | 508 | 508 |
| 2017 | 557 | 557 |
| 2018 | 531 | 531 |
| 2019 | 505 | 505 |

## Interpretação e limites

O resultado fornece forte evidência de compatibilidade entre o conjunto integrado recebido, a relação municipal recebida e os totais da série L0 durante todo o intervalo. Isso reforça o candidato geográfico com Tailândia em Lago para alinhar o grafo à **série fixa de notificação**, mantendo P4 como referência histórica. Não comprova identidade de cada registro subjacente nem a cadeia e os bytes efetivamente usados por Eze; tampouco estabelece que a mesma regionalização era administrativamente vigente em todos os meses. Dados municipais não observados e dados de residência/infecção não foram validados. Os mapas e atos oficiais conflitantes continuam documentados na [análise geográfica](2026-10-27-geografia-l0-kernel-ganf.md).

Não houve avaliação de detector, geração de grafo de produção, alteração do perfil P5/G4, aprovação de G3 ou repetição de E0*/FAR. O plano aprovado mantém D1 sem aprovação administrativa e D2 OD suspenso; uma nova execução e escolha de geografia exigem protocolo e revisão prospectivos.

## Reprodução

Com os arquivos fornecidos na raiz do worktree e o CSV L0 no checkout principal, executar o [script de auditoria](2026-10-28-auditar-integrated-dataset.py) com o Python e dependências existentes. Ele compara as estatísticas de arquivo no início e no fim da leitura, usa apenas as seis colunas necessárias e imprime totais agregados. Conferir os hashes acima antes de reproduzir; o CSV integrado não é versionado neste projeto.

```bash
/home/vinvs/projects/net-sci-epi/.venv/bin/python docs/research/2026-10-28-auditar-integrated-dataset.py
```
