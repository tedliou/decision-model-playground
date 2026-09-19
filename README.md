# VerveCode 模型實驗室

在瀏覽器輸入問題，讓 Laya 或 TypeSafe Jev 從 vervecode.dev 的文章中選出最推薦的一篇。顯示所有文章與「沒有可推薦的」的原始選項機率、機率條，以及載入、推論與整次請求的耗時。

這是獨立的本機實驗專案，不會修改或部署 vervecode.dev。

## 啟動

需要 Node.js 24 LTS、uv，以及 NVIDIA 驅動程式。Python 3.12 由 uv 管理。預設使用 CUDA；若要明確使用 CPU，在 `.env` 設定 `LAYA_DEVICE=cpu`。

在工作區根目錄執行：

```powershell
./scripts/setup.ps1
npm run dev
```

- 網頁：<http://127.0.0.1:5173>
- API 文件：<http://127.0.0.1:8000/docs>
- 關閉：在執行 `npm run dev` 的終端機按 `Ctrl+C`，會一併停止前後端。

第一次 setup 會安裝依賴並下載模型。**第一次送出問題會載入模型，後續請求重用同一個模型實例。** GPU 首次執行的初始化成本會包含在第一次推論耗時。開發伺服器刻意不對 Python 開啟自動重載，避免每次存檔重新載入 GPU 模型；修改後端後請重啟。

## 切換 Laya / Jev

頁面有模型選單。Laya 預設可用；Jev 未設定金鑰時會顯示「尚未設定」。

在根目錄 `.env` 填入以下欄位，再重啟後端：

```dotenv
JEV_API_KEY=你的金鑰
JEV_MODEL=jev-1.13.0
```

不要將金鑰放進 `VITE_*`、前端程式碼或 Git。前端只傳 `provider`，金鑰由後端讀取。選擇 Jev 並送出才會呼叫外部 API，送出的資料是問題與精簡選項；Laya 推論使用本機模型。

兩個 adapter 收到同一個 `Decision`。不做第二次 LLM 判斷、不以關鍵字覆寫結果，也不在模型失敗時自動改用另一個模型。

## 推薦如何計算

目前快照有 **18 篇文章＋1 個「沒有可推薦的」選項**。使用一次 `choice`，取得同一個分布下的所有選項機率，總和約為 1。這些是模型的相對選擇機率，不是每篇文章獨立「能解決問題」的機率，也不是已校準的正確率。

- `state`：使用者輸入的問題。
- `instructions`：選擇最能回答問題的文章；沒有合適文章就選 `none`。
- `criteria`：固定文章 ID 對應人工整理的精簡英文主題，例如 `a03: TouchDesigner AI control`。多語版接受中文問題。
- 中文完整標題、摘要與網址供介面呈現，**不會把文章全文或所有摘要一起送入模型**。模型實際看到的選項保存在 `data/descriptors.json`。
- `none` 是真正參與同一次推論的選項，不是以人為門檻或剩餘機率算出來的。
- 回傳值不重新正規化；上游四捨五入可能使總和略偏離 100%。

Laya 的選項區預算只有 256 tokens，而且 SDK 會自動截短選項。adapter 會在推論前檢查每個選項、題目與整體輸入，**任何會被截斷的請求都回傳 422**。新增文章需重新檢查預算，目前上限為 19 篇文章＋`none`。

初步對照發現：把所有文章描述放入 `state` 會嚴重干擾這個模型。採用簡短選項＋單純問題後有改善，但仍可能推薦錯誤或過度選擇 `none`。此專案保留真實結果，適合觀察模型侷限，不能用幾題測試宣稱正式準確率。

## 耗時定義

| 欄位          | 定義                                                  |
| ------------- | ----------------------------------------------------- |
| 模型載入      | Laya 初次匯入與載入本機權重的時間，後續為 0           |
| 模型推論      | Laya 輸入處理、GPU 執行、同步及輸出處理；不含模型載入 |
| 模型 API 往返 | Jev HTTP 請求的網路與服務端處理總時間                 |
| 後端總耗時    | 推薦處理開始至回應組裝，包含載入、預算檢查與推論      |
| 整次請求      | 瀏覽器送出到取得結果的時間，包含前後端傳輸與載入      |

Jev API 往返與 Laya 本機推論不是相同的測量範圍，不能直接當成純模型速度比較。

## 結構

```text
apps/
  api/
    src/playground/
      routes.py            # HTTP 介面與驗證
      schemas.py           # Pydantic 契約，產生 OpenAPI
      service.py           # 分布驗證、排序、推薦結果
      decision.py          # 共同題目與版本
      providers/           # DecisionProvider、Laya、Jev
    tests/                 # API 與供應者契約測試
    openapi.json           # 產生的 API 規格
  web/
    src/
      api/                 # OpenAPI 產生的型別與 client
      components/          # 結果卡與機率列表
      composables/         # 請求狀態、錯誤、計時
data/                      # 可追蹤的文章快照與精簡選項
scripts/                   # 安裝、下載、同步、契約產生、實測
models/                    # 模型權重與版本記錄，Git 忽略
.cache/                    # 工作區內的模型與安裝快取，Git 忽略
.env                       # 私密設定，Git 忽略
```

採 npm workspaces 管理前端、uv lock 管理 Python，FastAPI 與 Vue／TypeScript 分離。前端透過 Vite proxy 呼叫同源 `/api/v1`；不需要資料庫、訊息佇列或額外 API gateway。後端在執行緒中進行同步推論，單一模型實例以鎖防止重疊執行，忙碌時回傳 409，不無限排隊。

`DecisionProvider` 只有 `info()` 與 `predict(Decision)`。新增模型只需實作 adapter 並在 `main.py` 註冊，推薦排序和畫面不處理模型特有欄位。

## 資料與模型管理

```powershell
npm run articles:sync
npm run model:download
```

文章從官方 `https://vervecode.dev/index.xml` 取得；同步時若出現未準備精簡選項的新文章，會停止並提示編輯 `data/descriptors.json`，不會偷偷略過。更新後重啟後端。

模型只下載 `convaiinnovations/laya-multilingual`。`data/model.json` 固定 Hugging Face commit SHA，下載後另將來源存入 `models/laya-multilingual/provenance.json`；新建環境也會取得同一版本。`LAYA_MODEL_PATH` 必須位於工作區。Laya 推論設為離線，缺少檔案會報錯，不會在背景下載到使用者全域目錄。

模型授權為 Apache 2.0，來源與模型卡隨下載保存在模型目錄。文章原始標題、摘要與連結來自 vervecode.dev，精簡英文選項由本實驗人工整理。

## 驗證

```powershell
uv run --frozen pytest -q
uv run --frozen ruff check apps/api scripts
uv run --frozen ruff format --check apps/api scripts
npm run lint
npm test
npm run build
```

修改 Pydantic 回應或路由後，重新產生前端契約：

```powershell
npm run api:types
```

跑真實 Laya（會載入模型，不是 mock）：

```powershell
uv run --frozen python scripts/smoke_model.py
```

結果存入 `.logs/smoke-model.json`，包含預期答案、實際答案、所有機率與耗時。這是小型人工案例紀錄，不是正式 benchmark。單元測試不下載模型；Jev adapter 用 HTTP 契約測試驗證，真實 Jev 需自行提供金鑰。

專案已初始化本機 Git，沒有設定 GitHub 遠端；`.env`、權重、快取、依賴與實驗記錄均排除追蹤。
