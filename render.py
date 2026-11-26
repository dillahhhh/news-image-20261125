#!/usr/bin/env python3
"""Render page.html (1024x1024 broadsheet infographic) and screenshot it to
entry.png with headless Chrome. Stdlib only."""

import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_GEOJSON = os.environ.get("MAP_GEOJSON", "/home/ubuntu/mf/render/ne_110m_land.geojson")
PAGE_HTML = os.path.join(HERE, "page.html")
ENTRY_PNG = os.path.join(HERE, "entry.png")

# Equirectangular window for the map
LON_MIN, LON_MAX = -126.0, 166.0
LAT_MIN, LAT_MAX = -42.0, 70.0
MAP_W, MAP_H = 640, 236

REGIONS = [
    ("Americas", "#1f5f8b"),
    ("Europe", "#6b4fa0"),
    ("Middle East & Africa", "#b3261e"),
    ("Asia-Pacific", "#1d7a4c"),
]

# num, region index, lon, lat, place, line
STORIES = [
    (1, 0, -75.55, 10.39, "Colombia", "Cartagena supermarket storm; hostages freed"),
    (2, 0, -117.27, 32.85, "California", "record tides flood LA and La Jolla"),
    (3, 0, -93.62, 41.59, "Iowa", "Army detonates unstable lead azide at plant"),
    (4, 0, -75.70, 45.42, "Canada", "astronaut Kutryk becomes a father on the ISS"),
    (5, 0, -121.95, 37.35, "Nvidia", "Trump accounts traded its shares 44 times"),
    (6, 0, -74.01, 40.71, "New York", "Macy's parade postponed by high winds"),
    (7, 1, 19.04, 47.50, "Hungary", "PM Magyar meets Zelensky to reset ties"),
    (8, 1, 23.73, 37.98, "Greece", "general strike, ~15,000 march in Athens"),
    (9, 1, 13.40, 52.52, "Germany", "record €561bn 2027 budget strains coalition"),
    (10, 1, 6.13, 49.61, "EU court", "must set cage-free farming timeline"),
    (11, 1, 4.35, 50.85, "EU & UK", "fine fragrance cartel over €570m"),
    (12, 1, -3.70, 40.42, "Spain", "Abrego Garcia arrives in Madrid"),
    (13, 2, 34.30, 31.50, "Gaza", "Israeli strike kills Hamas official, family"),
    (14, 2, 45.03, 12.78, "Yemen", "Houthis advance on Aden, residents flee"),
    (15, 2, 44.36, 33.31, "Iraq", "court lets Baghdad take Kurdish borders, oil"),
    (16, 2, 40.75, 36.50, "Syria", "IS suicide bomber kills 2 in Hasakah"),
    (17, 2, -15.43, 28.10, "Canary Is.", "record of nearly 2,000 migrants in one day"),
    (18, 2, 7.48, 6.45, "Nigeria", "$220m of meth seized, 5 Mexicans held"),
    (19, 3, 107.61, -6.92, "Indonesia", "West Java gold mine flood: 9 dead, 17 trapped"),
    (20, 3, 90.41, 23.81, "Bangladesh", "unions reject 17,000-taka garment wage"),
    (21, 3, 159.95, -9.43, "Solomon Is.", "Australia treaty replaces China pact"),
    (22, 3, 104.92, 11.55, "Cambodia", "largest drill with China, ~3,000 troops"),
    (23, 3, 125.75, 39.03, "North Korea", "expels Swiss diplomat in sanctions row"),
    (24, 3, 151.21, -33.87, "Australia", "Sydney ex-policeman guilty of double murder"),
]

# Square lead-story pins: letter, lon, lat
LEAD_PINS = [("A", -77.04, 38.90), ("B", 31.24, 30.04), ("C", 100.10, 41.00)]

# Side boxes beside the map: title + list of items (each counts as a story)
SIDE_BOXES = [
    ("Science &middot; Space", [
        "Hera images show a stadium-sized crater on asteroid Dimorphos, made by NASA's DART probe in 2022. (BBC)",
    ]),
    ("Business", [
        "UK discount chain Poundland collapses into administration.",
        "Bank of England: UK food inflation could hit 5% next year. (BBC, Guardian)",
    ]),
    ("Culture &middot; Media", [
        "Duran Duran guitarist Andy Taylor dies at 65.",
        "Palestinian journalist killed in Gaza wins the Rory Peck prize. (BBC, DW, Guardian)",
    ]),
]

# Every item drawn on the page: 3 lead cards + 4 number tiles + numbered
# stories + each side-box item.
STORY_COUNT = 3 + 4 + len(STORIES) + sum(len(items) for _, items in SIDE_BOXES)


def project(lon, lat):
    x = (lon - LON_MIN) / (LON_MAX - LON_MIN) * MAP_W
    y = (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * MAP_H
    return x, y


def in_window(lon, lat):
    return LON_MIN - 0.5 <= lon <= LON_MAX + 0.5 and LAT_MIN - 0.5 <= lat <= LAT_MAX + 0.5


def ring_to_path(ring):
    """Convert one GeoJSON ring to SVG subpaths, dropping out-of-window runs."""
    parts = []
    run = []
    n = len(ring)
    for i in range(n):
        lon, lat = ring[i][0], ring[i][1]
        if in_window(lon, lat):
            x, y = project(lon, lat)
            run.append((x, y))
        else:
            if len(run) >= 2:
                d = "M" + "L".join(f"{p[0]:.1f},{p[1]:.1f}" for p in run) + "Z"
                parts.append(d)
            run = []
    if len(run) >= 2:
        parts.append("M" + "L".join(f"{p[0]:.1f},{p[1]:.1f}" for p in run) + "Z")
    return "".join(parts)


def geojson_to_svg_path(geojson_path):
    with open(geojson_path) as f:
        data = json.load(f)
    d_parts = []
    for feat in data["features"]:
        geom = feat["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            for ring in poly:
                d_parts.append(ring_to_path(ring))
    return "".join(d_parts)


def pin_positions():
    """Project story + lead pins, then nudge numbered pins apart."""
    numbered = []
    for num, reg, lon, lat, place, line in STORIES:
        x, y = project(lon, lat)
        numbered.append({"num": num, "reg": reg, "x": x, "y": y, "fixed": False})
    letters = []
    for letter, lon, lat in LEAD_PINS:
        x, y = project(lon, lat)
        letters.append({"letter": letter, "x": x, "y": y, "fixed": True})
    pins = numbered + letters
    min_dist = 23.0
    for _ in range(300):
        moved = False
        for i in range(len(pins)):
            for j in range(i + 1, len(pins)):
                dx = pins[j]["x"] - pins[i]["x"]
                dy = pins[j]["y"] - pins[i]["y"]
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < min_dist and dist > 1e-6:
                    push = (min_dist - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    for p, s in ((pins[i], -1), (pins[j], 1)):
                        if p["fixed"]:
                            continue
                        p["x"] += ux * push * s
                        p["y"] += uy * push * s
                        p["x"] = min(max(p["x"], 12), MAP_W - 12)
                        p["y"] = min(max(p["y"], 12), MAP_H - 12)
                        moved = True
        if not moved:
            break
    return numbered, letters


def svg_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_map_svg(land_d, numbered, letters):
    out = [f'<svg class="map" viewBox="0 0 {MAP_W} {MAP_H}" width="{MAP_W}" height="{MAP_H}" '
           f'xmlns="http://www.w3.org/2000/svg">']
    out.append(f'<rect width="{MAP_W}" height="{MAP_H}" fill="#dfe8ee"/>')
    out.append(f'<path d="{land_d}" fill="#cbbfa6" fill-rule="evenodd" stroke="#b3a68c" stroke-width="0.4"/>')
    for p in letters:
        out.append(
            f'<rect x="{p["x"]-9.5:.1f}" y="{p["y"]-9.5:.1f}" width="19" height="19" rx="2" '
            f'fill="#151515" stroke="#f6f1e7" stroke-width="1.2"/>'
            f'<text x="{p["x"]:.1f}" y="{p["y"]+3.6:.1f}" text-anchor="middle" '
            f'font-family="Liberation Serif" font-weight="bold" font-size="11" fill="#f2c230">{p["letter"]}</text>'
        )
    for p in numbered:
        color = REGIONS[p["reg"]][1]
        out.append(
            f'<circle cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="9.5" fill="{color}" '
            f'stroke="#f6f1e7" stroke-width="1.4"/>'
            f'<text x="{p["x"]:.1f}" y="{p["y"]+3.4:.1f}" text-anchor="middle" '
            f'font-family="Liberation Sans" font-weight="bold" font-size="10.5" fill="#ffffff">{p["num"]}</text>'
        )
    out.append("</svg>")
    return "".join(out)


def build_cards():
    # Solar wing helper for the Tiangong silhouette: panel + grid lines
    def wing(x, y, w, h):
        lines = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1" fill="#151515"/>']
        gx = x + 11
        while gx < x + w - 2:
            lines.append(f'<line x1="{gx:.0f}" y1="{y+1}" x2="{gx:.0f}" y2="{y+h-1}" stroke="#5c5c5c" stroke-width="0.6"/>')
            gx += 11
        return "".join(lines)

    station_svg = f"""
      <svg width="284" height="66" viewBox="0 0 284 66" xmlns="http://www.w3.org/2000/svg">
        {wing(6, 6, 92, 13)}{wing(186, 6, 92, 13)}
        {wing(6, 47, 92, 13)}{wing(186, 47, 92, 13)}
        <line x1="98" y1="12" x2="112" y2="27" stroke="#151515" stroke-width="2"/>
        <line x1="98" y1="53" x2="112" y2="38" stroke="#151515" stroke-width="2"/>
        <line x1="186" y1="12" x2="172" y2="27" stroke="#151515" stroke-width="2"/>
        <line x1="186" y1="53" x2="172" y2="38" stroke="#151515" stroke-width="2"/>
        <rect x="106" y="26" width="20" height="16" rx="2" fill="#151515"/>
        <rect x="128" y="24" width="30" height="20" rx="2" fill="#151515"/>
        <rect x="160" y="26" width="20" height="16" rx="2" fill="#151515"/>
        <rect x="136" y="47" width="14" height="6" rx="2" fill="#151515"/>
        <circle cx="128" cy="34" r="3" fill="#f6f1e7"/>
      </svg>
      <div class="station-cap">Shenzhou-24 &rarr; Tiangong &middot; 25 Nov</div>"""

    cards = []
    # --- Card A: Trade ---
    cards.append(f"""
    <div class="card">
      <div class="kicker"><span class="chip">A</span><span class="ktag">TRADE &middot; USA</span></div>
      <div class="headline">US proposes new tariffs on 14 economies</div>
      <div class="summary">China and the EU are targets; added 20% lifts duties on Chinese goods to ~40%.</div>
      <div class="card-src">USTR, Guardian, BBC</div>
      <div class="visual">
        <div class="bar-row"><span class="bar-label">China tariff now</span><span class="bar-track"><span class="bar grey" style="width:44%"></span></span><span class="bar-val">~20%</span></div>
        <div class="bar-row"><span class="bar-label">With proposal</span><span class="bar-track"><span class="bar red" style="width:88%"></span></span><span class="bar-val">~40%</span></div>
      </div>
    </div>""")
    # --- Card B: Disaster ---
    cards.append(f"""
    <div class="card">
      <div class="kicker"><span class="chip">B</span><span class="ktag">DISASTER &middot; EGYPT</span></div>
      <div class="headline">Fuel tanker blast kills 31 near Cairo</div>
      <div class="summary">An overturned tanker caught fire on the busy Ring Road in Giza; 21 injured and the toll may rise.</div>
      <div class="card-src">AP, Guardian, BBC</div>
      <div class="visual death">
        <div class="death-num"><span class="big-dead">31</span><span class="dead-word">dead</span></div>
        <div class="dead-sub">21 injured &middot; Ring Road, Giza</div>
      </div>
    </div>""")
    # --- Card C: Space ---
    cards.append(f"""
    <div class="card">
      <div class="kicker"><span class="chip">C</span><span class="ktag">SPACE &middot; PAKISTAN / CHINA</span></div>
      <div class="headline">First Pakistani astronaut in orbit</div>
      <div class="summary">Muhammad Zeeshan Ali flew on Shenzhou-24, the first foreigner aboard China's Tiangong station.</div>
      <div class="card-src">BBC</div>
      <div class="visual station">{station_svg}</div>
    </div>""")
    return "".join(cards)


def build_strip():
    tiles = [
        ("+26%", "UK energy cap", "£1,723 &rarr; £2,166 from January", "Ofgem"),
        ("&minus;6%", "Kospi", "falls over 6%; Samsung/SK Hynix lead", "Yonhap"),
        ("3.8%", "US inflation", "highest since May", "BLS"),
        ("5", "Russian jets hit &mdash; CLAIM", "Ukraine says, at Savasleyka airfield", ""),
    ]
    out = []
    for fig, label, detail, src in tiles:
        src_html = f' <span class="t-src">&middot; {src}</span>' if src else ""
        out.append(f'<div class="tile"><div class="t-fig">{fig}</div>'
                   f'<div class="t-label">{label}</div>'
                   f'<div class="t-detail">{detail}{src_html}</div></div>')
    return "".join(out)


def build_columns():
    cols = []
    for ri, (rname, rcolor) in enumerate(REGIONS):
        items = [s for s in STORIES if s[1] == ri]
        rows = []
        for num, reg, lon, lat, place, line in items:
            rows.append(
                f'<div class="item"><span class="dot" style="background:{rcolor}">{num}</span>'
                f'<div class="item-txt"><span class="place">{svg_escape(place)}</span>'
                f'<span class="iline">{svg_escape(line)}</span></div></div>'
            )
        cols.append(
            f'<div class="col"><div class="col-head" style="color:{rcolor}">{rname}'
            f'<span class="cc"> &middot; {len(items)}</span></div>'
            f'{"".join(rows)}</div>'
        )
    return "".join(cols)


CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1024px; height:1024px; overflow:hidden; }
body { background:#f6f1e7; color:#151515;
       font-family:"Liberation Sans", Arial, sans-serif; }
#page { width:1024px; height:1024px; position:relative; }
.masthead { position:absolute; left:24px; right:24px; top:22px; }
.brand { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
         font-size:54px; line-height:1.05; letter-spacing:0.5px; }
.date-line { font-weight:bold; font-size:25px; color:#b3261e; margin-top:6px;
             letter-spacing:1.5px; }
.mast-right { position:absolute; right:0; top:8px; text-align:right; }
.stories-num { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
               font-size:44px; line-height:1; }
.stories-sub { font-size:12.5px; color:#5a5a5a; margin-top:6px; }
.rule-double { border-top:3px solid #151515; border-bottom:1px solid #151515;
               height:5px; margin-top:14px; }
.cards { position:absolute; left:24px; right:24px; top:136px; display:flex; gap:16px; }
.card { flex:1; background:#fff; border:1px solid #cfc8b8; border-top:5px solid #151515;
        padding:8px 14px 7px; position:relative;
        display:flex; flex-direction:column; }
.kicker { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
.chip { display:inline-block; background:#151515; color:#f2c230;
        font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
        font-size:15px; width:22px; height:22px; line-height:22px; text-align:center; }
.ktag { font-size:10.5px; font-weight:bold; letter-spacing:1.2px; color:#555; }
.headline { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
            font-size:26px; line-height:1.15; margin-bottom:4px; }
.summary { font-size:12px; line-height:1.45; color:#333; margin-bottom:3px; }
.card-src { font-size:10.5px; color:#999; text-align:right; margin-bottom:1px; }
.visual { border-top:1px solid #e4ddcb; padding-top:4px; margin-top:auto;
          min-height:64px; }
.bar-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.bar-label { font-size:12.5px; color:#333; width:102px; }
.bar-track { flex:1; height:15px; background:#efe9da; position:relative; }
.bar { position:absolute; left:0; top:0; height:15px; display:block; }
.bar.grey { background:#9a917e; }
.bar.red { background:#b3261e; }
.bar-val { font-size:13.5px; font-weight:bold; width:44px; text-align:right; }
.visual.death .death-num { display:flex; align-items:baseline; gap:10px; }
.big-dead { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
            font-size:64px; color:#b3261e; line-height:1; }
.dead-word { font-weight:bold; font-size:15px; }
.dead-sub { font-size:11px; color:#555; margin-top:3px; }
.visual.station { display:flex; flex-direction:column; align-items:center;
                  justify-content:flex-end; padding-top:4px; }
.station-cap { font-size:9.5px; color:#6a6a6a; margin-top:3px; letter-spacing:0.4px; }
.strip { position:absolute; left:24px; right:24px; top:389px; display:flex; gap:6px; }
.tile { flex:1; background:#151515; padding:8px 10px 8px; }
.t-fig { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
         font-size:27px; color:#f2c230; line-height:1.05; }
.t-label { font-size:11.5px; font-weight:bold; color:#fff; margin-top:3px; }
.t-detail { font-size:10px; color:#9a9a9a; margin-top:2px; }
.t-src { color:#7a7a7a; }
.mid { position:absolute; left:24px; top:466px; }
.map-wrap { position:relative; width:640px; height:236px; }
.map-cap { font-size:10.5px; color:#6a6a6a; margin-top:3px; letter-spacing:0.3px; }
.side { position:absolute; left:676px; top:466px; width:324px; }
.box { background:#fff; border:1px solid #cfc8b8; padding:6px 11px 7px; margin-bottom:5px; }
.box h3 { font-family:"Liberation Serif", Georgia, serif; font-size:15px; font-weight:bold;
          margin-bottom:3px; }
.box p { font-size:11.5px; line-height:1.4; color:#333; margin-bottom:2px; }
.box p:last-child { margin-bottom:0; }
.cols { position:absolute; left:24px; right:24px; top:724px; display:flex; gap:14px; }
.col { flex:1; }
.col-head { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
            font-size:14px; padding-bottom:3px; border-bottom:2px solid #151515;
            margin-bottom:1px; }
.cc { font-weight:normal; opacity:0.65; }
.item { display:flex; gap:7px; padding:2.5px 0; border-bottom:1px solid #ddd5c2; }
.dot { flex:0 0 16px; height:16px; border-radius:50%; color:#fff;
       font-size:9px; font-weight:bold; display:flex; align-items:center;
       justify-content:center; margin-top:1px; }
.item-txt { display:flex; flex-direction:column; }
.place { font-size:10.5px; font-weight:bold; line-height:1.25; }
.iline { font-size:10px; color:#4a4a4a; line-height:1.3; }
.foot { position:absolute; left:24px; right:24px; top:948px;
        border:1px solid #b3261e; background:#fff; padding:6px 12px 5px; }
.dc-title { font-size:10px; font-weight:bold; color:#b3261e; letter-spacing:2px;
            margin-bottom:3px; }
.dc-body { font-size:10.5px; line-height:1.45; color:#333; }
.dc-line { display:flex; justify-content:space-between; gap:10px;
           font-size:9.5px; color:#8a8a8a; margin-top:4px; line-height:1.3; }
"""


def build_side_boxes():
    out = []
    for title, items in SIDE_BOXES:
        text = " ".join(svg_escape(i) for i in items)
        out.append(f'<div class="box"><h3>{title}</h3><p>{text}</p></div>')
    return "".join(out)


def build_html(land_d, numbered, letters):
    map_svg = build_map_svg(land_d, numbered, letters)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div id="page">
  <div class="masthead">
    <div class="mast-right">
      <div class="stories-num">{STORY_COUNT} stories</div>
      <div class="stories-sub">4 regions &middot; all reported Wed 25 Nov 2026</div>
    </div>
    <div class="brand">The World in One Day</div>
    <div class="date-line">WEDNESDAY 25 NOVEMBER 2026</div>
    <div class="rule-double"></div>
  </div>
  <div class="cards">{build_cards()}</div>
  <div class="strip">{build_strip()}</div>
  <div class="mid">
    <div class="map-wrap">{map_svg}</div>
    <div class="map-cap">&#9632; A&ndash;C lead stories &nbsp;&middot;&nbsp; &#9679; numbered stories below</div>
  </div>
  <div class="side">{build_side_boxes()}</div>
  <div class="cols">{build_columns()}</div>
  <div class="foot">
    <div class="dc-title">DATE CHECK</div>
    <div class="dc-body">Every item was reported on Wednesday 25 November 2026 (UTC). Left out as earlier news:
      Nvidia reinstates Jensen Huang (Tue 24) &middot; Ukraine naval drones hit Russian ships off Libya (Mon 23).</div>
    <div class="dc-line"><span>REPORTED = press report &middot; CLAIM = one side&rsquo;s account &middot; drawings are original</span>
      <span>Sources: AP, Reuters, AFP, BBC, Guardian, DW, Al Jazeera, Yonhap, NPR</span></div>
  </div>
</div></body></html>"""


def png_size(path):
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG")
        f.read(4)
        chunk = f.read(4)
        if chunk != b"IHDR":
            raise ValueError("missing IHDR")
        w, h = struct.unpack(">II", f.read(8))
    return w, h


def main():
    land_d = geojson_to_svg_path(MAP_GEOJSON)
    numbered, letters = pin_positions()
    html = build_html(land_d, numbered, letters)
    with open(PAGE_HTML, "w") as f:
        f.write(html)
    url = "file://" + PAGE_HTML
    subprocess.run(
        ["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", "--window-size=1024,1024",
         f"--screenshot={ENTRY_PNG}", url],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    size = os.path.getsize(ENTRY_PNG)
    w, h = png_size(ENTRY_PNG)
    print(f"entry.png: {w}x{h}, {size} bytes")
    if size > 1024 * 1024:
        print("ERROR: exceeds 1 MiB", file=sys.stderr)
        sys.exit(1)
    if (w, h) != (1024, 1024):
        print("ERROR: bad dimensions", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
