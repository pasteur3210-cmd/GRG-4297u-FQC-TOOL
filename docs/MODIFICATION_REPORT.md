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
