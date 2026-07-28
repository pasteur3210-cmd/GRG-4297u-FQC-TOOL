# Router OQC Status Tool V0.1.0

## 功能

- GUI輸入Router IP、Protocol、Username、Password、Timeout及測試識別碼
- 每次重新取得登入頁 `csrftoken`
- 密碼依Router登入頁邏輯轉成Base64
- 依 `common.js / postTableEncrypt()` 計算 `postSecurityFlag`
- 使用 `requests.Session()` 自動登入
- 自動讀取 `/status.asp`
- 解析System、LAN及WAN Status
- 產生：
  - `result.xlsx`
  - `result.json`
  - `execution.log`
  - `test.log`
  - `debug.log`
  - `raw/status_page.html`
- Log不保存明文密碼、Base64密碼、Token或Cookie值

## Windows執行

1. 安裝Python 3.11或3.12。
2. 在本專案資料夾開啟PowerShell。
3. 執行：

```powershell
py -m pip install -r requirements.txt
py main.py
```

## 測試

```powershell
py -m unittest discover -s tests -v
```

## 注意

- Router預設為自簽HTTPS憑證，本工具V0.1.0對指定Router連線使用 `verify=False`。
- Status頁可能每10秒在瀏覽器自動刷新；本工具只做單次HTTP GET。
- 此版本不修改Router設定。
- 此版本尚未加入GPON、WLAN、LAN Port測試及出貨資料比對。
- 密碼欄位每次執行後會清空，不儲存於設定檔。
