"""依 queue.json 把到時間、已核准的貼文發到 Instagram 與 Threads。由 .github/workflows/publish.yml 定時執行。

用法：python3 publish.py [--dry-run]
權杖從環境變數讀：IG_TOKEN_<帳號>、THREADS_TOKEN_<帳號>、FB_PAGE_TOKEN_<帳號>、
YT_REFRESH_TOKEN_<帳號>（另需 YT_CLIENT_ID、YT_CLIENT_SECRET），例如 IG_TOKEN_MAIN。
X 用 X_API_KEY、X_API_SECRET、X_ACCESS_TOKEN_<帳號>、X_ACCESS_SECRET_<帳號>；
TikTok 用 TIKTOK_REFRESH_TOKEN_<帳號>（另需 TIKTOK_CLIENT_KEY、TIKTOK_CLIENT_SECRET）。
發過的項目記在 posted.json，不會重發。
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

from content import ARTICLES
from reels_content import REELS

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = os.environ.get("SITE_URL") or "https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io"
IG = "https://graph.instagram.com/v21.0"
TH = "https://graph.threads.net/v1.0"
FB = "https://graph.facebook.com/v21.0"
FB_PAGE_NAME = "中華民國文化復興聯盟"  # 只允許發到這個名稱的粉專
YT_UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
DRY = "--dry-run" in sys.argv

ARTICLE = {a["slug"]: (i, a) for i, a in enumerate(ARTICLES, 1)}
REEL = {r["slug"]: r for r in REELS}


class ApiError(Exception):
    pass


def call(method, endpoint, **params):
    url = endpoint
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if "access token" in body.lower() or ('"code":190' in body):
            body += "\n→ 權杖可能過期或沒有發文權限，請照 SETUP-autopost.md 第 5 步重新產生並更新 Secrets。"
        raise ApiError(f"{e.code} {url.split('?')[0]}\n{body}") from None


def wait_ready(url, token, field):
    """等容器處理完（影片要比較久）。"""
    for _ in range(60):
        st = call("GET", url, fields=field, access_token=token).get(field)
        if st in ("FINISHED", "PUBLISHED"):
            return
        if st in ("ERROR", "EXPIRED"):
            raise ApiError(f"容器處理失敗：{st}（{url}）")
        time.sleep(10)
    raise ApiError("容器處理超過 10 分鐘仍未完成")


def check_public(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as r:
            if r.status == 200:
                return
    except urllib.error.URLError:
        pass
    raise ApiError(f"公開網址打不開：{url}\n→ 請確認 GitHub Pages 已開啟（Settings → Pages → main /docs），且網站已部署完成。")


def media(item):
    """把佇列項目換成要發的內容：(說明文字, [圖片或影片網址])。"""
    if "article" in item:
        i, a = ARTICLE[item["article"]]
        urls = [f"{BASE_URL}/ig/{i:02d}-{a['slug']}-{j}.jpg" for j in range(1, len(a["ig_slides"]) + 1)]
        # 臉書和 Threads 的連結點得開，用附網址的 Threads 版；IG 用說明文字版
        text = a["threads"] if item["platform"] in ("threads", "facebook") else a["ig_caption"]
        return text, urls
    r = REEL[item["reel"]]
    return r["caption"], [f"{BASE_URL}/reels/{r['slug']}.mp4"]


def post_instagram(item, token):
    text, urls = media(item)
    for u in urls:
        check_public(u)
    if DRY:
        return f"(試跑) IG {item['kind']}：{len(urls)} 個檔案，說明 {len(text)} 字"
    me = call("GET", f"{IG}/me", fields="user_id,username", access_token=token)
    uid = me["user_id"]
    if item["kind"] == "reel":
        cid = call("POST", f"{IG}/{uid}/media", media_type="REELS", video_url=urls[0], caption=text,
                   share_to_feed="true", access_token=token)["id"]
    else:
        kids = [call("POST", f"{IG}/{uid}/media", image_url=u, is_carousel_item="true", access_token=token)["id"] for u in urls]
        for k in kids:
            wait_ready(f"{IG}/{k}", token, "status_code")
        cid = call("POST", f"{IG}/{uid}/media", media_type="CAROUSEL", children=",".join(kids), caption=text,
                   access_token=token)["id"]
    wait_ready(f"{IG}/{cid}", token, "status_code")
    mid = call("POST", f"{IG}/{uid}/media_publish", creation_id=cid, access_token=token)["id"]
    return f"IG @{me.get('username')} 已發布，media id {mid}"


def post_threads(item, token):
    text, urls = media(item)
    assert len(text) <= 500, f"Threads 超過 500 字：{len(text)}"
    check_public(urls[0])
    if DRY:
        return f"(試跑) Threads：{len(text)} 字＋1 張圖"
    me = call("GET", f"{TH}/me", fields="id,username", access_token=token)
    params = {"media_type": "IMAGE", "image_url": urls[0], "text": text}
    if item["kind"] == "reel":
        params = {"media_type": "VIDEO", "video_url": urls[0], "text": text}
    cid = call("POST", f"{TH}/{me['id']}/threads", access_token=token, **params)["id"]
    wait_ready(f"{TH}/{cid}", token, "status")
    time.sleep(30)  # Threads 建議容器完成後再等一下才發布，太快會回「Media Not Found」
    mid = call("POST", f"{TH}/{me['id']}/threads_publish", creation_id=cid, access_token=token)["id"]
    return f"Threads @{me.get('username')} 已發布，id {mid}"


def post_facebook(item, token):
    """發到 Facebook 粉絲專頁：輪播→多圖貼文，Reels→影片。"""
    text, urls = media(item)
    for u in urls:
        check_public(u)
    page = call("GET", f"{FB}/me", fields="id,name,category", access_token=token)
    if page.get("name") != FB_PAGE_NAME:
        raise ApiError(
            f"權杖對應的是「{page.get('name')}」，不是粉專「{FB_PAGE_NAME}」，已中止，避免發到錯的帳號。\n"
            "→ 請在 me/accounts 的清單裡，找 name 是聯盟粉專的那一筆，複製它的 access_token。")
    if not page.get("category"):
        raise ApiError(
            f"權杖屬於個人帳號「{page.get('name')}」，不是粉絲專頁，發文會公開本名，已中止。\n"
            "→ 請照 SETUP-autopost.md「拿到永久的粉絲專頁權杖」第 3 步，改用 me/accounts 裡面粉專的 access_token。")
    if DRY:
        return f"(試跑) FB 粉專「{page['name']}」{item['kind']}：{len(urls)} 個檔案，說明 {len(text)} 字"
    if item["kind"] == "reel":
        vid = call("POST", f"{FB}/{page['id']}/videos", file_url=urls[0], description=text, access_token=token)["id"]
        return f"FB {page.get('name')} 已發布影片，id {vid}"
    photos = [call("POST", f"{FB}/{page['id']}/photos", url=u, published="false", access_token=token)["id"] for u in urls]
    attached = {f"attached_media[{i}]": json.dumps({"media_fbid": p}) for i, p in enumerate(photos)}
    pid = call("POST", f"{FB}/{page['id']}/feed", message=text, access_token=token, **attached)["id"]
    return f"FB {page.get('name')} 已發布，post id {pid}"


def post_youtube(item, refresh_token):
    """上傳 Reels 影片到 YouTube（直式、60 秒內會自動歸為 Shorts）。"""
    if item["kind"] != "reel":
        raise ApiError("YouTube 只能發影片（kind 要是 reel）")
    r = REEL[item["reel"]]
    path = os.path.join(ROOT, "docs", "reels", f"{r['slug']}.mp4")
    privacy = item.get("privacy", "public")
    title = item.get("title") or r.get("yt_title") or f"{r['title']} #Shorts"
    if DRY:
        return f"(試跑) YouTube：{os.path.getsize(path) // 1024} KB，標題「{title}」，{privacy}"
    tok = call("POST", "https://oauth2.googleapis.com/token", client_id=os.environ["YT_CLIENT_ID"],
               client_secret=os.environ["YT_CLIENT_SECRET"], refresh_token=refresh_token,
               grant_type="refresh_token")["access_token"]
    meta = {"snippet": {"title": title[:100], "description": r.get("yt_description", r["caption"]), "categoryId": "27",
                        "defaultLanguage": "zh-Hant", "tags": ["中華民國", "三民主義", "中華文化", "歷史"]},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    body = json.dumps(meta).encode()
    req = urllib.request.Request(YT_UPLOAD, data=body, method="POST", headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(os.path.getsize(path))})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            loc = resp.headers["Location"]
        with open(path, "rb") as f:
            up = urllib.request.Request(loc, data=f.read(), method="PUT", headers={
                "Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"})
        with urllib.request.urlopen(up, timeout=600) as resp:
            vid = json.load(resp)["id"]
    except urllib.error.HTTPError as e:
        raise ApiError(f"YouTube {e.code}\n{e.read().decode(errors='replace')}") from None
    return f"YouTube 已上傳（{privacy}），https://youtube.com/shorts/{vid}"


def x_weight(text):
    """X 的字數算法：中日韓文字算 2，其他算 1，上限 280。"""
    return sum(1 if ord(c) < 0x1100 else 2 for c in text)


def x_text(item):
    """X 版文字：不放網址（含網址的貼文 X 收費較高），超過 280 就截短。"""
    if item.get("text"):
        return item["text"]
    if "article" in item:
        _, a = ARTICLE[item["article"]]
        head, body, tags = a["title"], a.get("x") or a["ig_caption"], "#中華民國 #三民主義"
    else:
        r = REEL[item["reel"]]
        head, body, tags = r["title"], r.get("x") or r["caption"].split("\n\n")[0], "#中華民國 #" + r.get("series", "歷史")
    body = "\n".join(l for l in body.split("\n") if "http" not in l and not l.startswith("#"))
    room = 280 - x_weight(f"{head}\n\n\n\n{tags}") - 2
    if x_weight(body) > room:  # 截在最後一個句號或換行，避免斷在句子中間
        while x_weight(body) > room - 2:
            body = body[:-1]
        cut = max(body.rfind(c) for c in "。！？\n")
        body = (body[:cut + 1] if cut > 0 else body).rstrip() + "⋯"
    return f"{head}\n\n{body}\n\n{tags}" if body else f"{head}\n\n{tags}"


X_ACCT = "MAIN"


def oauth1(method, url, query=None):
    """X 的 OAuth 1.0a 簽章（API Key/Secret＋Access Token/Secret）。"""
    import base64, hashlib, hmac, secrets as sec
    ck, cs = os.environ["X_API_KEY"], os.environ["X_API_SECRET"]
    at, ats = os.environ[f"X_ACCESS_TOKEN_{X_ACCT}"], os.environ[f"X_ACCESS_SECRET_{X_ACCT}"]
    o = {"oauth_consumer_key": ck, "oauth_nonce": sec.token_hex(16), "oauth_signature_method": "HMAC-SHA1",
         "oauth_timestamp": str(int(time.time())), "oauth_token": at, "oauth_version": "1.0"}
    q = lambda v: urllib.parse.quote(str(v), safe="~")
    allp = {**o, **(query or {})}
    base = "&".join([method, q(url), q("&".join(f"{q(k)}={q(allp[k])}" for k in sorted(allp)))])
    o["oauth_signature"] = base64.b64encode(hmac.new(f"{q(cs)}&{q(ats)}".encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{k}="{q(v)}"' for k, v in sorted(o.items()))


def x_req(method, url, json_body=None, files=None, query=None):
    full = url + ("?" + urllib.parse.urlencode(query) if query else "")
    headers = {"Authorization": oauth1(method, url, query)}
    data = None
    if json_body is not None:
        data, headers["Content-Type"] = json.dumps(json_body).encode(), "application/json"
    elif files:
        b = "----roc" + str(int(time.time() * 1000))
        parts = []
        for k, v in files.items():
            if isinstance(v, bytes):
                parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="blob"\r\n'
                             f"Content-Type: application/octet-stream\r\n\r\n".encode() + v + b"\r\n")
            else:
                parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        data, headers["Content-Type"] = b"".join(parts) + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"
    try:
        with urllib.request.urlopen(urllib.request.Request(full, data=data, method=method, headers=headers), timeout=300) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if e.code in (401, 403):
            body += "\n→ 檢查 X 的四個金鑰是否正確、App 權限是否為 Read and Write（改權限後要重新產生 Access Token），以及帳戶是否已儲值。"
        raise ApiError(f"X {e.code} {url}\n{body}") from None


def x_upload(path, mime, category):
    """X v2 分段上傳圖片或影片，回傳 media id。"""
    X2 = "https://api.x.com/2/media/upload"
    size = os.path.getsize(path)
    mid = x_req("POST", f"{X2}/initialize", {"media_type": mime, "total_bytes": size, "media_category": category})["data"]["id"]
    with open(path, "rb") as f:
        i = 0
        while chunk := f.read(4 * 1024 * 1024):
            x_req("POST", f"{X2}/{mid}/append", files={"segment_index": str(i), "media": chunk})
            i += 1
    info = x_req("POST", f"{X2}/{mid}/finalize").get("data", {}).get("processing_info")
    for _ in range(60):
        if not info or info.get("state") == "succeeded":
            return mid
        if info.get("state") == "failed":
            raise ApiError(f"X 影片處理失敗：{info}")
        time.sleep(info.get("check_after_secs", 5))
        info = x_req("GET", X2, query={"command": "STATUS", "media_id": mid}).get("data", {}).get("processing_info")
    raise ApiError("X 影片處理超過時間")


def post_x(item, token):
    """發到 X：Reels→影片，輪播→最多 4 張圖。token 只用來確認已設定。"""
    global X_ACCT
    X_ACCT = item["account"].upper()
    text = x_text(item)
    if "article" in item:
        i, a = ARTICLE[item["article"]]
        files = [(os.path.join(ROOT, "docs", "ig", f"{i:02d}-{a['slug']}-{j}.jpg"), "image/jpeg", "tweet_image")
                 for j in range(1, min(len(a["ig_slides"]), 4) + 1)]
    else:
        files = [(os.path.join(ROOT, "docs", "reels", f"{item['reel']}.mp4"), "video/mp4", "tweet_video")]
    if DRY:
        return f"(試跑) X：{len(files)} 個檔案，文字 {x_weight(text)}/280\n{text}"
    ids = [x_upload(*f) for f in files]
    tid = x_req("POST", "https://api.x.com/2/tweets", {"text": text, "media": {"media_ids": ids}})["data"]["id"]
    return f"X 已發布，https://x.com/i/status/{tid}"


def post_tiktok(item, refresh_token):
    """上傳 Reels 到 TikTok。App 通過 TikTok 審核前只能發「僅自己可見」。"""
    if item["kind"] != "reel":
        raise ApiError("TikTok 目前只發影片（kind 要是 reel）")
    r = REEL[item["reel"]]
    path = os.path.join(ROOT, "docs", "reels", f"{r['slug']}.mp4")
    privacy = item.get("privacy", "SELF_ONLY")
    TT = "https://open.tiktokapis.com/v2"
    tok = call("POST", f"{TT}/oauth/token/", client_key=os.environ["TIKTOK_CLIENT_KEY"],
               client_secret=os.environ["TIKTOK_CLIENT_SECRET"], grant_type="refresh_token",
               refresh_token=refresh_token)
    if "access_token" not in tok:
        raise ApiError(f"TikTok 換權杖失敗：{tok}\n→ refresh token 一年後會過期，請照 SETUP-autopost.md 的 TikTok 第 4 步重新取得。")

    def tt(endpoint, body):
        req = urllib.request.Request(f"{TT}{endpoint}", data=json.dumps(body).encode(), method="POST", headers={
            "Authorization": f"Bearer {tok['access_token']}", "Content-Type": "application/json; charset=UTF-8"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                out = json.load(resp)
        except urllib.error.HTTPError as e:
            raise ApiError(f"TikTok {e.code} {endpoint}\n{e.read().decode(errors='replace')}") from None
        if out.get("error", {}).get("code") not in (None, "ok"):
            raise ApiError(f"TikTok {endpoint}：{out['error']}")
        return out.get("data", {})

    info = tt("/post/publish/creator_info/query/", {})
    if privacy not in info.get("privacy_level_options", []):
        raise ApiError(f"TikTok 不允許 {privacy}，可用：{info.get('privacy_level_options')}（App 未過審前只能 SELF_ONLY）")
    size = os.path.getsize(path)
    if DRY:
        return f"(試跑) TikTok @{info.get('creator_username')}：{size // 1024} KB，{privacy}"
    d = tt("/post/publish/video/init/", {
        "post_info": {"title": r["caption"][:2000], "privacy_level": privacy, "disable_duet": False,
                      "disable_comment": False, "disable_stitch": False},
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}})
    with open(path, "rb") as f:
        up = urllib.request.Request(d["upload_url"], data=f.read(), method="PUT", headers={
            "Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"})
    try:
        urllib.request.urlopen(up, timeout=600).read()
    except urllib.error.HTTPError as e:
        raise ApiError(f"TikTok 上傳失敗 {e.code}\n{e.read().decode(errors='replace')}") from None
    for _ in range(60):
        st = tt("/post/publish/status/fetch/", {"publish_id": d["publish_id"]})
        if st.get("status") == "PUBLISH_COMPLETE":
            return f"TikTok 已發布（{privacy}），publish id {d['publish_id']}"
        if st.get("status") == "FAILED":
            raise ApiError(f"TikTok 發布失敗：{st}")
        time.sleep(10)
    return f"TikTok 已上傳，處理中（{privacy}），publish id {d['publish_id']}"


# platform → (權杖環境變數前綴, 發文函式)
PLATFORMS = {
    "instagram": ("IG_TOKEN", post_instagram),
    "threads": ("THREADS_TOKEN", post_threads),
    "facebook": ("FB_PAGE_TOKEN", post_facebook),
    "youtube": ("YT_REFRESH_TOKEN", post_youtube),
    "x": ("X_ACCESS_TOKEN", post_x),
    "tiktok": ("TIKTOK_REFRESH_TOKEN", post_tiktok),
}


def main():
    queue = json.load(open(os.path.join(ROOT, "queue.json")))
    posted_path = os.path.join(ROOT, "posted.json")
    posted = json.load(open(posted_path)) if os.path.exists(posted_path) else {}
    now = datetime.now(timezone.utc)
    failed = False
    if DRY:  # 試跑時先確認每組臉書權杖對到哪個粉專，即使沒有待發項目
        for k, v in sorted(os.environ.items()):
            if k.startswith("FB_PAGE_TOKEN_") and v:
                try:
                    pg = call("GET", f"{FB}/me", fields="id,name,category", access_token=v)
                    ok = pg.get("name") == FB_PAGE_NAME and pg.get("category")
                    print(f"{'✓' if ok else '✗'} {k} 對應粉專「{pg.get('name')}」（{pg.get('category') or '不是粉專'}）")
                    failed |= not ok
                except ApiError as e:
                    print(f"✗ {k}：{e}")
                    failed = True
    for item in sorted(queue, key=lambda x: x["at"]):
        iid = item["id"]
        if iid in posted or not item.get("approved"):
            continue
        if datetime.fromisoformat(item["at"]) > now and not DRY:  # 試跑時連未到時間的也檢查
            continue
        if item.get("expires") and datetime.fromisoformat(item["expires"]) < now:
            print(f"略過 {iid}：已過期（{item['expires']}）")
            continue
        prefix, fn = PLATFORMS[item["platform"]]
        token = os.environ.get(f"{prefix}_{item['account'].upper()}")
        if not token:
            print(f"{'注意' if DRY else '略過'} {iid}：還沒設定 {prefix}_{item['account'].upper()}")
            if not DRY:
                continue
        try:
            msg = fn(item, token)
            print(f"✓ {iid}：{msg}")
            if not DRY:
                posted[iid] = {"at": now.isoformat(timespec="seconds"), "result": msg}
                json.dump(posted, open(posted_path, "w"), ensure_ascii=False, indent=2)
        except (ApiError, AssertionError) as e:
            failed = True
            print(f"✗ {iid} 失敗：{e}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
