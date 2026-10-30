# 自動發文設定教學

做完一次之後，GitHub 每 30 分鐘會檢查 `queue.json`，把到時間的貼文自動發到 IG 和 Threads。全程大約 30～40 分鐘。

> Meta 後台的按鈕名稱常常改版，下面寫的名稱可能和你看到的略有不同。卡住時截圖給 Claude 看就好。

## 第 0 步：確認前置條件

- [ ] GitHub Pages 已開啟（儲存庫 Settings → Pages → `main`、`/docs`）。IG 和 Threads 會從網站抓圖片和影片，網站沒開就發不出去。
- [ ] IG 帳號已切換成**專業帳號**（創作者或商家）：IG App → 設定 → 帳號類型和工具 → 切換為專業帳號。
- [ ] 已用同一個 IG 帳號登入 Threads App，建立 Threads 個人檔案。

## 第 1 步：建立 Meta 開發者帳號

1. 打開 https://developers.facebook.com ，右上角「Get Started / 開始使用」。
2. 這一步需要用一個 Facebook 帳號登入。**為了匿名，建議另外註冊一個 Facebook 帳號專門用來管開發者後台**，不要用你個人的帳號。開發者帳號和 IG 之間的關聯不會公開顯示，外人看不到。
3. 依指示驗證手機或信箱，完成註冊。

## 第 2 步：建立 Instagram 用的應用程式

1. 後台首頁「My Apps / 我的應用程式」→「Create App / 建立應用程式」。
2. 名稱隨意，例如 `roc-autopost`。
3. 「用途（Use case）」選 **「Manage messaging & content on Instagram」**（管理 Instagram 上的訊息和內容）。
4. 不用連結商家資產組合（Business portfolio），選「I don't want to connect…」略過。
5. 建好後，左側選單會出現「Instagram」→「API setup with Instagram login」（使用 Instagram 登入的 API 設定）。

## 第 3 步：產生 IG 權杖

1. 在「API setup with Instagram login」頁面，找到 **「Generate access tokens」（產生存取權杖）**，按「Add account」。
2. 跳出 IG 登入視窗，登入**聯盟的 IG 帳號**，允許權限。畫面上應該會列出 `instagram_business_basic`、`instagram_business_content_publish` 這兩個權限，都要允許。
   - 如果它說帳號沒有權限：到左側「App roles / 應用程式角色」→「Roles」→「Add People」→ 選「Instagram Tester」，輸入聯盟 IG 帳號名稱。然後在 IG App 裡「設定 → 網站權限 → 應用程式和網站 → 測試人員邀請」按接受，再回來重做一次。
3. 帳號加好之後，旁邊有「Generate token」，按下去複製那串很長的權杖。**這串就是 `IG_TOKEN_MAIN`。**它是長效權杖，效期 60 天。
4. 先貼到記事本暫存，下一步會用到。不要貼到聊天室裡。

## 第 4 步：產生 Threads 權杖

Threads 用途通常不能和 Instagram 用途放在同一個應用程式，所以**再建一個應用程式**。

1. 「Create App」→ 名稱例如 `roc-threads`→ 用途選 **「Access the Threads API」**（存取 Threads API）。
2. 進入應用程式後，左側選「Use cases / 使用案例」→ Threads 旁的「Customize / 自訂」→「Permissions / 權限」，確認 `threads_basic` 和 `threads_content_publish` 都有加入。
3. 「App roles / 應用程式角色」→「Roles」→「Add People」→ 選「Threads Tester」，輸入聯盟的 Threads 帳號名稱。
4. 到 Threads App：「設定 → 帳號 → 網站權限 → 邀請」，接受邀請。
5. 回到後台 Threads 用途的「Settings / 設定」頁，找「User Token Generator」或「Generate access token」，選聯盟帳號產生權杖。
   - 找不到產生器的話：用 Graph API Explorer（後台上方「Tools → Graph API Explorer」），右側「Meta App」選 `roc-threads`，網域切到 `threads.net`，勾 `threads_basic`、`threads_content_publish`，按「Generate Access Token」。
6. 用這個方法拿到的通常是**短效權杖（1 小時）**，要換成 60 天的長效權杖。把下面網址的兩個 `…` 換掉，貼到瀏覽器打開：
   ```
   https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=…應用程式密鑰…&access_token=…短效權杖…
   ```
   應用程式密鑰在後台「App settings → Basic → App secret」。畫面顯示的 `access_token` 就是**長效權杖，也就是 `THREADS_TOKEN_MAIN`**。

## 第 5 步：把權杖放進 GitHub Secrets

1. 打開儲存庫 → **Settings → Secrets and variables → Actions → New repository secret**。
2. 新增兩個：
   | Name | Secret |
   |---|---|
   | `IG_TOKEN_MAIN` | 第 3 步的 IG 權杖 |
   | `THREADS_TOKEN_MAIN` | 第 4 步的 Threads 長效權杖 |
3. 存好之後把記事本裡的權杖刪掉。Secrets 存進去以後，連你自己都看不到內容，只能覆蓋。

之後開宣傳部帳號時，重複第 3、4 步，名稱改成 `IG_TOKEN_PROMO`、`THREADS_TOKEN_PROMO`。

## 第 6 步：試跑

1. 儲存庫 →「Actions」→ 左邊選「publish」→ 右邊「Run workflow」。
2. 「試跑」保持勾選，按綠色「Run workflow」。
3. 一分鐘後點進去看紀錄：
   - 看到 `(試跑) IG carousel：4 個檔案…` 就是成功。
   - 看到「略過…還沒設定 IG_TOKEN_MAIN」：Secret 名稱打錯了。
   - 看到「公開網址打不開」：GitHub Pages 還沒開或還沒部署完成。

試跑只檢查網站上的檔案，不會碰 IG，所以權杖是否正確要等第一則真正發出去才知道。

## 第 7 步：正式上線

不用做任何事。排程每 30 分鐘跑一次，到時間就會發。也可以手動「Run workflow」並**取消勾選**「試跑」，立刻發出所有已經到時間的貼文。

發出去的貼文會記在 `posted.json`，同一則不會重發。如果某則失敗，紀錄裡會寫原因，下一輪會自動再試。

## 日常使用

### 排程在哪裡：`queue.json`

每一則是一行：

```json
{"id": "02-three-principles-ig", "at": "2026-10-26T20:00:00+08:00", "account": "main",
 "platform": "instagram", "kind": "carousel", "article": "three-principles", "approved": true}
```

| 欄位 | 意思 |
|---|---|
| `at` | 發文時間（`+08:00` 是臺灣時間）。排程實際可能晚 5～30 分鐘 |
| `account` | `main` 本部、`promo` 宣傳部 |
| `platform` | `instagram` 或 `threads` |
| `kind` | `carousel` 輪播圖、`reel` 短影音、`image` Threads 圖文 |
| `approved` | **`true` 才會發。**每週 Claude 排好的新貼文會先設成 `false`，你看過稿、回覆 OK 後才改成 `true` |
| `expires` | 選填。過了這個時間就不發，用在「今天是光復節」這種有時效的貼文 |

要暫停某一則：把它的 `approved` 改成 `false`。要全部暫停：Actions → publish → 右上「⋯」→「Disable workflow」。

### 權杖每 60 天要換一次

長效權杖 60 天後失效。建議每 50 天重做第 3、4 步，然後在 Secrets 用同樣的名稱覆蓋。權杖過期時，Actions 會失敗，GitHub 也會寄信通知你。

---

# 加開 Facebook 粉絲專頁與 YouTube 頻道

`publish.py` 已經支援這兩個平台，`queue.json` 裡把 `platform` 設成 `facebook` 或 `youtube` 就能發。

## Facebook 粉絲專頁

API 只能發到**粉絲專頁**，不能發到個人帳號，所以要開的是粉絲專頁。

### 1. 建立粉絲專頁

1. 用你建 Meta 開發者帳號的那個**新 Facebook 帳號**登入（不要用個人帳號）。
2. 左側選單「粉絲專頁」→「建立新的粉絲專頁」。名稱填「中華民國文化復興聯盟」，類別選「社群組織」或「非營利組織」。
3. 粉絲專頁不會公開顯示管理員是誰，外人只看得到專頁的建立日期和管理員所在國家。

### 2. 讓應用程式可以管理粉絲專頁

1. 開發者後台 → 你的 IG 應用程式 →「Use cases / 使用案例」→「Add use case」，選 **「Manage everything on your Page」**（管理粉絲專頁上的所有內容）。如果不能加在同一個應用程式，就另建一個應用程式選這個用途。
2. 確認權限包含 `pages_show_list`、`pages_read_engagement`、`pages_manage_posts`。

### 3. 拿到永久的粉絲專頁權杖

1. 後台上方「Tools → Graph API Explorer」。右側「Meta App」選這個應用程式；「User or Page」選「Get User Access Token」，勾選上面三個權限，按「Generate Access Token」並同意。
2. 這是 1 小時的短效權杖。把下面網址的三個 `…` 換掉，貼到瀏覽器打開，換成 60 天的長效使用者權杖：
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=…應用程式編號…&client_secret=…應用程式密鑰…&fb_exchange_token=…短效權杖…
   ```
3. 再打開這個網址（`…` 換成上一步的長效權杖）：
   ```
   https://graph.facebook.com/v21.0/me/accounts?access_token=…長效權杖…
   ```
   畫面會列出你的粉絲專頁，裡面的 `access_token` 就是**粉絲專頁權杖，不會過期**。
4. 存成 GitHub Secret：`FB_PAGE_TOKEN_MAIN`。
5. 想確認的話，把它貼到「Tools → Access Token Debugger」，「Expires」應該顯示「Never」。

## YouTube 頻道

### 1. 建立頻道

1. 註冊一個**新的 Google 帳號**（新 Gmail），不要用個人帳號。
2. 登入 YouTube → 右上頭像 →「建立頻道」。名稱填「中華民國文化復興聯盟」，帳號代碼（@）建議和 IG 一致，例如 `@roc_culture_revival`。

### 2. 建立 Google Cloud 專案並開啟 YouTube API

1. 用同一個 Google 帳號打開 https://console.cloud.google.com ，建立新專案，例如 `roc-autopost`。
2. 「API 和服務 → 程式庫」，搜尋 **YouTube Data API v3**，按「啟用」。
3. 「API 和服務 → OAuth 同意畫面」：使用者類型選「外部」，應用程式名稱隨意，支援信箱填新 Gmail。
   - 範圍（Scopes）加入 `https://www.googleapis.com/auth/youtube.upload`。
   - 「測試使用者」加入你的新 Gmail。
   - **最後按「發布應用程式」改成「正式版」。**維持「測試中」的話，權杖每 7 天就會失效。發布時會說應用程式未經驗證，自己用沒關係，不需要送審。
4. 「API 和服務 → 憑證 → 建立憑證 → OAuth 用戶端 ID」：類型選「網頁應用程式」，「已授權的重新導向 URI」加入 `https://developers.google.com/oauthplayground`。建好後記下**用戶端 ID** 和**用戶端密鑰**。

### 3. 拿到 refresh token（長期有效）

1. 打開 https://developers.google.com/oauthplayground 。
2. 右上齒輪 → 勾「Use your own OAuth credentials」，貼上用戶端 ID 和密鑰。
3. 左邊最下面「Input your own scopes」輸入 `https://www.googleapis.com/auth/youtube.upload`，按「Authorize APIs」，用新 Gmail 登入並允許。看到「Google 尚未驗證這個應用程式」時，按「進階 → 前往（不安全）」，因為這是你自己的應用程式。
4. 按「Exchange authorization code for tokens」，複製 **Refresh token**。

### 4. 存進 GitHub Secrets

| Name | Secret |
|---|---|
| `YT_CLIENT_ID` | 用戶端 ID |
| `YT_CLIENT_SECRET` | 用戶端密鑰 |
| `YT_REFRESH_TOKEN_MAIN` | Refresh token |

### 重要限制：新專案上傳的影片會被設成「私人」

Google 規定，2020 年 7 月以後建立、還沒通過稽核的 API 專案，用 API 上傳的影片一律只能是**私人**影片。所以一開始的流程是：

1. 自動上傳成私人影片。
2. 你到 YouTube Studio 把它改成「公開」，一則大約 10 秒。

想完全自動，要向 Google 申請 API 稽核（YouTube API Services Audit），通常要幾週。頻道穩定後我可以幫你準備申請資料。

`queue.json` 的 YouTube 項目可以加 `"privacy": "private"`（預設是 public，但未稽核前一律會變私人）和 `"title"`（不填就用 Reels 標題加 #Shorts）。

---

# 加開 X 與 TikTok

兩邊的金鑰一樣只放 GitHub Secrets（儲存庫 → Settings → Secrets and variables → Actions → New repository secret），不要貼到聊天裡。

## X（推特）

**先知道費用**：X 從 2026 年起不再有免費發文額度，改成用多少付多少，要先儲值。發一則一般貼文大約 US$0.015，含網址的貼文大約 US$0.20，所以程式發到 X 的內容一律不放網址。一天兩三則，一個月大約 US$1～2。

1. 用聯盟的 X 帳號登入 https://developer.x.com ，申請開發者帳號。用途照實寫：「發布本團體自己製作的歷史與文化教育內容到本團體自己的帳號，不讀取其他使用者資料」。
2. 到帳務（Billing）頁面儲值，最低金額就好（例如 US$5～10）。**把自動加值關掉，或設一個每月花費上限**，避免被自動扣大筆金額。
3. 在你的 App 裡找「User authentication settings → Set up」：
   - App permissions：**Read and write**
   - Type of App：**Web App, Automated App or Bot**
   - Callback URI 和 Website URL 都填：https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io/
4. 到「Keys and tokens」：
   - Consumer Keys 的 **API Key** 和 **API Key Secret** → 按 Regenerate，各存一份
   - Authentication Tokens 的 **Access Token** 和 **Access Token Secret** → 按 Generate，確認下面寫的是「Read and Write」
   （一定要先做第 3 步再產生 Access Token，不然權限只有唯讀，要重新產生。）
5. 存進 GitHub Secrets（名稱要一字不差）：
   - `X_API_KEY`、`X_API_SECRET`
   - `X_ACCESS_TOKEN_MAIN`、`X_ACCESS_SECRET_MAIN`
6. 跟 Claude 說「X 設好了」，我會先試跑，再把貼文排進佇列。

## TikTok

**先知道限制**：TikTok 的發文 API 要先通過 TikTok 審核。審核通過前，程式發出去的影片只會是「僅自己可見」，所以這段期間照樣手動上傳，自動發的只當測試。

1. 用聯盟的 TikTok 帳號（或聯盟 Gmail）登入 https://developers.tiktok.com ，建立開發者帳號。
2. 「Manage apps → Connect an app」建立 App：
   - App 名稱：中華民國文化復興聯盟發文工具
   - App icon：用本部頭貼（/mnt/project-files/roc-revival/profile/頭貼-本部.jpg）
   - Category：Education
   - Description：Publishes short history and culture videos made by our organization to our own TikTok account. No other users' data is accessed.
   - Terms of Service URL：https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io/terms.html
   - Privacy Policy URL：https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io/privacy.html
   - Platforms：勾 Web，網址填 https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io/
3. 「Add products」加入兩個：
   - **Login Kit**：Redirect URI 填 `https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io/tiktok-callback.html`
   - **Content Posting API**：打開 **Direct Post**
   - Scopes 確認有 `user.info.basic` 和 `video.publish`
4. 把 App 頁面上的 **Client key**、**Client secret** 存進 GitHub Secrets：`TIKTOK_CLIENT_KEY`、`TIKTOK_CLIENT_SECRET`。
5. 審核前要先把聯盟的 TikTok 帳號加成測試帳號：App 頁面切到 **Sandbox**，在「Target users」加入聯盟帳號。
6. 拿 refresh token（一年有效）：
   - 用電腦打開 https://rocculture2026-revival.github.io/roc-culture-revival-site.github.io/tiktok-callback.html
   - 貼上 Client key → 前往授權 → 用聯盟帳號登入並同意
   - 回到頁面後照畫面上的指令做，把拿到的 refresh_token 存成 `TIKTOK_REFRESH_TOKEN_MAIN`
7. 跟 Claude 說「TikTok 設好了」，我會先發一支「僅自己可見」的測試影片。成功後你把那支測試的畫面錄下來，跟 App 一起送審（「Submit for review」），審核通過後就能公開發。
