from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "steam_clean.csv"
OUTPUT_PATH = ROOT / "scene7_survivor_portrait.html"

MAIN_GENRES = ["Action", "Adventure", "Casual", "Simulation", "Strategy", "RPG"]


def get_primary_genre(value: object) -> str:
    if pd.isna(value):
        return "Other"
    for genre in str(value).split(","):
        genre = genre.strip()
        if genre in MAIN_GENRES:
            return genre
    return "Other"


def build_data() -> tuple[list[dict], list[dict], dict]:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df["primary_genre"] = df["Genres"].apply(get_primary_genre)

    survivors = df[
        (df["release_year"] >= 2020) &
        (df["total_reviews"] >= 5000)
    ].copy()
    survivors = survivors.nlargest(100, "total_reviews").reset_index(drop=True)
    survivors["dev_type"] = survivors["is_indie"].map({True: "Indie", False: "AAA / Mid-size"})
    survivors["price_mode"] = survivors["Price"].fillna(0).apply(lambda p: "Free to play" if p == 0 else "Premium")
    survivors["engagement_proxy"] = survivors["Peak CCU"].fillna(0)

    ghost_pool = df[
        (df["release_year"] >= 2020) &
        ((df["total_reviews"] < 5000) | (df["positive_pct"].fillna(0) < 70))
    ].copy()
    ghost_pool = ghost_pool[~ghost_pool["AppID"].isin(survivors["AppID"])]
    ghost_pool = ghost_pool.sample(n=min(3200, len(ghost_pool)), random_state=42).reset_index(drop=True)
    ghost_pool["dev_type"] = ghost_pool["is_indie"].map({True: "Indie", False: "AAA / Mid-size"})

    survivor_fields = [
        "AppID", "Name", "release_year", "total_reviews", "positive_pct",
        "owners_midpoint", "Price", "primary_genre", "dev_type",
        "Developers", "Estimated owners", "Peak CCU", "engagement_proxy",
        "price_mode",
    ]
    ghost_fields = [
        "AppID", "release_year", "total_reviews", "positive_pct", "is_indie", "dev_type"
    ]

    survivors_json = (
        survivors[survivor_fields]
        .fillna({"positive_pct": 0, "owners_midpoint": 0, "Price": 0, "Peak CCU": 0, "engagement_proxy": 0})
        .to_dict(orient="records")
    )
    ghosts_json = (
        ghost_pool[ghost_fields]
        .fillna({"positive_pct": 0, "total_reviews": 0})
        .to_dict(orient="records")
    )

    meta = {
        "survivor_count": int(len(survivors_json)),
        "ghost_count": int(len(ghosts_json)),
        "free_survivors": int((survivors["Price"].fillna(0) == 0).sum()),
        "premium_survivors": int((survivors["Price"].fillna(0) > 0).sum()),
    }
    return survivors_json, ghosts_json, meta


def build_html(survivors: list[dict], ghosts: list[dict], meta: dict) -> str:
    survivors_json = json.dumps(survivors, ensure_ascii=False)
    ghosts_json = json.dumps(ghosts, ensure_ascii=False)
    meta_json = json.dumps(meta, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Scene 7 - Survivor Portrait</title>
  <style>
    :root {{
      --bg: #ffffff;
      --surface: #ffffff;
      --line: rgba(15, 23, 42, 0.12);
      --text: #12202f;
      --muted: #5f6c7b;
      --accent: #1d3557;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--text);
    }}

    .scene {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 18px 18px 12px;
      background: var(--surface);
    }}

    .eyebrow {{
      font: 600 0.8rem/1.2 "Segoe UI", sans-serif;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 10px;
    }}

    h1 {{
      font-size: clamp(1.8rem, 3vw, 2.9rem);
      line-height: 1.05;
      color: #102a43;
      margin-bottom: 10px;
    }}

    .subtitle {{
      max-width: 920px;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.6;
      margin-bottom: 18px;
    }}

    .controls {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 14px;
      margin-bottom: 12px;
    }}

    .control-card,
    .summary-card {{
      border: 1px solid var(--line);
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,250,252,0.96));
      padding: 14px;
    }}

    .title-sm,
    .pill,
    .hint,
    .legend,
    .stat-label,
    .stat-value,
    .summary-copy {{
      font-family: "Segoe UI", sans-serif;
    }}

    .title-sm {{
      font: 700 0.95rem/1.3 "Segoe UI", sans-serif;
      color: #102a43;
      margin-bottom: 10px;
    }}

    .pill-row {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}

    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      background: #f8fafc;
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--muted);
      cursor: pointer;
      transition: all 140ms ease;
    }}

    .pill.active {{
      background: #e7eef8;
      border-color: rgba(29, 53, 87, 0.22);
      color: var(--accent);
      transform: translateY(-1px);
    }}

    .hint {{
      color: var(--muted);
      font-size: 0.8rem;
      line-height: 1.45;
    }}

    .summary-card {{
      display: grid;
      gap: 10px;
      align-content: start;
    }}

    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}

    .stat {{
      border-radius: 14px;
      border: 1px solid rgba(15, 23, 42, 0.08);
      background: rgba(255,255,255,0.72);
      padding: 10px;
    }}

    .stat-label {{
      color: var(--muted);
      font-size: 0.76rem;
      margin-bottom: 6px;
    }}

    .stat-value {{
      font: 800 1.06rem/1.15 "Segoe UI", sans-serif;
      color: #102a43;
    }}

    .summary-copy {{
      color: var(--muted);
      font-size: 0.83rem;
      line-height: 1.5;
    }}

    .legend {{
      display: flex;
      gap: 14px;
      align-items: center;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 0.8rem;
      margin-bottom: 10px;
    }}

    .legend-item {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}

    .swatch {{
      width: 12px;
      height: 12px;
      border-radius: 999px;
      border: 1px solid rgba(15, 23, 42, 0.12);
      background: #d8dee7;
    }}

    .ring {{
      background: transparent;
      border: 2px solid #457b9d;
    }}

    #vizWrap {{
      width: 100%;
      border-top: 1px solid rgba(15, 23, 42, 0.05);
      padding-top: 12px;
      position: relative;
    }}

    canvas {{
      display: block;
      width: 100%;
      height: 680px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(250,250,251,0.98));
    }}

    .tooltip {{
      position: fixed;
      display: none;
      pointer-events: none;
      z-index: 999;
      background: rgba(255, 255, 255, 0.98);
      border: 1px solid rgba(15, 23, 42, 0.12);
      box-shadow: 0 14px 40px rgba(15, 23, 42, 0.10);
      border-radius: 12px;
      padding: 10px 12px;
      color: var(--text);
      font: 12px/1.55 "Segoe UI", sans-serif;
      min-width: 230px;
      max-width: 300px;
    }}

    .tooltip.show {{
      display: block;
    }}

    .tooltip strong {{
      display: block;
      margin-bottom: 4px;
      color: #102a43;
      font-size: 12.5px;
    }}

    @media (max-width: 880px) {{
      .controls {{
        grid-template-columns: 1fr;
      }}

      .stat-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="scene">
    <div class="eyebrow">Closing</div>
    <h1>Survivor Portrait</h1>
    <p class="subtitle">
      The last chart no longer shows only the winners. A gray field of unsuccessful releases forms the landscape underneath,
      and the survivors float above it. The left side is the danger zone where quality falls under the threshold needed to stay visible.
      The upper-right corner is the elite corridor: the tiny pocket where quality and scale meet.
    </p>

    <div class="controls">
      <div class="control-card">
        <div class="title-sm">Filter the survivors</div>
        <div class="pill-row" id="filterPills">
          <button class="pill active" data-filter="all" type="button">All Survivors</button>
          <button class="pill" data-filter="indie" type="button">Indie Only</button>
          <button class="pill" data-filter="aaa" type="button">AAA / Mid-size</button>
          <button class="pill active" data-ghosts="on" type="button" id="ghostToggle">Ghost Layer On</button>
        </div>
        <div class="hint" id="sceneHint">
          Filled bubbles are premium games. Hollow bubbles are free-to-play. Hue still separates Indie and AAA / Mid-size, while deeper tones indicate higher concurrent engagement.
        </div>
      </div>

      <div class="summary-card">
        <div class="title-sm">What survival looks like</div>
        <div class="stat-grid">
          <div class="stat">
            <div class="stat-label">Survivors shown</div>
            <div class="stat-value" id="stat1Value"></div>
          </div>
          <div class="stat">
            <div class="stat-label">Free survivors</div>
            <div class="stat-value" id="stat2Value"></div>
          </div>
          <div class="stat">
            <div class="stat-label">Elite corner</div>
            <div class="stat-value" id="stat3Value"></div>
          </div>
        </div>
        <div class="summary-copy" id="summaryCopy"></div>
      </div>
    </div>

    <div class="legend">
      <div class="legend-item"><span class="swatch" style="background:#d9dde3"></span><span>Ghost background: games that never reached this survivor tier</span></div>
      <div class="legend-item"><span class="swatch" style="background:#56c7bc"></span><span>Indie survivor</span></div>
      <div class="legend-item"><span class="swatch" style="background:#d96b72"></span><span>AAA / Mid-size survivor</span></div>
      <div class="legend-item"><span class="swatch ring"></span><span>Free-to-play survivor</span></div>
    </div>

    <div id="vizWrap">
      <canvas id="chart" width="1040" height="680"></canvas>
    </div>
  </div>

  <div class="tooltip" id="tooltip"></div>

  <script>
    const survivors = {survivors_json};
    const ghosts = {ghosts_json};
    const meta = {meta_json};

    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");
    const tooltip = document.getElementById("tooltip");
    const summaryCopy = document.getElementById("summaryCopy");
    const stat1Value = document.getElementById("stat1Value");
    const stat2Value = document.getElementById("stat2Value");
    const stat3Value = document.getElementById("stat3Value");
    const sceneHint = document.getElementById("sceneHint");
    const filterPills = document.getElementById("filterPills");
    const ghostToggle = document.getElementById("ghostToggle");

    const W = canvas.width;
    const H = canvas.height;
    const margin = {{ top: 38, right: 40, bottom: 72, left: 76 }};
    const plotW = W - margin.left - margin.right;
    const plotH = H - margin.top - margin.bottom;

    const xMin = 50;
    const xMax = 100;
    const yMin = 1000;
    const yMax = Math.max(...survivors.map(d => d.total_reviews), 500000);
    const ownerMax = Math.max(...survivors.map(d => d.owners_midpoint || 0), 1);
    const engagementMax = Math.max(...survivors.map(d => d.engagement_proxy || 0), 1);

    const state = {{
      filter: "all",
      showGhosts: true,
      hovered: null
    }};

    function clamp(value, min, max) {{
      return Math.max(min, Math.min(max, value));
    }}

    function xScale(v) {{
      const t = (v - xMin) / (xMax - xMin);
      return margin.left + t * plotW;
    }}

    function yScale(v) {{
      const logMin = Math.log10(yMin);
      const logMax = Math.log10(yMax);
      const safe = Math.max(v, yMin);
      const t = (Math.log10(safe) - logMin) / (logMax - logMin);
      return margin.top + plotH - t * plotH;
    }}

    function sizeScale(v) {{
      return 7 + Math.sqrt((v || 0) / ownerMax) * 24;
    }}

    function engagementT(v) {{
      return clamp(Math.log10((v || 0) + 1) / Math.log10(engagementMax + 1), 0, 1);
    }}

    function interpolateColor(a, b, t) {{
      const ar = parseInt(a.slice(1, 3), 16);
      const ag = parseInt(a.slice(3, 5), 16);
      const ab = parseInt(a.slice(5, 7), 16);
      const br = parseInt(b.slice(1, 3), 16);
      const bg = parseInt(b.slice(3, 5), 16);
      const bb = parseInt(b.slice(5, 7), 16);
      const rr = Math.round(ar + (br - ar) * t);
      const rg = Math.round(ag + (bg - ag) * t);
      const rb = Math.round(ab + (bb - ab) * t);
      return `rgb(${{rr}}, ${{rg}}, ${{rb}})`;
    }}

    function survivorColor(d) {{
      const t = engagementT(d.engagement_proxy);
      if (d.dev_type === "Indie") {{
        return interpolateColor("#9adfd8", "#167a72", t);
      }}
      return interpolateColor("#efb4b8", "#a32731", t);
    }}

    function filteredSurvivors() {{
      if (state.filter === "indie") return survivors.filter(d => d.dev_type === "Indie");
      if (state.filter === "aaa") return survivors.filter(d => d.dev_type !== "Indie");
      return survivors;
    }}

    function filteredGhosts() {{
      if (!state.showGhosts) return [];
      if (state.filter === "indie") return ghosts.filter(d => d.dev_type === "Indie");
      if (state.filter === "aaa") return ghosts.filter(d => d.dev_type !== "Indie");
      return ghosts;
    }}

    function drawZones() {{
      const dangerX = xScale(70);
      const grad = ctx.createLinearGradient(margin.left, margin.top, dangerX, margin.top);
      grad.addColorStop(0, "rgba(193, 18, 31, 0.11)");
      grad.addColorStop(1, "rgba(193, 18, 31, 0.03)");
      ctx.fillStyle = grad;
      ctx.fillRect(margin.left, margin.top, dangerX - margin.left, plotH);

      ctx.fillStyle = "#9d1c24";
      ctx.font = "700 12px Segoe UI";
      ctx.fillText("Danger Zone", margin.left + 12, margin.top + 22);

      const eliteX = xScale(90);
      const eliteY = yScale(50000);
      ctx.save();
      ctx.strokeStyle = "rgba(201, 157, 45, 0.75)";
      ctx.lineWidth = 2;
      ctx.setLineDash([8, 6]);
      ctx.strokeRect(eliteX, eliteY, W - margin.right - eliteX, H - margin.bottom - eliteY);
      ctx.restore();

      ctx.fillStyle = "#8c6a0f";
      ctx.font = "700 12px Segoe UI";
      ctx.fillText("The 1% Elite", eliteX + 12, eliteY + 22);
    }}

    function drawAxes() {{
      ctx.save();
      ctx.strokeStyle = "rgba(15, 23, 42, 0.12)";
      ctx.lineWidth = 1;

      [60, 70, 80, 90, 100].forEach(v => {{
        const x = xScale(v);
        ctx.strokeStyle = "rgba(15, 23, 42, 0.06)";
        ctx.beginPath();
        ctx.moveTo(x, margin.top);
        ctx.lineTo(x, H - margin.bottom);
        ctx.stroke();

        ctx.fillStyle = "#5f6c7b";
        ctx.font = "12px Segoe UI";
        ctx.textAlign = "center";
        ctx.fillText(`${{v}}%`, x, H - margin.bottom + 26);
      }});

      [1000, 5000, 10000, 50000, 100000, 300000].forEach(v => {{
        const y = yScale(v);
        ctx.strokeStyle = "rgba(15, 23, 42, 0.06)";
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(W - margin.right, y);
        ctx.stroke();

        ctx.fillStyle = "#5f6c7b";
        ctx.font = "12px Segoe UI";
        ctx.textAlign = "right";
        const label = v >= 1000 ? `${{(v / 1000).toFixed(v >= 100000 ? 0 : 1).replace('.0','')}}k` : String(v);
        ctx.fillText(label, margin.left - 10, y + 4);
      }});

      ctx.strokeStyle = "rgba(15, 23, 42, 0.14)";
      ctx.beginPath();
      ctx.moveTo(margin.left, margin.top);
      ctx.lineTo(margin.left, H - margin.bottom);
      ctx.lineTo(W - margin.right, H - margin.bottom);
      ctx.stroke();

      ctx.fillStyle = "#102a43";
      ctx.font = "700 18px Georgia";
      ctx.textAlign = "left";
      ctx.fillText("Who made it out of the flood?", margin.left, 24);
      ctx.fillStyle = "#5f6c7b";
      ctx.font = "12px Segoe UI";
      ctx.fillText("Gray dots are the failed majority. Survivors rise above them only when quality and visibility arrive together.", margin.left, 42);

      ctx.save();
      ctx.translate(20, margin.top + plotH / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillStyle = "#5f6c7b";
      ctx.font = "12px Segoe UI";
      ctx.textAlign = "center";
      ctx.fillText("Total reviews (log scale)", 0, 0);
      ctx.restore();

      ctx.fillStyle = "#5f6c7b";
      ctx.font = "12px Segoe UI";
      ctx.textAlign = "center";
      ctx.fillText("Positive review percentage", margin.left + plotW / 2, H - 20);
      ctx.restore();
    }}

    function drawGhosts(ghostData) {{
      ctx.save();
      ghostData.forEach((d, idx) => {{
        const x = xScale(clamp(d.positive_pct || 0, xMin, xMax));
        const y = yScale(Math.max(d.total_reviews || 0, yMin));
        const jitter = ((idx % 7) - 3) * 0.8;
        ctx.beginPath();
        ctx.fillStyle = d.dev_type === "Indie" ? "rgba(135, 150, 165, 0.16)" : "rgba(165, 145, 145, 0.16)";
        ctx.arc(x + jitter, y + ((idx % 5) - 2) * 0.6, 2.2, 0, Math.PI * 2);
        ctx.fill();
      }});
      ctx.restore();
    }}

    function drawSurvivors(data) {{
      const hitboxes = [];
      data.forEach(d => {{
        const x = xScale(d.positive_pct);
        const y = yScale(d.total_reviews);
        const r = sizeScale(d.owners_midpoint || 0);
        const color = survivorColor(d);
        const hovered = state.hovered && state.hovered.AppID === d.AppID;

        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, r + 5, 0, Math.PI * 2);
        ctx.fillStyle = hovered ? "rgba(29, 53, 87, 0.10)" : "rgba(29, 53, 87, 0.05)";
        ctx.fill();

        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        if ((d.Price || 0) === 0) {{
          ctx.lineWidth = hovered ? 4 : 3;
          ctx.strokeStyle = color;
          ctx.stroke();
          ctx.fillStyle = "rgba(255,255,255,0.82)";
          ctx.fill();
        }} else {{
          ctx.fillStyle = color;
          ctx.fill();
          ctx.lineWidth = hovered ? 3 : 1.5;
          ctx.strokeStyle = "rgba(255,255,255,0.85)";
          ctx.stroke();
        }}

        if (hovered) {{
          ctx.fillStyle = "#102a43";
          ctx.font = "700 11px Segoe UI";
          ctx.textAlign = "left";
          ctx.fillText(d.Name, x + r + 8, y - r - 4);
        }}
        ctx.restore();

        hitboxes.push({{ ...d, x, y, r }});
      }});
      return hitboxes;
    }}

    function updateSummary(data) {{
      const elite = data.filter(d => d.positive_pct >= 90 && d.total_reviews >= 50000);
      const free = data.filter(d => (d.Price || 0) === 0);
      const premium = data.filter(d => (d.Price || 0) > 0);

      stat1Value.textContent = `${{data.length}} / ${{meta.survivor_count}}`;
      stat2Value.textContent = `${{free.length}} free`;
      stat3Value.textContent = `${{elite.length}} elite`;

      if (state.hovered) {{
        const d = state.hovered;
        summaryCopy.textContent =
          `${{d.Name}} sits at ${{d.positive_pct.toFixed(1)}}% positive with ${{d.total_reviews.toLocaleString("en-US")}} reviews. ` +
          `${{(d.Price || 0) === 0 ? "It is free-to-play," : "It is a paid release,"}} and its engagement proxy reaches a Peak CCU of ${{(d["Peak CCU"] || 0).toLocaleString("en-US")}}.`;
        sceneHint.textContent =
          `Current hover: ${{d.dev_type}} / ${{d.primary_genre}}. The bubble size represents estimated owner base, and the darkness reflects Peak CCU because playtime fields are flat in this cleaned dataset.`;
        return;
      }}

      const indieCount = data.filter(d => d.dev_type === "Indie").length;
      const aaaCount = data.filter(d => d.dev_type !== "Indie").length;
      summaryCopy.textContent =
        `This filter shows ${{indieCount}} Indie survivors and ${{aaaCount}} AAA / Mid-size survivors. ${{premium.length}} are paid games, ` +
        `while only ${{free.length}} survivors are free-to-play. The elite corner contains the tiny group that cleared both quality and large-scale attention.`;

      sceneHint.textContent =
        "Filled bubbles are premium games. Hollow bubbles are free-to-play. Hue still separates Indie and AAA / Mid-size, while deeper tones indicate higher concurrent engagement.";
    }}

    function draw() {{
      ctx.clearRect(0, 0, W, H);
      drawZones();
      drawAxes();
      drawGhosts(filteredGhosts());
      state.hitboxes = drawSurvivors(filteredSurvivors());
      updateSummary(filteredSurvivors());
    }}

    function showTooltip(d, evt) {{
      tooltip.innerHTML = `
        <strong>${{d.Name}}</strong>
        Developer type: ${{d.dev_type}}<br />
        Genre: ${{d.primary_genre}}<br />
        Released: ${{Math.round(d.release_year)}}<br />
        Positive reviews: ${{d.positive_pct.toFixed(1)}}%<br />
        Total reviews: ${{d.total_reviews.toLocaleString("en-US")}}<br />
        Price: $${{Number(d.Price || 0).toFixed(2)}} (${{d.price_mode}})<br />
        Estimated owners: ${{String(d["Estimated owners"] || "Unknown")}}<br />
        Peak CCU: ${{(d["Peak CCU"] || 0).toLocaleString("en-US")}}
      `;
      tooltip.classList.add("show");
      tooltip.style.left = `${{evt.clientX + 16}}px`;
      tooltip.style.top = `${{evt.clientY + 16}}px`;
    }}

    function hideTooltip() {{
      tooltip.classList.remove("show");
    }}

    canvas.addEventListener("mousemove", evt => {{
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const x = (evt.clientX - rect.left) * scaleX;
      const y = (evt.clientY - rect.top) * scaleY;

      const hit = (state.hitboxes || []).findLast(d => Math.hypot(d.x - x, d.y - y) <= d.r + 4);
      if (hit) {{
        state.hovered = hit;
        showTooltip(hit, evt);
      }} else {{
        state.hovered = null;
        hideTooltip();
      }}
      draw();
    }});

    canvas.addEventListener("mouseleave", () => {{
      state.hovered = null;
      hideTooltip();
      draw();
    }});

    filterPills.addEventListener("click", evt => {{
      const btn = evt.target.closest("button");
      if (!btn) return;

      const filter = btn.dataset.filter;
      if (filter) {{
        state.filter = filter;
        [...filterPills.querySelectorAll("[data-filter]")].forEach(node => node.classList.toggle("active", node.dataset.filter === filter));
      }}

      if (btn.id === "ghostToggle") {{
        state.showGhosts = !state.showGhosts;
        btn.classList.toggle("active", state.showGhosts);
        btn.textContent = state.showGhosts ? "Ghost Layer On" : "Ghost Layer Off";
      }}

      state.hovered = null;
      hideTooltip();
      draw();
    }});

    draw();
  </script>
</body>
</html>
"""


def main() -> None:
    survivors, ghosts, meta = build_data()
    OUTPUT_PATH.write_text(build_html(survivors, ghosts, meta), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
