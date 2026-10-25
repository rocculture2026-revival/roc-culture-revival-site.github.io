"""依 queue.json 把到時間、已核准的貼文發到 Instagram 與 Threads。由 .github/workflows/publish.yml 定時執行。

用法：python3 publish.py [--dry-run]
權杖從環境變數讀：IG_TOKEN_<帳號>、THREADS_TOKEN_<帳號>（例如 IG_TOKEN_MAIN）。
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
DRY = "--dry-run" in sys.argv

ARTICLE = {a["slug"]: (i, a) for i, a in enumerate(ARTICLES, 1)}
REEL = {r["slug"]: r for r in REELS}


class ApiError(Exception):
    pass


def call(method, url, **params):
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if "access token" in body.lower() or "OAuthException" in body:
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
        text = a["threads"] if item["platform"] == "threads" else a["ig_caption"]
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
    mid = call("POST", f"{TH}/{me['id']}/threads_publish", creation_id=cid, access_token=token)["id"]
    return f"Threads @{me.get('username')} 已發布，id {mid}"


def main():
    queue = json.load(open(os.path.join(ROOT, "queue.json")))
    posted_path = os.path.join(ROOT, "posted.json")
    posted = json.load(open(posted_path)) if os.path.exists(posted_path) else {}
    now = datetime.now(timezone.utc)
    failed = False
    for item in sorted(queue, key=lambda x: x["at"]):
        iid = item["id"]
        if iid in posted or not item.get("approved"):
            continue
        if datetime.fromisoformat(item["at"]) > now and not DRY:  # 試跑時連未到時間的也檢查
            continue
        if item.get("expires") and datetime.fromisoformat(item["expires"]) < now:
            print(f"略過 {iid}：已過期（{item['expires']}）")
            continue
        prefix = "IG_TOKEN" if item["platform"] == "instagram" else "THREADS_TOKEN"
        token = os.environ.get(f"{prefix}_{item['account'].upper()}")
        if not token:
            print(f"{'注意' if DRY else '略過'} {iid}：還沒設定 {prefix}_{item['account'].upper()}")
            if not DRY:
                continue
        try:
            fn = post_instagram if item["platform"] == "instagram" else post_threads
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
