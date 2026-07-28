# Changelog

## V0.1.1 - 2026-07-28

### Fixed
- 修正Realtek/Boa舊Webserver直接以HTML開頭、缺少標準HTTP Status Line時，Python requests發生 `BadStatusLine`。
- 新增Legacy Raw TLS/HTTP 1.0備援傳輸。
- 強制 `Connection: close`。
- 停用系統Proxy繼承。
- Debug Log會標示是否啟用Legacy Transport。

## V0.1.0 - 2026-07-28

### Added
- Router IP、Protocol、帳號、密碼、Timeout、識別碼及輸出資料夾GUI。
- Realtek Router登入流程。
- 動態CSRF Token解析。
- Base64密碼處理。
- `postSecurityFlag` JavaScript相容Checksum。
- Device Status、LAN及WAN解析。
- Excel、JSON、Execution Log、Test Log、Debug Log及原始HTML。
- 敏感資料遮蔽。
- Parser與Checksum離線單元測試。
