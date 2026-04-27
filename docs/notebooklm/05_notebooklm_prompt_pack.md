# NotebookLM 提問模板包｜AI Engineering Decision Agent

## 這份文件的用途
這份文件提供可直接貼進 NotebookLM 的提問模板，幫你把已上傳的來源材料轉成：
- 競賽簡報初稿
- 報名表答案
- demo 口播稿
- 評審 Q&A 準備稿

---

## 提問模板 1｜競賽簡報初稿
請根據目前專案來源，幫我產出一份 10~12 頁的競賽簡報初稿。

要求如下：
- 使用繁體中文
- 風格要像工程競賽提案，不要像行銷文案
- 主線請聚焦在「把 scattered evidence 收斂成 decision-ready view 的 AI Agent」
- 請明確說出這不是 chatbot，而是具備 decision workflow 的 AI Agent
- 請把簡報結構排成：痛點 → 核心定位 → 為何是 Agent → 技術架構 → demo output → 代表案例 → 差異化 → 目前成果 → 未來方向
- 每頁請提供：頁標題、3~5 個 bullet、建議口播重點
- 請保守表述成果，不要虛構未驗證的量化數字

---

## 提問模板 2｜報名表答案版
請根據目前專案來源，直接幫我填寫競賽報名表需要的內容。

請產出以下欄位：
- 作品名稱（Project Title）
- 最相關領域（Relevant Field）
- 應用場景（Application Scenario）
- 實施方法與技術架構（Implementation Method & Technical Architecture）
- 量化成效與實施成果（Quantitative Benefits & Implementation Results）
- 未來展望（Future Outlook）
- 其他補充資料（Additional Information）

要求如下：
- 每一欄請先給正式版，再給精簡版
- 語氣正式、可信、工程導向
- 不要浮誇，也不要把 prototype 說成 production-ready
- 要明確凸顯 autonomous decision-making 與 environment interaction

---

## 提問模板 3｜3 分鐘 demo 口播稿
請根據目前專案來源，幫我寫一份 3 分鐘 demo 口播稿。

要求如下：
- 用繁體中文
- 口吻自然但專業
- 開頭先講痛點，再講解法，再講為什麼是 Agent
- 中間請用 triage / verification / closure 的案例邏輯帶出作品能力
- 最後收斂到目前成果與未來方向
- 不要太像背稿，要像比賽 demo 口頭說明

---

## 提問模板 4｜5 分鐘 demo 影片腳本
請根據目前專案來源，幫我寫一份 5 分鐘 demo 影片腳本。

要求如下：
- 用時間軸方式呈現，例如 0:00–0:30、0:30–1:30
- 說明這個作品要解的問題、系統怎麼運作、輸出長什麼樣子、案例如何證明能力
- 請至少納入一個 triage case、一個 verification case、一個 closure case
- 語氣要像工程競賽 demo，不要太像廣告

---

## 提問模板 5｜評審 Q&A 準備稿
請根據目前專案來源，幫我準備 10 題評審可能會問的問題，以及每題的建議回答。

請至少包含以下主題：
- 為什麼這是 Agent，不是 chatbot？
- 目前與一般 AI 工具的差異是什麼？
- 目前是否已有量化成效？
- 沒有最終答案時，Agent 為何仍有價值？
- 如何避免錯誤知識被累積進去？
- 未來如何串接更多資料來源？
- 為什麼這個方向值得持續投資？

要求如下：
- 回答要保守、可信
- 不要虛構 production 成果
- 要能凸顯 engineering decision assistance 的價值

---

## 提問模板 6｜幫我把簡報做得更像評審會買單的版本
請根據目前專案來源，幫我重新整理一版更適合競賽評審閱讀的簡報內容。

要求如下：
- 減少內部開發文件口氣
- 保留核心技術深度，但表達更清楚
- 強化「這個作品解決了真實業務痛點」
- 強化「為什麼現在就值得 early submission」
- 指出哪些頁最值得放 demo 截圖或代表案例

---

## 提問模板 7｜幫我濃縮成主管可讀的一頁版
請根據目前專案來源，幫我濃縮成一頁簡報摘要，讓主管或評審可以在 1 分鐘內看懂。

要求如下：
- 只保留最有說服力的內容
- 包含：痛點、解法、為什麼是 Agent、目前完成度、未來方向
- 風格偏高層 summary，但不要失真

---

## 使用提醒
當 NotebookLM 生成內容時，若出現以下情況，請要求它修正：
- 把作品寫成 generic chatbot
- 過度強調「AI 已自動找出答案」
- 虛構量化 ROI
- 沒有凸顯 triage / verification / closure 的 decision stage coverage
- 沒有明確說明 lifecycle signal 與 next-step guidance
