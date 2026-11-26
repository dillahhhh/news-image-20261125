# The World in One Day — news-image-20261125

A 1024×1024 broadsheet-style infographic summing up Wednesday 25 November 2026
world news in a single image, for the
[make.fun](https://make.fun/bounty/news-image-20261125) competition.

[![bounty](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/dillahhhh/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/dillahhhh/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125)

## What's inside

- Masthead: "The World in One Day — Wednesday 25 November 2026" with a
  computed story count (**36 stories**: 3 lead cards + 4 number tiles +
  24 numbered stories + 5 side-box items)
- Three lead stories (A trade/USA, B disaster/Egypt, C space/Pakistan–China)
  with drawn visuals and per-card source lines
- Black numbers strip: UK energy cap, Kospi, US inflation, and a
  "Russian jets hit — CLAIM" tile, each with a grey source tag
- Equirectangular world map (Natural Earth 110m land) with 24 numbered,
  region-coloured story pins plus A/B/C lead pins
- Three side boxes beside the map: Science · Space, Business, Culture · Media
- Four region columns (Americas, Europe, Middle East & Africa, Asia-Pacific)
  with per-region story counts in the headings
- A red-bordered DATE CHECK box naming what was reported on the day, what
  was left out as earlier news, and the REPORTED vs CLAIM legend

## Rebuild

Requires Python 3, Google Chrome, and a Natural Earth 110m land GeoJSON
(point `MAP_GEOJSON` at it):

```sh
MAP_GEOJSON=/path/to/ne_110m_land.geojson python3 render.py   # writes page.html + entry.png
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts           # validates + copies to out/entry.png
```

`main.ts` also defaults to writing `/output/entry.png` when
`MAKEFUN_OUTPUT_DIR` is unset. Output is deterministic: same input, same bytes.
