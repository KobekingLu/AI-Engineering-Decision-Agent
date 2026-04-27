# AI Engineering Decision Agent 報名稿草案

> 說明：本稿以工程競賽常見欄位撰寫，可直接複製到報名表或提案文件中。若主辦方有固定字數限制，可再依欄位縮寫。

## 1. 作品名稱

AI Engineering Decision Agent

## 2. 作品類別

AI Agent / 工程決策輔助 / Knowledge-assisted Decision Workflow

## 3. 團隊名稱

[待填]

## 4. 成員名單

[待填]

## 5. 指導單位 / 部門

[待填]

## 6. 專案摘要

本專案是一個面向 AE / PM / RD / DQA 的 AI Engineering Decision Agent，核心定位是**把 scattered evidence 收斂成 decision-ready view**。  

在真實工程流程中，單一 bug 或 issue 的重要資訊往往分散在 bug 描述、status history、log、PDF、HTML、截圖、comment 與過往案例中，導致團隊需要花大量時間來回整理、判讀與溝通。  

本專案的 AI Agent 並非聊天機器人，而是執行一條多步 decision-assistance workflow：接收 case evidence、正規化資料、抽取 lifecycle signal、檢索相似案例、推論 issue family / subtype / decision stage，最後輸出 uncertainty-aware 的 recommended action 與 HTML report。  

本系統目前已可作為可執行、可展示的 demo prototype，用來支援在資訊不完整時的工程決策輔助。

## 7. 問題痛點

目前工程團隊在處理 issue 時，常見痛點包括：

- 資訊分散在多個來源，難以快速建立完整脈絡
- 很多 case 尚未有最終結論，但仍需要先做有效決策
- 不同角色看到的 evidence 不一致，討論成本高
- 容易產生 generic 的 triage 建議，卻無法真正推進調查
- 即使有 lifecycle evidence，也可能沒有被系統化反映到 decision stage

## 8. 解決方案

本專案提出的解決方案是建立一個工程決策輔助 AI Agent，專門負責在資訊不完整的情況下，將 scattered evidence 收斂為可支撐下一步工程判斷的 decision-ready view。

目前系統可執行的流程包括：

1. 接收使用者輸入的 case 資料  
   支援文字貼上、多檔案上傳、PDF / HTML / 圖片 / TXT / JSON

2. 將輸入 evidence 正規化為統一 case structure  
   包括 issue description、comments、config、fail signal、lifecycle evidence 等欄位

3. 從 case 中抽取 decision-relevant signals  
   包括 issue family / subtype、status history、root cause / solution / retest pass 等 lifecycle evidence

4. 檢索相似 historical reference patterns  
   以 issue family、trigger、symptom、verification pattern 等資訊做輔助比對

5. 產出 decision assistance output  
   包括 decision stage、confidence、missing information、recommended action、next-step focus、HTML report

## 9. 作品特色

### 9.1 這是 AI Agent，不是 chatbot

本系統不是單純回答使用者提問，而是執行完整 decision-assistance workflow，具備 intake、normalization、retrieval、reasoning、report output 等步驟。

### 9.2 專注於 incomplete-information 下的工程決策

本專案不是要背 closed bug 的最終答案，而是要在尚未有結論時，協助團隊找對方向、抓對 evidence、做對下一步。

### 9.3 lifecycle-aware stage inference

系統會將 `clarifying / fixing / ready for DQA test / verifying / fixed / retest pass / solution / root cause` 等 lifecycle 訊號納入 decision stage 推論，而不是只看 issue 描述表面文字。

### 9.4 多來源 evidence 收斂

可將貼文字、PDF、HTML、圖片、log 等不同來源 evidence 匯整成單一 case view，降低工程討論的 context switching 成本。

### 9.5 知識治理方向清楚

本專案未來不會採無治理的自動學習，而是規劃以 provenance、trust level、human-confirmed feedback 為基礎，逐步建立 governed engineering knowledge loop。

## 10. 目前完成度

目前已完成的項目包括：

- 單一 case intake 與分析流程
- 本地 web app demo
- OCR 與多格式檔案處理
- issue family / subtype classification
- decision stage inference
- lifecycle evidence extraction
- historical retrieval
- JSON summary output
- bilingual HTML report
- benchmark-driven regression 檢查

## 11. 目前可保守主張的成果

目前可以保守主張：

- 已完成一個可執行、可展示的工程決策輔助 AI Agent prototype
- 能將多來源 case evidence 收斂成統一的 decision-ready view
- 輸出已具備工程可讀的 stage / evidence / next-step structure
- 與早期版本相比，issue subtype、decision stage 與 lifecycle-aware reasoning 已有實質提升

目前不主張：

- 已達 production-ready
- 已完全自動化取代人工判斷
- 已有未經證明的量化效益數字

## 12. 技術方法

目前系統主要使用：

- Python
- 本地 web app（Streamlit）
- rule-based + retrieval-assisted reasoning
- local OCR for scanned evidence
- normalized schema for case analysis
- HTML / JSON artifact generation

## 13. 與一般 AI 工具的差異

相較於一般 chatbot 或單次摘要工具，本專案的差異在於：

- 有明確的 engineering decision workflow
- 有 decision stage 概念
- 會處理 lifecycle evidence
- 會指出 missing information 與 unresolved gap
- 會產出可 review 的 decision artifact
- 有 knowledge accumulation with governance 的長期方向

## 14. 未來發展方向

下一步規劃包括：

- 接入 Redmine bug / note / status / attachment
- 納入 bug review meeting notes 與討論紀錄
- 建立更完整的 `CaseRecord / EvidenceRecord / KnowledgeRecord / DecisionArtifact` schema
- 增加 trust-aware retrieval ranking
- 區分 machine-generated artifact 與 human-confirmed knowledge
- 逐步形成 governed engineering knowledge loop

## 15. 適用場景

本專案適合用於：

- 跨 AE / PM / RD / DQA 的 issue review
- 尚未有最終 root cause 的中途案件
- 需要快速收斂 next-step action 的工程調查場景
- 需要將多來源證據整理為 demo-friendly / review-friendly artifact 的情境

## 16. 結語

AI Engineering Decision Agent 的價值，不在於宣稱 AI 已經知道所有答案，而在於它能在工程資訊仍不完整時，幫助團隊更快從 scattered evidence 走向 decision-ready view，進而提升後續討論與判斷效率。

