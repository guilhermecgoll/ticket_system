import json
import sqlite3
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Sistema de Chamados")

DB_PATH = "tickets.db"

HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sistema de Chamados</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f4f6f9; color: #333; }
    header { background: #2563eb; color: #fff; padding: 1rem 2rem; }
    header h1 { font-size: 1.4rem; font-weight: 600; }
    main { max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }
    .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 1.5rem; margin-bottom: 1.5rem; }
    h2 { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #1e40af; }
    table { width: 100%; border-collapse: collapse; font-size: .875rem; }
    th { background: #f1f5f9; text-align: left; padding: .6rem .8rem; font-weight: 600; border-bottom: 2px solid #e2e8f0; white-space: nowrap; }
    td { padding: .6rem .8rem; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
    tr.summary-row:last-of-type td { border-bottom: none; }
    tr.summary-row:hover td { background: #f8fafc; cursor: pointer; }
    .badge { display: inline-block; background: #dbeafe; color: #1d4ed8; padding: .15rem .5rem; border-radius: 4px; font-size: .8rem; font-weight: 600; }
    .badge-green { background: #dcfce7; color: #166534; }
    .empty { text-align: center; color: #94a3b8; padding: 2rem; font-size: .9rem; }
    .btn { background: #e0e7ff; color: #3730a3; border: none; padding: .4rem .9rem; border-radius: 6px; cursor: pointer; font-size: .85rem; }
    .btn:hover { background: #c7d2fe; }
    .status { font-size: .8rem; color: #64748b; margin-top: .75rem; }
    .detail-row td { padding: 0; border-bottom: 1px solid #e2e8f0; }
    .detail-box { display: none; background: #0f172a; padding: 1rem 1.25rem; overflow-x: auto; }
    .detail-box.open { display: block; }
    pre { font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: .8rem; color: #e2e8f0; white-space: pre-wrap; word-break: break-word; }
    .toggle-btn { font-size: .75rem; color: #6366f1; background: none; border: none; cursor: pointer; padding: 0; }
    .toggle-btn:hover { text-decoration: underline; }
    .actions { float: right; display: flex; gap: .5rem; align-items: center; }
  </style>
</head>
<body>
  <header><h1>Sistema de Chamados</h1></header>
  <main>
    <div class="card">
      <div class="actions">
        <button class="btn" onclick="load()">Atualizar</button>
      </div>
      <h2>Chamados Registrados</h2>
      <div id="table-wrap"><p class="empty">Carregando...</p></div>
      <p class="status" id="status"></p>
    </div>
  </main>
  <script>
    function esc(s) {
      return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    function toggle(id) {
      const box = document.getElementById('detail-' + id);
      box.classList.toggle('open');
    }

    async function load() {
      const res = await fetch('/tickets');
      const data = await res.json();
      const wrap = document.getElementById('table-wrap');
      const status = document.getElementById('status');
      status.textContent = data.length + ' chamado(s) — atualizado em ' + new Date().toLocaleTimeString('pt-BR');

      if (!data.length) {
        wrap.innerHTML = '<p class="empty">Nenhum chamado registrado ainda.</p>';
        return;
      }

      let rows = '';
      for (const t of data) {
        const d = t.dados;
        const changesets = (d.changesets || []).map(c => '<span class="badge badge-green">' + esc(c) + '</span>').join(' ');
        rows += `
          <tr class="summary-row" onclick="toggle(${t.id})">
            <td><span class="badge">${esc(d.numero_trm)}</span></td>
            <td>${esc(d.tipo_demanda)}</td>
            <td>${esc(d.modulo_sistema)}</td>
            <td>${esc(d.release ?? '—')}</td>
            <td>${changesets || '—'}</td>
            <td>${esc(d.data_liberacao ?? '—')}</td>
            <td>${new Date(t.criado_em + 'Z').toLocaleString('pt-BR')}</td>
            <td><button class="toggle-btn">ver JSON ▾</button></td>
          </tr>
          <tr class="detail-row">
            <td colspan="8">
              <div class="detail-box" id="detail-${t.id}">
                <pre>${esc(JSON.stringify(d, null, 2))}</pre>
              </div>
            </td>
          </tr>`;
      }

      wrap.innerHTML = `<table>
        <thead>
          <tr>
            <th>TRM</th><th>Tipo</th><th>Módulo</th><th>Release</th>
            <th>Changesets</th><th>Liberação</th><th>Registrado em</th><th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
    }

    load();
  </script>
</body>
</html>"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_trm TEXT NOT NULL,
                dados     TEXT NOT NULL,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_db()


class TicketIn(BaseModel):
    numero_trm: str
    tipo_demanda: str
    modulo_sistema: str
    objeto_afetado: Optional[str] = None
    descricao_problema: str
    descricao_solucao: str
    release: Optional[str] = None
    patch: Optional[str] = None
    tag_customizacao: Optional[str] = None
    changesets: list[str] = []
    data_liberacao: Optional[str] = None
    especifico_cliente: bool = False


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


@app.post("/tickets", status_code=201)
async def create_tickets(request: Request):
    body = await request.json()

    items = body if isinstance(body, list) else [body]
    parsed = [TicketIn(**item) for item in items]

    inserted = []
    with get_conn() as conn:
        for ticket in parsed:
            cur = conn.execute(
                "INSERT INTO tickets (numero_trm, dados) VALUES (?, ?)",
                (ticket.numero_trm, ticket.model_dump_json()),
            )
            inserted.append({"id": cur.lastrowid, "numero_trm": ticket.numero_trm})

    return {"inseridos": len(inserted), "registros": inserted}


@app.get("/tickets")
def list_tickets():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tickets ORDER BY criado_em DESC").fetchall()
        return [
            {"id": r["id"], "criado_em": r["criado_em"], "dados": json.loads(r["dados"])}
            for r in rows
        ]
