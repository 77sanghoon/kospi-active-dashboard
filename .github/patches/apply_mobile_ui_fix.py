from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

styles_path = ROOT / "dashboard" / "styles.css"
styles = styles_path.read_text(encoding="utf-8")
mobile_marker = "/* mobile-ui-runtime-fix */"
mobile_css = r'''
/* mobile-ui-runtime-fix */
@media (max-width: 720px) {
  :root {
    --bg: #f4f6f8;
    --ink: #111827;
    --muted: #667085;
    --line: #d9dee7;
    --panel: #ffffff;
  }

  body {
    min-width: 0;
    background: var(--bg);
    -webkit-text-size-adjust: 100%;
  }

  .topbar {
    position: sticky;
    top: 0;
    z-index: 20;
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 14px 14px 12px;
    box-shadow: 0 1px 0 rgba(17, 24, 39, 0.06);
  }

  .eyebrow {
    font-size: 12px;
    margin-bottom: 4px;
  }

  h1 {
    font-size: 20px;
    line-height: 1.25;
  }

  h2 {
    font-size: 16px;
  }

  .status {
    display: grid;
    grid-template-columns: 1fr;
    gap: 6px;
    font-size: 12px;
  }

  .status span {
    min-height: 32px;
    display: flex;
    align-items: center;
    padding: 6px 8px;
    border-radius: 6px;
  }

  main {
    width: 100%;
    padding: 12px 10px 28px;
  }

  .toolbar {
    position: sticky;
    top: 103px;
    z-index: 15;
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    margin: 0 -10px 12px;
    padding: 10px;
    background: rgba(244, 246, 248, 0.96);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--line);
  }

  label {
    gap: 4px;
    font-size: 12px;
  }

  select {
    width: 100%;
    min-width: 0;
    height: 40px;
    font-size: 14px;
    border-radius: 7px;
  }

  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 10px;
  }

  .metric {
    min-height: 74px;
    padding: 10px;
    border-radius: 8px;
  }

  .metric span {
    font-size: 11px;
  }

  .metric strong {
    margin-top: 6px;
    font-size: clamp(17px, 5vw, 22px);
    line-height: 1.2;
    overflow-wrap: anywhere;
  }

  .panel {
    padding: 12px;
    border-radius: 8px;
  }

  .source-panel,
  .layout {
    margin-bottom: 10px;
  }

  .panel-title {
    display: grid;
    grid-template-columns: 1fr;
    gap: 4px;
    margin-bottom: 10px;
  }

  .panel-title p {
    font-size: 12px;
    line-height: 1.45;
  }

  .layout {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .table-wrap,
  .table-wrap.compact {
    max-height: none;
    overflow: visible;
  }

  table,
  thead,
  tbody,
  tr,
  th,
  td {
    display: block;
  }

  thead {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }

  tbody {
    display: grid;
    gap: 8px;
  }

  tr {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    overflow: hidden;
  }

  td {
    display: grid;
    grid-template-columns: minmax(86px, 32%) minmax(0, 1fr);
    gap: 8px;
    align-items: start;
    min-height: 34px;
    padding: 8px 10px;
    border-bottom: 1px solid #edf0f5;
    font-size: 13px;
    line-height: 1.4;
    overflow-wrap: anywhere;
  }

  td:last-child {
    border-bottom: 0;
  }

  td::before {
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    line-height: 1.4;
  }

  td[colspan] {
    display: block;
    padding: 12px;
    color: var(--muted);
  }

  td[colspan]::before {
    content: "";
    display: none;
  }

  .stock {
    font-size: 14px;
  }

  .code {
    font-size: 11px;
  }

  .tag {
    white-space: normal;
    line-height: 1.25;
  }

  #commonBody td:nth-child(1)::before { content: "종목"; }
  #commonBody td:nth-child(2)::before { content: "ETF"; }
  #commonBody td:nth-child(3)::before { content: "비중 증감"; }
  #commonBody td:nth-child(4)::before { content: "수량 증감"; }
  #commonBody td:nth-child(5)::before { content: "해석"; }

  #expansionBody td:nth-child(1)::before { content: "ETF"; }
  #expansionBody td:nth-child(2)::before { content: "종목"; }
  #expansionBody td:nth-child(3)::before { content: "비중"; }
  #expansionBody td:nth-child(4)::before { content: "비중 증감"; }
  #expansionBody td:nth-child(5)::before { content: "수량 증감"; }
  #expansionBody td:nth-child(6)::before { content: "연속"; }
  #expansionBody td:nth-child(7)::before { content: "해석"; }

  #growthBody td:nth-child(1)::before { content: "순위"; }
  #growthBody td:nth-child(2)::before { content: "종목"; }
  #growthBody td:nth-child(3)::before { content: "점수"; }
  #growthBody td:nth-child(4)::before { content: "변화 ETF"; }
  #growthBody td:nth-child(5)::before { content: "동시 확대"; }
  #growthBody td:nth-child(6)::before { content: "비중 증감"; }
  #growthBody td:nth-child(7)::before { content: "수량 증감"; }
  #growthBody td:nth-child(8)::before { content: "근거"; }

  #candidateBody td:nth-child(1)::before { content: "순위"; }
  #candidateBody td:nth-child(2)::before { content: "종목"; }
  #candidateBody td:nth-child(3)::before { content: "점수"; }
  #candidateBody td:nth-child(4)::before { content: "보유 ETF"; }
  #candidateBody td:nth-child(5)::before { content: "합산 비중"; }
  #candidateBody td:nth-child(6)::before { content: "비중 증감"; }
  #candidateBody td:nth-child(7)::before { content: "근거"; }
  #candidateBody td:nth-child(8)::before { content: "확인 포인트"; }

  #signalsBody td:nth-child(1)::before { content: "종목"; }
  #signalsBody td:nth-child(2)::before { content: "신호"; }
  #signalsBody td:nth-child(3)::before { content: "ETF"; }
  #signalsBody td:nth-child(4)::before { content: "합산 비중"; }
  #signalsBody td:nth-child(5)::before { content: "비중 증감"; }
  #signalsBody td:nth-child(6)::before { content: "이유 추정"; }

  #sourceStatusBody td:nth-child(1)::before { content: "ETF"; }
  #sourceStatusBody td:nth-child(2)::before { content: "제공처"; }
  #sourceStatusBody td:nth-child(3)::before { content: "시작일"; }
  #sourceStatusBody td:nth-child(4)::before { content: "최신일"; }
  #sourceStatusBody td:nth-child(5)::before { content: "기준일"; }
  #sourceStatusBody td:nth-child(6)::before { content: "누적 행"; }

  #jobRunsBody td:nth-child(1)::before { content: "실행"; }
  #jobRunsBody td:nth-child(2)::before { content: "기준일"; }
  #jobRunsBody td:nth-child(3)::before { content: "상태"; }
  #jobRunsBody td:nth-child(4)::before { content: "메시지"; }

  .leader-list {
    gap: 8px;
  }

  .leader {
    border-radius: 8px;
  }

  .leader h3 {
    font-size: 13px;
  }

  .leader ol {
    font-size: 12px;
  }

  canvas {
    height: 260px;
    border-radius: 8px;
  }
}

@media (max-width: 420px) {
  .metrics {
    grid-template-columns: 1fr;
  }

  td {
    grid-template-columns: minmax(78px, 34%) minmax(0, 1fr);
    padding: 8px;
  }
}
'''.strip()

if mobile_marker not in styles:
    styles = styles.rstrip() + "\n\n" + mobile_css + "\n"
styles_path.write_text(styles, encoding="utf-8")

app_path = ROOT / "dashboard" / "app.js"
app = app_path.read_text(encoding="utf-8")

if "function fitCanvas" not in app:
    app = app.replace(
        '  const ctx = canvas.getContext("2d");\n',
        '  const ctx = canvas.getContext("2d");\n\n'
        '  function fitCanvas() {\n'
        '    const rect = canvas.getBoundingClientRect();\n'
        '    const mobile = window.matchMedia("(max-width: 720px)").matches;\n'
        '    const nextWidth = Math.max(320, Math.floor(rect.width || 1100));\n'
        '    const nextHeight = mobile ? 260 : 360;\n'
        '    if (canvas.width !== nextWidth) canvas.width = nextWidth;\n'
        '    if (canvas.height !== nextHeight) canvas.height = nextHeight;\n'
        '  }\n',
    )
    app = app.replace(
        '  function renderTrend(signals) {\n    ctx.clearRect(0, 0, canvas.width, canvas.height);',
        '  function renderTrend(signals) {\n    fitCanvas();\n    ctx.clearRect(0, 0, canvas.width, canvas.height);',
    )
    app = app.replace(
        '  signalSelect.addEventListener("change", render);\n  render();',
        '  signalSelect.addEventListener("change", render);\n  window.addEventListener("resize", render);\n  render();',
    )
app_path.write_text(app, encoding="utf-8")

print("Applied mobile dashboard UI fixes.")
