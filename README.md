# Sistema de Chamados

API e interface web para registro e consulta de chamados de suporte.

## Requisitos

- Python 3.10+

## Instalação

```bash
pip install -r requirements.txt
```

## Executando

```bash
uvicorn main:app --reload
```

A aplicação sobe em `http://localhost:8000`.

> Na primeira execução, o arquivo `tickets.db` é criado automaticamente no diretório corrente.

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Interface web |
| `POST` | `/tickets` | Registrar chamado(s) |
| `GET` | `/tickets` | Listar todos os chamados (JSON) |
| `GET` | `/docs` | Documentação interativa (Swagger) |

### POST /tickets

Aceita um objeto único ou um array de objetos.

**Payload:**

```json
{
  "numero_trm": "278163",
  "tipo_demanda": "Melhoria",
  "modulo_sistema": "Financeiro — Atributos de Cobrança / Itens de Cobrança",
  "objeto_afetado": "GnAtributoCobComissionados (coleção Classificação)",
  "descricao_problema": "Descrição do problema enfrentado pelo cliente.",
  "descricao_solucao": "Descrição da solução implementada.",
  "release": "6.00.147",
  "patch": "PacoteComplementar_6.0.143.7",
  "tag_customizacao": null,
  "changesets": ["TFS 92874", "TFS 92941"],
  "data_liberacao": "2021-07-15",
  "especifico_cliente": true
}
```

Campos obrigatórios: `numero_trm`, `tipo_demanda`, `modulo_sistema`, `descricao_problema`, `descricao_solucao`.

**Resposta:**

```json
{
  "inseridos": 1,
  "registros": [{ "id": 1, "numero_trm": "278163" }]
}
```

## Client Python

O arquivo `client.py` contém dois exemplos de payload prontos e um menu interativo para envio.

```bash
python client.py
```

```
Escolha o modo de envio:
  1 - Enviar um único chamado (primeiro exemplo)
  2 - Enviar múltiplos chamados (array com dois exemplos)
Opção:
```
