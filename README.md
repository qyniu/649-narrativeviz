# The Indie Game Gold Rush: Narrative Visualization

**Team**: Qingyuan Niu (qyniu), Jiayi Yu (yujiayi) | SI 649 | April 2026

> *In 2024, 89% of games released on Steam received zero reviews. Not bad reviews — zero.*

---

## Story

This is a data journalism piece structured as a scrollytelling article. The central argument: Steam's open-gate policy democratized *publishing*, not *success*. As game output exploded 30×, the pool of player attention stayed fixed — and the probability of anyone noticing your game collapsed by 22×.

---

## File Structure

```
narrativeviz/
├── steam_narrative_viz.ipynb   ← All 5 visualizations (this notebook)
├── data/
│   └── steam_clean.csv         ← Cleaned Steam dataset (86,975 games)
├── viz2_waffle.png             ← Exported waffle chart (Viz 2)
└── README.md
```

---

## Running the Notebook

```bash
pip install pandas numpy altair matplotlib
jupyter notebook steam_narrative_viz.ipynb
```

Run all cells top to bottom. The setup cell must execute first — it loads and preprocesses the data for all downstream visualizations.

---

## Visualizations

### Viz 1 — The Flood: Annotated Stacked Area Chart
**Scene**: How dramatically did Steam game output increase (2008–2024)?

- Stacked area: Indie (teal) vs. Non-Indie (red) releases per year
- Annotated with key policy changes: **Steam Greenlight (2012)** and **Steam Direct (2017)**
- **Interactive**: click legend to isolate game type; hover for exact counts
- Key insight: Steam Direct's $100 flat fee triggered near-vertical growth — Indie releases grew from ~400/year (2013) to ~10,000+ (2024)

---

### Viz 2 — The Invisible Games: Waffle Chart
**Scene**: What does "89% received zero reviews" actually look like?

- Each square = 1% of all games released that year
- Gray = zero reviews (invisible); red = at least 1 review (seen)
- Shows 4 snapshot years: 2013, 2017, 2020, 2024
- Key insight: The gray tide rose from 83% (2013) → 89% (2024) as the volume of releases outpaced player capacity

---

### Viz 3 — The Scissors Effect: Dual-Axis Diverging Chart
**Scene**: How much did success odds shrink?

- Teal area (left axis): total new games released per year — rising steeply
- Red line + points (right axis): "hit rate" (% of games reaching 1,000+ reviews) — falling steeply
- The two trends form a visual scissors/diverging effect
- **Interactive**: hover red points for exact hit rate and hit game count
- Key insight: Hit rate fell from **8.35% (2013) → 0.38% (2024)** — a 22× collapse. Absolute hit count (~40–110/year) barely changed; the denominator grew 30×.

---

### Viz 4 — Who's Still Winning? Interactive Strip Plot
**Scene**: In this sea of failures, which games still break through?

- Each dot = one game; X = total reviews (log₁₀ scale); Y = release year (jittered)
- Color-coded by primary genre (Action, Adventure, Casual, RPG, etc.)
- **Interactive**: dropdown to highlight a specific genre; hover for game name, review count, positive %
- The dense cluster near x=0 (≈zero reviews) is the invisible mass; outliers on the right are breakout hits
- Key insight: No genre is immune — the right tail (hits) exists in every year but thins proportionally

---

### Viz 5 — Genre Survival Map: Side-by-Side Heatmaps
**Scene**: If you're a developer, which genre gives the best shot?

- Left heatmap: hit rate (% reaching 1,000+ reviews) by genre × year — color = orange/red gradient
- Right heatmap: median review count by genre × year — color = blue gradient
- Both heatmaps share hover tooltips with total games, hit count, hit rate, and median reviews
- Key insight: Action and RPG genres consistently hold the highest hit rates; Casual, despite massive volume, shows near-zero hit rates in recent years

---

## Data Notes

- **Source**: Steam Games dataset (cleaned), 86,975 games, 2008–2024
- **Hit definition**: ≥ 1,000 total reviews (positive + negative)
- **Invisible**: 0 total reviews
- **Primary genre**: first genre in the `Genres` column matching a curated list; games with only `Indie`/`Free To Play` fall back to `Other`
- Viz 4 samples 30% of zero-review games for rendering performance (~35K points total)

---

## Key Statistics

| Metric | 2013 | 2024 |
|--------|------|------|
| Games released | 455 | 12,452 |
| Hit rate (≥1K reviews) | 8.35% | 0.38% |
| % with zero reviews | 83.3% | 89.1% |
| Hit games (absolute) | 38 | 47 |
