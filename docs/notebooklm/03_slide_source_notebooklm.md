# AI Engineering Decision Agent｜NotebookLM 簡報來源包

## 這份文件的用途
這份文件是給 NotebookLM 生成競賽簡報用的 slide-ready 來源材料。
每一頁都包含：
- slide title
- key message
- 建議內容重點
- 建議可放畫面
- 本頁評審應記住的一句話

建議最終簡報控制在 10~12 頁。

---

## 第 1 頁｜封面
### Slide title
AI Engineering Decision Agent

### Key message
這是一個把 scattered evidence 收斂成 decision-ready view 的工程決策輔助 AI Agent。

### 建議內容重點
- 副標：Turning scattered engineering evidence into a decision-ready view
- 團隊名稱 / 成員 / 部門
- 一句話定位

### 建議可放畫面
- 專案名稱大標
- 簡潔 subtitle
- 小型 workflow icon 或工程場景背景

### 評審應記住的一句話
這個作品的重點不是聊天，而是幫工程團隊更快形成下一步決策。

---

## 第 2 頁｜問題背景
### Slide title
工程 issue 的真正痛點不是沒有資料，而是資料太分散

### Key message
工程案件的 bottleneck 常在於 evidence scattered，而不是 evidence absent。

### 建議內容重點
- bug / log / PDF / HTML / comment / status / 截圖分散
- 很多案件尚未有最終答案，但仍需先做決策
- 團隊常把時間花在整理 context，而不是推進調查

### 建議可放畫面
- 一個案件周圍散落多種資料來源的示意圖
- bug、log、PDF、comment、history icon 圖

### 評審應記住的一句話
這個專案在解決的是工程決策瓶頸，不只是資料摘要問題。

---

## 第 3 頁｜核心定位
### Slide title
從 scattered evidence 到 decision-ready view

### Key message
本作品的核心任務，是在資訊不完整時，協助團隊更快走到可做下一步判斷的狀態。

### 建議內容重點
- 核心定位：把 scattered evidence 收斂成 decision-ready view
- 強化目標：improve decision assistance quality under incomplete information
- 不追求 AI 直接宣稱最終答案

### 建議可放畫面
- 「scattered evidence → decision-ready view」箭頭圖
- 左側碎片化資料，右側結構化決策視圖

### 評審應記住的一句話
這個作品不是替工程師判決，而是加速工程師形成下一步判斷。

---

## 第 4 頁｜為什麼是 AI Agent
### Slide title
這不是 chatbot，而是一條可執行的 decision workflow

### Key message
Agent 的價值在於主動完成多步驟 decision-assistance pipeline。

### 建議內容重點
- intake case evidence
- normalize 多來源資料
- 抽取 lifecycle signal
- retrieval 相似 historical pattern
- infer issue family / subtype / decision stage
- output recommended action / HTML artifact

### 建議可放畫面
- 6~7 步驟的 pipeline 圖

### 評審應記住的一句話
它不是回答一段話，而是主動完成一條 decision workflow。

---

## 第 5 頁｜技術架構
### Slide title
目前 MVP 架構與未來擴充方向

### Key message
系統已具備 ingestion、normalization、retrieval、reasoning、artifact output 的基本骨架。

### 建議內容重點
- Data ingestion
- Knowledge normalization
- Retrieval
- Decision assistance
- Knowledge feedback
- 未來可接 Redmine / meeting notes / known issues

### 建議可放畫面
- 五層式架構圖

### 評審應記住的一句話
這不是一次性 demo，而是有清楚演進方向的 decision-assistance architecture。

---

## 第 6 頁｜輸入形式
### Slide title
單一 case 可收多種 evidence

### Key message
系統設計刻意貼近真實工程資料環境，而非只接受乾淨結構化文字。

### 建議內容重點
- text
- TXT / JSON
- PDF / HTML
- image / scanned evidence
- OCR 與多檔案 bundle

### 建議可放畫面
- 多格式檔案 icon
- intake 畫面或 demo 截圖

### 評審應記住的一句話
真實工程案件本來就很雜，這個 Agent 的價值之一就是能吃進這種雜訊環境。

---

## 第 7 頁｜輸出內容
### Slide title
輸出不是摘要，而是 decision artifact

### Key message
產出的重點是支撐下一步判斷，而不是只給一段結論文字。

### 建議內容重點
- issue family / subtype
- decision stage
- action mode / resolution state
- confidence / uncertainty
- decisive evidence
- missing information / unresolved gap
- recommended action / next-step focus
- lifecycle evidence summary

### 建議可放畫面
- HTML report hero 區塊截圖
- 結構化欄位示意

### 評審應記住的一句話
這個作品產出的是可 review、可討論、可追蹤的 decision artifact。

---

## 第 8 頁｜代表案例
### Slide title
Demo 不只一種情境，而是覆蓋不同 decision stage

### Key message
目前 prototype 已能展示 triage、verification、closure 三種典型情境。

### 建議內容重點
- Triage case：新案、先判別 issue family / next step
- Verification case：fixed / ready for DQA test，但仍需原 fail condition retest evidence
- Closure case：已有 fixed + PASS evidence，可推向 closure-ready view

### 建議可放畫面
- 三個案例縮圖卡片
- 用不同顏色標出 triage / verification / closure

### 建議可放的案例
- triage：143084
- verification：135177 或 135322
- closure：141307

### 評審應記住的一句話
這不是單一 bug summarizer，而是能辨識案件目前該往哪個決策階段走。

---

## 第 9 頁｜與一般 AI 工具的差異
### Slide title
與一般 chatbot / summarizer 的差異化

### Key message
差異不在於會不會生成文字，而在於有沒有 decision stage 與 evidence-driven workflow。

### 建議內容重點
- 不是 generic Q&A
- 不只摘要 evidence
- 會處理 lifecycle signal
- 會指出 unresolved gap
- 會輸出 next-step guidance
- 有 knowledge governance 方向

### 建議可放畫面
- 比較表：一般 chatbot vs AI Engineering Decision Agent

### 評審應記住的一句話
真正的差異化在於 stage-aware reasoning 與可執行的 next-step guidance。

---

## 第 10 頁｜目前成果與保守主張
### Slide title
目前已完成什麼，以及我們保守怎麼表述成果

### Key message
目前應強調 prototype feasibility 與實質改善，不應過度宣稱未驗證成效。

### 建議內容重點
- 已完成可展示 prototype
- 已具備多來源 intake、reasoning、artifact output
- 已在真實案例中展示 stage-aware decision assistance
- 保守主張：降低整理成本、提升共識形成速度、讓 next step 更清楚
- 不主張：已全面自動化、已量化證明大規模 ROI

### 建議可放畫面
- prototype 畫面
- 可展示 output 清單

### 評審應記住的一句話
這個作品最有說服力的地方是「已經能動」，而且方向清楚可信。

---

## 第 11 頁｜未來方向
### Slide title
從 demo prototype 走向 governed engineering knowledge loop

### Key message
長期目標不是一次性分析工具，而是可累積、可治理、可擴充的工程決策平台能力。

### 建議內容重點
- 接入 Redmine / note / attachment / status
- 接入 meeting notes
- 建立 trust-aware schema
- 區分 raw case / machine artifact / human-confirmed knowledge
- 強化 retrieval ranking 與 lifecycle pattern reasoning

### 建議可放畫面
- roadmap 圖
- future architecture diagram

### 評審應記住的一句話
這個作品的延展性來自於：它可以逐步變成工程知識與決策的基礎層。

---

## 第 12 頁｜結語
### Slide title
AI 幫忙把工程討論更快推進到 decision-ready 狀態

### Key message
AI 的角色不是取代工程師，而是幫工程團隊更快推進判斷流程。

### 建議內容重點
- 聚焦 incomplete-information 下的 decision assistance
- 已完成可展示 prototype
- 核心價值：從 scattered evidence 到 decision-ready view

### 建議可放畫面
- 簡單總結圖
- 專案 slogan

### 評審應記住的一句話
我們不是在做一個更會聊天的 AI，而是在做一個更能推進工程判斷的 AI Agent。

---

## 給 NotebookLM 的生成提醒
當你用這份來源生成簡報時，請注意：
- 保持工程競賽語氣，不要太像行銷文案
- 每頁先抓一個 key message，不要只是堆 bullet
- 主線順序應為：痛點 → 定位 → 為何是 Agent → 架構 → demo → 差異化 → 成果 → 未來
- 請反覆強化「decision-ready view」這個主軸
