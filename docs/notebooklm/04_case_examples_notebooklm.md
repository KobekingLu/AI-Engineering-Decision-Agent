# AI Engineering Decision Agent｜代表案例包（NotebookLM 版）

## 這份文件的用途
這份文件專門提供 NotebookLM 在生成簡報、demo script、評審 Q&A 時使用的案例來源。
用途不是逐字重述 case，而是幫 NotebookLM 知道：
- 哪些案例最值得拿來講
- 每個案例代表什麼能力
- 如何用案例證明這不只是 summarizer

---

## 案例 1｜Triage case
### Case ID
143084

### 案件定位
這是一個典型的新案初判情境，重點不是立即找出最終 root cause，而是先判斷問題類型與下一步最有效的檢查方向。

### 問題摘要
案件中，E3.S device 在 Node 2 被偵測為 x2 PCIe link width，而預期應為 x4。實際 comment 也提到對調不同 E3.S device 與拆 tray 後，異常仍跟隨同一路徑。這類 evidence 比較像是 path / slot / tray 相關問題，而不是單純 device 本身故障。

### Agent 主要輸出
- issue family：PCIe
- issue subtype：link width downgrade
- decision stage：triage
- action mode：triage
- resolution state：open
- 建議下一步：優先確認 x2 是否固定在同一 node / slot / tray，而不是先全面重跑壓力測試

### 為什麼這個案例重要
它能證明 Agent 不是看到 PCIe 就只回「請檢查 hardware」，而是能把新案整理成具體可執行的初判方向。

### 這個案例拿來證明的能力
- 新案 triage
- issue family / subtype inference
- next-step guidance
- decision-ready view under incomplete information

### 簡報可怎麼講
這個案例用來證明：Agent 可以把一個還沒有 fix path 的新案，快速收斂成具有明確下一步的 triage artifact。

---

## 案例 2｜Verification case
### Case ID
135177

### 案件定位
這是一個典型 verification 情境。表面上看起來已有 PASS signal 與 Ready for DQA test，但真正的重點是：是否已在原 fail condition 下補齊 enough evidence，足以支持往 closure 前進。

### 問題摘要
案例中出現 Uncorrectable PCIe AER / ACS violation，且 comment 指出 Reboot cycle 與 DC power cycle 測試可 PASS，但問題只在 AC power loss restore 條件下出現。這表示並不是單純「已經好了」，而是需要更精準地回到原 trigger condition 做複驗。

### Agent 主要輸出
- issue family：PCIe
- issue subtype：uncorrectable AER or ACS violation
- decision stage：verification
- lifecycle status：Ready for DQA test
- lifecycle signals：verification signal、PASS signal
- 建議下一步：優先回到原 AC restore / runtime trigger 下，確認 failing AER signature 已消失，並補齊 before/after verification logs

### 為什麼這個案例重要
它能證明 Agent 會讀 lifecycle signal，但不會因為看到 fixed-like wording 就直接誤判成 closure-ready。它會要求證據回到原 fail condition 下被驗證。

### 這個案例拿來證明的能力
- lifecycle-aware reasoning
- verification stage inference
- 原 fail condition 思維
- missing evidence / unresolved gap 指出

### 簡報可怎麼講
這個案例用來證明：Agent 不只是做 bug 摘要，而是會因 lifecycle signal 與 trigger condition 不同，要求不同層次的 verification evidence。

---

## 案例 3｜Closure case
### Case ID
141307

### 案件定位
這是一個接近 closure 的案例。重點是整理哪些 evidence 足以支持結案，而不是只看到 Fixed 就直接結束。

### 問題摘要
案例與 memory margin / DIMM population sensitive 有關。comment 指出在 only one DIMM per channel 的條件下可以 PASS，代表該問題與 DIMM population topology 有明顯關聯。Agent 將其視為 closure stage，但同時提醒 closure package 仍需整理 final BIOS / DIMM matrix 與 traceable closure note。

### Agent 主要輸出
- issue family：memory
- issue subtype：DIMM population sensitive
- decision stage：closure
- action mode：close
- resolution state：fixed_verified
- 建議下一步：整理 final BIOS / DIMM matrix、PASS evidence on original fail case、closure note

### 為什麼這個案例重要
它能證明 Agent 不只是說「已 Fixed」，而是能把 closure 前真正該整理的 evidence package 點出來。

### 這個案例拿來證明的能力
- closure stage inference
- closure package thinking
- PASS evidence interpretation
- structure-aware decision artifact output

### 簡報可怎麼講
這個案例用來證明：Agent 不只支援 triage，也能支援接近結案的 evidence organization。

---

## 三個案例合在一起要傳達什麼
這三個案例合起來，不是在展示三種 bug，而是在展示三種 **decision stage**：
- **Triage**：先找對問題家族與下一步檢查路線
- **Verification**：不要太早當成已解決，要確認原 fail condition 下的 retest evidence
- **Closure**：要整理 closure package，而不是只看 status

這是本作品最重要的 demo 主張之一：
**它不是單一 bug summarizer，而是能協助不同 decision stage 的工程判斷。**

---

## 給 NotebookLM 的使用提醒
當你根據這份文件生成簡報、demo script 或 Q&A 時：
- 不要把案例講成最終 root cause 已完全確定
- 要強調每個案例代表的是 decision-assistance capability
- 優先講「這個案例證明了什麼能力」，而不只是案件內容本身
- 若篇幅有限，請優先保留 triage / verification / closure 這三個 decision stage 的對照
