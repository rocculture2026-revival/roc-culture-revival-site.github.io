"""把 reels_content.py 的字卡做成 1080×1920 直式影片（無聲）。用法：python3 reels.py [slug]"""
import html, json, os, subprocess, sys
from build import FONTS, PLUM, SITE_NAME
from reels_content import REELS

ROOT = os.path.dirname(os.path.abspath(__file__))
FADE = 0.4

CARD_CSS = """
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1920px;overflow:hidden;font-family:"Noto Sans TC",sans-serif}
.c{width:1080px;height:1920px;background:#1b2a5c;color:#f4f5f7;display:flex;flex-direction:column;justify-content:center;gap:56px;padding:0 100px;position:relative}
.c.end{background:#f4f5f7;color:#151c2e;align-items:center;text-align:center}
.k{font-size:46px;letter-spacing:.2em;color:#e0545e;font-weight:700}
.c.end .k{color:#b8232f}
h1{font-family:"Noto Serif TC",serif;font-weight:900;font-size:124px;line-height:1.3;white-space:pre-line}
.b{font-size:52px;line-height:1.6;opacity:.9;white-space:pre-line}
.plum{width:150px;height:150px} .plum circle{fill:#b8232f} .plum .core{fill:#f4f5f7}
.foot{position:absolute;left:100px;right:100px;bottom:260px;font-size:34px;opacity:.6}
.bar{position:absolute;left:0;top:0;height:14px;background:#b8232f}
"""


def card_html(c, i, n):
    e = html.escape
    end = c.get("end")
    inner = (PLUM if end else "") + f'<div class="k">{e(c["kicker"])}</div><h1>{e(c["head"])}</h1>'
    if c.get("body"):
        inner += f'<div class="b">{e(c["body"])}</div>'
    if not end:
        inner += f'<div class="foot">{SITE_NAME}</div>'
    bar = f'<div class="bar" style="width:{(i + 1) / n * 100:.1f}%"></div>'
    return f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{CARD_CSS}</style></head><body><div class="c{" end" if end else ""}">{bar}{inner}</div></body></html>'


def build(reel):
    tmp = os.path.join(ROOT, "_preview", "reels", reel["slug"])
    os.makedirs(tmp, exist_ok=True)
    cards = reel["cards"]
    jobs = []
    for i, c in enumerate(cards):
        src = os.path.join(tmp, f"{i}.html")
        open(src, "w").write(card_html(c, i, len(cards)))
        jobs.append([src, os.path.join(tmp, f"{i}.jpg")])
    subprocess.run(["node", os.path.join(ROOT, "render_ig.js"), json.dumps(jobs), "1080", "1920"], check=True)

    # 每張字卡做成一段帶輕微推近的影片，再以淡入淡出串接
    args, filt, offset = [], [], 0.0
    for i, c in enumerate(cards):
        args += ["-i", jobs[i][1]]  # 單張圖，由 zoompan 展開成 sec 秒
        frames = int(c["sec"] * 30)
        filt.append(f"[{i}:v]scale=1188:2112,zoompan=z='1+0.04*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,setsar=1[v{i}]")
    last = "v0"
    for i in range(1, len(cards)):
        offset += cards[i - 1]["sec"] - FADE
        filt.append(f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[x{i}]")
        last = f"x{i}"
    out_dir = os.path.join(ROOT, "docs", "reels")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{reel['slug']}.mp4")
    # 加一條無聲音軌：IG 的 Reels 規格要求 AAC 音訊
    total = sum(c["sec"] for c in cards) - FADE * (len(cards) - 1)
    args += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex", ";".join(filt), "-map", f"[{last}]",
                    "-map", f"{len(cards)}:a", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", "30", "-movflags", "+faststart", out], check=True)
    open(os.path.join(out_dir, f"{reel['slug']}.txt"), "w").write(reel["caption"])
    print(out)


if __name__ == "__main__":
    want = sys.argv[1:] or [r["slug"] for r in REELS]
    for r in REELS:
        if r["slug"] in want:
            build(r)
