# 驗證報告

## 已完成的離線驗證
- Golden Sample `postSecurityFlag = 22879`：PASS
- Device Name解析：PASS
- Serial Number解析：PASS
- CPU / Memory `aria-valuenow`解析：PASS
- LAN MAC格式正規化：PASS
- WAN缺少開頭`<tr>`的備援解析：PASS

## 尚需現場驗證
- 正確帳號及各台不同密碼的實機登入。
- 錯誤帳密的實機回應特徵。
- 不同Model／Firmware的Status HTML相容性。
- Router開機中、斷線、Session逾時等情境。
- Windows EXE打包後的現場運作。

本報告不宣稱已完成實機驗證。
