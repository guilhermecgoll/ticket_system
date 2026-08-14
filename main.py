import json
import logging
import sqlite3
from typing import Optional, Union
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator

logger = logging.getLogger("ticket_system")

BM25_URL = "http://localhost:8008"

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
    .badge-score { background: #fef9c3; color: #854d0e; }
    .searching { color: #64748b; font-size: .9rem; padding: .5rem 0; }
    .tab-bar { display: flex; border-bottom: 2px solid #e2e8f0; margin-bottom: 1rem; }
    .tab-btn { background: none; border: none; padding: .4rem .9rem; font-size: .85rem; cursor: pointer; color: #64748b; border-bottom: 2px solid transparent; margin-bottom: -2px; }
    .tab-btn.active { color: #1e40af; border-bottom-color: #2563eb; font-weight: 600; }
    .tab-btn:hover { color: #1e40af; }
    .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .6rem; margin-bottom: .75rem; }
    .field-grid input { padding: .5rem .75rem; border: 1px solid #e2e8f0; border-radius: 6px; font-size: .875rem; outline: none; width: 100%; }
    .field-grid input:focus, .field-grid input:hover { border-color: #93c5fd; }
    .solve-box { margin-top: 1.25rem; border-radius: 8px; padding: 1.25rem 1.5rem; }
    .solve-yes { background: #f0fdf4; border: 1px solid #bbf7d0; }
    .solve-no  { background: #fef9c3; border: 1px solid #fde68a; color: #78350f; }
    .solve-section { margin-bottom: 1rem; }
    .solve-section:last-child { margin-bottom: 0; }
    .solve-section strong { display: block; font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; color: #166534; margin-bottom: .35rem; }
    .solve-no strong { color: #92400e; }
    .solve-section p, .solve-section ol { font-size: .875rem; line-height: 1.6; color: #1e293b; }
    .solve-section ol { padding-left: 1.25rem; }
    .solve-section ol li { margin-bottom: .25rem; }
    .solve-code { background: #0f172a; border-radius: 6px; padding: .75rem 1rem; margin-top: .5rem; }
    .solve-code pre { font-size: .8rem; color: #e2e8f0; white-space: pre-wrap; word-break: break-word; }
    .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 100; align-items: center; justify-content: center; }
    .modal-overlay.open { display: flex; }
    .modal { background: #fff; border-radius: 10px; padding: 1.5rem; width: 560px; max-width: 95vw; box-shadow: 0 8px 32px rgba(0,0,0,.2); }
    .modal h3 { font-size: 1rem; font-weight: 600; color: #1e40af; margin-bottom: 1rem; }
    .modal-footer { display: flex; align-items: center; gap: .75rem; margin-top: .75rem; }
  </style>
</head>
<body>
  <header><h1>Sistema de Chamados</h1></header>
  <main>
    <div class="card">
      <h2>Buscar Chamados Similares</h2>
      <div class="tab-bar">
        <button class="tab-btn active" id="tab-simples" onclick="setTab('simples')">Simples</button>
        <button class="tab-btn" id="tab-ponderada" onclick="setTab('ponderada')">Ponderada</button>
      </div>

      <div id="section-simples">
        <div style="display:flex;gap:.75rem;margin-bottom:1rem;">
          <input id="search-input" type="text" placeholder="Descreva o problema para encontrar chamados similares..."
                 style="flex:1;padding:.5rem .75rem;border:1px solid #e2e8f0;border-radius:6px;font-size:.875rem;outline:none;" />
          <input id="threshold-input" type="number" min="0" max="1" step="0.01" value="0.5" placeholder="Threshold"
                 style="width:110px;padding:.5rem .75rem;border:1px solid #e2e8f0;border-radius:6px;font-size:.875rem;outline:none;" />
          <button class="btn" onclick="buscar()">Buscar</button>
        </div>
      </div>

      <div id="section-ponderada" style="display:none">
        <div class="field-grid" style="grid-template-columns:1fr;">
          <input id="w-query" type="text" placeholder="Descreva o problema para encontrar chamados similares..." />
        </div>
        <div class="field-grid">
          <input id="w-modulo" type="text" placeholder="Módulo do sistema (opcional)" />
          <input id="w-top-n" type="number" min="1" step="1" placeholder="Top N resultados (opcional)" />
        </div>
        <div class="field-grid">
          <input id="w-release" type="text" placeholder="Releases separadas por vírgula (opcional)" />
          <input id="w-patch" type="text" placeholder="Patches separados por vírgula (opcional)" />
        </div>
        <div style="display:flex;gap:.75rem;margin-bottom:1rem;align-items:center;">
          <input id="w-threshold" type="number" min="0" max="1" step="0.01" placeholder="Threshold (vazio = sem filtro)"
                 style="width:220px;padding:.5rem .75rem;border:1px solid #e2e8f0;border-radius:6px;font-size:.875rem;outline:none;" />
          <button class="btn" onclick="buscar()">Buscar</button>
        </div>
      </div>

      <div id="search-results"></div>
    </div>
    <div class="modal-overlay" id="import-modal" onclick="fecharModal(event)">
      <div class="modal">
        <h3>Importar Chamados</h3>
        <textarea id="import-input" rows="8" placeholder='Cole aqui um objeto JSON { } ou um array [ ] de chamados...'
                  style="width:100%;padding:.5rem .75rem;border:1px solid #e2e8f0;border-radius:6px;font-size:.8rem;font-family:monospace;resize:vertical;outline:none;"></textarea>
        <div class="modal-footer">
          <button class="btn" style="background:#dcfce7;color:#166534;" onclick="importar()">Importar</button>
          <span id="import-status" style="font-size:.85rem;color:#64748b;"></span>
          <button class="btn" style="margin-left:auto;" onclick="document.getElementById('import-modal').classList.remove('open')">Cancelar</button>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="actions">
        <button class="btn" style="background:#dcfce7;color:#166534;" onclick="document.getElementById('import-modal').classList.add('open')">Importar</button>
        <button class="btn" onclick="load()">Atualizar</button>
        <button class="btn" style="background:#fee2e2;color:#991b1b;" onclick="limparBase()">Limpar Base</button>
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

    let activeTab = 'simples';
    let lastSolveQuery = '';
    let lastSolveDocuments = [];

    function setTab(tab) {
      activeTab = tab;
      lastSolveQuery = '';
      lastSolveDocuments = [];
      document.getElementById('section-simples').style.display = tab === 'simples' ? '' : 'none';
      document.getElementById('section-ponderada').style.display = tab === 'ponderada' ? '' : 'none';
      document.getElementById('tab-simples').classList.toggle('active', tab === 'simples');
      document.getElementById('tab-ponderada').classList.toggle('active', tab === 'ponderada');
      document.getElementById('search-results').innerHTML = '';
    }

    function renderResultados(data, wrap, query) {
      if (!data.length) {
        lastSolveQuery = '';
        lastSolveDocuments = [];
        wrap.innerHTML = '<p class="empty">Nenhum registro similar foi localizado.</p>';
        return;
      }
      lastSolveQuery = query;
      lastSolveDocuments = data;
      let rows = '';
      for (const r of data) {
        rows += `<tr>
          <td><span class="badge">${esc(r.numero_trm)}</span></td>
          <td>${esc(r.tipo_demanda)}</td>
          <td>${esc(r.modulo_sistema)}</td>
          <td style="max-width:260px">${esc(r.descricao_problema)}</td>
          <td style="max-width:260px">${esc(r.descricao_solucao)}</td>
          <td><span class="badge badge-score">${r.score.toFixed(2)}</span></td>
        </tr>`;
      }
      wrap.innerHTML = `<table>
        <thead>
          <tr><th>TRM</th><th>Tipo</th><th>Módulo</th><th>Problema</th><th>Solução</th><th>Score</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <div style="margin-top:1rem;display:flex;align-items:center;gap:.75rem;">
        <button class="btn" id="btn-solve" style="background:#e0e7ff;color:#3730a3;" onclick="buscarSolucao()">Analisar Solução com IA</button>
        <span id="solve-status" style="font-size:.85rem;color:#64748b;"></span>
      </div>
      <div id="solve-result"></div>`;
    }

    async function buscar() {
      const wrap = document.getElementById('search-results');

      if (activeTab === 'simples') {
        const q = document.getElementById('search-input').value.trim();
        if (!q) return;
        wrap.innerHTML = '<p class="searching">Buscando...</p>';
        const rawThreshold = document.getElementById('threshold-input').value.trim();
        const threshold = rawThreshold === '' ? null : parseFloat(rawThreshold);
        try {
          const res = await fetch('/buscar-similares', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: q, threshold})
          });
          if (!res.ok) throw new Error('Erro na busca');
          renderResultados(await res.json(), wrap, q);
        } catch (e) {
          wrap.innerHTML = '<p class="empty">Erro ao conectar com o serviço de busca.</p>';
        }
        return;
      }

      const q = document.getElementById('w-query').value.trim();
      if (!q) return;
      wrap.innerHTML = '<p class="searching">Buscando...</p>';

      const modulo     = document.getElementById('w-modulo').value.trim();
      const releaseRaw = document.getElementById('w-release').value.trim();
      const patchRaw   = document.getElementById('w-patch').value.trim();
      const topNRaw    = document.getElementById('w-top-n').value.trim();
      const thrRaw     = document.getElementById('w-threshold').value.trim();

      const payload = {query: q};
      if (modulo)      payload.modulo_sistema = modulo;
      if (releaseRaw)  payload.release = releaseRaw.split(',').map(s => s.trim()).filter(Boolean);
      if (patchRaw)    payload.patch   = patchRaw.split(',').map(s => s.trim()).filter(Boolean);
      if (topNRaw)     payload.top_n   = parseInt(topNRaw);
      payload.threshold = thrRaw !== '' ? parseFloat(thrRaw) : null;

      try {
        const res = await fetch('/search/weighted', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('Erro na busca');
        renderResultados(await res.json(), wrap, q);
      } catch (e) {
        wrap.innerHTML = '<p class="empty">Erro ao conectar com o serviço de busca.</p>';
      }
    }

    async function buscarSolucao() {
      const btn = document.getElementById('btn-solve');
      const statusEl = document.getElementById('solve-status');
      const resultEl = document.getElementById('solve-result');
      btn.disabled = true;
      statusEl.style.color = '#64748b';
      statusEl.textContent = 'Analisando com IA...';
      resultEl.innerHTML = '';
      try {
        const res = await fetch('/solve', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({query: lastSolveQuery, documents: lastSolveDocuments})
        });
        if (!res.ok) throw new Error('Erro na análise');
        const d = await res.json();
        statusEl.textContent = '';
        if (!d.solucionavel) {
          resultEl.innerHTML = `<div class="solve-box solve-no">
            <div class="solve-section"><strong>Sem solução identificada</strong><p>${esc(d.mensagem)}</p></div>
          </div>`;
        } else {
          const passos = (d.passos || []).map(p => `<li>${esc(p)}</li>`).join('');
          const fontes = (d.fontes || []).map(f => `<span class="badge">${esc(f)}</span>`).join(' ');
          const codigo = d.envolve_codigo && d.detalhes_codigo ? `
            <div class="solve-section">
              <strong>Detalhes técnicos</strong>
              <div class="solve-code"><pre>${esc(d.detalhes_codigo)}</pre></div>
            </div>` : '';
          resultEl.innerHTML = `<div class="solve-box solve-yes">
            <div class="solve-section"><strong>Análise</strong><p>${esc(d.analise)}</p></div>
            <div class="solve-section"><strong>Passos</strong><ol>${passos}</ol></div>
            ${codigo}
            <div class="solve-section"><strong>Fontes</strong><div>${fontes}</div></div>
          </div>`;
        }
      } catch (e) {
        statusEl.style.color = '#991b1b';
        statusEl.textContent = 'Erro ao analisar: ' + e.message;
      } finally {
        btn.disabled = false;
      }
    }

    async function importar() {
      const raw = document.getElementById('import-input').value.trim();
      const statusEl = document.getElementById('import-status');
      if (!raw) { statusEl.textContent = 'Cole um JSON antes de importar.'; return; }

      let payload;
      try {
        payload = JSON.parse(raw);
      } catch (e) {
        statusEl.style.color = '#991b1b';
        statusEl.textContent = 'JSON inválido: ' + e.message;
        return;
      }

      const firstChar = raw[0];
      if (firstChar !== '{' && firstChar !== '[') {
        statusEl.style.color = '#991b1b';
        statusEl.textContent = 'JSON deve começar com { ou [.';
        return;
      }

      statusEl.style.color = '#64748b';
      statusEl.textContent = 'Enviando...';
      try {
        const res = await fetch('/tickets', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const err = await res.text();
          throw new Error(err);
        }
        const data = await res.json();
        statusEl.style.color = '#166534';
        statusEl.textContent = data.inseridos + ' chamado(s) importado(s) com sucesso.';
        document.getElementById('import-input').value = '';
        document.getElementById('import-modal').classList.remove('open');
        load();
      } catch (e) {
        statusEl.style.color = '#991b1b';
        statusEl.textContent = 'Erro ao importar: ' + e.message;
      }
    }

    async function limparBase() {
      if (!confirm('Deseja apagar todos os chamados da base local e do índice de busca?')) return;
      try {
        const res = await fetch('/tickets', { method: 'DELETE' });
        if (!res.ok) throw new Error('Erro ao limpar a base');
        load();
      } catch (e) {
        alert('Falha ao limpar a base: ' + e.message);
      }
    }

    function fecharModal(e) {
      if (e.target === document.getElementById('import-modal')) {
        document.getElementById('import-modal').classList.remove('open');
      }
    }

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') document.getElementById('import-modal').classList.remove('open');
    });

    document.getElementById('search-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') buscar();
    });
    document.getElementById('w-query').addEventListener('keydown', e => {
      if (e.key === 'Enter') buscar();
    });

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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_trm TEXT NOT NULL,
                dados     TEXT NOT NULL,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )


init_db()


class SearchQuery(BaseModel):
    query: str
    threshold: Optional[float] = 0.5


async def _index_bm25(tickets: list) -> None:
    docs = [
        {
            "numero_trm": t.numero_trm,
            "tipo_demanda": t.tipo_demanda,
            "modulo_sistema": t.modulo_sistema,
            "objeto_afetado": t.objeto_afetado or "",
            "descricao_inicial": t.descricao_inicial,
            "descricao_problema": t.descricao_problema,
            "descricao_solucao": t.descricao_solucao,
            "release": t.release,
            "patch": t.patch,
            "tag_customizacao": t.tag_customizacao,
            "changesets": t.changesets,
            "data_liberacao": t.data_liberacao,
            "especifico_cliente": t.especifico_cliente,
        }
        for t in tickets
    ]
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{BM25_URL}/index", json=docs, timeout=10)
    except Exception as exc:
        logger.warning("BM25 indexação falhou (worker indisponível?): %s", exc)


def _coerce_str_list(v: Union[str, list, None]) -> Optional[str]:
    if isinstance(v, list):
        return ", ".join(str(i) for i in v) if v else None
    return v


class TicketIn(BaseModel):
    numero_trm: str
    tipo_demanda: str
    modulo_sistema: Optional[str] = None
    objeto_afetado: Optional[str] = None
    descricao_inicial: Optional[str] = None
    descricao_problema: str
    descricao_solucao: str
    release: Optional[Union[str, list]] = None
    patch: Optional[Union[str, list]] = None
    tag_customizacao: Optional[str] = None
    changesets: list[str] = []
    data_liberacao: Optional[str] = None
    especifico_cliente: bool = False

    @field_validator("release", "patch", mode="before")
    @classmethod
    def coerce_list_to_str(cls, v):
        return _coerce_str_list(v)


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

    await _index_bm25(parsed)

    return {"inseridos": len(inserted), "registros": inserted}


@app.post("/buscar-similares")
async def buscar_similares(body: SearchQuery):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BM25_URL}/search",
                json={"query": body.query, "threshold": body.threshold},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return []
    except Exception as exc:
        logger.warning("BM25 busca falhou: %s", exc)
        return []


class WeightedSearchQuery(BaseModel):
    query: str
    modulo_sistema: Optional[str] = None
    release: Optional[list[str]] = None
    patch: Optional[list[str]] = None
    top_n: Optional[int] = None
    threshold: Optional[float] = None


@app.post("/search/weighted")
async def buscar_similares_weighted(body: WeightedSearchQuery):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BM25_URL}/search/weighted",
                json=body.model_dump(),
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return []
    except Exception as exc:
        logger.warning("BM25 busca ponderada falhou: %s", exc)
        return []


class SolveQuery(BaseModel):
    query: str
    documents: list


@app.post("/solve")
async def solve(body: SolveQuery):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BM25_URL}/solve",
                json=body.model_dump(),
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("BM25 /solve retornou erro HTTP: %s", exc)
        raise
    except Exception as exc:
        logger.warning("BM25 /solve falhou: %s", exc)
        raise


@app.delete("/tickets")
async def clear_tickets():
    with get_conn() as conn:
        conn.execute("DELETE FROM tickets")
    try:
        async with httpx.AsyncClient() as client:
            await client.delete(f"{BM25_URL}/index", timeout=10)
    except Exception as exc:
        logger.warning("BM25 limpeza do índice falhou: %s", exc)
    return {"apagados": True}


@app.get("/tickets")
def list_tickets():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tickets ORDER BY criado_em DESC").fetchall()
        return [
            {
                "id": r["id"],
                "criado_em": r["criado_em"],
                "dados": json.loads(r["dados"]),
            }
            for r in rows
        ]
