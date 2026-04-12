from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/debug", tags=["observability"])

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Hub v2 Observability</title>
  <style>
    :root{
      --bg:#08111f;
      --panel:#13223d;
      --line:#294268;
      --text:#dce7f8;
      --muted:#8ea3c2;
      --strong:#f9fbff;
      --blue:#5d85ff;
      --green:#32c48d;
      --yellow:#f4bf4f;
      --red:#ff6b6b;
      --card:#0d172b;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      background:linear-gradient(180deg,#08111f 0%,#0c1527 100%);
      color:var(--text);
      font-family:Inter,'Segoe UI',sans-serif;
      height:100vh;
      overflow:hidden;
    }
    .page{
      height:100vh;
      display:grid;
      grid-template-columns:340px minmax(440px,1.1fr) minmax(420px,1fr);
      gap:16px;
      padding:16px;
    }
    .panel{
      min-height:0;
      display:flex;
      flex-direction:column;
      background:rgba(19,34,61,.96);
      border:1px solid var(--line);
      border-radius:18px;
      overflow:hidden;
    }
    .head{padding:16px 18px;border-bottom:1px solid rgba(255,255,255,.06)}
    .eyebrow{
      font-size:.72rem;
      font-weight:800;
      letter-spacing:.08em;
      text-transform:uppercase;
      color:var(--muted);
      margin-bottom:8px;
    }
    .title{font-size:1rem;font-weight:800;color:var(--strong);margin:0}
    .subtitle{margin:8px 0 0;color:var(--muted);font-size:.84rem;line-height:1.55}
    .body{min-height:0;overflow:auto;padding:16px}
    .toolbar{display:flex;gap:10px;flex-wrap:wrap}
    .btn{
      padding:10px 14px;
      border-radius:12px;
      border:1px solid var(--line);
      background:var(--card);
      color:var(--text);
      font-weight:800;
      cursor:pointer;
    }
    .trace-list,.stack,.timeline{display:flex;flex-direction:column;gap:12px}
    .trace-item{
      padding:12px;
      border:1px solid var(--line);
      border-radius:14px;
      background:rgba(13,23,43,.82);
      cursor:pointer;
    }
    .trace-item.active{border-color:var(--blue);box-shadow:0 0 0 1px rgba(93,133,255,.25) inset}
    .trace-top,.event-top{
      display:flex;
      justify-content:space-between;
      gap:8px;
      align-items:flex-start;
    }
    .trace-kind{font-size:.76rem;color:#bfd0ff;font-weight:800}
    .trace-status,.badge,.chip{
      padding:5px 8px;
      border-radius:999px;
      font-size:.72rem;
      font-weight:800;
    }
    .status-running{background:rgba(93,133,255,.18);color:#bfd0ff}
    .status-response_sent,.status-completed{background:rgba(50,196,141,.18);color:#9cf3cd}
    .status-timeout,.status-failed{background:rgba(255,107,107,.16);color:#ffc3c3}
    .trace-message{
      margin:10px 0 6px;
      color:var(--strong);
      font-size:.9rem;
      line-height:1.45;
      display:-webkit-box;
      -webkit-line-clamp:2;
      -webkit-box-orient:vertical;
      overflow:hidden;
    }
    .trace-meta,.event-meta{font-size:.78rem;color:var(--muted);line-height:1.5}
    .trace-summary,.badge-row,.chip-row{
      display:flex;
      gap:6px;
      flex-wrap:wrap;
      margin-top:10px;
    }
    .trace-slowest{
      margin-top:8px;
      padding-top:8px;
      border-top:1px solid rgba(255,255,255,.06);
      font-size:.77rem;
      color:#cbd8f0;
    }
    .card,.metric-card{
      border:1px solid var(--line);
      border-radius:14px;
      background:rgba(13,23,43,.78);
      padding:14px;
    }
    .card h3{margin:0 0 10px;font-size:.92rem;color:var(--strong)}
    .kv{display:grid;grid-template-columns:120px 1fr;gap:8px;font-size:.82rem}
    .kv div:nth-child(odd){color:var(--muted)}
    .metrics{
      display:grid;
      grid-template-columns:repeat(2,minmax(0,1fr));
      gap:12px;
    }
    .metric-card{padding:12px}
    .metric-label{font-size:.74rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
    .metric-value{margin-top:6px;font-size:1.05rem;font-weight:800;color:var(--strong);word-break:break-word}
    .event{
      padding:12px;
      border:1px solid var(--line);
      border-radius:14px;
      background:rgba(13,23,43,.78);
    }
    .event.hot{border-color:rgba(244,191,79,.35);box-shadow:0 0 0 1px rgba(244,191,79,.14) inset}
    .event-title{font-weight:800;color:var(--strong);font-size:.88rem}
    .badge-info,.chip-info{background:rgba(93,133,255,.16);color:#bfd0ff}
    .badge-ok,.chip-ok{background:rgba(50,196,141,.16);color:#9cf3cd}
    .badge-warn,.chip-warn{background:rgba(244,191,79,.16);color:#ffd88a}
    .badge-error,.chip-error{background:rgba(255,107,107,.16);color:#ffc3c3}
    .chip-muted{background:rgba(142,163,194,.16);color:#d6e0f0}
    .event-pre{
      margin-top:10px;
      padding:12px;
      border-radius:12px;
      background:#0a1222;
      border:1px solid rgba(255,255,255,.05);
      font-family:'JetBrains Mono',monospace;
      font-size:.75rem;
      white-space:pre-wrap;
      word-break:break-word;
      color:#b9d2ff;
    }
    .alert{
      padding:12px;
      border-radius:14px;
      border:1px solid rgba(255,255,255,.08);
    }
    .alert-warning{background:rgba(244,191,79,.12);border-color:rgba(244,191,79,.28)}
    .alert-error{background:rgba(255,107,107,.12);border-color:rgba(255,107,107,.28)}
    .alert-info{background:rgba(93,133,255,.12);border-color:rgba(93,133,255,.28)}
    .alert-title{font-weight:800;margin-bottom:6px}
    .mono{font-family:'JetBrains Mono',monospace}
    .empty{color:var(--muted);font-size:.84rem;line-height:1.6}
    .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    @media (max-width:1450px){
      .page{grid-template-columns:320px 1fr}
      .right{grid-column:1 / -1}
    }
    @media (max-width:980px){
      body{overflow:auto}
      .page{height:auto;grid-template-columns:1fr}
      .right{grid-column:auto}
      .metrics,.grid2{grid-template-columns:1fr}
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="panel">
      <div class="head">
        <div class="eyebrow">Recent Requests</div>
        <h1 class="title">Trace Explorer</h1>
        <p class="subtitle">The list view now works as triage. You can see intent, degraded search, plan proposal signals, persona, and the slowest stage before opening a trace.</p>
      </div>
      <div class="body">
        <div class="toolbar" style="margin-bottom:12px">
          <button class="btn" id="refreshBtn" type="button">Refresh</button>
          <button class="btn" id="toggleAutoBtn" type="button">Auto Refresh: ON</button>
        </div>
        <div id="traceList" class="trace-list"></div>
      </div>
    </section>
    <section class="panel">
      <div class="head">
        <div class="eyebrow">Timeline</div>
        <h2 class="title">Request Timeline</h2>
        <p class="subtitle">Use the middle panel to see total duration, slowest stage, WAS reads and writes, and where a trace degraded.</p>
      </div>
      <div class="body">
        <div id="overview" class="stack"></div>
        <div style="height:14px"></div>
        <div id="timeline" class="timeline"></div>
      </div>
    </section>
    <section class="panel right">
      <div class="head">
        <div class="eyebrow">Snapshots</div>
        <h2 class="title">WAS / State / Logs</h2>
        <p class="subtitle">Raw snapshots stay available for deep inspection, but the page now pushes the important debug signals to the top first.</p>
      </div>
      <div class="body stack">
        <div id="alertsSection" class="stack"></div>
        <div class="grid2">
          <div class="card"><h3>WAS User Profile</h3><div id="profileData" class="event-pre empty">No trace selected.</div></div>
          <div class="card"><h3>WAS Today Plan</h3><div id="todayPlanData" class="event-pre empty">No trace selected.</div></div>
        </div>
        <div class="grid2">
          <div class="card"><h3>WAS Workout Full Plan</h3><div id="workoutPlanData" class="event-pre empty">No trace selected.</div></div>
          <div class="card"><h3>WAS Diet Full Plan</h3><div id="dietPlanData" class="event-pre empty">No trace selected.</div></div>
        </div>
        <div class="card"><h3>State Summary</h3><div id="stateSummary" class="event-pre empty">No trace selected.</div></div>
        <div class="card"><h3>Response</h3><div id="responseSummary" class="event-pre empty">No trace selected.</div></div>
        <div class="card"><h3>Trace Logs</h3><div id="traceLogs" class="event-pre empty">No trace selected.</div></div>
        <div class="card"><h3>Recent Global Logs</h3><div id="globalLogs" class="event-pre empty">Loading...</div></div>
      </div>
    </section>
  </div>
  <script>
    let autoRefresh = true;
    let selectedTraceId = null;
    let autoTimer = null;

    const traceListEl = document.getElementById('traceList');
    const overviewEl = document.getElementById('overview');
    const timelineEl = document.getElementById('timeline');
    const alertsEl = document.getElementById('alertsSection');
    const profileDataEl = document.getElementById('profileData');
    const todayPlanDataEl = document.getElementById('todayPlanData');
    const workoutPlanDataEl = document.getElementById('workoutPlanData');
    const dietPlanDataEl = document.getElementById('dietPlanData');
    const stateSummaryEl = document.getElementById('stateSummary');
    const responseSummaryEl = document.getElementById('responseSummary');
    const traceLogsEl = document.getElementById('traceLogs');
    const globalLogsEl = document.getElementById('globalLogs');
    const toggleAutoBtn = document.getElementById('toggleAutoBtn');

    function pretty(value){
      if(value === null || value === undefined) return 'None';
      return JSON.stringify(value, null, 2);
    }

    function escapeHtml(value){
      return String(value ?? '')
        .replaceAll('&','&amp;')
        .replaceAll('<','&lt;')
        .replaceAll('>','&gt;')
        .replaceAll('"','&quot;')
        .replaceAll("'", '&#39;');
    }

    function shortText(value, max = 96){
      const text = String(value ?? '');
      return text.length > max ? `${text.slice(0, max - 1)}...` : text;
    }

    function formatMs(value){
      if(value === null || value === undefined || Number.isNaN(Number(value))) return '-';
      const number = Number(value);
      return number >= 100 ? `${Math.round(number)}ms` : `${number.toFixed(2)}ms`;
    }

    function formatDuration(value){
      if(value === null || value === undefined) return '-';
      const ms = Number(value);
      if(Number.isNaN(ms)) return '-';
      if(ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
      return formatMs(ms);
    }

    function statusClass(status){
      if(['ok','response_sent','completed'].includes(status)) return 'status-response_sent';
      if(['timeout','failed','error'].includes(status)) return 'status-timeout';
      return 'status-running';
    }

    function badgeClass(status){
      if(status === 'ok') return 'badge-ok';
      if(status === 'warn' || status === 'warning') return 'badge-warn';
      if(status === 'error') return 'badge-error';
      return 'badge-info';
    }

    function chipClass(kind){
      if(kind === 'ok') return 'chip-ok';
      if(kind === 'warn') return 'chip-warn';
      if(kind === 'error') return 'chip-error';
      if(kind === 'muted') return 'chip-muted';
      return 'chip-info';
    }

    function chip(label, value, kind = 'info'){
      if(value === null || value === undefined || value === '') return '';
      return `<span class="chip ${chipClass(kind)}">${escapeHtml(label)}: ${escapeHtml(value)}</span>`;
    }

    function computeDurationMs(trace){
      if(!trace.started_at || !trace.completed_at) return null;
      const started = Date.parse(trace.started_at);
      const completed = Date.parse(trace.completed_at);
      if(Number.isNaN(started) || Number.isNaN(completed)) return null;
      return completed - started;
    }

    function findSlowest(trace){
      let slowest = null;

      (trace.events || []).forEach(event => {
        const duration = event.duration_ms;
        if(duration === null || duration === undefined) return;
        if(!slowest || duration > slowest.duration_ms){
          slowest = {
            label: event.stage || event.title,
            duration_ms: duration,
          };
        }
      });

      [...(trace.was_reads || []), ...(trace.was_writes || [])].forEach(item => {
        const duration = item.duration_ms;
        if(duration === null || duration === undefined) return;
        if(!slowest || duration > slowest.duration_ms){
          slowest = {
            label: `${item.method || 'WAS'} ${item.path || ''}`.trim(),
            duration_ms: duration,
          };
        }
      });

      return slowest;
    }

    function renderSummaryChips(summary){
      const planLabel = summary.proposed_plan_count
        ? `${summary.proposed_plan_type || 'plan'} ${summary.proposed_plan_action || 'create'} x${summary.proposed_plan_count}`
        : null;

      return [
        chip('intent', summary.intent, 'info'),
        chip('search', summary.search_quality, summary.search_quality === 'degraded' ? 'warn' : summary.search_quality ? 'ok' : 'muted'),
        chip('modify', summary.modify_target, 'warn'),
        chip('plan', planLabel, planLabel ? 'ok' : 'muted'),
        chip('writes', summary.pending_writes_count, summary.pending_writes_count ? 'warn' : 'muted'),
        chip('persona', summary.resolved_persona_id, 'muted'),
      ].filter(Boolean).join('');
    }

    async function fetchJson(url){
      const response = await fetch(url, {cache:'no-store'});
      if(!response.ok){
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    }

    async function loadTraces(){
      const traces = await fetchJson('/debug/api/traces?limit=40');
      renderTraceList(traces);
      if(!selectedTraceId && traces.length){
        selectedTraceId = traces[0].trace_id;
      }
      if(selectedTraceId){
        const stillExists = traces.some(trace => trace.trace_id === selectedTraceId);
        if(!stillExists && traces.length){
          selectedTraceId = traces[0].trace_id;
        }
      }
      if(selectedTraceId){
        await loadTraceDetail(selectedTraceId);
      }
    }

    function renderTraceList(traces){
      if(!traces.length){
        traceListEl.innerHTML = '<div class="empty">No traces yet. Send a request through the app and it will appear here.</div>';
        return;
      }

      traceListEl.innerHTML = traces.map(trace => {
        const summary = trace.summary || {};
        const slowest = summary.slowest_label
          ? `<div class="trace-slowest">slowest: <span class="mono">${escapeHtml(summary.slowest_label)}</span> / ${escapeHtml(formatDuration(summary.slowest_duration_ms))}</div>`
          : '';

        return `
          <div class="trace-item ${trace.trace_id === selectedTraceId ? 'active' : ''}" data-trace-id="${trace.trace_id}">
            <div class="trace-top">
              <div class="trace-kind">${escapeHtml(trace.kind)}</div>
              <div class="trace-status ${statusClass(trace.status)}">${escapeHtml(trace.status)}</div>
            </div>
            <div class="trace-message">${escapeHtml(trace.message || '(no message)')}</div>
            <div class="trace-meta">
              user: ${escapeHtml(trace.user_id || '-')}<br>
              session: ${escapeHtml(trace.session_id || '-')}<br>
              alerts: ${trace.alert_count} / events: ${trace.event_count}
            </div>
            <div class="trace-summary">${renderSummaryChips(summary)}</div>
            ${slowest}
          </div>
        `;
      }).join('');

      document.querySelectorAll('[data-trace-id]').forEach(item => {
        item.addEventListener('click', async () => {
          selectedTraceId = item.dataset.traceId;
          renderTraceList(traces);
          await loadTraceDetail(selectedTraceId);
        });
      });
    }

    async function loadTraceDetail(traceId){
      const trace = await fetchJson(`/debug/api/traces/${traceId}`);
      renderOverview(trace);
      renderTimeline(trace);
      renderAlerts(trace);
      renderSnapshots(trace);
    }

    function renderOverview(trace){
      const responseText = trace.response?.response || '-';
      const summary = trace.state_summary || {};
      const slowest = findSlowest(trace);
      const durationMs = computeDurationMs(trace);

      overviewEl.innerHTML = `
        <div class="card">
          <h3>Request Summary</h3>
          <div class="kv">
            <div>trace_id</div><div class="mono">${escapeHtml(trace.trace_id)}</div>
            <div>kind</div><div>${escapeHtml(trace.kind)}</div>
            <div>status</div><div>${escapeHtml(trace.status)}</div>
            <div>user_id</div><div>${escapeHtml(trace.user_id || '-')}</div>
            <div>session_id</div><div class="mono">${escapeHtml(trace.session_id || '-')}</div>
            <div>message</div><div>${escapeHtml(trace.message || '-')}</div>
            <div>started_at</div><div>${escapeHtml(trace.started_at)}</div>
            <div>completed_at</div><div>${escapeHtml(trace.completed_at || '-')}</div>
            <div>response</div><div>${escapeHtml(shortText(responseText, 180))}</div>
          </div>
        </div>
        <div class="card">
          <h3>Debug Signals</h3>
          <div class="chip-row">${renderSummaryChips(summary) || '<span class="empty">No state summary yet.</span>'}</div>
        </div>
        <div class="metrics">
          <div class="metric-card">
            <div class="metric-label">Total Duration</div>
            <div class="metric-value">${escapeHtml(formatDuration(durationMs))}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Slowest Stage</div>
            <div class="metric-value">${escapeHtml(slowest?.label || '-')}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Slowest Duration</div>
            <div class="metric-value">${escapeHtml(formatDuration(slowest?.duration_ms))}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Counts</div>
            <div class="metric-value">events ${trace.events?.length || 0} / alerts ${trace.alerts?.length || 0}</div>
          </div>
        </div>
      `;
    }

    function renderTimeline(trace){
      const items = [
        ...(trace.events || []).map(item => ({...item, kind:'event'})),
        ...(trace.was_reads || []).map(item => ({...item, kind:'was', stage:'was_read'})),
        ...(trace.was_writes || []).map(item => ({...item, kind:'was', stage:'was_write'})),
      ].sort((a, b) => String(a.timestamp).localeCompare(String(b.timestamp)));

      if(!items.length){
        timelineEl.innerHTML = '<div class="empty">No timeline events for this trace yet.</div>';
        return;
      }

      timelineEl.innerHTML = items.map(item => {
        const duration = item.duration_ms;
        const hotClass = Number(duration) >= 2000 ? ' hot' : '';

        if(item.kind === 'was'){
          const label = `${item.method} ${item.path}`;
          const detail = {
            status: item.status,
            duration_ms: item.duration_ms,
            request_body: item.request_body,
            error: item.error,
          };
          return `
            <div class="event${hotClass}">
              <div class="event-top">
                <div class="event-title">${escapeHtml(label)}</div>
                <div class="badge-row">
                  <span class="badge ${badgeClass(item.status === 'ok' ? 'ok' : item.error ? 'error' : 'info')}">${escapeHtml(item.status)}</span>
                  <span class="badge ${Number(duration) >= 2000 ? 'badge-warn' : 'badge-info'}">${escapeHtml(formatDuration(duration))}</span>
                </div>
              </div>
              <div class="event-meta">${escapeHtml(item.timestamp)} / ${escapeHtml(item.stage)}</div>
              <div class="event-pre">${escapeHtml(pretty(detail))}</div>
            </div>
          `;
        }

        return `
          <div class="event${hotClass}">
            <div class="event-top">
              <div class="event-title">${escapeHtml(item.title)}</div>
              <div class="badge-row">
                <span class="badge ${badgeClass(item.status)}">${escapeHtml(item.status)}</span>
                ${duration !== null && duration !== undefined ? `<span class="badge ${Number(duration) >= 2000 ? 'badge-warn' : 'badge-info'}">${escapeHtml(formatDuration(duration))}</span>` : ''}
              </div>
            </div>
            <div class="event-meta">${escapeHtml(item.timestamp)} / ${escapeHtml(item.stage)}</div>
            <div class="event-pre">${escapeHtml(pretty(item.detail || {}))}</div>
          </div>
        `;
      }).join('');
    }

    function renderAlerts(trace){
      if(!trace.alerts?.length){
        alertsEl.innerHTML = '';
        return;
      }
      alertsEl.innerHTML = trace.alerts.map(alert => `
        <div class="alert alert-${escapeHtml(alert.severity === 'error' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info')}">
          <div class="alert-title">${escapeHtml(alert.severity.toUpperCase())} / ${escapeHtml(alert.message)}</div>
          <div class="mono">${escapeHtml(pretty(alert.detail || {}))}</div>
        </div>
      `).join('');
    }

    function renderSnapshots(trace){
      profileDataEl.textContent = pretty(trace.was_data?.user_profile);
      todayPlanDataEl.textContent = pretty(trace.was_data?.today_plan);
      workoutPlanDataEl.textContent = pretty(trace.was_data?.workout_full_plan);
      dietPlanDataEl.textContent = pretty(trace.was_data?.diet_full_plan);
      stateSummaryEl.textContent = pretty(trace.state_summary);
      responseSummaryEl.textContent = pretty(trace.response);
      traceLogsEl.textContent = trace.logs?.length
        ? trace.logs.map(log => `[${log.timestamp}] ${log.level} ${log.logger}: ${log.message}`).join('\\n')
        : 'No trace-local logs.';
    }

    async function loadGlobalLogs(){
      const logs = await fetchJson('/debug/api/logs?limit=160');
      globalLogsEl.textContent = logs.length
        ? logs.map(log => `[${log.timestamp}] ${log.level} ${log.logger}${log.trace_id ? ` [trace:${log.trace_id}]` : ''}: ${log.message}`).join('\\n')
        : 'No logs yet.';
    }

    async function refreshAll(){
      try{
        await Promise.all([loadTraces(), loadGlobalLogs()]);
      }catch(error){
        console.error(error);
      }
    }

    function scheduleAutoRefresh(){
      clearInterval(autoTimer);
      if(autoRefresh){
        autoTimer = setInterval(refreshAll, 4000);
      }
    }

    document.getElementById('refreshBtn').addEventListener('click', refreshAll);
    toggleAutoBtn.addEventListener('click', () => {
      autoRefresh = !autoRefresh;
      toggleAutoBtn.textContent = `Auto Refresh: ${autoRefresh ? 'ON' : 'OFF'}`;
      scheduleAutoRefresh();
    });

    refreshAll();
    scheduleAutoRefresh();
  </script>
</body>
</html>
"""


@router.get("/observability", response_class=HTMLResponse)
async def observability_page() -> HTMLResponse:
    return HTMLResponse(HTML)


@router.get("/api/traces")
async def list_traces(request: Request, limit: int = Query(default=30, ge=1, le=120)):
    return request.app.state.trace_store.list_traces(limit=limit)


@router.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str, request: Request):
    trace = request.app.state.trace_store.get_trace(trace_id)
    if trace is None:
        return {"status": "not_found", "trace_id": trace_id}
    return trace


@router.get("/api/logs")
async def list_logs(request: Request, limit: int = Query(default=160, ge=1, le=500)):
    return request.app.state.trace_store.list_logs(limit=limit)
