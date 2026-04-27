# AI Engineering Decision Agent｜NotebookLM 專案簡介

## 這份文件的用途
這份文件是給 NotebookLM 快速建立專案世界觀用的來源材料。
它的任務不是當簡報逐頁稿，也不是當報名表答案，而是讓系統先理解：
- 這個作品到底是什麼
- 它解決什麼痛點
- 為什麼它是 AI Agent，不是 chatbot
- 目前做到哪裡、還沒做到哪裡

---

## 一句話定位
**AI Engineering Decision Agent 是一個把工程案件中的 scattered evidence 收斂成 decision-ready view 的工程決策輔助 AI Agent。**

更直白地說，它不是替工程師下最終判決，而是把分散在 bug、log、PDF、HTML、comments、lifecycle status 與歷史案例中的資訊整理成「下一步可判斷、可討論、可推進」的決策視圖。

---

## 核心價值主張
在真實工程流程中，團隊常常不是缺資料，而是缺：
- 能快速拼出完整脈絡的方法
- 能在資訊不完整時先做下一步判斷的能力
- 能把不同角色看到的 evidence 收斂成同一個 decision-ready view 的工具

本作品的價值在於：
**在最終 root cause 尚未確認前，先幫 AE / PM / RD / DQA 更快形成下一步判斷。**

---

## 目標使用者
本作品目前主要面向以下角色：
- **AE**：需要快速掌握案件脈絡與下一步調查方向
- **PM**：需要知道目前風險、目前階段、是否能往下推進
- **RD**：需要知道目前 evidence 指向什麼問題家族、哪裡還缺證據
- **DQA**：需要更快整理 case、對齊 verification / closure 所需資訊

---

## 真正要解決的痛點
單一工程案件的重要資訊常分散在：
- bug 描述
- status 與 lifecycle 變化
- comment 討論
- test log / report
- PDF / HTML / 截圖 / 附件
- 過往類似案例與 retest notes

因此常見問題是：
1. **資訊散落**：需要花時間來回切換資料來源
2. **階段不清楚**：案件現在到底在 triage、verification 還是 closure，不容易快速對齊
3. **next step 模糊**：即使看過很多資料，還是不知道下一步最該補哪個 evidence
4. **generic 建議太多**：系統容易只給「請進一步確認」這種沒法推進的回答
5. **lifecycle signal 沒被吃進判斷**：例如 fixed、ready for DQA test、clarifying、retest pass 等狀態，常沒有被系統化納入 decision stage inference

---

## 為什麼這是 AI Agent，不是 chatbot
### 不是 chatbot 的原因
一般 chatbot 多半是：
- 收到問題
- 回覆一段文字
- 偏重對話與摘要

本作品則是主動執行一條 decision workflow：
1. intake case evidence
2. normalize 成統一 case structure
3. 抽取 lifecycle signal
4. 檢索 historical pattern
5. 推論 issue family / subtype / decision stage
6. 產出 uncertainty-aware next-step guidance
7. 生成 JSON / HTML decision artifact

### 符合 AI Agent 的兩個核心點
**1. 主動決策能力（autonomous decision-making）**
- 不只回應提問，而是主動推論 decision stage、risk、resolution state、next step
- 會指出 missing information 與 unresolved gap

**2. 環境互動能力（environment interaction）**
- 可讀取多種 case evidence
- 可與輸入文件、log、附件、歷史案例資料互動
- 未來可再擴充連接 Redmine、meeting notes、DUT probe、known issue database

---

## 目前已完成的能力
目前已具備可 demo 的能力包括：
- 多格式 case intake
  - 文字
  - TXT / JSON
  - PDF / HTML
  - 圖片與掃描型 evidence
- evidence normalization
- issue family / subtype classification
- decision stage inference
- lifecycle-aware reasoning
- historical pattern retrieval
- confidence / uncertainty / missing information output
- bilingual HTML report
- 本地 web demo prototype

---

## 目前輸出的重點欄位
系統目前可輸出以下 decision artifact：
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

---

## 目前做到什麼
目前可以保守主張：
- 已完成一個可執行、可展示的 engineering decision assistance prototype
- 可將多來源 case evidence 收斂成統一的 case view
- 可根據不同 evidence 與 lifecycle signal 輸出 stage-aware decision artifact
- 已能以真實工程案例展示 triage / verification / closure 等不同 decision stage 的輸出

---

## 目前還沒做到什麼
目前不主張：
- 已達 production-ready
- 已全面串接正式 Redmine / attachment backend
- 已完全取代人工工程判斷
- 已有大規模、嚴格驗證過的量化 ROI
- 已將所有歷史案例都治理進高信任知識庫

---

## benchmark / historical cases 的用途
historical cases 的用途不是讓系統背答案，而是讓系統學會：
- 如何辨識 issue family / subtype
- 如何抓到真正重要的 evidence
- 如何看懂 lifecycle signal 對 decision stage 的影響
- 如何提出更具工程可執行性的 next step
- 如何在資訊不完整時做較好的 decision assistance

所以這個作品的重點不是 answer memorization，而是 **decision assistance quality**。

---

## 代表案例摘要（供 NotebookLM 理解作品範圍）
### 案例類型 A：Triage
- 新案剛進來，還沒有 fix path
- Agent 可先判斷 issue family / subtype
- 協助團隊先確認要不要做 slot swap、path check、對調驗證

### 案例類型 B：Verification
- 狀態已有 fixed / ready for DQA test / clarifying 等 lifecycle signal
- Agent 不只看 subject，而是會要求補原 fail condition 下的 retest / before-after logs
- 協助團隊不要太早當成可結案

### 案例類型 C：Closure
- 狀態已有 fixed 且有 PASS evidence
- Agent 可將案件推向 closure-ready view
- 同時提醒 closure package 要有哪些 final evidence

---

## 長期架構方向
本專案未來預計發展成一個 governed engineering knowledge loop，包含：
1. **Data ingestion layer**：接入 Redmine、meeting notes、uploaded files、manual summaries
2. **Knowledge normalization layer**：整理成統一 schema 與 provenance-aware evidence
3. **Retrieval layer**：用 symptom / subtype / trigger / verification pattern 找相似案例
4. **Decision assistance layer**：輸出 decision-ready view，而不是冒充最終答案
5. **Knowledge feedback layer**：區分 raw data、machine artifact、human-confirmed knowledge，避免知識污染

---

## 知識治理原則
本專案不採「每個新 case 都直接自動學進高信任知識庫」的模式。

治理原則包括：
- raw case data 可以保存，但不等於 confirmed knowledge
- machine-generated summary 只是 artifact
- 只有 human-confirmed root cause / solution / verification result 才能進 high-trust knowledge base
- 未結案 case 可作為 reference pattern，但只能低信任使用
- meeting notes 必須保留 source / speaker / date / context

---

## 現階段適合競賽的亮點
- 明確是 AI Agent，而不是一般 chatbot
- 解的是工程流程中的真實決策痛點
- 不是只做摘要，而是做 decision stage inference 與 next-step guidance
- 能處理 incomplete information、uncertainty、lifecycle signal、historical retrieval
- 已有可展示的 prototype 與多案例輸出
- 未來擴展方向清楚，且有治理思維

---

## 給 NotebookLM 的使用提醒
當你用這份來源生成簡報、口播稿或競賽說明時，請優先維持以下口徑：

### 主版本定位
**把 scattered evidence 收斂成 decision-ready view 的 AI engineering decision agent**

### 不要把作品描述成
- 一般 bug summarizer
- generic chatbot
- 萬用 AI assistant
- 已全面取代工程師的自動決策系統

### 應優先強調
- decision-ready view
- stage-aware reasoning
- lifecycle signal
- historical pattern retrieval
- next-step guidance
- incomplete information 下的 decision assistance
