# NotebookLM 提示詞

把下面這段直接貼到 NotebookLM，並先上傳這兩個檔案：

- `docs/notebooklm/ai_engineering_decision_agent_notebooklm_master.md`
- `docs/notebooklm/09_current_progress_snapshot.md`

## 可直接貼上的提示詞

```text
請根據我上傳的資料，幫我產出一版符合 AI_Agent_Innovation_Contest_2026_Template 的 19 頁簡報大綱。

要求：
1. 中文優先，必要時保留少量英文對應。
2. 每一頁只講一個重點。
3. 要符合官方模板要求：Data Input → AI Agents → Delivery、具體資料來源、具名 Agent 與單一職責、量化效益、具名 owner、AI 技術選型、起始 domain。
4. 內容必須偏向工程決策輔助，不要寫成一般聊天機器人。
5. 請以 `09_current_progress_snapshot.md` 的內容為準，優先反映目前真的已完成的部分。
6. 目前已完成的核心能力要明確寫出：Streamlit UI、OpenClaw-style local HTTP bridge、demo launcher、knowledge base rebuild / governance。
7. 如果 older planning notes 和 current progress snapshot 有衝突，請以 current progress snapshot 為準。
8. 若證據不足，請用 likely / uncertain / reference 這種保守語氣，不要過度宣稱。
9. 不要把 closed case 當成答案標籤，不要硬寫 final root cause。
10. 不要把 OpenClaw / NemoClaw / Hermes 說成已經完整正式整合；如果只是方向，請明確標成 future alignment。
11. 請特別強調：
   - scattered engineering evidence
   - lifecycle-aware reasoning
   - uncertainty-aware output
   - governed knowledge loop
   - HTML decision artifact
   - bridge / tool gateway
   - rebuildable knowledge base
   - provenance
12. 請在每頁輸出以下欄位：
   - slide title
   - core message
   - must include bullets
   - visual / image suggestion
   - must avoid

請先輸出：
1. 一版 19 頁 slide-by-slide markdown outline
2. 一版 1 頁 executive summary markdown
3. 一版適合評審快速閱讀的中文摘要

另外，請在簡報中額外加強這三個區塊：
- Current implementation vs future alignment
- OpenClaw bridge / demo stack
- governed knowledge base / provenance
```

