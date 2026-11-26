#!/usr/bin/env python3
"""Render page.html (1024x1024 illustrated news page) and screenshot it to
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

INK = "#151515"
CREAM = "#f6f1e7"
RED = "#b3261e"
PAPER = "#fbf8f1"

# Equirectangular window for the map
LON_MIN, LON_MAX = -126.0, 166.0
LAT_MIN, LAT_MAX = -42.0, 70.0
MAP_W, MAP_H = 312, 182

REGIONS = [
    ("AMERICAS", "Americas", "#1f5f8b"),
    ("EUROPE", "Europe", "#6b4fa0"),
    ("MEA", "Middle East & Africa", "#b3261e"),
    ("APAC", "Asia-Pacific", "#1d7a4c"),
    ("WORLD", "World & Space", "#8a6508"),
]

SURES = ["OFFICIAL", "CONFIRMED", "REPORTED", "CLAIM"]

# num, region idx, lon, lat, place, topic, sure, headline, detail, sources, scene
CARDS = [
    dict(n=1, r=0, lon=-77.04, lat=38.90, place="WASHINGTON", topic="TRADE",
         sure="CONFIRMED", scene="ship",
         head="US proposes tariffs on 14 economies",
         det="An added 20% on Chinese goods would lift duties to ~40%; China and the EU are among the 14 targets.",
         src="Guardian \u00b7 BBC"),
    dict(n=2, r=2, lon=31.24, lat=30.04, place="CAIRO", topic="DISASTER",
         sure="CONFIRMED", scene="cairo",
         head="Fuel tanker fire kills 31 on Cairo highway",
         det="The tanker overturned on the Ring Road and caught fire; 21 injured.",
         src="AP \u00b7 BBC \u00b7 Guardian \u00b7 DW"),
    dict(n=3, r=4, lon=100.10, lat=41.00, place="TIANGONG", topic="SPACE",
         sure="CONFIRMED", scene="space",
         head="First Pakistani astronaut reaches China's station",
         det="Muhammad Zeeshan Ali flew on Shenzhou-24 and became the first foreigner aboard Tiangong.",
         src="BBC \u00b7 Guardian"),
    dict(n=4, r=2, lon=50.17, lat=26.65, place="SAUDI ARABIA", topic="",
         sure="REPORTED", scene="refinery",
         head="Houthis hit Saudi Arabia's largest refinery",
         det="Attack damages Ras Tanura plant in the Eastern Province.",
         src="NBC News"),
    dict(n=5, r=1, lon=-0.13, lat=51.51, place="LONDON", topic="ENERGY",
         sure="OFFICIAL", scene="house",
         head="UK energy cap to jump 26% in January",
         det="Typical bill \u00a31,723 \u2192 \u00a32,166 a year.",
         src="Ofgem \u00b7 BBC"),
    dict(n=6, r=3, lon=126.98, lat=37.57, place="SEOUL", topic="MARKETS",
         sure="CONFIRMED", scene="chart",
         head="Kospi falls over 6% on AI fears",
         det="Samsung and SK Hynix lead the slide.",
         src="Yonhap \u00b7 BBC"),
    dict(n=7, r=1, lon=36.45, lat=49.95, place="RUSSIA", topic="WAR",
         sure="CLAIM", scene="jet",
         head="Ukraine says five Russian jets hit",
         det="Airbase for hypersonic jets; Russia has not confirmed.",
         src="BBC"),
    dict(n=8, r=3, lon=159.95, lat=-9.43, place="HONIARA", topic="",
         sure="CONFIRMED", scene="flags",
         head="Solomon Islands picks Australia as security partner",
         det="Treaty replaces its 2022 pact with China.",
         src="BBC \u00b7 NBC News"),
    dict(n=9, r=3, lon=90.41, lat=23.81, place="DHAKA", topic="LABOUR",
         sure="REPORTED", scene="factory",
         head="Garment wage set at 17,000 taka, unions refuse",
         det="Up from 12,500; at least 140 factories shut.",
         src="AFP \u00b7 Daily Star"),
    dict(n=10, r=0, lon=-75.55, lat=10.39, place="CARTAGENA", topic="",
         sure="REPORTED", scene="store",
         head="All hostages freed as police storm supermarket",
         det="Daylong siege in Colombian tourist city ends.",
         src="Guardian"),
    dict(n=11, r=0, lon=-90.98, lat=41.48, place="IOWA", topic="ARMY",
         sure="CONFIRMED", scene="blast",
         head="Army detonates 5 tons of lead azide",
         det="Degrading explosive at Middletown plant; area evacuated.",
         src="AFP \u00b7 CNN \u00b7 DW"),
]

# "Also on Wednesday" items: (region idx, place, fact incl. sources)
ALSO = [
    (0, "US", "inflation 3.8%, highest since May (Guardian)"),
    (0, "Wall St", "Nasdaq down almost 4% on AI fears (BBC)"),
    (0, "US", "Trump accounts traded Nvidia shares 44 times (BBC)"),
    (0, "California", "record tides flood LA, La Jolla (Guardian)"),
    (0, "New York", "Macy's parade postponed by winds (Guardian)"),
    (0, "US", "judge blocks FCC action on ABC (Guardian \u00b7 DW)"),
    (0, "Madrid", "Abrego Garcia arrives after leaving US (AFP \u00b7 RFI)"),
    (1, "Hungary", "PM Magyar meets Zelensky to reset ties (DW)"),
    (1, "Athens", "general strike, ~15,000 march (DW)"),
    (1, "Germany", "\u20ac561bn 2027 budget strains coalition (DW)"),
    (1, "Germany", "domestic violence at record high (DW)"),
    (1, "EU court", "sets cage-free farming timeline (DW)"),
    (1, "EU & UK", "\u20ac570m fine for fragrance cartel (AFP)"),
    (1, "Canary Is.", "record of nearly 2,000 migrants in a day (DW)"),
    (1, "UK", "Poundland collapses into administration (BBC)"),
    (1, "UK", "BoE says food inflation could hit 5% (Guardian)"),
    (2, "Gaza", "strike kills Hamas official and family (Al Jazeera)"),
    (2, "Yemen", "Houthis advance on Aden; residents flee (Guardian)"),
    (2, "Iraq", "court lets Baghdad oversee Kurdish oil (AFP)"),
    (2, "Syria", "IS suicide bomber kills 2 in Hasakah (AA)"),
    (2, "Nigeria", "$220m of meth seized, 5 held (DW)"),
    (2, "Cameroon", "elephants kill Swiss tourist (Guardian)"),
    (3, "Indonesia", "West Java mine flood: 9 dead, 17 trapped"),
    (3, "Cambodia", "largest drill with China, ~3,000 troops (France 24)"),
    (3, "Bangladesh", "108 border-guard platoons deployed (Daily Star)"),
    (3, "North Korea", "Swiss diplomat expelled in sanctions row (BBC)"),
    (3, "Sydney", "ex-policeman guilty of double murder (BBC)"),
    (3, "India", "food inflation broadens (BBC)"),
    (4, "Space", "Hera images show Dimorphos crater (BBC)"),
    (4, "ISS", "Kutryk becomes a father in orbit (BBC)"),
    (4, "Music", "Andy Taylor of Duran Duran dies at 65 (DW)"),
    (4, "Press", "Gaza journalist wins Rory Peck prize (Guardian)"),
    (4, "Film", "Pitt and Jolie settle winery battle (Guardian)"),
]

NUMBERS = [
    ("14", "economies in US tariff plan"),
    ("31", "killed in Cairo tanker fire"),
    ("+26%", "UK energy cap from Jan"),
    ("\u22126%", "Kospi, Seoul"),
    ("3.8%", "US inflation, Oct"),
    ("17,000 taka", "Bangladesh garment wage"),
    ("\u20ac570m", "EU-UK fragrance cartel fines"),
    ("15,000", "marchers in Athens strike"),
]

STORY_COUNT = len(CARDS) + len(ALSO)
REGION_COUNTS = [0] * len(REGIONS)
for c in CARDS:
    REGION_COUNTS[c["r"]] += 1
for r, _, _ in ALSO:
    REGION_COUNTS[r] += 1


def project(lon, lat, w=MAP_W, h=MAP_H):
    x = (lon - LON_MIN) / (LON_MAX - LON_MIN) * w
    y = (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * h
    return x, y


def in_window(lon, lat):
    return LON_MIN - 0.5 <= lon <= LON_MAX + 0.5 and LAT_MIN - 0.5 <= lat <= LAT_MAX + 0.5


def ring_to_path(ring, w=MAP_W, h=MAP_H):
    parts = []
    run = []
    for lon, lat, *_ in ring:
        if in_window(lon, lat):
            run.append(project(lon, lat, w, h))
        else:
            if len(run) >= 2:
                parts.append("M" + "L".join(f"{p[0]:.1f},{p[1]:.1f}" for p in run) + "Z")
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
    pins = []
    for c in CARDS:
        x, y = project(c["lon"], c["lat"])
        pins.append({"n": c["n"], "r": c["r"],
                     "x": min(max(x, 10), MAP_W - 10),
                     "y": min(max(y, 10), MAP_H - 10)})
    min_dist = 20.0
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
                        p["x"] = min(max(p["x"] + ux * push * s, 10), MAP_W - 10)
                        p["y"] = min(max(p["y"] + uy * push * s, 10), MAP_H - 10)
                        moved = True
        if not moved:
            break
    return pins


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------- SVG scenes ----------------

def scene_ship():
    # sky 0-102, sea 104-140; hull+containers sit on the waterline ~100
    out = ['<svg viewBox="0 0 318 140" width="318" height="140" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">',
           '<rect width="318" height="140" fill="#d8e6f0"/>']
    # tag in clear sky, top-left
    out.append('<rect x="10" y="8" width="132" height="20" rx="3" fill="#151515"/>')
    out.append('<text x="18" y="22" font-family="Liberation Sans" font-size="10" font-weight="bold" fill="#f6f1e7" letter-spacing="1">NEW US TARIFF PLAN</text>')
    # containers: two rows stacked on deck; labels painted inside containers
    row1 = [(44, 62, "#b3261e", "CHINA +20%"), (112, 40, "#1f5f8b", "EU"),
            (158, 30, "#1d7a4c", ""), (192, 30, "#8a6508", ""), (226, 30, "#6b4fa0", ""),
            (260, 30, "#b3261e", "")]
    row2 = [(44, 34, "#1f5f8b", ""), (82, 34, "#8a4a2a", ""), (120, 34, "#5a6e4a", ""),
            (158, 34, "#b3261e", ""), (196, 34, "#1d7a4c", ""), (234, 34, "#8a6508", ""),
            (272, 18, "#6b4fa0", "")]
    for x, w, col, lab in row1:
        out.append(f'<rect x="{x}" y="56" width="{w}" height="18" fill="{col}"/>')
        out.append(f'<rect x="{x}" y="56" width="{w}" height="3" fill="#ffffff" opacity="0.18"/>')
        if lab:
            out.append(f'<text x="{x+4}" y="69" font-family="Liberation Sans" font-size="8.5" font-weight="bold" fill="#f6f1e7">{lab}</text>')
    for x, w, col, lab in row2:
        out.append(f'<rect x="{x}" y="76" width="{w}" height="18" fill="{col}"/>')
        out.append(f'<rect x="{x}" y="76" width="{w}" height="3" fill="#ffffff" opacity="0.18"/>')
        if lab:
            out.append(f'<text x="{x+4}" y="89" font-family="Liberation Sans" font-size="8.5" font-weight="bold" fill="#f6f1e7">{lab}</text>')
    # deck + hull
    out.append('<rect x="26" y="94" width="268" height="6" fill="#22303c"/>')
    out.append('<path d="M26 100 L290 100 L276 124 L40 124 Z" fill="#2e3a46"/>')
    out.append('<path d="M290 100 L276 124 L266 124 L282 102 Z" fill="#22303c"/>')
    # sea + wake
    out.append('<rect y="124" width="318" height="16" fill="#7fa8c4"/>')
    out.append('<path d="M44 128 q60 7 120 5 q70 -3 110 -5" stroke="#d8e6f0" stroke-width="3" fill="none" opacity="0.8"/>')
    out.append('<path d="M60 133 q80 6 160 4" stroke="#d8e6f0" stroke-width="2" fill="none" opacity="0.5"/>')
    out.append('</svg>')
    return "".join(out)


def scene_cairo():
    out = ['<svg viewBox="0 0 318 140" width="318" height="140" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">',
           '<rect width="318" height="140" fill="#54406b"/>',
           '<rect y="70" width="318" height="22" fill="#c96f4a"/>',
           '<rect y="90" width="318" height="50" fill="#2e2a33"/>',
           # highway deck
           '<rect x="0" y="96" width="318" height="10" fill="#4a4550"/>',
           '<rect x="0" y="94" width="318" height="2" fill="#6a6474"/>',
           '<rect x="40" y="106" width="10" height="34" fill="#3a3540"/>',
           '<rect x="268" y="106" width="10" height="34" fill="#3a3540"/>',
           # overturned tanker: tank + cab, rotated
           '<g transform="rotate(-14 160 92)">',
           '<rect x="96" y="82" width="120" height="18" rx="4" fill="#c8c2b8"/>',
           '<rect x="96" y="82" width="120" height="6" rx="3" fill="#a89f92"/>',
           '<rect x="216" y="84" width="34" height="14" rx="3" fill="#b3261e"/>',
           '<rect x="222" y="86" width="10" height="6" fill="#7a1d18"/>',
           '<circle cx="106" cy="104" r="8" fill="#1c1a20"/>',
           '<circle cx="202" cy="104" r="8" fill="#1c1a20"/>',
           '</g>',
           # flames
           '<path d="M140 78 q-6 -14 4 -22 q2 10 8 12 q10 -8 8 -20 q16 12 8 30 q-8 10 -20 10 q-8 0 -8 -10 Z" fill="#e8762a"/>',
           '<path d="M150 80 q-3 -8 3 -13 q4 6 8 8 q6 -5 5 -13 q10 8 5 19 q-5 7 -12 7 q-5 0 -9 -8 Z" fill="#f2b53a"/>',
           # smoke
           '<circle cx="150" cy="34" r="14" fill="#241f2b" opacity="0.8"/>',
           '<circle cx="168" cy="22" r="18" fill="#241f2b" opacity="0.7"/>',
           '<circle cx="188" cy="10" r="20" fill="#241f2b" opacity="0.6"/>']
    out.append('<rect x="10" y="10" width="150" height="20" rx="3" fill="#151515"/>')
    out.append('<text x="18" y="24" font-family="Liberation Sans" font-size="10" font-weight="bold" fill="#f6f1e7" letter-spacing="1">31 DEAD \u00b7 21 INJURED</text>')
    out.append('<rect x="196" y="14" width="62" height="16" rx="2" fill="#f6f1e7" opacity="0.92"/>')
    out.append('<text x="202" y="26" font-family="Liberation Sans" font-size="9" fill="#151515">RING ROAD</text>')
    out.append('</svg>')
    return "".join(out)


def scene_space():
    out = ['<svg viewBox="0 0 318 140" width="318" height="140" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">',
           '<rect width="318" height="140" fill="#0d1b2e"/>']
    # stars (kept clear of the top-left tag zone)
    for x, y in [(20,44),(52,18),(96,20),(150,14),(230,16),(280,30),(310,60),
                 (60,70),(120,96),(300,100),(40,120),(200,120),(260,130),(160,36)]:
        out.append(f'<circle cx="{x}" cy="{y}" r="1.3" fill="#cfd8e3"/>')
    # tag top-left, clear of everything
    out.append('<rect x="8" y="8" width="100" height="18" rx="3" fill="#f6f1e7"/>')
    out.append('<text x="14" y="21" font-family="Liberation Sans" font-size="10" font-weight="bold" fill="#151515" letter-spacing="1">SHENZHOU-24</text>')
    # earth limb
    out.append('<circle cx="170" cy="295" r="185" fill="#1f4e79"/>')
    out.append('<circle cx="170" cy="295" r="185" fill="none" stroke="#3f74a3" stroke-width="3"/>')
    out.append('<path d="M20 126 q70 -12 150 -6 q80 6 148 -4" stroke="#7fb3d5" stroke-width="2" fill="none" opacity="0.5"/>')
    # solar wings: two panels each side of the core
    def wing(x, y, w, h):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1" fill="#1a2c44" stroke="#4a6a8a" stroke-width="0.8"/>'
        gx = x + 9
        while gx < x + w - 2:
            s += f'<line x1="{gx:.0f}" y1="{y+1}" x2="{gx:.0f}" y2="{y+h-1}" stroke="#3a5878" stroke-width="0.5"/>'
            gx += 9
        return s
    out.append(wing(104, 50, 62, 15) + wing(104, 86, 62, 15))
    out.append(wing(244, 50, 62, 15) + wing(244, 86, 62, 15))
    # struts
    out.append('<line x1="166" y1="57" x2="176" y2="64" stroke="#8fa8c0" stroke-width="1.5"/>')
    out.append('<line x1="166" y1="93" x2="176" y2="86" stroke="#8fa8c0" stroke-width="1.5"/>')
    out.append('<line x1="232" y1="57" x2="222" y2="64" stroke="#8fa8c0" stroke-width="1.5"/>')
    out.append('<line x1="232" y1="93" x2="222" y2="86" stroke="#8fa8c0" stroke-width="1.5"/>')
    # modules (core)
    out.append('<rect x="176" y="60" width="18" height="26" rx="2" fill="#cfd8e3"/>')
    out.append('<rect x="194" y="56" width="28" height="34" rx="2" fill="#e8eef4"/>')
    out.append('<rect x="222" y="60" width="18" height="26" rx="2" fill="#cfd8e3"/>')
    out.append('<circle cx="208" cy="70" r="4" fill="#1a2c44"/>')
    # docking port + approaching capsule, lower right
    out.append('<rect x="212" y="90" width="10" height="8" rx="2" fill="#8fa8c0"/>')
    out.append('<line x1="226" y1="92" x2="252" y2="96" stroke="#8fa8c0" stroke-width="1" stroke-dasharray="3 3"/>')
    out.append('<line x1="226" y1="97" x2="252" y2="100" stroke="#8fa8c0" stroke-width="1" stroke-dasharray="3 3"/>')
    out.append('<rect x="254" y="90" width="18" height="13" rx="3" fill="#f6f1e7"/>')
    out.append('<circle cx="266" cy="96" r="4" fill="#e8762a"/>')
    # Pakistan + China flags on booms beside the capsule
    out.append('<line x1="200" y1="60" x2="186" y2="40" stroke="#8fa8c0" stroke-width="1"/>')
    out.append('<rect x="176" y="36" width="11" height="8" fill="#1d7a4c"/><rect x="176" y="38.7" width="11" height="2.6" fill="#f6f1e7"/><path d="M181 38.5 a1.8 1.8 0 1 0 0.1 0 M182.2 38.2 l-0.5 0.5 M182.2 39.8 l-0.5 -0.5" stroke="#f6f1e7" stroke-width="0.5" fill="none"/>')
    out.append('<line x1="216" y1="60" x2="232" y2="40" stroke="#8fa8c0" stroke-width="1"/>')
    out.append('<rect x="230" y="36" width="11" height="8" fill="#b3261e"/>')
    for sx in (232.5, 235.5):
        for sy in (38, 40.5):
            out.append(f'<circle cx="{sx}" cy="{sy}" r="0.6" fill="#f2c230"/>')
    out.append('</svg>')
    return "".join(out)


# small-card icons, viewBox 0 0 64 56
def icon_refinery():
    return ('<svg viewBox="0 0 64 56" width="64" height="56" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="8" y="34" width="10" height="20" fill="#3a3a3a"/><rect x="8" y="30" width="10" height="5" fill="#555"/>'
            '<rect x="27" y="26" width="10" height="28" fill="#4a4a4a"/><rect x="27" y="22" width="10" height="5" fill="#666"/>'
            '<rect x="46" y="38" width="10" height="16" fill="#3a3a3a"/><rect x="46" y="34" width="10" height="5" fill="#555"/>'
            '<rect x="30" y="8" width="4" height="14" fill="#3a3a3a"/><rect x="44" y="12" width="4" height="10" fill="#3a3a3a"/>'
            '<path d="M32 22 q-3 -8 2 -13 q1 6 5 7 q6 -5 4 -13 q10 8 4 20 q-5 7 -11 7 q-4 0 -4 -8 Z" fill="#e8762a"/>'
            '<path d="M32 18 q-2 -6 2 -10 q5 5 3 12 Z" fill="#f2b53a"/>'
            '<circle cx="32" cy="6" r="4" fill="#555" opacity="0.6"/><circle cx="36" cy="3" r="5" fill="#555" opacity="0.45"/>'
            '<rect x="0" y="52" width="64" height="4" fill="#999"/></svg>')


def icon_house():
    return ('<svg viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M14 30 L32 14 L50 30" stroke="#151515" stroke-width="4" fill="none"/>'
            '<rect x="18" y="30" width="28" height="20" fill="#151515"/>'
            '<rect x="28" y="38" width="8" height="12" fill="#f6f1e7"/>'
            '<path d="M44 44 l10 -12 M50 44 l4 -5 M54 44 l2 -3" stroke="#1d7a4c" stroke-width="3" fill="none"/>'
            '<text x="52" y="30" font-size="9" font-weight="bold" fill="#1d7a4c" font-family="Liberation Sans">&#163;</text></svg>')


def icon_chart():
    return ('<svg viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">'
            '<line x1="8" y1="8" x2="8" y2="48" stroke="#999" stroke-width="2"/>'
            '<line x1="8" y1="48" x2="58" y2="48" stroke="#999" stroke-width="2"/>'
            '<polyline points="10,16 22,22 32,20 44,34 56,44" stroke="#b3261e" stroke-width="3.5" fill="none"/>'
            '<path d="M56 44 l-7 -1 M56 44 l-2 -7" stroke="#b3261e" stroke-width="2.5"/>'
            '<circle cx="56" cy="44" r="3.5" fill="#b3261e"/>'
            '<text x="10" y="10" font-size="7" font-weight="bold" fill="#b3261e" font-family="Liberation Sans">KOSPI</text></svg>')


def icon_jet():
    return ('<svg viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M8 34 L34 26 L56 30 L60 34 L56 36 L36 34 L20 42 L14 44 L12 38 Z" fill="#151515"/>'
            '<path d="M34 26 L40 18 L44 18 L42 26 Z" fill="#151515"/>'
            '<path d="M10 40 l4 -4 M12 46 l4 -4 M8 34 l-4 2" stroke="#b3261e" stroke-width="3"/>'
            '<path d="M48 42 q3 -4 0 -8 q-4 -3 -7 0 q-3 4 1 7 q3 2 6 1 Z" fill="#999" opacity="0.7"/>'
            '<circle cx="50" cy="16" r="6" fill="none" stroke="#b3261e" stroke-width="2.5"/>'
            '<path d="M50 8 v5 M50 19 v5 M42 16 h5 M53 16 h5" stroke="#b3261e" stroke-width="2.5"/></svg>')


def icon_flags():
    return ('<svg viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="8" y="10" width="22" height="30" rx="2" fill="#f6f1e7" stroke="#999" stroke-width="1"/>'
            '<rect x="12" y="16" width="14" height="8" fill="#1d7a4c"/><rect x="12" y="19" width="14" height="2.5" fill="#f6f1e7"/>'
            '<rect x="34" y="16" width="14" height="8" fill="#b3261e"/><circle cx="41" cy="20" r="1.8" fill="#f2c230"/>'
            '<line x1="12" y1="30" x2="26" y2="30" stroke="#bbb" stroke-width="1.5"/><line x1="12" y1="35" x2="26" y2="35" stroke="#bbb" stroke-width="1.5"/>'
            '<path d="M38 28 l10 -8 M44 34 l8 -6" stroke="#1d7a4c" stroke-width="3"/></svg>')


def icon_factory():
    return ('<svg viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="10" y="26" width="26" height="24" fill="#151515"/>'
            '<rect x="16" y="14" width="6" height="14" fill="#151515"/><rect x="30" y="18" width="6" height="10" fill="#151515"/>'
            '<rect x="12" y="32" width="6" height="8" fill="#f6f1e7"/><rect x="24" y="32" width="6" height="8" fill="#f6f1e7"/>'
            '<circle cx="19" cy="10" r="4" fill="#999" opacity="0.7"/><circle cx="33" cy="13" r="5" fill="#999" opacity="0.5"/>'
            '<rect x="40" y="30" width="18" height="11" rx="1.5" fill="#1d7a4c"/>'
            '<circle cx="49" cy="35.5" r="3" fill="#f6f1e7"/><text x="49" y="37.5" font-size="5.5" text-anchor="middle" fill="#1d7a4c" font-family="Liberation Sans" font-weight="bold">TK</text>'
            '<rect x="14" y="24" width="4" height="4" fill="#b3261e"/><rect x="22" y="24" width="4" height="4" fill="#1f5f8b"/>'
            '<rect x="30" y="20" width="4" height="4" fill="#b3261e"/><rect x="38" y="20" width="4" height="4" fill="#1f5f8b"/></svg>')


def icon_store():
    return ('<svg viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="10" y="18" width="44" height="30" fill="#f6f1e7" stroke="#151515" stroke-width="2"/>'
            '<path d="M10 18 l6 -8 h32 l6 8 Z" fill="#b3261e"/>'
            '<rect x="22" y="11" width="5" height="5" fill="#b3261e"/><rect x="37" y="11" width="5" height="5" fill="#1f5f8b"/>'
            '<rect x="26" y="32" width="12" height="16" fill="#151515"/>'
            '<circle cx="14" cy="46" r="4" fill="#b3261e"/><circle cx="50" cy="46" r="4" fill="#1f5f8b"/>'
            '<rect x="10" y="22" width="44" height="3" fill="#f2c230"/></svg>')


def icon_blast():
    return ('<svg viewBox="0 0 64 56" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 8 L56 46 L8 46 Z" fill="#f2c230" stroke="#151515" stroke-width="2.5"/>'
            '<rect x="29" y="24" width="6" height="14" fill="#151515"/><circle cx="32" cy="42" r="2.5" fill="#151515"/>'
            '<path d="M50 8 l4 -4 M54 14 l5 -2 M8 10 l-3 -4 M4 16 l-5 -1" stroke="#b3261e" stroke-width="3"/>'
            '<circle cx="18" cy="12" r="5" fill="#999" opacity="0.6"/><circle cx="46" cy="10" r="6" fill="#999" opacity="0.5"/>'
            '<circle cx="8" cy="40" r="4" fill="#999" opacity="0.55"/></svg>')


SCENES = {"ship": scene_ship, "cairo": scene_cairo, "space": scene_space}
ICONS = {"refinery": icon_refinery, "house": icon_house, "chart": icon_chart,
         "jet": icon_jet, "flags": icon_flags, "factory": icon_factory,
         "store": icon_store, "blast": icon_blast}


def sure_badge(sure):
    cls = "sure sure-" + sure.lower()
    return f'<span class="{cls}">{sure}</span>'


def build_heroes():
    out = []
    for c in CARDS[:3]:
        rc = REGIONS[c["r"]][2]
        out.append(f"""
    <div class="hcard" style="--rc:{rc}">
      <div class="scene">{SCENES[c['scene']]()}</div>
      <div class="hbody">
        <div class="hkick"><span class="numb" style="background:{rc}">{c['n']}</span>
          <span class="kicker" style="color:{rc}">{esc(c['place'])} &middot; {esc(c['topic'])}</span>
          {sure_badge(c['sure'])}</div>
        <div class="hhead">{esc(c['head'])}</div>
        <div class="hdet">{esc(c['det'])}</div>
        <div class="hsrc">{esc(c['src'])}</div>

      </div>
    </div>""")
    return "".join(out)


def build_smalls():
    out = []
    for c in CARDS[3:]:
        rc = REGIONS[c["r"]][2]
        tint = rc + "1f"
        out.append(f"""
    <div class="scard" style="--rc:{rc}">
      <div class="spanel" style="background:{tint}">{ICONS[c['scene']]()}<span class="numb sm" style="background:{rc}">{c['n']}</span></div>
      <div class="sbody">
        <div class="skick"><span class="kicker" style="color:{rc}">{esc(c['place'] + (' · ' + c['topic'] if c.get('topic') else ''))}</span>
          {sure_badge(c['sure'])}</div>
        <div class="shead">{esc(c['head'])}</div>
        <div class="sdet">{esc(c['det'])} <span class="ssrc">&middot; {esc(c['src'])}</span></div>
      </div>
    </div>""")
    return "".join(out)


def build_map():
    land_d = geojson_to_svg_path(MAP_GEOJSON)
    pins = pin_positions()
    out = [f'<svg viewBox="0 0 {MAP_W} {MAP_H}" width="{MAP_W}" height="{MAP_H}" '
           f'xmlns="http://www.w3.org/2000/svg">']
    out.append(f'<rect width="{MAP_W}" height="{MAP_H}" fill="#dfe8ee"/>')
    out.append(f'<path d="{land_d}" fill="#cbbfa6" fill-rule="evenodd" stroke="#b3a68c" stroke-width="0.5"/>')
    for p in pins:
        color = REGIONS[p["r"]][2]
        out.append(
            f'<circle cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="8.5" fill="{color}" '
            f'stroke="#f6f1e7" stroke-width="1.3"/>'
            f'<text x="{p["x"]:.1f}" y="{p["y"]+3:.1f}" text-anchor="middle" '
            f'font-family="Liberation Sans" font-weight="bold" font-size="9.5" fill="#ffffff">{p["n"]}</text>'
        )
    out.append("</svg>")
    return "".join(out), pins


def build_bottom():
    map_svg, pins = build_map()
    # legend: region chips with counts
    leg = []
    for i, (short, name, color) in enumerate(REGIONS):
        leg.append(f'<span class="rleg"><i style="background:{color}"></i>{short} {REGION_COUNTS[i]}</span>')
    legend = '<div class="rlegend">' + "".join(leg) + "</div>"
    sure = ('<div class="slegend">'
            '<b>HOW SURE</b> '
            '<span><i class="dot o"></i>OFFICIAL = the authority&rsquo;s own statement</span>'
            '<span><i class="dot c"></i>CONFIRMED = two or more outlets</span>'
            '<span><i class="dot r"></i>REPORTED = one outlet so far</span>'
            '<span><i class="dot cl"></i>CLAIM = one side&rsquo;s account, unverified</span></div>')
    left = f'<div class="bleft"><div class="mapbox">{map_svg}</div>{legend}{sure}</div>'
    # right: also list, two columns
    items = []
    for idx, (r, place, fact) in enumerate(ALSO):
        n = len(CARDS) + idx + 1
        color = REGIONS[r][2]
        items.append(
            f'<div class="aitem"><span class="anum" style="background:{color}">{n}</span>'
            f'<span class="atxt"><b>{esc(place)}</b> {esc(fact)}</span></div>')
    half = (len(items) + 1) // 2
    right = (f'<div class="bright"><div class="ahead">ALSO ON WEDNESDAY 25 NOVEMBER '
             f'&mdash; {len(ALSO)} MORE STORIES</div>'
             f'<div class="acols"><div class="acol">{"".join(items[:half])}</div>'
             f'<div class="acol">{"".join(items[half:])}</div></div></div>')
    return left + right


CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1024px; height:1024px; overflow:hidden; }
body { background:""" + CREAM + """; color:""" + INK + """;
       font-family:"Liberation Sans", Arial, sans-serif; }
#page { width:1024px; height:1024px; position:relative; }

.topbar { position:absolute; left:0; right:0; top:0; height:22px; background:#14213d;
          display:flex; align-items:center; justify-content:space-between;
          padding:0 20px; }
.tb-l { font-size:10.5px; font-weight:bold; color:#f6f1e7; letter-spacing:2.5px; }
.tb-r { font-size:9px; color:#cfd9ec; letter-spacing:1.2px; }

.mast { position:absolute; left:20px; right:20px; top:32px; }
.h1 { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
      font-size:60px; line-height:1.02; letter-spacing:-0.5px; }
.dek { font-family:"Liberation Serif", Georgia, serif; font-style:italic;
       font-size:14.5px; color:#3c3c3c; margin-top:8px; line-height:1.4; }

.chips { position:absolute; left:20px; right:20px; top:128px; display:flex; gap:8px; }
.chip { padding:5px 12px; color:#fff; font-size:10.5px; font-weight:bold;
        letter-spacing:1px; border-radius:2px; }
.chip i { font-style:normal; opacity:0.75; font-weight:normal; margin-left:6px; }

.numsec { position:absolute; left:20px; right:20px; top:158px; }
.num-label { font-size:10px; font-weight:bold; letter-spacing:2px; color:#6a6a6a;
             margin-bottom:5px; }
.nums { display:flex; gap:1px; background:#cfc8b8; border:1px solid #cfc8b8; }
.ncell { flex:1; background:""" + PAPER + """; padding:6px 8px 6px; text-align:center; }
.nnum { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
        font-size:20px; line-height:1.05; }
.nlab { font-size:9px; color:#5a5a5a; line-height:1.3; margin-top:2px; }

.heroes { position:absolute; left:20px; right:20px; top:238px; display:flex; gap:14px; }
.hcard { flex:1; background:#fff; border:1px solid #d8d0bd; }
.scene { width:100%; height:98px; overflow:hidden; }
.scene svg { display:block; width:100%; height:98px; }
.hbody { padding:7px 11px 8px; }
.hkick { display:flex; align-items:center; gap:7px; margin-bottom:4px; }
.numb { display:inline-block; color:#fff; font-size:11px; font-weight:bold;
        min-width:19px; height:19px; line-height:19px; text-align:center;
        border-radius:50%; padding:0 4px; }
.numb.sm { position:absolute; left:4px; top:4px; font-size:9px;
           min-width:16px; height:16px; line-height:16px; z-index:2; }
.kicker { font-size:10px; font-weight:bold; letter-spacing:0.6px; }
.sure { margin-left:auto; font-size:9px; font-weight:bold; letter-spacing:0.5px;
        border:1px solid #999; color:#555; padding:1px 4px; border-radius:2px; white-space:nowrap; }
.sure-claim { border-color:#b3261e; color:#b3261e; }
.sure-official { border-color:#1d7a4c; color:#1d7a4c; }
.hhead { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
         font-size:17.5px; line-height:1.12; margin-bottom:3px; }
.hdet { font-size:10px; line-height:1.38; color:#3c3c3c; margin-bottom:3px; }
.hsrc { font-size:9px; color:#999; }

.smalls { position:absolute; left:20px; right:20px; top:466px; }
.sgrid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }
.scard { background:#fff; border:1px solid #d8d0bd; display:flex; flex-direction:row; }
.spanel { position:relative; flex:0 0 64px; display:flex; align-items:center; justify-content:center; }
.spanel svg { width:58px; height:51px; }
.sbody { padding:4px 7px 6px; flex:1; min-width:0; display:flex; flex-direction:column; }
.skick { display:flex; align-items:center; gap:4px; margin-bottom:2px; }
.skick .kicker { font-size:9px; letter-spacing:0.2px; white-space:nowrap; }
.skick .sure { padding:1px 3px; }
.shead { font-family:"Liberation Serif", Georgia, serif; font-weight:bold;
         font-size:12px; line-height:1.15; margin-bottom:1px; }
.sdet { font-size:9px; line-height:1.35; color:#4a4a4a; margin-bottom:1px; }
.ssrc { font-size:9px; color:#999; }

.bottom { position:absolute; left:20px; right:20px; top:662px; display:flex; gap:16px; }
.bleft { width:330px; flex:0 0 330px; }
.mapbox { border:1px solid #d8d0bd; background:#fff; padding:4px; }
.mapbox svg { display:block; width:312px; height:182px; }
.rlegend { display:flex; flex-wrap:wrap; gap:2px 10px; margin-top:6px; }
.rleg { font-size:9px; font-weight:bold; letter-spacing:0.5px; color:#444; }
.rleg i { display:inline-block; width:8px; height:8px; border-radius:50%;
          margin-right:4px; }
.slegend { margin-top:5px; font-size:9px; color:#5a5a5a; line-height:1.5; }
.slegend b { font-size:9px; letter-spacing:1px; }
.slegend span { display:inline-block; margin-right:10px; }
.dot { display:inline-block; width:7px; height:7px; border-radius:50%;
       margin-right:4px; }
.dot.o { background:#1d7a4c; } .dot.c { background:#1f5f8b; }
.dot.r { background:#b98a1e; } .dot.cl { background:#b3261e; }
.bright { flex:1; min-width:0; }
.ahead { font-size:10px; font-weight:bold; letter-spacing:1.2px; color:#444;
         margin-bottom:4px; }
.acols { display:flex; gap:16px; }
.acol { flex:1; min-width:0; }
.aitem { display:flex; align-items:baseline; gap:5px; padding:0 0;
         border-bottom:1px solid #e4ddcb; }
.anum { flex:0 0 16px; height:12px; color:#fff; font-size:9px; font-weight:bold;
        line-height:12px; text-align:center; border-radius:2px; }
.atxt { font-size:9.5px; color:#333; line-height:1.28; white-space:nowrap; }
.atxt b { font-weight:bold; }

.dc { position:absolute; left:20px; right:20px; top:934px;
      border:1px solid #b3261e; background:#fff; padding:6px 12px 6px; }
.dc-title { font-size:10px; font-weight:bold; color:#b3261e; letter-spacing:2px;
            margin-bottom:3px; }
.dc-body { font-size:10.5px; line-height:1.4; color:#333; }

.foot { position:absolute; left:20px; right:20px; top:998px;
        font-size:9px; color:#777; letter-spacing:0.3px; }
"""


def build_html():
    chips = "".join(
        f'<div class="chip" style="background:{REGIONS[i][2]}">{REGIONS[i][0]}'
        f'<i>{REGION_COUNTS[i]}</i></div>' for i in range(len(REGIONS)))
    nums = "".join(
        f'<div class="ncell"><div class="nnum">{esc(n)}</div><div class="nlab">{esc(l)}</div></div>'
        for n, l in NUMBERS)
    also_half_items = build_bottom()
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div id="page">
  <div class="topbar"><span class="tb-l">THE WORLD IN ONE DAY</span>
    <span class="tb-r">{STORY_COUNT} STORIES &middot; 5 REGIONS &middot; EVERY ONE REPORTED WED 25 NOV 2026</span></div>
  <div class="mast">
    <div class="h1">Wednesday 25 November 2026</div>
    <div class="dek">US proposes tariffs on 14 economies &middot; Fuel tanker fire kills 31 in Cairo &middot; First Pakistani astronaut reaches China's station</div>
  </div>
  <div class="chips">{chips}</div>
  <div class="numsec"><div class="num-label">THE DAY IN NUMBERS</div>
    <div class="nums">{nums}</div></div>
  <div class="heroes">{build_heroes()}</div>
  <div class="smalls"><div class="sgrid">{build_smalls()}</div></div>
  <div class="bottom">{also_half_items}</div>
  <div class="dc"><div class="dc-title">DATE CHECK</div>
    <div class="dc-body">Every item was reported on Wednesday 25 November 2026 (UTC). Left out as other days&rsquo; news:
      Nvidia reinstates Jensen Huang (Mon 23 Nov) &middot; CAS gives Africa Cup title back to Senegal (Tue 24 Nov) &middot; Bangkok oil depot explosion (Thu 26 Nov).</div></div>
  <div class="foot">Sources: AP, AFP, Reuters, BBC, Guardian, DW, Al Jazeera, NPR, NBC News, CNN, AA, France 24, Yonhap, Daily Star &middot; Drawings original, no photographs &middot; no forecasts</div>
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
    html = build_html()
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
