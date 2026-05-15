# AI Engineering Decision Agent NotebookLM Master Pack

> 單檔版 NotebookLM source pack。上傳這一份就夠了。
>
> 這份文件把官方模板要求、專案背景、流程、治理、效益與未來整合方向整合在一起，方便 NotebookLM 直接拿來產出簡報大綱、摘要頁與文案。

## 0. 使用方式

- 這份文件是單一來源版本，避免再散成多個 markdown。
- 如果要讓 NotebookLM 產出簡報，請用中文優先的方式詢問。
- 內容原則是 `decision assistance`，不是一般聊天機器人。
- 證據不足時請用 `likely / uncertain / reference`，不要過度宣稱。

## 1. 官方模板真正要的內容

官方 `AI_Agent_Innovation_Contest_2026_Template.pptx` 要求的不是純技術報告，而是一份能讓評審快速看懂的 AI Agent 提案。

它特別在意：

- 這個 Agent 解什麼問題
- 資料從哪裡來
- Agent 如何分工與決策
- 輸出長什麼樣子
- 有沒有量化效益
- 有沒有具名 owner / business users / AI builder
- 用了哪些 AI 技術與平台
- 起始 domain 是什麼
- 怎麼跟公司既有 AI 生態對齊
- 後續怎麼擴充與治理

### 官方要求的 19 頁結構

1. 封面
- `Project Title`
- `Domain — Key Area & Application`
- `Core Team`
- `Date`

2. 目錄
- Executive Summary
- Business Scenario & Pain Point
- Agent Workflow & Architecture
- OpenClaw / NemoClaw / Hermes Agent Alignment
- Demo / Prototype / Current Progress
- Business Impact & Quantified Benefits
- Feasibility & Scaling Plan
- Appendix

3. 官方寫作指引
- 要有清楚的 `Data Input → AI Agents → Delivery` 流程圖
- 要具體列出資料來源，不能只寫「內部資料」
- 要明確寫出每個 AI Agent 的名字與單一職責
- 要有可量化的效益
- 要寫出具名 owner / business users / AI builder
- 要寫清楚 LLM、平台、整合方式
- 要先鎖定一個起始 domain

4. Executive Summary
- Data Input
- AI Agents
- Delivery
- Resources
- AI Platform
- quantified benefit
- starting domain
- owner

5. Example summary page
- 這是版型範例，不是要照抄內容

6. Reference-only page
- 這一頁只是引導，不是正式內容

7. Business Scenario & Pain Point
- 誰在用
- 現行流程怎麼做
- 痛點是什麼
- 影響範圍有多大

8. Agent Workflow
- 導入後流程怎麼改
- Agent 如何主動決策
- 如何與資料或系統互動

9. Technical Architecture
- 資料層、推理層、交付層怎麼分工

10. Alignment
- 現有原型如何對齊 OpenClaw / NemoClaw / Hermes Agent

11. Demo / Current Progress
- 現在做到哪裡
- 有沒有可展示的 prototype
- 有沒有影片或測試結果

12. DEMO
- 若仍在提案階段，可用使用者情境表達完成後的樣子

13. Business Impact & Quantified Benefits
- productivity improvement
- process optimization
- cost savings
- accuracy enhancement
- revenue impact
- ROI

14. Feasibility & Scaling Plan
- 怎麼落地
- 風險限制
- 後續可以擴到哪些 BU / Domain / Region

15. Executive Summary supplement
- 補充說明頁

16. Appendix
- 技術細節
- 測試數據
- 流程截圖
- Prompt / Agent 設計

17. More one-page examples
- 更多摘要頁範例

18. Leads Discovery example 1
- 用來理解摘要頁如何把流程、平台、owner、效益放在一起

19. Leads Discovery example 2
- 延續範例，重點是人、資料、平台、輸出要一起說清楚

## 2. Project Identity

- **Project name**: AI Engineering Decision Agent
- **One-line summary**: turn scattered engineering evidence into a decision-ready view
- **Core audience**: AE / PM / RD / DQA
- **What it is**: an engineering decision-assistance Agent
- **What it is not**: a generic chatbot, a final root-cause oracle, or a benchmark answer memorizer

### Names to fill before final submission

- **Project Owner**: `[fill with real name]`
- **Business Users**: `[fill with real names and regions]`
- **AI Builder**: `[fill with real name(s)]`

## 3. Project Goal

The project improves decision assistance quality under incomplete information.

It helps the team move faster from:

- fragmented evidence
- uncertain lifecycle state
- open questions
- repeated context switching

to:

- a decision-ready summary
- a clear next-step recommendation
- a reviewable HTML artifact

## 4. Problem Statement

Engineering case data is usually scattered across many places:

- issue descriptions
- comments and discussion threads
- logs
- PDF / HTML reports
- screenshots
- test results
- status history
- meeting notes
- known issue references

The real bottleneck is not only reading the data.

The bottleneck is aligning:

- evidence
- lifecycle state
- uncertainty
- missing information
- next action

### Why lifecycle signals matter

Lifecycle evidence should be treated as a first-class signal, not incidental wording.

Examples:

- `clarifying`
- `fixing`
- `ready for DQA test`
- `verifying`
- `fixed`
- `retest pass`
- `root cause`
- `solution`

These signals should strongly influence:

- decision stage
- action mode
- resolution state
- next-step recommendation

## 5. Input Sources

Recommended sources for this project:

- Redmine bug / task / note / attachment
- `decision_agent/knowledge_base/redmine_bug_summary_merged.csv`
- `decision_agent/knowledge_base/BUG Review/`
- logs
- PDF and HTML reports
- screenshots
- OCR output for scanned evidence
- comments and review notes
- meeting notes
- manual engineer summaries

Each source should preserve provenance:

- source type
- source path or link
- author or speaker when available
- timestamp
- extraction status

## 6. Agent Workflow

The agent workflow should be understood as a sequence of focused steps:

1. **Intake**
   - collect case text, logs, PDFs, screenshots, and notes

2. **Normalize**
   - turn scattered evidence into a consistent case record

3. **Extract lifecycle signals**
   - identify `clarifying`, `fixing`, `verifying`, `fixed`, `retest pass`, `solution`, `root cause`

4. **Retrieve**
   - find similar cases, known issues, and verification patterns

5. **Infer**
   - issue family
   - issue subtype
   - decision stage
   - confidence
   - uncertainty

6. **Recommend**
   - missing information
   - decisive evidence
   - next-step focus
   - smallest useful follow-up action

7. **Report**
   - generate a shareable HTML decision artifact

## 7. Output Schema

The final decision artifact should include:

- issue family
- issue subtype
- decision stage
- action mode
- resolution state
- confidence
- decisive evidence
- unresolved gap
- missing information
- likely root-cause hypothesis
- recommended action
- next-step focus
- lifecycle evidence summary

The key is to make the output useful for review, not to claim final certainty.

## 8. Knowledge Governance

The project uses a governed knowledge loop.

Recommended trust levels:

- **low**
  - raw case data
  - open discussion
  - machine-only summary

- **medium**
  - reviewed summary
  - strong but not fully confirmed evidence

- **high**
  - human-confirmed root cause
  - human-confirmed solution
  - human-confirmed verification result

Recommended write-back objects:

- `CaseRecord`
- `EvidenceRecord`
- `KnowledgeRecord`
- `DecisionArtifact`

The repository should keep raw data, machine artifacts, and human-confirmed knowledge separate.

## 9. Current Implementation Status

The current project already supports a working prototype style demo.

Current demo elements include:

- Streamlit-style UI
- case text input
- file upload support
- local OCR for scanned evidence
- local Gemma 4 mode
- deterministic fallback when the model is unavailable
- HTML decision report output
- multi-case review artifacts

### Runtime, Bridge, and Knowledge Base

- The Streamlit UI is the human-facing entry point for the demo.
- The local OpenClaw-style bridge exposes health and tool endpoints on `http://127.0.0.1:8787`.
- The bridge can serve `analyze_single_case` as a local tool layer for agent-style workflows.
- `demo.bat`, `start_demo.bat`, `start_demo.ps1`, `stop_demo.bat`, and `stop_demo.ps1` control the demo stack.
- The bridge can run in local Gemma 4 mode or deterministic fallback mode.
- The knowledge base can be rebuilt from `decision_agent/knowledge_base/redmine_bug_summary_merged.csv` and `decision_agent/knowledge_base/BUG Review/` into a generated SQLite artifact under `.tmp/knowledge_base.generated.sqlite3`.
- The generated SQLite knowledge base is a rebuildable artifact, not a human-confirmed source of truth.

The project should be described as a prototype that is already useful, not as a fully deployed enterprise platform.

## 10. Quantified Benefit

Use conservative numbers and phrase them carefully.

The current story should say:

- a first-pass manual review can be reduced from tens of minutes to a much shorter initial decision view
- context switching is reduced
- stage inference becomes more consistent
- follow-up becomes faster

If a number is still an estimate, say so explicitly.

## 11. Future Integration Alignment

The project should be framed as future-compatible with the company AI ecosystem.

### OpenClaw

Likely role:

- workflow orchestration
- intake
- tool gateway / local bridge
- retrieval
- report generation

### NemoClaw

Likely role:

- governed engineering knowledge
- issue history
- known issue patterns
- retrieval memory
- rebuildable knowledge base

### Hermes Agent

Likely role:

- action and system integration
- Redmine
- log repository
- test report
- follow-up actions

Important boundary:

- do not say these are already fully integrated
- the current code already has a local bridge and governed KB rebuild, but the broader OpenClaw / NemoClaw / Hermes story should still be presented as alignment and scaling direction
- present them as future alignment directions

## 12. Recommended Deck Story

For a contest deck, the slide story should be:

- Slide 1: title, domain, team, date
- Slide 2: table of contents
- Slide 3: official template expectations
- Slide 4: one-page executive summary
- Slide 5: concrete example summary structure
- Slide 6: reference-only note
- Slide 7: business scenario and pain point
- Slide 8: agent workflow
- Slide 9: technical architecture
- Slide 10: OpenClaw bridge / local tool gateway
- Slide 11: governed knowledge base and provenance
- Slide 12: OpenClaw / NemoClaw / Hermes alignment
- Slide 13: current progress
- Slide 14: demo scene or prototype showcase
- Slide 15: quantified benefit
- Slide 16: feasibility and scaling plan
- Slide 17: executive summary supplement
- Slide 18: appendix
- Slide 19: more one-page summary examples

## 13. Visual Direction

For the final deck, the visual style should be:

- Chinese-first
- one slide, one message
- image-driven
- fewer paragraphs, more diagrams
- readable from a distance

Good visual types:

- evidence bridge diagram
- bridge health / manifest panel
- workflow pipeline
- architecture layers
- knowledge base rebuild flow
- decision dashboard mockup
- governance loop
- stage matrix

Avoid:

- huge text blocks
- unreadable full-page screenshots
- generic abstract images without context

## 14. What Not to Claim

- do not present the project as a generic chatbot
- do not claim final root-cause certainty when evidence is incomplete
- do not say historical cases are answer keys
- do not say OpenClaw / NemoClaw / Hermes Agent are already fully integrated
- do not say the generated SQLite knowledge base is a trusted final answer source
- do not turn raw machine summaries into trusted knowledge

## 15. Short Summary

AI Engineering Decision Agent is an engineering decision-assistance Agent.

It turns scattered evidence into a decision-ready view, keeps uncertainty visible, and supports better next-step action under incomplete information.
