# Forge MCP Server

讓 Cline 直接呼叫 forge 功能，不用跳出去跑終端機。

## 它做什麼

```
之前：                              現在：
Cline 做完事                        Cline 做完事
  → 你跳出 Cline                     → Cline 呼叫 forge_umb
  → 開終端機                           → Python 寫磁碟
  → python forge.py umb                → 不離開 Cline
  → 打三個答案
  → 關終端機
  → 回 Cline
```

五個 tool，全部純 Python，零 LLM 呼叫：

| Tool | 功能 | 何時用 |
|------|------|-------|
| `forge_health` | 回傳 memory-bank 狀態 + 膨脹警告 | 對話開始（Opus 自動） |
| `forge_lessons` | 分析 systemPatterns.md | 想提煉經驗成 skill 時 |
| `forge_umb` | 更新 memory-bank（context / decision / pattern）| commit 後，使用者確認 |
| `forge_init` | 初始化 memory-bank + skills + .clinerules | 第一次使用 |
| `forge_clean` | 清理 .tmp 殘留 | 偶爾清一下 |

## 安裝

### 1. 裝 MCP SDK

```bash
pip install mcp
```

### 2. 放 forge_mcp.py

把 `forge_mcp.py` 放到你的專案根目錄：

```
your-project/
├── forge_mcp.py       ← MCP Server
├── memory-bank/
├── skills/
├── .clinerules
└── ...
```

### 3. 設定 Cline MCP

編輯 Cline 的 MCP 設定檔：

**Windows:**
```
%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

**macOS/Linux:**
```
~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

加入以下設定：

```json
{
  "mcpServers": {
    "forge": {
      "command": "python",
      "args": ["forge_mcp.py"],
      "cwd": "f:/Programs/forge_light",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

⚠️ **`cwd` 必須是你的專案根目錄**（memory-bank/ 所在位置）。

### 4. 驗證

在 Cline 裡說：「初始化 Forge」

Cline 應該會呼叫 `forge_init` 並回傳：

```
✅ 建立 memory-bank/activeContext.md
✅ 建立 memory-bank/progress.md
✅ 建立 memory-bank/systemPatterns.md
✅ 建立 memory-bank/productContext.md
✅ 建立 memory-bank/decisionLog.md
✅ 建立 memory-bank/techContext.md
✅ 建立 .clinerules（MCP-native 版本）

🎉 初始化完成。Cline 已準備好使用 Forge MCP。
```

## 使用方式

### forge_init — 第一次初始化

```
你：「初始化 Forge」
Opus → 呼叫 forge_init()
→ 建立 memory-bank/ + skills/ + .clinerules
→ 🎉 完成
```

### forge_health — 對話開始自動檢查

`.clinerules` 第 1 條會讓 Opus 自動呼叫：

```
Opus（自動）：「檢查 memory-bank 狀態...」
→ 🟢 activeContext.md: 12 行
→ 🟢 decisionLog.md: 45 行
→ 🟢 systemPatterns.md: 22 行
→ 🟢 總計約 720 token
```

或者你手動說「檢查 memory」，Opus 會呼叫 `forge_health`。

### forge_umb — 存記憶（最重要的 tool）

**正確流程：你確認後 Opus 才呼叫。**

```
你：「commit 了」
Opus（自動）：「這次改動：完成 SAML metadata parser，用 lxml 處理 namespace。
              要存進 memory-bank 嗎？」
你：「存」
Opus → 呼叫 forge_umb(
    context="SAML 整合，metadata parser 完成",
    decision="用 lxml 而非 xml.etree，原因是要處理 XML namespace"
)
→ ✅ activeContext.md 已更新
→ ✅ decisionLog.md 已追加
```

**三個參數都是 optional：**

| 參數 | 寫入 | 方式 | 什麼時候用 |
|------|------|------|----------|
| `context` | activeContext.md | 覆寫 | 「現在在忙什麼」變了 |
| `decision` | decisionLog.md | 追加 | 做了重要決定 |
| `pattern` | systemPatterns.md | 追加 | 踩到坑或發現規範 |

### forge_lessons — 提煉經驗

```
你：「跑 lessons 看看有什麼值得提煉」
Opus → 呼叫 forge_lessons()
→ 📊 重複關鍵詞：error handling (5次), retry (4次), ...
→ 📋 Pattern 標題：[Error Handling], [Retry Logic], ...
→ 💡 這些值得寫成 skill 嗎？
```

### forge_clean — 清 .tmp

```
你：「清一下 tmp」
Opus → 呼叫 forge_clean()
→ 🧹 清掉 3 個 .tmp 檔案
```

## .clinerules 完整版（MCP-native）

`forge_init` 會自動建立這個版本：

```
# Forge Rules for Cline

1. 每次對話開始，呼叫 forge_health 檢查 memory-bank 狀態。
   讀取 memory-bank/ 和 skills/ 裡的所有 .md 檔案作為上下文。

2. 收到模糊需求時，先用一段話複述你的理解（打算做什麼、影響範圍、假設），
   確認後再開始。

3. 改完 code 後立即執行測試指令（pytest / npm test / make test）。
   不要只回報「已完成」——要實際跑測試並貼出結果。測試通過才 commit。

4. 不要在 memory-bank/ 檔案裡記錄程式碼細節（變數名、API 列表），
   那些交給 codebase 本身。只記高階意圖與決策原因。

5. commit 後，用一段話總結這次改動的意圖和決策，詢問使用者是否要存進 memory-bank。
   使用者確認後才呼叫 forge_umb。不要自行決定記憶內容。

6. 看到 memory-bank 膨脹警告（🟡 或 🔴）時，主動建議瘦身方案，
   並協助使用者提煉成 skill。
```

## 安全設計

| 疑慮 | 設計 |
|------|------|
| Cline 會不會亂寫記憶？ | forge_umb 的 docstring 明確寫「呼叫前先跟使用者確認」+ .clinerules 第 5 條強化 |
| 寫錯了怎麼辦？ | memory-bank/ 是純文字，git diff 看得到，git checkout 還原 |
| MCP Server 會不會呼叫 LLM？ | 不會。forge_mcp.py 全部是 Path.read_text / write_text，零 API 呼叫 |

## 故障排除

**Q: Cline 說找不到 forge MCP server？**
確認 `cwd` 路徑正確，且 `forge_mcp.py` 在那個目錄裡。在終端機 `cd` 到那個目錄跑 `python forge_mcp.py` 看有沒有 error。

**Q: forge_health 回傳「memory-bank/ 不存在」？**
先呼叫 `forge_init`。

**Q: forge_umb 存了我不想要的內容？**
`git diff memory-bank/` 看改了什麼，`git checkout memory-bank/` 還原。memory-bank 是純文字，完全在 git 控制下。

**Q: Windows 上 python 找不到？**
把 `"command": "python"` 改成 `"command": "python3"` 或完整路徑 `"command": "C:/Python312/python.exe"`。

**Q: 多個專案怎麼辦？**
每個專案自己的 `forge_mcp.py` + 自己的 MCP config `cwd`。切專案時 Cline 會載入對應的 MCP server。

## 進階：提煉 Skill

當 memory-bank 膨脹時，Opus 會建議提煉成 skill。流程：

```
Opus：「systemPatterns.md 有 150 行，建議提煉。」
你：「跑 lessons 看看」
Opus → 呼叫 forge_lessons()
→ 📊 重複關鍵詞：error handling (5次), retry (4次), ...
→ 📋 Pattern 標題：[Error Handling], [Retry Logic], ...

你：「寫個 skill 叫 error-handling.md」
Opus：「好，我寫進 skills/error-handling.md，然後刪掉 systemPatterns.md 裡的相關內容」
你：「確認」
Opus → 建立 skills/error-handling.md + 更新 systemPatterns.md
```

Skill 會自動注入到每次對話的上下文，Opus 就會記住這些規則。

## 為什麼用 MCP

| 之前 | 現在 |
|------|------|
| 跑 `python forge.py umb` | Opus 呼叫 `forge_umb` |
| 手動檢查 memory | Opus 自動呼叫 `forge_health` |
| 跳出 Cline 打斷心流 | 全程在 Cline 裡，零中斷 |
| 容易忘記存記憶 | .clinerules 強制 commit 後提議 |
| 不確定什麼時候該做什麼 | Opus 讀 .clinerules 自動執行 |

**核心：Opus 是你的 SOP 執行者。你只需要確認理解、看結果、決定下一步。**

## 參考

- 詳細 SOP：見 `forge_cline_sop.md`
- 成本控制：見 SOP 裡的「典型 Cycle 成本」表格
- 初始化後的流程：見 SOP 裡的「日常流程」
