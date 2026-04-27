# AI Engineering Decision Agent 簡報素材大綱

> 建議頁數：11 頁  
> 使用方式：可直接餵給 NotebookLM，再延伸成講稿、投影片文案、Q&A 準備稿。

---

## 第 1 頁｜封面

### 標題
AI Engineering Decision Agent

### 副標
把 scattered evidence 收斂成 decision-ready view 的工程決策輔助 AI Agent

### 建議口播重點

- 這個專案的核心不是做 chatbot，而是做 engineering decision assistance
- 目標使用者是 AE / PM / RD / DQA
- 要解的問題是：真實工程 issue 的證據太分散，難以快速形成下一步判斷

---

## 第 2 頁｜問題背景

### 標題
工程 issue 的真正痛點不是沒有資料，而是資料太分散

### 內容重點

- bug 描述、status、comment、log、PDF、HTML、截圖分散在不同位置
- 很多 case 尚未有最終 root cause，但仍需要先做決策
- 團隊常常花很多時間整理 context，而不是推進真正的調查

### 建議口播重點

- 我們想處理的是 decision bottleneck，不只是資料摘要
- 在工程現場，資訊不完整其實是常態，不是例外

---

## 第 3 頁｜我們的核心定位

### 標題
從 scattered evidence 到 decision-ready view

### 內容重點

- 核心定位統一為：
  **把 scattered evidence 收斂成 decision-ready view**
- 專案強化目標是：
  **improve decision assistance quality under incomplete information**

### 建議口播重點

- 我們不是在追求 AI 直接下最後判決
- 我們是在幫工程團隊更快走到「可以做下一步決策」的狀態

---

## 第 4 頁｜為什麼這是 AI Agent，不是 chatbot

### 標題
這不是問答機器人，而是一條可執行的 decision workflow

### 內容重點

Agent 會執行：

1. intake case evidence
2. normalize 多來源資料
3. 抽取 lifecycle signal
4. retrieval 相似案例
5. 判斷 issue family / subtype / decision stage
6. 輸出 recommended action 與 HTML report

### 建議口播重點

- chatbot 偏向回應問題
- agent 則會主動完成一連串 decision-assistance steps

---

## 第 5 頁｜目前系統架構

### 標題
目前 MVP 與未來架構方向

### 內容重點

五層架構：

1. Data ingestion
2. Knowledge normalization
3. Retrieval
4. Decision assistance
5. Knowledge feedback

### 建議口播重點

- 現在已經有 intake、normalization、retrieval、report output
- feedback 與 trust governance 是下一步重點

---

## 第 6 頁｜目前可處理的輸入

### 標題
單一 case 可收多種 evidence

### 內容重點

- 貼文字
- JSON / TXT
- PDF / HTML
- 圖片與掃描型 evidence
- OCR 與多檔案 bundle intake

### 建議口播重點

- 我們刻意讓輸入形式貼近真實工程情境
- 因為真實 bug case 很少只有一段乾淨文字

---

## 第 7 頁｜目前輸出內容

### 標題
輸出不只是摘要，而是 decision artifact

### 內容重點

目前輸出包含：

- issue family / subtype
- decision stage
- action mode / resolution state
- confidence / uncertainty
- decisive evidence
- unresolved gap
- missing information
- next-step focus
- recommended action
- lifecycle evidence summary

### 建議口播重點

- 我們要的是支撐決策的 artifact，不是只有一段結論文字

---

## 第 8 頁｜benchmark cases 的真正用途

### 標題
benchmark 不是答案庫，而是教材

### 內容重點

benchmark cases 用來學習：

- 更準確的 issue family / subtype 判斷
- 更好的 evidence prioritization
- 更清楚的 uncertainty 表達
- 更合理的 decision stage inference
- 更具工程可執行性的 next-step recommendation

### 建議口播重點

- 我們不希望 agent 只是背 closed case 的最終答案
- 真正重要的是：在沒有最終答案時，能不能幫團隊做出更好的下一步判斷

---

## 第 9 頁｜目前已看得到的進步

### 標題
從 generic summary 走向 stage-aware decision assistance

### 內容重點

目前已看得到的改善方向：

- issue family / subtype 更細
- decision stage 結構更完整
- lifecycle signal 已納入推論
- uncertainty / missing-information 輸出更結構化
- recommendation 開始依 case 類型分流

### 建議口播重點

- 我們保守地說是「已看得到實質改善」
- 不宣稱未經驗證的量化成果

---

## 第 10 頁｜差異化亮點

### 標題
與一般 AI 工具相比，我們的差異

### 內容重點

- 不是 chatbot，而是 decision agent
- 不只摘要 evidence，而是整理 decision-ready view
- 不只看關鍵字，也開始看 lifecycle signal 與 stage
- 不把機器產出直接當 trusted knowledge
- 有明確的 knowledge accumulation with governance 方向

### 建議口播重點

- 這個專案的重點，是把 AI 用在工程決策流程裡，而不是只做文字生成

---

## 第 11 頁｜未來方向

### 標題
從 demo prototype 走向 governed engineering knowledge loop

### 內容重點

下一步規劃：

- 接入 Redmine bug / note / status / attachment
- 接入 meeting notes / issue review notes
- 建立 trust-aware knowledge schema
- 區分 raw case / machine artifact / human-confirmed knowledge
- 強化 retrieval 與 lifecycle pattern reasoning

### 建議口播重點

- 長期目標不是一次性分析工具
- 而是可治理、可累積、可持續成長的 engineering decision agent

---

## 第 12 頁｜結語

### 標題
AI 幫忙把工程討論更快推進到 decision-ready 狀態

### 內容重點

- 本專案聚焦在工程資訊不完整時的 decision assistance
- 已完成可展示、可操作的 AI Agent prototype
- 核心價值是讓團隊更快從 scattered evidence 走向 decision-ready view

### 建議口播重點

- 我們沒有宣稱 AI 取代工程師
- 我們希望的是：AI 能把工程團隊的判斷流程往前推進

