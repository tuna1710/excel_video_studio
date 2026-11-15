import json
import os
import time
from typing import Any, Dict, List, Tuple
from playwright.sync_api import sync_playwright


def _build_html(plan: Dict[str, Any], aspect_ratio: str, show_subtitles: bool) -> str:
    is_vertical = aspect_ratio.startswith("9:16")
    headers = plan.get("headers", ["Cột A", "Cột B"])
    rows = plan.get("rows", [])
    chart = plan.get("chart")
    title = plan.get("title", "Excel Tutorial")
    sheet_name = plan.get("sheet_name", "Sheet1")

    plan_json = json.dumps(
        {
            "headers": headers,
            "rows": rows,
            "chart": chart,
            "title": title,
            "sheet_name": sheet_name,
            "show_subtitles": show_subtitles,
        },
        ensure_ascii=False,
    )

    body_scale_css = """
      .app-shell {
        width: 100vw;
        height: 100vh;
        display: flex;
        flex-direction: column;
        background: #f3f2f1;
      }
    """

    layout_css = (
        """
        .workspace {
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 18px;
          gap: 18px;
          overflow: hidden;
        }
        .sheet-wrap { flex: 0 0 auto; }
        .chart-wrap { flex: 1; min-height: 360px; }
        .ribbon-btn { padding: 10px 14px; font-size: 16px; }
        .tab-btn { padding: 10px 18px; font-size: 18px; }
        table.excel-grid th, table.excel-grid td { height: 52px; font-size: 20px; padding: 0 14px; }
        .subtitle-box { bottom: 90px; font-size: 32px; max-width: 90%; padding: 16px 26px; }
        """
        if is_vertical
        else """
        .workspace {
          flex: 1;
          display: flex;
          flex-direction: row;
          padding: 20px;
          gap: 24px;
          overflow: hidden;
        }
        .sheet-wrap { flex: 1.1; }
        .chart-wrap { flex: 0.9; }
        .ribbon-btn { padding: 10px 16px; font-size: 15px; }
        .tab-btn { padding: 10px 20px; font-size: 16px; }
        table.excel-grid th, table.excel-grid td { height: 46px; font-size: 18px; padding: 0 14px; }
        .subtitle-box { bottom: 48px; font-size: 28px; max-width: 78%; padding: 14px 28px; }
        """
    )

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }}
  body {{ overflow: hidden; background: #f3f2f1; user-select: none; }}
  {body_scale_css}

  /* Excel Top Bar */
  .title-bar {{
    background: #217346;
    color: #fff;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 18px;
    font-weight: 600;
  }}
  .title-badge {{
    background: rgba(255,255,255,0.18);
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 14px;
  }}

  /* Ribbon Tabs */
  .ribbon-tabs {{
    background: #217346;
    display: flex;
    gap: 4px;
    padding: 0 16px;
  }}
  .tab-btn {{
    color: rgba(255,255,255,0.88);
    background: transparent;
    border: none;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
  }}
  .tab-btn.active {{
    background: #ffffff;
    color: #217346;
    font-weight: 700;
  }}

  /* Ribbon Toolbar */
  .ribbon-bar {{
    background: #ffffff;
    border-bottom: 1px solid #d4d4d4;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    min-height: 68px;
  }}
  .ribbon-group {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding-right: 14px;
    border-right: 1px solid #e5e5e5;
  }}
  .ribbon-btn {{
    background: #f8f9fa;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #222;
    transition: all 0.2s;
  }}
  .ribbon-btn.active-btn {{
    background: #e6f4ea;
    border-color: #217346;
    color: #217346;
    box-shadow: 0 0 0 3px rgba(33,115,70,0.2);
    transform: scale(1.04);
  }}

  /* Formula Bar */
  .formula-bar {{
    background: #fff;
    border-bottom: 1px solid #d4d4d4;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 17px;
  }}
  .name-box {{
    width: 110px;
    border: 1px solid #d4d4d4;
    padding: 6px 10px;
    border-radius: 4px;
    text-align: center;
    font-weight: 600;
    background: #fafafa;
  }}
  .fx-label {{
    color: #217346;
    font-weight: 700;
    font-style: italic;
    font-size: 18px;
  }}
  .formula-input {{
    flex: 1;
    border: 1px solid #d4d4d4;
    padding: 6px 12px;
    border-radius: 4px;
    background: #fff;
    min-height: 36px;
    font-family: Consolas, monospace;
    font-size: 17px;
    color: #111;
  }}

  {layout_css}

  /* Grid */
  .sheet-wrap {{
    background: #fff;
    border: 1px solid #d4d4d4;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  }}
  table.excel-grid {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }}
  table.excel-grid th {{
    background: #f0f0f0;
    color: #444;
    font-weight: 600;
    border: 1px solid #d4d4d4;
    text-align: center;
  }}
  table.excel-grid th.row-hdr {{
    width: 54px;
  }}
  table.excel-grid td {{
    border: 1px solid #e1e1e1;
    color: #111;
    background: #fff;
    position: relative;
    transition: background 0.25s;
  }}
  table.excel-grid td.header-cell {{
    background: #217346;
    color: #fff;
    font-weight: 700;
    text-align: center;
  }}
  table.excel-grid td.num-cell {{
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  table.excel-grid td.selected {{
    background: rgba(33, 115, 70, 0.14) !important;
    outline: 2px solid #217346;
    outline-offset: -2px;
  }}
  table.excel-grid td.header-cell.selected {{
    background: #185c37 !important;
    outline: 3px solid #ffd54f;
    outline-offset: -3px;
  }}
  table.excel-grid td.highlight-pop {{
    background: #fff8e1 !important;
    outline: 3px solid #f59e0b;
    outline-offset: -3px;
    font-weight: 700;
  }}

  /* Chart Panel */
  .chart-wrap {{
    background: #fff;
    border: 1px solid #d4d4d4;
    border-radius: 10px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    opacity: 0;
    transform: translateY(20px) scale(0.96);
    transition: all 0.55s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .chart-wrap.visible {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
  .chart-title {{
    font-size: 22px;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 14px;
    text-align: center;
  }}
  .chart-svg {{
    width: 100%;
    height: 100%;
    max-height: 460px;
  }}

  /* Sheet Tab Footer */
  .sheet-footer {{
    background: #e6e6e6;
    padding: 8px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-top: 1px solid #ccc;
  }}
  .sheet-pill {{
    background: #fff;
    color: #217346;
    font-weight: 700;
    padding: 5px 16px;
    border-radius: 4px;
    border-bottom: 3px solid #217346;
    font-size: 15px;
  }}

  /* Subtitle Overlay */
  .subtitle-box {{
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(15, 23, 42, 0.88);
    color: #ffffff;
    font-weight: 600;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 8px 24px rgba(0,0,0,0.28);
    z-index: 900;
    line-height: 1.35;
    border: 1px solid rgba(255,255,255,0.18);
  }}

  /* Virtual Mouse Cursor */
  #cursor {{
    position: fixed;
    width: 34px;
    height: 34px;
    left: 120px;
    top: 220px;
    z-index: 9999;
    pointer-events: none;
    transition: left 0.65s cubic-bezier(0.22, 1, 0.36, 1), top 0.65s cubic-bezier(0.22, 1, 0.36, 1);
    filter: drop-shadow(0 3px 5px rgba(0,0,0,0.35));
  }}
  .click-ripple {{
    position: fixed;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 3px solid #f59e0b;
    background: rgba(245, 158, 11, 0.25);
    transform: translate(-50%, -50%) scale(0.4);
    opacity: 1;
    pointer-events: none;
    z-index: 9998;
    animation: ripple 0.55s ease-out forwards;
  }}
  @keyframes ripple {{
    to {{ transform: translate(-50%, -50%) scale(1.6); opacity: 0; }}
  }}
</style>
</head>
<body>
<div class="app-shell">
  <div class="title-bar">
    <span>📊 Excel Video Studio — {title}</span>
    <span class="title-badge">AutoSave: ON</span>
  </div>

  <div class="ribbon-tabs">
    <button class="tab-btn active" data-tab="Home">Home</button>
    <button class="tab-btn" data-tab="Insert">Insert</button>
    <button class="tab-btn" data-tab="Formulas">Formulas</button>
    <button class="tab-btn" data-tab="Data">Data</button>
  </div>

  <div class="ribbon-bar" id="ribbon-bar"></div>

  <div class="formula-bar">
    <div class="name-box" id="name-box">A1</div>
    <span class="fx-label">fx</span>
    <div class="formula-input" id="formula-input"></div>
  </div>

  <div class="workspace">
    <div class="sheet-wrap">
      <table class="excel-grid" id="excel-grid"></table>
    </div>
    <div class="chart-wrap" id="chart-wrap" style="display:none;">
      <div class="chart-title" id="chart-title"></div>
      <svg class="chart-svg" id="chart-svg" viewBox="0 0 640 360"></svg>
    </div>
  </div>

  <div class="sheet-footer">
    <div class="sheet-pill">{sheet_name}</div>
  </div>
</div>

<div class="subtitle-box" id="subtitle-box" style="display:none;"></div>

<!-- SVG Mouse Pointer -->
<svg id="cursor" viewBox="0 0 24 24">
  <path d="M4 2 L4 20 L9.5 15 L13.5 22 L16.5 20.5 L12.5 13.5 L19 13.5 Z"
        fill="#ffffff" stroke="#111827" stroke-width="1.8" stroke-linejoin="round"/>
</svg>

<script>
const CFG = {plan_json};

const RIBBONS = {{
  "Home": [
    {{ id: "Format", label: "🎨 Format" }},
    {{ id: "AutoSum", label: "∑ AutoSum" }},
    {{ id: "Sort", label: "↕️ Sort & Filter" }}
  ],
  "Insert": [
    {{ id: "PivotTable", label: "📑 PivotTable" }},
    {{ id: "Column Chart", label: "📊 Column Chart" }},
    {{ id: "Line Chart", label: "📈 Line Chart" }},
    {{ id: "Pie Chart", label: "🥧 Pie Chart" }}
  ],
  "Formulas": [
    {{ id: "Insert Function", label: "fx Insert Function" }},
    {{ id: "AutoSum", label: "∑ AutoSum" }}
  ],
  "Data": [
    {{ id: "Filter", label: "🌪️ Filter" }},
    {{ id: "Remove Duplicates", label: "🧹 Clean" }}
  ]
}};

function renderRibbon(tabName) {{
  document.querySelectorAll('.tab-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.tab === tabName);
  }});
  const bar = document.getElementById('ribbon-bar');
  bar.innerHTML = '';
  const grp = document.createElement('div');
  grp.className = 'ribbon-group';
  (RIBBONS[tabName] || RIBBONS["Home"]).forEach(item => {{
    const btn = document.createElement('button');
    btn.className = 'ribbon-btn';
    btn.dataset.btn = item.id;
    btn.textContent = item.label;
    grp.appendChild(btn);
  }});
  bar.appendChild(grp);
}}

function renderGrid() {{
  const table = document.getElementById('excel-grid');
  const numCols = Math.max(CFG.headers.length, 3);
  const numRows = Math.max(CFG.rows.length + 2, 7);

  let html = '<thead><tr><th class="row-hdr"></th>';
  for (let c = 0; c < numCols; c++) {{
    html += `<th>${{String.fromCharCode(65 + c)}}</th>`;
  }}
  html += '</tr></thead><tbody>';

  for (let r = 1; r <= numRows; r++) {{
    html += `<tr><th class="row-hdr">${{r}}</th>`;
    for (let c = 0; c < numCols; c++) {{
      const coord = `${{String.fromCharCode(65 + c)}}${{r}}`;
      let val = '';
      let cls = '';
      if (r === 1 && c < CFG.headers.length) {{
        val = CFG.headers[c];
        cls = 'header-cell';
      }} else if (r >= 2 && (r - 2) < CFG.rows.length && c < CFG.rows[r - 2].length) {{
        val = CFG.rows[r - 2][c];
        if (typeof val === 'number') cls = 'num-cell';
      }}
      html += `<td id="cell-${{coord}}" class="${{cls}}">${{val}}</td>`;
    }}
    html += '</tr>';
  }}
  html += '</tbody>';
  table.innerHTML = html;
}}

function parseRange(rangeStr) {{
  const parts = rangeStr.trim().toUpperCase().split(':');
  const parseCoord = (s) => {{
    const m = s.match(/^([A-Z]+)(\\d+)$/);
    if (!m) return [0, 1];
    return [m[1].charCodeAt(0) - 65, parseInt(m[2], 10)];
  }};
  const [c1, r1] = parseCoord(parts[0]);
  const [c2, r2] = parts[1] ? parseCoord(parts[1]) : [c1, r1];
  const coords = [];
  for (let r = Math.min(r1, r2); r <= Math.max(r1, r2); r++) {{
    for (let c = Math.min(c1, c2); c <= Math.max(c1, c2); c++) {{
      coords.push(`${{String.fromCharCode(65 + c)}}${{r}}`);
    }}
  }}
  return coords;
}}

function clearSelection() {{
  document.querySelectorAll('td.selected, td.highlight-pop').forEach(el => {{
    el.classList.remove('selected', 'highlight-pop');
  }});
  document.querySelectorAll('.ribbon-btn').forEach(b => b.classList.remove('active-btn'));
}}

function moveCursorToEl(el) {{
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const x = rect.left + rect.width * 0.5;
  const y = rect.top + rect.height * 0.5;
  const cur = document.getElementById('cursor');
  cur.style.left = x + 'px';
  cur.style.top = y + 'px';
  setTimeout(() => {{
    const rip = document.createElement('div');
    rip.className = 'click-ripple';
    rip.style.left = x + 'px';
    rip.style.top = y + 'px';
    document.body.appendChild(rip);
    setTimeout(() => rip.remove(), 600);
  }}, 550);
}}

function renderChartSVG() {{
  const chart = CFG.chart;
  if (!chart) return;
  const wrap = document.getElementById('chart-wrap');
  wrap.style.display = 'flex';
  document.getElementById('chart-title').textContent = chart.title || CFG.title;
  const svg = document.getElementById('chart-svg');
  svg.innerHTML = '';

  const xCol = chart.x_col ?? 0;
  const yCol = chart.y_col ?? 1;
  const items = CFG.rows
    .filter(r => r[xCol] !== undefined && typeof r[yCol] === 'number')
    .map(r => ({{ label: String(r[xCol]), val: Number(r[yCol]) }}));

  if (!items.length) return;
  const maxVal = Math.max(...items.map(i => i.val)) * 1.15;
  const colors = ['#217346', '#2b8a57', '#3b82f6', '#f59e0b', '#10b981', '#6366f1'];

  if (chart.type === 'pie') {{
    const total = items.reduce((s, i) => s + i.val, 0) || 1;
    let angle = -Math.PI / 2;
    const cx = 220, cy = 180, rad = 135;
    items.forEach((item, idx) => {{
      const slice = (item.val / total) * Math.PI * 2;
      const x1 = cx + rad * Math.cos(angle);
      const y1 = cy + rad * Math.sin(angle);
      const x2 = cx + rad * Math.cos(angle + slice);
      const y2 = cy + rad * Math.sin(angle + slice);
      const large = slice > Math.PI ? 1 : 0;
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M ${{cx}} ${{cy}} L ${{x1}} ${{y1}} A ${{rad}} ${{rad}} 0 ${{large}} 1 ${{x2}} ${{y2}} Z`);
      path.setAttribute('fill', colors[idx % colors.length]);
      path.setAttribute('stroke', '#fff');
      path.setAttribute('stroke-width', '2');
      svg.appendChild(path);

      // Legend
      const ly = 55 + idx * 38;
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', '410'); rect.setAttribute('y', ly);
      rect.setAttribute('width', '20'); rect.setAttribute('height', '20');
      rect.setAttribute('rx', '4');
      rect.setAttribute('fill', colors[idx % colors.length]);
      svg.appendChild(rect);

      const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      txt.setAttribute('x', '440'); txt.setAttribute('y', ly + 15);
      txt.setAttribute('font-size', '16'); txt.setAttribute('fill', '#1f2937');
      txt.textContent = `${{item.label}} (${{item.val}})`;
      svg.appendChild(txt);
      angle += slice;
    }});
  }} else if (chart.type === 'line') {{
    const padL = 60, padB = 45, w = 550, h = 270;
    // Axes
    svg.innerHTML += `<line x1="${{padL}}" y1="25" x2="${{padL}}" y2="${{25+h}}" stroke="#9ca3af" stroke-width="2"/>`;
    svg.innerHTML += `<line x1="${{padL}}" y1="${{25+h}}" x2="${{padL+w}}" y2="${{25+h}}" stroke="#9ca3af" stroke-width="2"/>`;
    const stepX = w / Math.max(items.length - 1, 1);
    const pts = items.map((it, idx) => {{
      const x = padL + idx * stepX;
      const y = 25 + h - (it.val / maxVal) * h;
      return [x, y, it];
    }});
    const poly = pts.map(p => `${{p[0]}},${{p[1]}}`).join(' ');
    svg.innerHTML += `<polyline fill="none" stroke="#217346" stroke-width="4" points="${{poly}}"/>`;
    pts.forEach(([x, y, it]) => {{
      svg.innerHTML += `<circle cx="${{x}}" cy="${{y}}" r="7" fill="#217346" stroke="#fff" stroke-width="2"/>`;
      svg.innerHTML += `<text x="${{x}}" y="${{y - 14}}" text-anchor="middle" font-size="15" font-weight="700" fill="#111">${{it.val}}</text>`;
      svg.innerHTML += `<text x="${{x}}" y="${{25 + h + 24}}" text-anchor="middle" font-size="14" fill="#374151">${{it.label}}</text>`;
    }});
  }} else {{
    // Column / Bar chart
    const padL = 55, w = 555, h = 270;
    svg.innerHTML += `<line x1="${{padL}}" y1="25" x2="${{padL}}" y2="${{25+h}}" stroke="#9ca3af" stroke-width="2"/>`;
    svg.innerHTML += `<line x1="${{padL}}" y1="${{25+h}}" x2="${{padL+w}}" y2="${{25+h}}" stroke="#9ca3af" stroke-width="2"/>`;
    const slot = w / items.length;
    const barW = Math.min(56, slot * 0.6);
    items.forEach((it, idx) => {{
      const bh = (it.val / maxVal) * h;
      const x = padL + idx * slot + (slot - barW) / 2;
      const y = 25 + h - bh;
      svg.innerHTML += `<rect x="${{x}}" y="${{y}}" width="${{barW}}" height="${{bh}}" rx="6" fill="#217346"/>`;
      svg.innerHTML += `<text x="${{x + barW/2}}" y="${{y - 8}}" text-anchor="middle" font-size="15" font-weight="700" fill="#111">${{it.val}}</text>`;
      svg.innerHTML += `<text x="${{x + barW/2}}" y="${{25 + h + 24}}" text-anchor="middle" font-size="14" fill="#374151">${{it.label}}</text>`;
    }});
  }}
  requestAnimationFrame(() => wrap.classList.add('visible'));
}}

window.runStep = function(step) {{
  const subBox = document.getElementById('subtitle-box');
  if (CFG.show_subtitles && step.subtitle) {{
    subBox.style.display = 'block';
    subBox.textContent = step.subtitle;
  }} else {{
    subBox.style.display = 'none';
  }}

  const act = step.action;
  const tgt = step.target || '';

  if (act === 'select_range') {{
    clearSelection();
    const coords = parseRange(tgt);
    coords.forEach(c => {{
      const el = document.getElementById('cell-' + c);
      if (el) el.classList.add('selected');
    }});
    document.getElementById('name-box').textContent = tgt;
    const first = document.getElementById('cell-' + coords[0]);
    const last = document.getElementById('cell-' + coords[coords.length - 1]);
    moveCursorToEl(last || first);
  }} else if (act === 'click_tab') {{
    const tabEl = document.querySelector(`.tab-btn[data-tab="${{tgt}}"]`);
    moveCursorToEl(tabEl);
    setTimeout(() => renderRibbon(tgt), 500);
  }} else if (act === 'click_button') {{
    let btnEl = document.querySelector(`.ribbon-btn[data-btn="${{tgt}}"]`);
    if (!btnEl) {{
      // Fallback: switch tab if button is on Insert or Home
      if (tgt.toLowerCase().includes('chart')) renderRibbon('Insert');
      btnEl = document.querySelector(`.ribbon-btn[data-btn="${{tgt}}"]`) || document.querySelector('.ribbon-btn');
    }}
    moveCursorToEl(btnEl);
    setTimeout(() => {{
      if (btnEl) btnEl.classList.add('active-btn');
      if (tgt.toLowerCase().includes('chart') && CFG.chart) {{
        renderChartSVG();
      }}
    }}, 550);
  }} else if (act === 'type_formula') {{
    const coord = tgt.split(':')[0];
    const cell = document.getElementById('cell-' + coord);
    clearSelection();
    if (cell) cell.classList.add('selected');
    document.getElementById('name-box').textContent = coord;
    moveCursorToEl(cell);
    const fInput = document.getElementById('formula-input');
    const formula = step.formula || '';
    fInput.textContent = '';
    let i = 0;
    const timer = setInterval(() => {{
      if (i < formula.length) {{
        fInput.textContent += formula[i];
        if (cell) cell.textContent = fInput.textContent;
        i++;
      }} else {{
        clearInterval(timer);
        setTimeout(() => {{
          if (cell && step.result_value) {{
            cell.textContent = step.result_value;
            cell.classList.add('highlight-pop');
          }}
        }}, 450);
      }}
    }}, 55);
  }} else if (act === 'show_chart') {{
    renderChartSVG();
    const wrap = document.getElementById('chart-wrap');
    moveCursorToEl(wrap);
  }} else if (act === 'highlight_cells') {{
    clearSelection();
    const coords = parseRange(tgt || 'A1');
    coords.forEach(c => {{
      const el = document.getElementById('cell-' + c);
      if (el) el.classList.add('highlight-pop');
    }});
    moveCursorToEl(document.getElementById('cell-' + coords[0]));
  }} else if (act === 'finish') {{
    // Keep current visual state clean
  }}
}};

renderRibbon('Home');
renderGrid();
</script>
</body>
</html>
"""


def record_excel_video(
    plan: Dict[str, Any],
    steps_with_audio: List[Dict[str, Any]],
    aspect_ratio: str,
    show_subtitles: bool,
    out_dir: str,
) -> Tuple[str, List[float]]:
    """Render the Excel HTML scene and record video via Playwright. Returns (webm_path, step_start_times)."""
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, "scene.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(_build_html(plan, aspect_ratio, show_subtitles))

    width, height = (1080, 1920) if aspect_ratio.startswith("9:16") else (1920, 1080)
    video_dir = os.path.join(out_dir, "raw_video")
    os.makedirs(video_dir, exist_ok=True)

    step_start_times: List[float] = []

    with sync_playwright() as p:
        launch_kwargs: Dict[str, Any] = {"headless": True}
        # On Colab, Playwright's bundled chromium is used. In sandbox/Linux fallback to google-chrome if needed.
        if os.path.exists("/usr/bin/google-chrome"):
            try:
                browser = p.chromium.launch(**launch_kwargs)
            except Exception:
                launch_kwargs["executable_path"] = "/usr/bin/google-chrome"
                browser = p.chromium.launch(**launch_kwargs)
        else:
            browser = p.chromium.launch(**launch_kwargs)

        context = browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=video_dir,
            record_video_size={"width": width, "height": height},
        )
        page = context.new_page()
        page.goto(f"file://{os.path.abspath(html_path)}")
        page.wait_for_timeout(400)

        t0 = time.monotonic()
        for step in steps_with_audio:
            step_start_times.append(time.monotonic() - t0)
            page.evaluate("(s) => window.runStep(s)", step)
            wait_ms = int(step["duration"] * 1000)
            page.wait_for_timeout(wait_ms)

        page.wait_for_timeout(400)
        video_path = page.video.path()
        context.close()
        browser.close()

    return video_path, step_start_times
