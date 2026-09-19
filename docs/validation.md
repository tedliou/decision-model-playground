# 驗證紀錄

以下為 **2026-09-19 初始版本 `a2bbba2` 的本機實驗紀錄**，不是每次提交都會更新的驗收狀態，也不代表已適合正式環境。

環境：Windows、RTX 3070 8GB、Python 3.12、Node.js 24。

模型：`convaiinnovations/laya-multilingual`，固定版本 `052592a15d198d9ad47da779604259b10b47b7aa`。

## 功能驗證

- 真實瀏覽器送出繁體中文問題，後端使用 CUDA 執行 Laya。
- 「我想讓 AI 幫我操作 TouchDesigner」選出 td-cli，機率 96.13%。
- 「怎麼煮出好吃的義大利麵？」選出「沒有可推薦的」，機率 55.50%。
- 每次保留全部 18 篇文章及 `none`，介面顯示 19 個機率條。
- 首次模型載入約 10.2 秒、首次推論約 377 ms；後續瀏覽器測到約 65–69 ms。硬體負載與 GPU 初始化會影響數字。
- 已檢查 1280px 與 390px 寬度，沒有水平溢出；窄螢幕送出後會捲到結果。
- Jev 未設定金鑰時不可從選單送出；直接呼叫也會明確回報不可用。
- Jev adapter 已以 HTTP mock 驗證請求與回應契約，**沒有真實 Jev 呼叫紀錄**。

## 模型品質的限制

以四個手動題目做 smoke check，不是正式測試集：

| 題目                     | 預期             | 實際         |
| ------------------------ | ---------------- | ------------ |
| AI 操作 TouchDesigner    | td-cli           | td-cli       |
| Astro 部署很慢           | Astro 建置快取   | 沒有可推薦的 |
| Unity 使用 VS Code 寫 C# | Unity 編輯器連動 | 沒有可推薦的 |
| 義大利麵料理             | 沒有可推薦的     | 沒有可推薦的 |

這組資料說明目前模型仍會漏掉相關文章，不能以可成功執行推論推導推薦品質可靠。前端原樣顯示模型答案，不加入關鍵字補分或隱藏的第二次推論。

曾對照兩種輸入：所有文章描述放在 `state` 時，四題均偏向 Minecraft 指令文章；改成 `state` 只放問題、`criteria` 放精簡主題後才有上述結果。當前題目版本為 `article-choice-v2`。中文問題沒有先翻譯成英文。

## 可重跑的檢查

請見 [README 的驗證指令](../README.md#驗證)。當次後端 18 個測試與前端 2 個測試涵蓋分布完整性、`none`、供應者切換、輸入驗證、上游錯誤、機率條及重複送出防護。TypeScript 型別檢查、Vite 的 production build、ESLint、Ruff 皆通過，當次 npm audit 未回報已知漏洞；build 通過僅表示前端可產生建置產物。

當次 pytest 有兩個上游棄用警告：Starlette TestClient 的 httpx 整合與 AnyIO BlockingPortal alias；未影響該次測試結果。
