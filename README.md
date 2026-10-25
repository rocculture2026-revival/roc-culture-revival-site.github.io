# 中華民國文化復興聯盟：網站與社群帳號計畫

民國115年10月25日初稿。

## 一、資料夾內容

| 路徑 | 用途 |
|---|---|
| `content.py` | 所有文章的唯一來源。每篇有網站全文、IG 輪播文字與說明、Threads 貼文三個版本 |
| `build.py` | 執行 `python3 build.py`，重新產生下面三樣東西 |
| `docs/index.html` | 網站本體，GitHub Pages 從 `docs/` 發布 |
| `posts/*.md` | 每篇文章的 IG 說明與 Threads 貼文稿，可直接複製貼上 |
| `docs/ig/*.jpg` | IG 輪播圖，1080×1350（4:5 直式），每篇 4 張 |

## 二、網站架構與技術選項

**建議：GitHub Pages＋純靜態 HTML（目前做法）。** 免費、不用主機、不用資料庫，換自己的網域也只要設定 DNS。內容由 `content.py` 產生，沒有建置工具要學。

其他選項，等文章超過 20 篇再考慮：

| 選項 | 優點 | 缺點 |
|---|---|---|
| GitHub Pages＋Hugo／Astro | 文章用 Markdown 寫，自動分頁、標籤、RSS | 要學建置工具 |
| WordPress.com | 有後台，非技術成員也能發文 | 免費版有廣告，自訂網域要付費 |
| Cloudflare Pages | 與 GitHub Pages 相同，但在臺灣連線通常較快 | 要多開一個帳號 |

網站結構（第一版為單頁，以錨點切換）：報頭（名稱、民國紀年、IG／Threads 連結）→ 關於聯盟 → 文章目錄 → 各篇全文 → 頁尾立場聲明。

**網址：** https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io/ （GitHub Pages，來源為 main 分支的 `docs/` 資料夾）。IG 圖的公開網址為 `…/ig/<檔名>.jpg`，可直接給 Graph API 用。

## 三、IG 與 Threads 帳號

### 帳號名稱（Threads 會沿用 IG 的帳號名稱）

依序嘗試，第一個能用的就用；註冊後若名稱不同，改 `build.py` 裡的 `HANDLE` 再重新產生。

1. `roc.revival`
2. `roc_revival`
3. `rocrevival.tw`
4. `roc.culture.revival`

顯示名稱：**中華民國文化復興聯盟**

### 簡介（IG 上限 150 字，Threads 上限 150 字）

```
民間自發團體｜傳承中華民國正統・重讀三民主義・守護自由
引用必附出處，文章皆為本聯盟立場
與任何政府機關、政黨無隸屬關係
```

連結欄位填網站網址。

### 視覺建議

- **大頭貼：** 五瓣梅花（國花）置中，深藍底、梅紅花瓣、白色花心。網站與 IG 圖已用同一個梅花圖形。
- **避免用國徽（青天白日徽）當標誌。** 《國徽國旗法》對國徽使用有限制，而且容易讓人誤以為是政府帳號。國旗可以在貼文內容中出現，但不建議當大頭貼。
- **配色：** 深藍 `#1b2a5c`、梅紅 `#b8232f`、淺灰白 `#f4f5f7`。
- **字體：** 標題用思源宋體（Noto Serif TC）粗體，內文用思源黑體（Noto Sans TC），兩者都免費可商用。
- **版型：** 每組輪播第 1 張深藍封面，其餘淺色內文，右下角標頁碼，左下角標聯盟名稱。

### 註冊注意事項

1. 先註冊 IG，到「設定 → 帳號類型和工具 → 切換為專業帳號」，選「創作者」或「商家」。政治倡議團體選「創作者」類別較單純。
2. 用同一個 IG 帳號登入 Threads App 建立個人檔案。
3. 開啟兩步驟驗證。帳號密碼不要給任何人，包括我。
4. 跟政治或社會議題相關的**付費廣告**，Meta 要求先完成身分驗證並加上「出資者」標示。單純發文不需要。
5. Meta 預設會減少對非追蹤者推薦政治內容。初期成長主要靠分享與標籤，這點先有心理準備。

## 四、之後用 Graph API 自動發文需要什麼

兩個平台的 API 都只能發到你自己擁有、且在 Meta 開發者應用程式中有角色的帳號。只發自己帳號的話，應用程式維持「開發模式」即可，不需要送審。

### 共同前置

1. 到 developers.facebook.com 註冊開發者帳號，建立一個應用程式。
2. 把聯盟的 IG 帳號加為該應用程式的測試人員（Threads 同樣要加為 Threads 測試人員），並在 App 裡接受邀請。

### Instagram（用「Instagram 登入」的版本，不需要 Facebook 粉專）

| 項目 | 內容 |
|---|---|
| 權限 | `instagram_business_basic`、`instagram_business_content_publish` |
| 權杖 | 先拿短效權杖（1 小時），換成長效權杖（60 天），到期前呼叫 refresh 端點延長 |
| 需要的 ID | IG 使用者 ID |
| 發輪播流程 | 每張圖建立一個 `is_carousel_item` 容器 → 建立 `CAROUSEL` 容器 → `media_publish` |
| 限制 | 圖片必須是**公開網址上的 JPEG**（可放在 GitHub Pages 的 `ig/` 資料夾）；24 小時內透過 API 發文有數量上限 |

若改走「Facebook 登入」的版本，則需要一個連結的 Facebook 粉絲專頁，權限改為 `instagram_basic`、`instagram_content_publish`、`pages_show_list`、`pages_read_engagement`。

### Threads

| 項目 | 內容 |
|---|---|
| 權限 | `threads_basic`、`threads_content_publish`（要回覆留言再加 `threads_manage_replies`） |
| 權杖 | 同樣是短效換長效（60 天），可 refresh |
| 發文流程 | 建立容器（`media_type=TEXT` 或 `IMAGE`）→ 等約 30 秒 → `threads_publish` |
| 限制 | 單篇 500 字；24 小時內有發文數量上限 |

### 權杖怎麼交給自動化

權杖等同帳號密碼，**不要貼在對話或寫進程式碼**。之後做自動發文時，把權杖存成 GitHub 儲存庫的 Secrets（例如 `IG_TOKEN`、`IG_USER_ID`、`THREADS_TOKEN`、`THREADS_USER_ID`），由 GitHub Actions 讀取並排程發文，也順便每月自動 refresh 權杖。

> API 的確切額度與權限名稱 Meta 會調整，實際申請時以 developers.facebook.com 上的文件為準。

## 五、內容原則（每篇都要過一次）

- 每篇結尾標示「本文為中華民國文化復興聯盟立場」。
- 引用原文（例如孫文演講、憲法條文）要附出處；年份與事件以總統府、國史館等公開資料為準。
- 不冒用任何個人或機構名義；提到「中華文化總會」等相近名稱的團體時，說明無隸屬關係。
- 批評對象是制度與政策，不針對民族或個人。
