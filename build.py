"""產生網站、各平台貼文稿與 IG 輪播圖。用法：python3 build.py [--no-images]"""
import html, os, sys
from content import ARTICLES

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_NAME = "中華民國文化復興聯盟"
EMAIL = "rocculture2026@gmail.com"
HANDLE = "roc_culture_revival"  # 帳號註冊後若名稱不同，改這裡

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@600;900&family=Noto+Sans+TC:wght@400;500;700&display=swap">'


def minguo(iso):
    y, m, d = map(int, iso.split("-"))
    return f"民國{y - 1911}年{m}月{d}日"


PLUM = """<svg class="plum" viewBox="-50 -50 100 100" aria-hidden="true">{petals}<circle r="9" class="core"/></svg>""".format(
    petals="".join(f'<circle r="20" cx="0" cy="-27" transform="rotate({a})"/>' for a in range(0, 360, 72)))

CSS = """
/* 版面：單欄閱讀，報頭用民國紀年，梅花為唯一裝飾 */
:root{
  --paper:#f4f5f7; --surface:#ffffff; --ink:#151c2e; --muted:#59617a;
  --navy:#1b2a5c; --plum:#b8232f; --line:#d9dce5; --on-navy:#f4f5f7;
  --display:"Noto Serif TC","Songti TC","PMingLiU",serif;
  --body:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --paper:#10131c; --surface:#171b27; --ink:#e8eaf0; --muted:#9aa1b5;
  --navy:#0b1230; --plum:#e0545e; --line:#2a3042; --on-navy:#e8eaf0; color-scheme:dark}}
:root[data-theme="dark"]{
  --paper:#10131c; --surface:#171b27; --ink:#e8eaf0; --muted:#9aa1b5;
  --navy:#0b1230; --plum:#e0545e; --line:#2a3042; --on-navy:#e8eaf0; color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.85}
.wrap{max-width:720px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header.mast{background:var(--navy);color:var(--on-navy)}
header.mast .wrap{padding-block:48px 40px;display:grid;gap:14px}
.date{font-size:14px;letter-spacing:.12em;opacity:.8}
h1.name{font-family:var(--display);font-weight:900;font-size:clamp(32px,7vw,52px);line-height:1.2;margin:0;text-wrap:balance;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.plum{width:1em;height:1em;flex:none}
.plum circle{fill:var(--plum)} .plum .core{fill:var(--on-navy)}
.tagline{margin:0;font-size:18px;opacity:.9;max-width:34em}
nav.follow{display:flex;gap:10px;flex-wrap:wrap;font-size:14px}
nav.follow a{color:var(--on-navy);border:1px solid color-mix(in srgb,var(--on-navy) 40%,transparent);padding:4px 12px;border-radius:999px;text-decoration:none}
nav.follow a:hover,nav.follow a:focus-visible{background:color-mix(in srgb,var(--on-navy) 15%,transparent);outline:none}
main .wrap{padding-block:40px 64px;display:grid;gap:48px}
.index h2,.about h2{font-family:var(--display);font-size:15px;letter-spacing:.2em;color:var(--plum);margin:0 0 12px}
.index ol{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.index li{border-bottom:1px solid var(--line)}
.index a{display:grid;gap:2px;padding:16px 0;color:inherit;text-decoration:none}
.index a:hover .t,.index a:focus-visible .t{color:var(--plum)}
.index .k{font-size:13px;color:var(--muted);letter-spacing:.08em}
.index .t{font-family:var(--display);font-weight:600;font-size:21px;line-height:1.4}
article{background:var(--surface);border:1px solid var(--line);border-radius:4px;padding:32px clamp(18px,5vw,40px);min-width:0}
article .k{font-size:13px;color:var(--plum);letter-spacing:.12em}
article h1{font-family:var(--display);font-weight:900;font-size:clamp(26px,5vw,34px);line-height:1.35;margin:6px 0 12px;text-wrap:balance}
article .lede{color:var(--muted);font-size:18px;margin:0 0 8px}
article h2{font-family:var(--display);font-weight:600;font-size:22px;margin:32px 0 4px;text-wrap:balance}
article p,article li{margin:10px 0}
article ol,article ul{padding-left:1.4em}
.note{font-size:14px;color:var(--muted);border-left:3px solid var(--line);padding-left:12px}
.stance{font-size:13px;color:var(--muted);margin-top:28px;padding-top:12px;border-top:1px dashed var(--line)}
.timeline{display:grid;gap:12px;margin:12px 0}
.timeline div{display:grid;grid-template-columns:64px 1fr;gap:14px;align-items:baseline}
.timeline b{font-family:var(--display);font-size:20px;color:var(--plum);font-variant-numeric:tabular-nums}
.timeline span{min-width:0}
.about p{margin:0;color:var(--muted)}
footer{border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
footer .wrap{padding-block:24px 40px}
a{color:var(--plum)}
.contact{margin-top:48px;padding-top:24px;border-top:1px solid var(--line)}
.contact a{overflow-wrap:anywhere}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
"""


def page_body():
    idx = "".join(
        f'<li><a href="#{a["slug"]}"><span class="k">{a["tag"]}・{minguo(a["date"])}</span><span class="t">{html.escape(a["title"])}</span></a></li>'
        for a in ARTICLES)
    arts = "".join(f"""
<article id="{a['slug']}">
<div class="k">{a['tag']}・{minguo(a['date'])}</div>
<h1>{html.escape(a['title'])}</h1>
<p class="lede">{html.escape(a['lede'])}</p>
{a['web']}
<p class="stance">本文由{SITE_NAME}撰寫，代表本聯盟立場。</p>
</article>""" for a in ARTICLES)
    return f"""
<header class="mast"><div class="wrap">
<div class="date">{minguo(ARTICLES[0]['date'])}</div>
<h1 class="name">{PLUM}{SITE_NAME}</h1>
<p class="tagline">傳承中華民國正統，重讀三民主義，守護自由的生活方式。</p>
<nav class="follow" aria-label="社群帳號">
<a href="https://www.instagram.com/{HANDLE}/">Instagram @{HANDLE}</a>
<a href="https://www.threads.net/@{HANDLE}">Threads @{HANDLE}</a>
</nav>
</div></header>
<main><div class="wrap">
<section class="about"><h2>關於聯盟</h2><p>本聯盟為民間自發團體，與任何政府機關、政黨或既有組織均無隸屬關係。站上文章皆為本聯盟立場，引用皆附出處。</p></section>
<section class="index"><h2>文章</h2><ol>{idx}</ol></section>
{arts}
<section class="about contact" id="contact"><h2>聯絡我們</h2><p>合作、投稿或指正，歡迎來信：<a href="mailto:{EMAIL}">{EMAIL}</a></p></section>
</div></main>
<footer><div class="wrap">© 民國一一五年 {SITE_NAME}。本站內容為本聯盟觀點，歡迎註明出處轉載。<a href="privacy.html">隱私權政策</a></div></footer>
"""


def write_site():
    os.makedirs(os.path.join(ROOT, "docs", "ig"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "_preview"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "posts"), exist_ok=True)
    body = page_body()
    full = f"""<!doctype html>
<html lang="zh-Hant-TW"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{SITE_NAME}</title>
<meta name="description" content="傳承中華民國正統，重讀三民主義，守護自由的生活方式。">
{FONTS}
<style>{CSS}</style>
</head><body>{body}</body></html>
"""
    open(os.path.join(ROOT, "docs", "index.html"), "w").write(full)
    # 預覽版（給 claude.ai Artifact 用，外層骨架由平台補上）
    preview = f"""<title>{SITE_NAME}</title>
<meta name="claude:viewport-fit-sides" content="cover">
{FONTS}
<style>{CSS}</style>
{body}"""
    open(os.path.join(ROOT, "_preview", "index.html"), "w").write(preview)


def write_posts():
    for i, a in enumerate(ARTICLES, 1):
        n = len(a["threads"])
        assert n <= 500, f"{a['slug']} Threads 超過 500 字：{n}"
        slides = "\n".join(f"{j}. docs/ig/{i:02d}-{a['slug']}-{j}.jpg" for j in range(1, len(a["ig_slides"]) + 1))
        md = f"""# {a['title']}

發布日：{a['date']}（{minguo(a['date'])}）　網站錨點：`#{a['slug']}`

## Instagram

輪播圖（依序上傳，1080×1350 JPEG；Graph API 只收 JPEG）：
{slides}

貼文說明（{len(a['ig_caption'])} 字，上限 2,200）：

```
{a['ig_caption']}
```

## Threads

（{n} 字，上限 500）

```
{a['threads']}
```
"""
        open(os.path.join(ROOT, "posts", f"{i:02d}-{a['slug']}.md"), "w").write(md)
        print(f"{a['slug']}: threads {n} 字, ig caption {len(a['ig_caption'])} 字")


SLIDE_CSS = """
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1350px;font-family:"Noto Sans TC",sans-serif;overflow:hidden}
.s{width:1080px;height:1350px;padding:110px 100px;display:flex;flex-direction:column;position:relative}
.cover{background:#1b2a5c;color:#f4f5f7;justify-content:center;gap:40px}
.paper{background:#f4f5f7;color:#151c2e;gap:48px;justify-content:center}
.kick{font-size:34px;letter-spacing:.3em;color:#e0545e;font-weight:700}
.paper .kick{color:#b8232f}
h1{font-family:"Noto Serif TC",serif;font-weight:900;font-size:112px;line-height:1.25;white-space:pre-line}
.paper h1{font-size:76px}
.sub{font-size:40px;opacity:.85}
.body{font-size:46px;line-height:1.75;white-space:pre-line}
ul{list-style:none;padding:0;display:grid;gap:36px}
li{font-size:46px;line-height:1.5;padding-left:56px;position:relative}
li::before{content:"";position:absolute;left:0;top:.45em;width:26px;height:26px;border-radius:50%;background:#b8232f}
.tl{display:grid;grid-template-columns:190px 1fr;row-gap:10px;font-size:42px;align-items:baseline}
.tl b{font-family:"Noto Serif TC",serif;color:#b8232f;font-size:50px}
blockquote{font-family:"Noto Serif TC",serif;font-size:54px;line-height:1.6;border-left:10px solid #b8232f;padding-left:36px}
cite{font-size:34px;color:#59617a;font-style:normal}
.foot{position:absolute;left:100px;right:100px;bottom:70px;display:flex;justify-content:space-between;font-size:28px;opacity:.7}
.plum{width:64px;height:64px} .plum circle{fill:#b8232f} .plum .core{fill:#f4f5f7}
.cover .plum{width:120px;height:120px}
"""


def slide_html(s, idx, total):
    e = html.escape
    if s["kind"] == "cover":
        inner = f'{PLUM}<div class="kick">{e(s["kicker"])}</div><h1>{e(s["head"])}</h1><div class="sub">{e(s["sub"])}</div>'
        cls = "cover"
    else:
        cls = "paper"
        inner = f'<h1>{e(s["head"])}</h1>'
        if s["kind"] == "text":
            inner += f'<div class="body">{e(s["body"])}</div>'
        elif s["kind"] == "list":
            inner += "<ul>" + "".join(f"<li>{e(x)}</li>" for x in s["items"]) + "</ul>"
        elif s["kind"] == "timeline":
            inner += '<div class="tl">' + "".join(f"<b>{y}</b><span>{e(t)}</span>" for y, t in s["items"]) + "</div>"
        elif s["kind"] == "quote":
            inner += f'<blockquote>「{e(s["quote"])}」</blockquote><cite>── {e(s["cite"])}</cite><div class="body">{e(s["body"])}</div>'
    foot = f'<div class="foot"><span>{SITE_NAME}</span><span>{idx}/{total}</span></div>'
    return f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{SLIDE_CSS}</style></head><body><div class="s {cls}">{inner}{foot}</div></body></html>'


def write_images():
    """先輸出每張投影片的 HTML，再用 Node 版 Playwright 截圖（render_ig.js）。"""
    import json, subprocess
    tmp = os.path.join(ROOT, "_preview", "slides")
    os.makedirs(tmp, exist_ok=True)
    jobs = []
    for i, a in enumerate(ARTICLES, 1):
        sl = a["ig_slides"]
        for j, s in enumerate(sl, 1):
            src = os.path.join(tmp, f"{i:02d}-{a['slug']}-{j}.html")
            open(src, "w").write(slide_html(s, j, len(sl)))
            jobs.append([src, os.path.join(ROOT, "docs", "ig", f"{i:02d}-{a['slug']}-{j}.jpg")])
    subprocess.run(["node", os.path.join(ROOT, "render_ig.js"), json.dumps(jobs)], check=True)


if __name__ == "__main__":
    write_site()
    write_posts()
    if "--no-images" not in sys.argv:
        write_images()
    print("done")
