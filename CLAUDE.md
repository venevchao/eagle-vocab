# 養鷹達人 eagle-vocab — 專案憲法

本檔只放**不變式**；當前狀態、backlog、數據解讀住在長期記憶（vocab-app）與 vault 數據資料夾。兩邊衝突時，以本檔紅線為準。

## 專案是什麼

9 歲兒子「允」的 sight words 每日練習 App。單一靜態 HTML（`index.html`，全繁中介面），GitHub Pages 部署：`https://venevchao.github.io/eagle-vocab/`。
**驗收標準永遠是：兒子明天願不願意再打開。**

## 工作環境與部署

- 唯一改動檔 `index.html`（`manual-preview.html` 是祕笈設計原稿存檔，勿當作業區）。
- 部署＝`git add/commit/push`（commit 訊息繁中），Pages 自動更新；生效驗證用 `curl | grep`。
- 本機無 node：JS 語法檢查用 `osascript -l JavaScript` 包 `new Function(src)`（先 sed 抽出 script 區塊）。
- 測試沙盒：網址加 `?test=1`（獨立 localStorage `word-birds-test-v1`＋紫色警示條）。功能驗證**走純點擊路徑**——用 JS 直跳狀態會產生假警報。
- 麥克風等硬體行為只能 iPad 真機驗收；程式端一律 graceful fallback。
- 風險分級部署：小修直推；視覺改版／實驗性功能先出獨立預覽頁。判準：**「壞掉時孩子第一眼會不會看到？」**
- **並行紅線（2026-08-06 教訓）**：同時段只允許**一個**視窗改動本 repo。commit 前必查 `git status`＋`git diff --stat`，確認 diff 只含本次任務的改動；發現他窗未收尾的痕跡→**停下協調，不 commit**。背景：git commit 對整個工作目錄拍照，`git add index.html` 會把他窗的半成品一併掃進歷史（8/6 匯入窗三個 commit 夾帶了批次窗的未完工修改）。跨窗交接資訊寫進對應規格記憶，勿只留在對話裡。

## 紅線（違反即錯）

- 勿動：三拍制結構、spellLog、localStorage key（`word-birds-v1` / `-session` / `-test-v1`）、`?test` 模式、階段圖示（🦜 保留，只能改文字）。
- 勿加 `apple-mobile-web-app-capable`（iOS standalone 用獨立儲存，會讓既有進度「消失」）。
- **絕不評分發音**；錄音永遠 optional，任何錄音步驟不得成為離場門。
- 星星永不扣；答錯語氣不懲罰；按鈕用祈使句；介面全繁中台灣用語（禁陸語詞彙）。
- 新增持久化資料一律 profile-ready（預留孩子維度，二寶將至）。
- spellLog 計時語意變更必須加版本標記（7/13 教訓：新舊資料不可混用校準）。

## 視覺（本專案專屬，勿跨案套用）

奇幻傳說感、金色＋鷹羽母題（鷹羽＝英語）、青銅莊重 CTA。通用紀律：字級與顏色嚴格對應資訊位階；慶祝動畫走 overlay 不佔版面流；iPad 橫式（1024×690）任何狀態主按鈕一屏內可及。

## 字庫匯入流程

- 新批次＝續接 `SEED2` 陣列（`['word','中文','例句',listNum]`），tier 與 batch 由 `.map` 統一掛上；已學批次才標 `known:1`。
- 三軌命名（2026-08-06 定案，內部鍵不變）：**聽懂** `recognize`（只聽選、Lv4 畢業）／**練熟** `familiar`（Lv0–2 緩坡→產出、Lv5）／**複習** `master`（已會字維護，搭配 `known:1` 從 Lv1 起步）。新字入口只有聽懂或練熟；複習軌專供在校已學批次。匯入面板為兩問制（已經會了嗎？＋要練多深？），組合由程式判定軌別。
- 進場順序＝陣列順序，每日新字節流 `NEW_CAP=5`、受複習債調節（>25 待複習→0 新字）。
- **例句先過機械檢查，人眼只驗品味層**：
  ```
  python3 tools/check_sentences.py              # 全庫回歸掃描
  python3 tools/check_sentences.py --draft 檔案  # 待匯入草稿預檢（行格式同 SEED2 條目）
  ```
  機械層（腳本管）：目標字必在句中、句長 5–9 字（規範 v2，List 3 起）、不可引用尚未進場的批次字、表外字清點、撇號提醒。
  品味層（人管）：加壓字選字（聽覺熟、視覺尚未識讀）、獎勵名詞個人化（興趣清單見記憶）、避免不能自然拼讀的字（如 sword 的默音 w）。
- 課外已知字清單維護在 `tools/check_sentences.py` 頂部 `EXTRA_KNOWN`，媽媽確認新的已知字後就地增補。

## 收尾義務

- 交付前以**九歲孩子＋家長**身分把改動完整走一遍（體驗走查，不只功能對）。
- 更新長期記憶 vocab-app；段落收尾附「下一步提醒」（1–3 項，各附建議執行模型）。
