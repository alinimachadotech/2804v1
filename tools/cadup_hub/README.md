# CADUP Hub v2

Ferramenta CLI interna para consultas CADUP baseadas em MariaDB.

Esta etapa mantem o CADUP isolado do backend principal do Gerax Manager:

- nao registra rotas FastAPI;
- nao altera configuracoes do app principal;
- nao integra com frontend;
- nao usa credenciais hardcoded;
- nao altera a logica read-only do NextRouter.

## Variaveis de ambiente

O CLI le as seguintes variaveis:

- `DB_HOST`, padrao seguro: `127.0.0.1`
- `DB_PORT`, padrao seguro: `3306`
- `DB_USER`, sem padrao real
- `DB_PASSWORD`, sem padrao real
- `DB_NAME`, padrao seguro: `cadup_hub`

## Comandos

```powershell
python -m tools.cadup_hub.cli consultar-numero 551320201234
python -m tools.cadup_hub.cli capacidade --empresa "TIM" --tipo M
python -m tools.cadup_hub.cli ranking --tipo M --ddd 11
python -m tools.cadup_hub.cli gerar --nome-lote "teste_sp_movel" --empresa "TIM" --ddd 11 --tipo M --quantidade 100 --limite-por-faixa 10 --saida saida/teste_sp_movel.csv --com-55 --cabecalho destino
python -m tools.cadup_hub.cli consultar-lote 1
```

Se o banco nao estiver acessivel, o CLI exibe uma mensagem amigavel sem vazar
credenciais.

## Geracao controlada

O comando `gerar` sempre cria um lote antes de selecionar numeros, salva os
numeros em `cadup_numeros_gerados`, registra auditoria em `cadup_audit_log` e
gera um CSV simples com uma coluna.

Por padrao, a geracao aplica heuristicas de blacklist, respeita a tabela
`cadup_blocklist`, ignora numeros ja registrados anteriormente e limita a
quantidade por faixa.
