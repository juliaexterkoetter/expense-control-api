# Expense Control API

API REST em Python para cadastro, consulta, exclusão e consolidação de despesas operacionais usando SQLite.

O projeto foi construído com bibliotecas nativas do Python para facilitar execução em ambientes simples, sem depender de frameworks externos. Ele demonstra estrutura de backend, validação de dados, persistência em banco e geração de relatórios consolidados.

## Recursos

- Cadastro de despesas via JSON.
- Consulta de despesas cadastradas.
- Filtros por categoria e período.
- Consulta individual por ID.
- Exclusão de registros.
- Relatório consolidado por categoria.
- Persistência em banco SQLite.
- Testes automatizados cobrindo validação e regras principais.

## Tecnologias

- Python
- SQLite
- REST API
- JSON
- Testes automatizados

## Como executar

```bash
python src/server.py
```

Por padrão, a API fica disponível em:

```text
http://127.0.0.1:8000
```

Também é possível informar porta e banco de dados:

```bash
python src/server.py --port 8080 --database data/expenses.db
```

## Exemplos de uso

Criar uma despesa:

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d "{\"description\":\"Hospedagem do sistema\",\"category\":\"tecnologia\",\"amount\":\"120.50\",\"expense_date\":\"2026-08-26\",\"payment_method\":\"cartao\"}"
```

Listar despesas:

```bash
curl http://127.0.0.1:8000/expenses
```

Filtrar por categoria:

```bash
curl "http://127.0.0.1:8000/expenses?category=Tecnologia"
```

Gerar relatório por categoria:

```bash
curl http://127.0.0.1:8000/reports/categories
```

## Rotas

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/health` | Verifica se a API está ativa |
| POST | `/expenses` | Cadastra uma nova despesa |
| GET | `/expenses` | Lista despesas com filtros opcionais |
| GET | `/expenses/{id}` | Consulta uma despesa específica |
| DELETE | `/expenses/{id}` | Remove uma despesa |
| GET | `/reports/categories` | Consolida valores por categoria |

## Como validar

```bash
python -m unittest discover -s tests
```

## Estrutura

```text
src/
  database.py   Conexão e migração do banco SQLite
  expenses.py   Regras de validação e operações de despesas
  server.py     Servidor HTTP e rotas REST
tests/
  test_expenses.py
docs/
  APRESENTACAO_COMERCIAL.md
```

## Tags

`#programacao` `#python` `#backend` `#api` `#sqlite` `#automacao`
