"""Reels 字卡用的示意地圖（SVG）。底圖：Natural Earth 1:50m（公有領域），只畫陸地與河流，不畫國界。

字卡加上 "map": {...} 即可，格式：
  bbox:   [西經度, 南緯度, 東經度, 北緯度]，會自動置中、等比縮放
  points: [{"at": "武昌", "label": "武昌起義", "sub": "1911.10", "hl": True, "pos": "r"}]
          at 可以是 PLACES 裡的地名或 [經度, 緯度]；pos 是標籤位置 r/l/t/b；hl 表示強調（較大，預設紅色，color 可改 blue）
  routes: [{"via": ["廣州", "長沙", "武漢"], "dash": False, "hl": True, "label": "北伐路線"}]
  shade:  ["Taiwan"]  要填色強調的陸地（Natural Earth 名稱）
  colors: {"Taiwan": "blue", "China": "red"}  指定陸地顏色（blue／red 或色碼）
"""
import html, json, math, os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 880, 820
GEO = json.load(open(os.path.join(ROOT, "assets", "geo", "east_asia.json")))

PLACES = {  # 經度, 緯度
    "武昌": (114.31, 30.55), "武漢": (114.31, 30.55), "南京": (118.80, 32.06), "廣州": (113.26, 23.13),
    "長沙": (112.94, 28.23), "北平": (116.40, 39.90), "上海": (121.47, 31.23), "重慶": (106.55, 29.56),
    "瀋陽": (123.43, 41.80), "台兒莊": (117.73, 34.56), "昆明": (102.83, 24.88), "畹町": (98.07, 24.08),
    "臘戌": (97.75, 22.93), "仁安羌": (94.87, 20.47), "雷多": (95.73, 27.29), "密支那": (97.39, 25.38),
    "八莫": (97.24, 24.27), "阿薩姆": (95.0, 27.5), "臺北": (121.56, 25.04), "金門": (118.32, 24.44),
    "馬祖": (119.95, 26.16), "澎湖": (119.58, 23.57), "臺灣": (120.9, 23.7), "東北": (125.5, 44.0), "西安": (108.94, 34.34), "杭州": (120.16, 30.27), "南昌": (115.86, 28.68),
}

SEA, LAND, LAND_HL, RIVER = "#101a3e", "#37508f", "#a23344", "#6f8fd6"
LAND_BLUE = "#2f6fe0"
RED, GOLD, INK, MUTE = "#e0545e", "#f2c14e", "#f4f5f7", "#aab3d0"


def _proj(bbox):
    x0, y0, x1, y1 = bbox
    k = math.cos(math.radians((y0 + y1) / 2))
    sx = W / ((x1 - x0) * k)
    sy = H / (y1 - y0)
    s = min(sx, sy)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return lambda lon, lat: (W / 2 + (lon - cx) * k * s, H / 2 - (lat - cy) * s)


def _ll(at):
    return PLACES[at] if isinstance(at, str) else tuple(at)


def _path(pts, p, close):
    xy = [p(x, y) for x, y in pts]
    d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in xy)
    return d + ("Z" if close else "")


def svg_map(spec):
    bbox = spec["bbox"]
    p = _proj(bbox)
    x0, y0, x1, y1 = bbox
    pad = 6
    near = lambda pts: any(x0 - pad < x < x1 + pad and y0 - pad < y < y1 + pad for x, y in pts)
    shade = set(spec.get("shade", []))
    colors = {k: {"blue": LAND_BLUE, "red": LAND_HL}.get(v, v) for k, v in spec.get("colors", {}).items()}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="Noto Sans TC, sans-serif">',
           '<defs><clipPath id="clip"><rect width="100%" height="100%" rx="28"/></clipPath>'
           f'<marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
           f'<path d="M0 0L10 5L0 10z" fill="{GOLD}"/></marker>'
           f'<marker id="am" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
           f'<path d="M0 0L10 5L0 10z" fill="{MUTE}"/></marker></defs>',
           f'<g clip-path="url(#clip)"><rect width="100%" height="100%" fill="{SEA}"/>']
    for f in GEO["land"]:
        if near(f["ring"]):
            fill = colors.get(f["name"]) or (LAND_HL if f["name"] in shade else LAND)
            out.append(f'<path d="{_path(f["ring"], p, True)}" fill="{fill}" stroke="{fill}" stroke-width="1"/>')
    for r in GEO["rivers"]:
        if near(r):
            out.append(f'<path d="{_path(r, p, False)}" fill="none" stroke="{RIVER}" stroke-width="2.5" '
                       f'stroke-linejoin="round" opacity=".8"/>')
    for rt in spec.get("routes", []):
        pts = [p(*_ll(a)) for a in rt["via"]]
        d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        col = GOLD if rt.get("hl", True) else MUTE
        dash = ' stroke-dasharray="16 12"' if rt.get("dash") else ""
        mk = "ah" if rt.get("hl", True) else "am"
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round" '
                   f'stroke-linejoin="round"{dash} marker-end="url(#{mk})"/>')
        if rt.get("label"):
            mx, my = p(*_ll(rt["label_at"])) if rt.get("label_at") else _midway(pts)
            out.append(_label(mx, my, rt["label"], None, rt.get("pos", "r"), col, 30))
    for pt in spec.get("points", []):
        x, y = p(*_ll(pt["at"]))
        hl = pt.get("hl")
        if hl:
            dot = {"blue": "#4d8bff", "red": RED}.get(pt.get("color", "red"), pt.get("color"))
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="26" fill="{dot}" opacity=".3"/>'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="{dot}" stroke="{INK}" stroke-width="4"/>')
        else:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{MUTE}"/>')
        out.append(_label(x, y, pt.get("label", pt["at"] if isinstance(pt["at"], str) else ""), pt.get("sub"),
                          pt.get("pos", "r"), INK if hl else MUTE, 40 if hl else 32))
    out.append(f'<text x="{W - 20}" y="{H - 16}" text-anchor="end" font-size="18" fill="{MUTE}" opacity=".7">'
               f'示意圖・底圖 Natural Earth</text></g></svg>')
    return "".join(out)


def _label(x, y, text, sub, pos, col, size):
    e = html.escape
    gap = 26
    dx, dy, anchor = {"r": (gap, 0, "start"), "l": (-gap, 0, "end"), "t": (0, -gap - 8, "middle"),
                      "b": (0, gap + size * .7, "middle")}[pos]
    ty = y + dy + size * .35
    halo = f'stroke="{SEA}" stroke-width="8" paint-order="stroke" stroke-linejoin="round"'
    s = (f'<text x="{x + dx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" font-size="{size}" font-weight="700" '
         f'fill="{col}" {halo}>{e(text)}</text>')
    if sub:
        s += (f'<text x="{x + dx:.1f}" y="{ty + size * 1.05:.1f}" text-anchor="{anchor}" font-size="{size * .72:.0f}" '
              f'font-weight="700" fill="{GOLD}" {halo}>{e(sub)}</text>')
    return s


def _midway(pts):
    """折線全長一半處的座標，用來放路線名稱。"""
    segs = [(a, b, math.dist(a, b)) for a, b in zip(pts, pts[1:])]
    half = sum(d for *_, d in segs) / 2
    for (ax, ay), (bx, by), d in segs:
        if half <= d:
            t = half / d if d else 0
            return ax + (bx - ax) * t, ay + (by - ay) * t
        half -= d
    return pts[-1]
