# The World in One Day — news-image-20261125

A 1024×1024 broadsheet-style infographic summing up Wednesday 25 November 2026
world news in a single image, for the
[make.fun](https://make.fun/bounty/news-image-20261125) competition.

[![bounty](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/dillahhhh/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/dillahhhh/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125)

## What's inside

- Thin navy top bar + heavy serif dateline "Wednesday 25 November 2026" with
  an italic dek; story count is computed from the data (**44 stories**:
  11 cards + 33 "also" items) and shown as "44 STORIES · 5 REGIONS"
- Five region chips (Americas, Europe, Middle East & Africa, Asia-Pacific,
  World & Space) with computed per-region counts
- "The Day in Numbers" strip: eight big figures (tariff targets, Cairo dead,
  UK energy cap, Kospi, US inflation, Bangladesh wage, cartel fines, Athens
  marchers)
- Three hero stories with ~100px drawn SVG scenes (US tariffs/ship, Cairo
  tanker fire, Tiangong space dock), number badges, how-sure badges
  (OFFICIAL / CONFIRMED / REPORTED / CLAIM) and source lines
- Eight smaller illustrated cards (refinery, energy cap, Kospi chart, jet,
  flags, garment factory, supermarket siege, controlled blast) in a 4×2 grid
- Bottom band: a small equirectangular map (Natural Earth 110m land) with
  region-coloured numbered pins for stories 1–11, a region legend with counts,
  and a HOW SURE legend; beside it "Also on Wednesday — 33 more stories" in
  two numbered columns
- Red-bordered DATE CHECK box naming earlier news left out, a sources footer,
  and the note that all drawings are original

## Rebuild

Requires Python 3, Google Chrome, and a Natural Earth 110m land GeoJSON
(point `MAP_GEOJSON` at it):

```sh
MAP_GEOJSON=/path/to/ne_110m_land.geojson python3 render.py   # writes page.html + entry.png
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts           # validates + copies to out/entry.png
```

`main.ts` also defaults to writing `/output/entry.png` when
`MAKEFUN_OUTPUT_DIR` is unset. Output is deterministic: same input, same bytes.
