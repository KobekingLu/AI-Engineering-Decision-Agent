# AI Engineering Decision Agent 專案簡介

## 1. 專案名稱

AI Engineering Decision Agent

副標：
把 scattered evidence 收斂成 decision-ready view 的工程決策輔助 AI Agent

## 2. 一句話定位

這不是聊天機器人，也不是單純的 log summarizer；這是一個面向 AE / PM / RD / DQA 的 AI Agent，負責把分散在 bug 文字、log、PDF、HTML、截圖、comment 與 lifecycle 訊號中的工程證據，收斂成可支撐下一步判斷的 decision-ready view。

## 3. 問題背景

在真實工程流程中，單一 issue 的關鍵資訊常常分散在多個來源：

- Redmine bug 描述與 status history
- log / test result
- DQA / RD / AE / PM comment
- HTML report、PDF、截圖與附件
- 已知案例的 root cause / solution / verification notes

團隊真正的痛點通常不是「資料完全不存在」，而是：

- 資訊散落，難以快速拼成完整脈絡
- 需要反覆比對 issue family、trigger、symptom 與 status
- 在尚未有最終答案前，很難判斷下一步該先做什麼
- 容易產生 generic 建議，卻無法真正推進工程調查

## 4. 核心目標

本專案的核心目標是：

**improve decision assistance quality under incomplete information**

也就是在資訊尚未完整、尚未結案、尚未確認最終 root cause 的情況下，協助團隊更快做到：

- 判斷目前最可能的 issue family / subtype
- 辨識最有價值的 evidence
- 指出缺哪些資訊才足以往下一個 decision stage 前進
- 產出更像工程師會採取的 next-step recommendation
- 用 uncertainty-aware 的方式支援 AE / PM / RD / DQA 討論

## 5. Agent 角色定義

這個系統的角色是 **AI Agent**，不是 chatbot。

它的工作方式不是被動回覆一段問題，而是主動執行一條 decision-assistance pipeline：

1. intake 多種 case evidence
2. normalize 成可分析的 case structure
3. 抽取 lifecycle evidence
4. 檢索相似 historical patterns
5. 推論 issue family / subtype / decision stage
6. 產出 uncertainty-aware summary 與 next-step guidance
7. 輸出 JSON 與 HTML report 供團隊 review

## 6. 現階段已完成能力

目前專案已具備以下可 demo 能力：

- 單一 case 多格式 intake
  - 貼文字
  - JSON / TXT / PDF / HTML
  - 圖片與掃描型檔案的本地 OCR
- evidence normalization
- issue family / subtype classification
- decision stage inference
- lifecycle-aware reasoning
- retrieval of similar historical cases
- uncertainty / confidence / missing-information output
- bilingual HTML report
- 本地 web demo app

## 7. 目前輸出重點

目前 agent 可輸出：

- issue family
- issue subtype
- decision stage
- action mode
- resolution state
- confidence
- decisive evidence
- unresolved gap
- missing information
- likely root cause hypothesis
- recommended action
- next-step focus
- lifecycle evidence summary

## 8. benchmark cases 的用途

這批 benchmark cases 的用途，不是讓 agent 背 closed case 的最終答案。

它們的用途是作為教材，讓系統學會：

- 如何在資訊不完整時做更好的工程判斷
- 如何分辨 issue subtype
- 如何辨識重要 evidence
- 如何根據 lifecycle signal 調整 decision stage
- 如何提出更有工程可執行性的 next step

換句話說，benchmark 的價值在於提升 **decision assistance quality**，不是做 answer memorization。

## 9. 目前架構方向

本專案未來預計發展為一個可治理、可累積的 engineering knowledge loop，包含五層：

1. Data ingestion layer  
   接入 Redmine、meeting notes、uploaded files、manual summaries 等資料來源

2. Knowledge normalization layer  
   將不同來源整理成統一 schema 與 provenance-aware evidence

3. Retrieval layer  
   用 symptom / subtype / trigger / verification pattern 檢索相似案例

4. Decision assistance layer  
   產出 decision-ready view，而不是冒充最終答案

5. Knowledge feedback layer  
   區分 raw record、machine artifact、human-confirmed knowledge，避免污染知識庫

## 10. 知識治理原則

本專案不採「每個新 case 都直接自動學進去」的方式。

治理原則包括：

- raw case data 可以保存，但不等於 confirmed knowledge
- machine-generated summary 只是 artifact
- 只有 human-confirmed root cause / solution / verification result 才可進 high-trust knowledge base
- meeting notes 必須保留 source / speaker / date / context
- 未結案 case 只能作為 low-confidence reference

## 11. 現階段可保守主張的價值

在目前 demo 階段，可以保守主張的價值是：

- 提供一個可展示、可操作的 engineering decision assistance prototype
- 將 scattered evidence 收斂為統一的 case view
- 讓 issue 判讀與 next-step 建議更具結構
- 幫助團隊更快形成可討論的 decision-ready view

目前**不主張**未經驗證的量化成效，也不宣稱已取代人工工程判斷。

## 12. 適合競賽的亮點

- 明確是 AI Agent，而非一般問答 chatbot
- 針對工程流程中的真實決策痛點
- 可展示多步 workflow，而不是單次回覆
- 同時處理不完整資訊、歷史知識、uncertainty 與 lifecycle signal
- 已具備本地 web demo 與 HTML report
- 已有持續擴充到 Redmine / meeting notes / governed knowledge base 的清楚方向

