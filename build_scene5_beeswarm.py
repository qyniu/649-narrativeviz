from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "steam_clean.csv"
OUTPUT_PATH = ROOT / "scene5_disappearing_middle.html"


COLOR_BY_BUCKET = {
    "0": "#e9ecef",
    "1-9": "#ced4da",
    "10-99": "#adb5bd",
    "100-999": "#2a9d8f",
    "1K-9999": "#f4a261",
    "10K-99K": "#e76f51",
    "100K+": "#e63946",
}

LABEL_BY_BUCKET = {
    "0": "Ghost (0)",
    "1-9": "Micro (1-9)",
    "10-99": "Whisper (10-99)",
    "100-999": "Modest (100-999)",
    "1K-9999": "Hit (1K-9.9K)",
    "10K-99K": "Major (10K-99K)",
    "100K+": "Icon (100K+)",
}


def load_data() -> tuple[list[dict], dict]:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = df[df["release_year"].isin([2013, 2024])].copy()
    df["release_year"] = df["release_year"].astype(int)
    df["review_bucket"] = df["review_bucket"].fillna("0")
    df["positive_pct"] = df["positive_pct"].round(1)
    df["Estimated owners"] = df["Estimated owners"].fillna("Unknown")

    points = []
    for _, row in df.iterrows():
        points.append(
            {
                "appId": int(row["AppID"]),
                "name": str(row["Name"]),
                "year": int(row["release_year"]),
                "reviews": int(row["total_reviews"] or 0),
                "bucket": str(row["review_bucket"]),
                "bucketLabel": LABEL_BY_BUCKET.get(str(row["review_bucket"]), str(row["review_bucket"])),
                "isIndie": bool(row["is_indie"]),
                "positivePct": None if pd.isna(row["positive_pct"]) else float(row["positive_pct"]),
                "owners": str(row["Estimated owners"]),
            }
        )

    stats = {}
    for year in [2013, 2024]:
        year_df = df[df["release_year"] == year]
        total = len(year_df)
        bucket_counts = year_df["review_bucket"].value_counts().to_dict()
        stats[year] = {
            "total": total,
            "ghost_pct": round(bucket_counts.get("0", 0) / total * 100, 1) if total else 0,
            "modest_pct": round(bucket_counts.get("100-999", 0) / total * 100, 1) if total else 0,
            "hit_pct": round(bucket_counts.get("1K-9999", 0) / total * 100, 1) if total else 0,
        }

    return points, stats


def build_html(points: list[dict], stats: dict) -> str:
    data_json = json.dumps(points, ensure_ascii=False)
    stats_json = json.dumps(stats, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Scene 5 - The Disappearing Middle</title>
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
      max-width: 860px;
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
      font: 800 1.08rem/1.15 "Segoe UI", sans-serif;
      color: #102a43;
    }}

    .summary-copy {{
      color: var(--muted);
      font-size: 0.83rem;
      line-height: 1.5;
    }}

    .legend {{
      display: flex;
      gap: 12px;
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
      cursor: pointer;
      user-select: none;
    }}

    .legend-item.muted {{
      opacity: 0.35;
    }}

    .swatch {{
      width: 12px;
      height: 12px;
      border-radius: 999px;
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
      height: 640px;
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
      min-width: 220px;
      max-width: 280px;
    }}

    .tooltip.show {{
      display: block;
    }}

    @media (max-width: 900px) {{
      .scene {{
        padding: 10px 10px 6px;
      }}

      .controls {{
        grid-template-columns: 1fr;
      }}

      .stat-grid {{
        grid-template-columns: 1fr;
      }}

      canvas {{
        height: 560px;
      }}
    }}
  </style>
</head>
<body>
  <section class="scene">
    <div class="eyebrow">Scene 5</div>
    <h1>The Disappearing Middle</h1>
    <p class="subtitle">
      Here the market splits into two poles. In 2013, review outcomes still spread upward across the ladder. By 2024, most points collapse into the bottom floor while only a tiny elite remains aloft. Use the filters to isolate indie games and watch how the missing middle becomes even clearer.
    </p>

    <div class="controls">
      <div class="control-card">
        <div class="title-sm">Filters</div>
        <div class="pill-row">
          <button class="pill active" data-filter="all">All Games</button>
          <button class="pill" data-filter="indie">Indie Only</button>
        </div>
        <div class="hint">
          Each dot is one game. Left column: 2013. Right column: 2024. Vertical position uses a log review scale, so “falling to the bottom” means the game never escaped invisibility.
        </div>
      </div>

      <div class="summary-card">
        <div class="title-sm">Yearly survival snapshot</div>
        <div class="stat-grid">
          <div class="stat">
            <div class="stat-label">Ghost share</div>
            <div class="stat-value" id="ghostStat">83.3%</div>
          </div>
          <div class="stat">
            <div class="stat-label">Modest share</div>
            <div class="stat-value" id="modestStat">7.0%</div>
          </div>
          <div class="stat">
            <div class="stat-label">Hit share</div>
            <div class="stat-value" id="hitStat">5.7%</div>
          </div>
        </div>
        <div class="summary-copy" id="summaryCopy">
          In 2013, the middle of the market was still visible: modest and hit games together formed a meaningful vertical band instead of a few isolated specks.
        </div>
      </div>
    </div>

    <div class="legend" id="legend"></div>
    <div id="vizWrap">
      <canvas id="chart"></canvas>
    </div>
  </section>

  <div class="tooltip" id="tooltip"></div>

  <script>
    const POINTS = {data_json};
    const YEAR_STATS = {stats_json};
    const COLORS = {json.dumps(COLOR_BY_BUCKET)};
    const LABELS = {json.dumps(LABEL_BY_BUCKET)};
    const ORDER = {json.dumps(list(COLOR_BY_BUCKET.keys()))};
    const YEARS = [2013, 2024];

    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");
    const tooltip = document.getElementById("tooltip");
    const pills = Array.from(document.querySelectorAll(".pill"));
    const legend = document.getElementById("legend");
    const ghostStat = document.getElementById("ghostStat");
    const modestStat = document.getElementById("modestStat");
    const hitStat = document.getElementById("hitStat");
    const summaryCopy = document.getElementById("summaryCopy");

    let activeFilter = "all";
    let highlightedBucket = null;
    let renderedPoints = [];
    let dimensions = null;

    function showTip(html, event) {{
      tooltip.innerHTML = html;
      tooltip.classList.add("show");
      moveTip(event);
    }}

    function moveTip(event) {{
      tooltip.style.left = Math.min(event.clientX + 16, window.innerWidth - 290) + "px";
      tooltip.style.top = Math.max(12, event.clientY - 12) + "px";
    }}

    function hideTip() {{
      tooltip.classList.remove("show");
    }}

    function seededRandom(seed) {{
      const value = Math.sin(seed * 928.371) * 43758.5453;
      return value - Math.floor(value);
    }}

    function filteredPoints() {{
      return POINTS.filter((d) => activeFilter === "all" || d.isIndie);
    }}

    function updateLegend() {{
      legend.innerHTML = "";
      ORDER.forEach((bucket) => {{
        const item = document.createElement("div");
        item.className = "legend-item" + (highlightedBucket && highlightedBucket !== bucket ? " muted" : "");
        item.innerHTML = `<span class="swatch" style="background:${{COLORS[bucket]}}"></span><span>${{LABELS[bucket]}}</span>`;
        item.onclick = () => {{
          highlightedBucket = highlightedBucket === bucket ? null : bucket;
          updateLegend();
          draw();
        }};
        legend.appendChild(item);
      }});
    }}

    function updateSummary(year, bucketKey = "100-999") {{
      const filtered = filteredPoints().filter((d) => d.year === year);
      const total = filtered.length || 1;
      const bucketPct = (bucket) => filtered.filter((d) => d.bucket === bucket).length / total * 100;
      const nowPct = bucketPct(bucketKey);
      const year2013 = filteredPoints().filter((d) => d.year === 2013);
      const year2024 = filteredPoints().filter((d) => d.year === 2024);
      const pctIn = (arr, bucket) => arr.length ? arr.filter((d) => d.bucket === bucket).length / arr.length * 100 : 0;

      ghostStat.textContent = `${{bucketPct("0").toFixed(1)}}%`;
      modestStat.textContent = `${{bucketPct("100-999").toFixed(1)}}%`;
      hitStat.textContent = `${{bucketPct("1K-9999").toFixed(1)}}%`;

      summaryCopy.textContent =
        `In ${{year}}, ${{LABELS[bucketKey]}} games were ${{nowPct.toFixed(1)}}% of this view. In 2013 they were ${{pctIn(year2013, bucketKey).toFixed(1)}}%; by 2024 they were ${{pctIn(year2024, bucketKey).toFixed(1)}}%.`;
    }}

    function tooltipHtml(point) {{
      const view2013 = filteredPoints().filter((d) => d.year === 2013);
      const view2024 = filteredPoints().filter((d) => d.year === 2024);
      const pctIn = (arr, bucket) => arr.length ? arr.filter((d) => d.bucket === bucket).length / arr.length * 100 : 0;
      const pos = point.positivePct == null ? "n/a" : `${{point.positivePct.toFixed(1)}}%`;
      return [
        `<div style="font-weight:700;margin-bottom:4px;">${{point.name}}</div>`,
        `<div>${{point.year}} · ${{point.bucketLabel}}</div>`,
        `<div>Total reviews: <b>${{point.reviews.toLocaleString()}}</b></div>`,
        `<div>Positive %: <b>${{pos}}</b></div>`,
        `<div>Estimated owners: <b>${{point.owners}}</b></div>`,
        `<div style="margin-top:6px;color:#52606d;">In 2013, this tier was <b>${{pctIn(view2013, point.bucket).toFixed(1)}}%</b> of the market. In 2024, it was <b>${{pctIn(view2024, point.bucket).toFixed(1)}}%</b>.</div>`
      ].join("");
    }}

    function resizeCanvas() {{
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      dimensions = {{
        width: rect.width,
        height: rect.height,
        margin: {{ top: 34, right: 34, bottom: 40, left: 72 }}
      }};
    }}

    function computeLayout() {{
      const pts = filteredPoints();
      const {{ width, height, margin }} = dimensions;
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      const columnX = {{
        2013: margin.left + innerWidth * 0.25,
        2024: margin.left + innerWidth * 0.75
      }};
      const yScale = (value) => {{
        const minLog = 0;
        const maxLog = Math.log10(100000 + 1);
        const t = (Math.log10((value || 0) + 1) - minLog) / (maxLog - minLog);
        return margin.top + innerHeight * (1 - t);
      }};

      const grouped = {{ 2013: {{}}, 2024: {{}} }};
      pts.forEach((point) => {{
        const year = point.year;
        const row = Math.round(yScale(point.reviews) / 6) * 6;
        const key = `${{year}}-${{row}}-${{point.bucket}}`;
        if (!grouped[year][key]) grouped[year][key] = [];
        grouped[year][key].push(point);
      }});

      const placed = [];
      Object.entries(grouped).forEach(([year, groups]) => {{
        Object.values(groups).forEach((arr) => {{
          arr.sort((a, b) => a.appId - b.appId);
          arr.forEach((point, i) => {{
            const direction = i % 2 === 0 ? 1 : -1;
            const layer = Math.ceil(i / 2);
            const jitterBase = direction * layer * 5.6;
            const jitterNoise = (seededRandom(point.appId) - 0.5) * 2.2;
            const cx = columnX[year] + jitterBase + jitterNoise;
            const cy = yScale(point.reviews) + (seededRandom(point.appId + 7) - 0.5) * 2.6;
            placed.push({{
              ...point,
              cx,
              cy,
              r: point.reviews >= 100000 ? 4.8 : point.reviews >= 10000 ? 4.1 : point.reviews >= 1000 ? 3.6 : 3.1
            }});
          }});
        }});
      }});

      return {{
        points: placed,
        columnX,
        yScale,
        innerWidth,
        innerHeight
      }};
    }}

    function drawAxes(layout) {{
      const {{ width, height, margin }} = dimensions;
      const {{ innerHeight }} = layout;
      ctx.save();
      ctx.translate(0.5, 0.5);
      ctx.strokeStyle = "rgba(15, 23, 42, 0.08)";
      ctx.fillStyle = "#5f6c7b";
      ctx.font = "11px Segoe UI";

      const ticks = [0, 10, 100, 1000, 10000, 100000];
      ticks.forEach((tick) => {{
        const y = layout.yScale(tick);
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(width - margin.right, y);
        ctx.stroke();
        ctx.fillText(tick === 0 ? "0" : d3Format(tick), 14, y + 4);
      }});

      Object.entries(layout.columnX).forEach(([year, x]) => {{
        ctx.fillStyle = "#102a43";
        ctx.font = "700 18px Segoe UI";
        ctx.textAlign = "center";
        ctx.fillText(year, x, height - 12);
      }});

      ctx.save();
      ctx.translate(20, margin.top + innerHeight / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.textAlign = "center";
      ctx.fillStyle = "#5f6c7b";
      ctx.font = "12px Segoe UI";
      ctx.fillText("Total Reviews (log scale)", 0, 0);
      ctx.restore();

      ctx.restore();
    }}

    function d3Format(value) {{
      if (value >= 1000) return value >= 100000 ? "100k" : `${{Math.round(value / 1000)}}k`;
      return String(value);
    }}

    function drawGuide(layout) {{
      if (!hoveredYear) return;
      ctx.save();
      ctx.strokeStyle = "rgba(29, 53, 87, 0.28)";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(layout.columnX[hoveredYear], dimensions.margin.top);
      ctx.lineTo(layout.columnX[hoveredYear], dimensions.height - dimensions.margin.bottom + 4);
      ctx.stroke();
      ctx.restore();
    }}

    let hoveredPoint = null;
    let hoveredYear = 2013;

    function draw() {{
      resizeCanvas();
      const layout = computeLayout();
      renderedPoints = layout.points;
      ctx.clearRect(0, 0, dimensions.width, dimensions.height);
      drawAxes(layout);

      renderedPoints.forEach((point) => {{
        const muted = highlightedBucket && highlightedBucket !== point.bucket;
        ctx.beginPath();
        ctx.fillStyle = COLORS[point.bucket];
        ctx.globalAlpha = muted ? 0.16 : 0.88;
        ctx.arc(point.cx, point.cy, point.r, 0, Math.PI * 2);
        ctx.fill();
      }});
      ctx.globalAlpha = 1;
      drawGuide(layout);

      if (hoveredPoint) {{
        ctx.beginPath();
        ctx.strokeStyle = "#1d3557";
        ctx.lineWidth = 1.5;
        ctx.arc(hoveredPoint.cx, hoveredPoint.cy, hoveredPoint.r + 2.5, 0, Math.PI * 2);
        ctx.stroke();
      }}
    }}

    function nearestPoint(mx, my) {{
      let best = null;
      let bestDist = Infinity;
      renderedPoints.forEach((point) => {{
        const dx = point.cx - mx;
        const dy = point.cy - my;
        const dist = Math.hypot(dx, dy);
        if (dist < bestDist && dist < Math.max(8, point.r + 5)) {{
          bestDist = dist;
          best = point;
        }}
      }});
      return best;
    }}

    canvas.addEventListener("mousemove", (event) => {{
      const rect = canvas.getBoundingClientRect();
      const mx = event.clientX - rect.left;
      const my = event.clientY - rect.top;
      hoveredPoint = nearestPoint(mx, my);
      hoveredYear = Math.abs(mx - dimensions.width * 0.28) < Math.abs(mx - dimensions.width * 0.72) ? 2013 : 2024;
      if (hoveredPoint) {{
        hoveredYear = hoveredPoint.year;
        updateSummary(hoveredPoint.year, hoveredPoint.bucket);
        showTip(tooltipHtml(hoveredPoint), event);
      }} else {{
        hideTip();
        updateSummary(hoveredYear, "100-999");
      }}
      draw();
    }});

    canvas.addEventListener("mouseleave", () => {{
      hoveredPoint = null;
      hoveredYear = 2013;
      hideTip();
      updateSummary(2013, "100-999");
      draw();
    }});

    pills.forEach((pill) => {{
      pill.addEventListener("click", () => {{
        activeFilter = pill.dataset.filter;
        pills.forEach((button) => button.classList.toggle("active", button === pill));
        hoveredPoint = null;
        highlightedBucket = null;
        updateLegend();
        updateSummary(2013, "100-999");
        draw();
      }});
    }});

    let resizeTimer = null;
    const resizeObserver = new ResizeObserver(() => {{
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(draw, 80);
    }});
    resizeObserver.observe(canvas);

    updateLegend();
    updateSummary(2013, "100-999");
    draw();
  </script>
</body>
</html>
"""


def main() -> None:
    points, stats = load_data()
    OUTPUT_PATH.write_text(build_html(points, stats), encoding="utf-8")
    print(f"Built {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
