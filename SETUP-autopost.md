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
