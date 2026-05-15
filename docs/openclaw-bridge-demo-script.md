# OpenClaw Bridge 現場展示腳本

## 這個 demo 要證明什麼

這個 demo 要證明的，不只是我們有一個 Streamlit 網頁。

更重要的是，這個專案後面還有一層可以被 agent 呼叫的本機 HTTP 工具層，也就是 OpenClaw-style bridge。

在這個 repo 裡，角色分工是：

- `web_app/`：給人看的 Streamlit UI
- `decision_agent/openclaw_bridge.py`：OpenClaw-style bridge
- `decision_agent/service.py`：真正的決策核心
- `Gemma 4`：目前 demo profile 裡的本地 note 輔助層

你在現場最重要的一句話可以是：

> OpenClaw 是 orchestration / tool gateway 層，不是決策引擎本身。

## 建議的啟動方式

先用一鍵啟動：

```powershell
.\demo.bat
```

如果 demo 結束後要關掉：

```powershell
.\stop_demo.bat
```

## 啟動後應該看到什麼

啟動完成後，你應該可以打開：

- `http://127.0.0.1:8501`，這是 Streamlit UI
- `http://127.0.0.1:8787/health`，這是 OpenClaw bridge 健康檢查
- `http://127.0.0.1:8787/manifest`，這是 tool manifest

bridge 的健康檢查最好要看到：

- `assistant_mode: local`
- `local_model_configured: true`
- `local_model_model: google/gemma-4-26B-A4B-it`

## 現場展示流程

### 1. 先開人看的 UI

先打開 Streamlit 頁面，並簡單說：

- 這是給人操作的入口
- 可以貼 case 文字，也可以上傳檔案
- 會輸出 decision-ready analysis 和 HTML report

這段不用講太多，重點是先讓大家知道：bridge 不是取代 UI，而是補在 UI 後面。

### 2. 再秀 bridge health

打開：

```text
http://127.0.0.1:8787/health
```

你可以這樣講：

- 這是 OpenClaw-style tool layer
- 它跟 UI 是分開的
- 這層提供穩定的契約給 agent runtime 呼叫
- 目前 demo profile 已經接到本地 Gemma 4

你可以指給大家看：

- `assistant_mode`
- `assistant_style`
- `local_model_configured`
- `local_model_model`

### 3. 再秀 tool manifest

打開：

```text
http://127.0.0.1:8787/manifest
```

你可以這樣講：

- 這是 agent 可以先讀到的工具契約
- 重點工具是 `analyze_single_case`
- agent 不需要知道 repo 內部怎麼寫
- 它只要知道 tool 名稱和 input schema 就行

你可以指給大家看：

- `analyze_single_case`
- `case_input`
- `case_path`
- `assistant_mode`
- `assistant_style`
- `local_model`

### 4. 實際跑一次 bridge call

先用這個 sample case：

- `decision_agent/input/case_003_dqa_issue.json`

PowerShell 範例：

```powershell
$body = @{
  case_path = "E:\decision-agent-demo\decision_agent\input\case_003_dqa_issue.json"
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8787/tools/analyze_single_case" `
  -ContentType "application/json" `
  -Body $body
```

你可以這樣講：

- 這其實是同一套 decision core
- 只是現在被包成一個可以呼叫的 tool
- bridge 回傳的是結構化 summary 和 assistant note
- note 層可以用 local model，但 demo 也有 deterministic fallback，所以不會因為模型卡住就整個失敗

你可以指給大家看的欄位：

- `summary`
- `assistant`
- `meta.assistant_mode`
- `meta.local_model_configured`
- `summary.issue_family`
- `summary.decision_stage`
- `summary.missing_information`
- `summary.recommended_action`

### 5. 再切回 Streamlit UI

把畫面切回 Streamlit，讓大家看到同一個 case 在 UI 上的結果。

你可以這樣講：

- UI 是給人看的
- bridge 是給 agent runtime 與 orchestration 用的
- 兩層其實都在呼叫同一個 decision core

如果要補最後的分享 artifact，可以打開：

- `output/web_app/html/case_003_dqa_issue.html`

## 可以直接念的口條

你可以直接這樣講：

> 你現在看到的，不只是一般網頁。  
> Streamlit 頁面是給人操作的入口，但這次競賽真正重要的是後面的 OpenClaw-style bridge。  
> 這個 bridge 把同一套 decision core 變成本機 HTTP tool，所以 agent runtime 不需要知道我們內部 Python 的結構，就可以直接呼叫。  
> 當我把 case 送進 bridge，它回來的不是單純一句回答，而是一份 decision-ready summary，包含 issue family、subtype、decision stage、missing information、recommended action，以及 confidence context。  
> 所以這個 demo 的價值，不是單純模型回覆，而是一條把 scattered evidence 變成可被工具呼叫的 decision workflow。  

如果你想講短一點，可以在「decision-ready summary」後面停住。

## 現場應該強調什麼

- OpenClaw 是 orchestration / tool gateway 層
- 真正的 decision engine 仍然是 `decision_agent`
- bridge 提供穩定 API contract
- demo 已經接到本地 Gemma 4
- 如果模型層暫時不可用，系統還是有 fallback

## 現場不要過度承諾

- 不要說 bridge 取代了人的判斷
- 不要說系統已經知道最終 root cause
- 不要說這是正式 production 的 OpenClaw 整合
- 不要說 model layer 才是這個專案的主價值

## 如果現場出現狀況

- 如果 web app 有開，但 bridge 沒健康，先看 `http://127.0.0.1:8787/health`
- 如果 bridge port 被占用，先跑 `.\stop_demo.bat` 再重啟
- 如果 local model 回得慢，就先把 demo 往前推，靠 deterministic fallback 撐住
- 如果想穩一點，可以直接用 Streamlit UI 展示 `case_003_dqa_issue.json`

## 收尾句

> 我們要做的，不是單次聊天機器人，而是把散落的工程 evidence 變成可被工具呼叫的決策工作流。

