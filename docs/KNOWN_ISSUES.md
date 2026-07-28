# Known Issues

1. 尚未用實體Router執行登入；需由使用者現場驗證。
2. 若登入失敗頁面沒有`Device Login`特徵，可能需要再補強失敗判定。
3. 不同Firmware可能修改欄位名稱或URL。
4. V0.1.0不保存登入頁原始HTML，避免無意保存Token；僅保存Status原始HTML。
5. 工具目前沒有強制停止正在進行中的HTTP呼叫；Timeout後會恢復GUI。
