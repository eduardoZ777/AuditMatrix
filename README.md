# AuditMatrix

O AuditMatrix é um projeto criado com um objetivo claro: mapear, tratar e identificar os erros reais que ocorrem nos sistemas. Quando uma operação trava, a interface costuma exibir apenas um aviso genérico, enquanto a verdadeira causa da falha fica escondida. A origem do problema — como uma coluna inválida no banco de dados, uma violação de chave ou uma exceção interna — acaba soterrada em arquivos de log gigantescos e difíceis de interpretar. O projeto atua diretamente na solução desse problema, automatizando a triagem para que seja possível saber exatamente onde e por que a aplicação falha mais.

Para entregar essa solução, o script roda em segundo plano monitorando o arquivo de log original de forma contínua. Assim que o sistema registra uma linha confusa de erro, o código a intercepta na mesma hora. Utilizando expressões regulares, a aplicação limpa o texto bruto e extrai apenas a informação útil: a data, a tela que apresentou o defeito e o motivo técnico real da falha. O mapeamento desses dados consolidados permite analisar o comportamento do sistema e atuar na causa raiz. Para garantir a consistência de toda a extração, apliquei a biblioteca Pydantic na validação de cada registro.


## Como o Sistema Funciona

A lógica da aplicação separa totalmente a leitura do texto sujo da gravação do texto limpo, operando de forma assíncrona.

```mermaid
graph LR
    Sistema[Sistema Original] -->|Gera log confuso| log_ativo.log
    log_ativo.log -->|Monitoramento contínuo| Monitor[Script Python]
    Monitor -->|Regex & Pydantic| Limpeza[Mapeamento da Falha Real]
    Limpeza -->|Cria um arquivo por dia| output[auditoria_YYYY-MM-DD.txt]
