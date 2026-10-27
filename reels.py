"""把 reels_content.py 的字卡做成 1080×1920 直式影片。用法：python3 reels.py [slug]

字卡有 "say"（旁白）時：用 Google 文字轉語音產生旁白（需環境變數 GCP_TTS_KEY），
字卡長度自動拉長到旁白念完，畫面下方顯示字幕，配樂自動壓低。
旁白音檔快取在 assets/tts/，同一句不會重複產生。"""
import base64, hashlib, html, json, os, subprocess, sys, urllib.request
from build import FONTS, PLUM, SITE_NAME
from reels_content import REELS
from maps import svg_map

ROOT = os.path.dirname(os.path.abspath(__file__))
FADE = 0.4

CARD_CSS = """
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1920px;overflow:hidden;font-family:"Noto Sans TC",sans-serif}
.c{width:1080px;height:1920px;background:#1b2a5c;color:#f4f5f7;display:flex;flex-direction:column;justify-content:center;gap:56px;padding:0 100px;position:relative}
.c.v{justify-content:flex-start;padding-top:480px}
.c.end{background:#f4f5f7;color:#151c2e;align-items:center;text-align:center}
.k{font-size:46px;letter-spacing:.2em;color:#e0545e;font-weight:700}
.c.end .k{color:#b8232f}
h1{font-family:"Noto Serif TC",serif;font-weight:900;font-size:124px;line-height:1.3;white-space:pre-line}
.b{font-size:52px;line-height:1.6;opacity:.9;white-space:pre-line}
.plum{width:150px;height:150px} .plum circle{fill:#b8232f} .plum .core{fill:#f4f5f7}
.foot{position:absolute;left:100px;right:100px;bottom:260px;font-size:34px;opacity:.6}
.bar{position:absolute;left:0;top:0;height:14px;background:#b8232f}
.sub{position:absolute;left:70px;right:70px;bottom:330px;font-size:50px;line-height:1.5;font-weight:700;color:#fff;
  background:rgba(10,14,30,.72);padding:22px 32px;border-radius:14px;text-align:center}
.c.end .sub{color:#fff}
.c.m{justify-content:flex-start;padding-top:200px;gap:30px}
.c.m h1{font-size:92px;line-height:1.2}
.map{margin:6px -10px 0;border-radius:28px;overflow:hidden;box-shadow:0 0 0 2px rgba(255,255,255,.12)}
.map svg{display:block;width:880px;height:800px}
"""
VOICE = {"languageCode": "cmn-TW", "name": "cmn-TW-Wavenet-C"}  # 臺灣口音男聲；女聲可改 cmn-TW-Wavenet-A
TTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "tts")


def tts(text):
    """回傳旁白 mp3 路徑；沒有金鑰又沒有快取時回傳 None。"""
    key = hashlib.sha1(f"{VOICE['name']}|{text}".encode()).hexdigest()[:16]
    path = os.path.join(TTS_DIR, f"{key}.mp3")
    if os.path.exists(path):
        return path
    api_key = os.environ.get("GCP_TTS_KEY")
    if not api_key:
        return None
    body = json.dumps({"input": {"text": text}, "voice": VOICE,
                       "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.1}}).encode()
    req = urllib.request.Request(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        audio = base64.b64decode(json.load(r)["audioContent"])
    os.makedirs(TTS_DIR, exist_ok=True)
    open(path, "wb").write(audio)
    return path


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def card_html(c, i, n):
    e = html.escape
    end = c.get("end")
    inner = (PLUM if end else "") + f'<div class="k">{e(c["kicker"])}</div><h1>{e(c["head"])}</h1>'
    if c.get("body"):
        inner += f'<div class="b">{e(c["body"])}</div>'
    if c.get("map"):
        inner += f'<div class="map">{svg_map(c["map"])}</div>'
    if not end:
        inner += f'<div class="foot">{SITE_NAME}</div>'
    if c.get("say") and not end:
        inner += f'<div class="sub">{e(c["say"])}</div>'
    bar = f'<div class="bar" style="width:{(i + 1) / n * 100:.1f}%"></div>'
    return f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{CARD_CSS}</style></head><body><div class="c{" end" if end else ""}{" m" if c.get("map") else " v" if c.get("say") and not end else ""}">{bar}{inner}</div></body></html>'


def build(reel):
    tmp = os.path.join(ROOT, "_preview", "reels", reel["slug"])
    os.makedirs(tmp, exist_ok=True)
    cards = [dict(c) for c in reel["cards"]]
    # 旁白：字卡長度至少要念得完
    voices = []
    for c in cards:
        v = tts(c["say"]) if c.get("say") else None
        if v:
            c["sec"] = max(c["sec"], duration(v) + 0.6)
        elif c.get("say") and not c.get("end"):
            c["sec"] = max(c["sec"], 1.2 + len(c["say"]) / 6)  # 無旁白：留足閱讀時間（約每秒 6 字）
        voices.append(v)
    if any(c.get("say") for c in cards) and not any(voices):
        print(f"注意 {reel['slug']}：沒有 GCP_TTS_KEY，先做無旁白版（字幕照常顯示）")
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
    # 配樂（music.py 產生的原創國風配樂）＋旁白；有旁白時配樂壓低。reel 可用 "music": null 關掉配樂
    total = sum(c["sec"] for c in cards) - FADE * (len(cards) - 1)
    music = reel.get("music", "bgm-pentatonic.m4a")
    n_in = len(cards)
    if music:
        args += ["-stream_loop", "-1", "-i", os.path.join(ROOT, "assets", music)]
    else:
        args += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    vol = 0.22 if any(voices) else 1.0
    filt.append(f"[{n_in}:a]atrim=0:{total:.2f},volume={vol},afade=t=out:st={total - 2:.2f}:d=2,aresample=44100[bg]")
    mix, start = ["[bg]"], 0.0
    for i, (c, v) in enumerate(zip(cards, voices)):
        if v:
            idx = n_in + len(mix)
            args += ["-i", v]
            ms = int((start + 0.25) * 1000)
            filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[n{i}]")
            mix.append(f"[n{i}]")
        start += c["sec"] - FADE
    if len(mix) > 1:
        filt.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0[a]")
    else:
        filt.append("[bg]anull[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex", ";".join(filt), "-map", f"[{last}]",
                    "-map", "[a]", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", "30", "-movflags", "+faststart", out], check=True)
    open(os.path.join(out_dir, f"{reel['slug']}.txt"), "w").write(reel["caption"])
    print(out)


if __name__ == "__main__":
    want = sys.argv[1:] or [r["slug"] for r in REELS]
    for r in REELS:
        if r["slug"] in want:
            build(r)
