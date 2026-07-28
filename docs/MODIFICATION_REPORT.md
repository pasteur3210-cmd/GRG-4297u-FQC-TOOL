# 修改報告

- 版本：V0.1.0
- 日期：2026-07-28
- 修改類型：初版建立

## 需求
1. 每台Router可輸入不同帳號與密碼。
2. 自動登入並取得Device Status。
3. 保留執行記錄、Test Log及Debug Record。
4. 每版保留修改、查核及驗證紀錄。

## 實作
- GUI不保存密碼，執行後清空。
- 登入時動態取得CSRF Token。
- Python重現Router `postTableEncrypt()` Checksum。
- Status解析依欄位名稱，不依固定列號。
- WAN表格增加不完整HTML備援解析。
- 報表輸出為Excel及JSON。

## V0.1.1修正

### 問題
實機回傳HTML時缺少標準HTTP Status Line，Python `http.client`拋出：
`BadStatusLine: <HTML lang='en'><HEAD><TITLE>Login</TITLE></HEAD>`

### 根因
這是舊版Realtek/Boa Webserver的非標準HTTP/0.9風格回應，不是帳號、密碼或TLS憑證錯誤。

### 修正
1. requests預設Headers改成接近Edge。
2. 強制Connection close。
3. Session不繼承Windows Proxy。
4. 捕捉BadStatusLine後切換Raw TLS + HTTP/1.0。
5. Legacy模式接受直接以HTML開頭的回應。
6. Cookie與Location Header在存在時仍會處理。
