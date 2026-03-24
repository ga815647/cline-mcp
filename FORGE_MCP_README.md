# Forge MCP Server

讓 Cline 直接呼叫 forge 功能，不用跳出去跑終端機。

## 核心特性

- **無腦自動化**：commit 後自動存記憶，無需確認
- **自動瘦身**：decisionLog 超過 50 行自動裁剪
- **膨脹提醒**：systemPatterns 等檔案膨脹時提醒手動介入
- **設定檢查**：每次對話開始自動檢查是否完成初始化

## 它做什麼

```
之前：                              現在：
Cline 做完事                        Cline 做完事
  → 你跳出 Cline                     → Cline 自動呼叫 forge_umb
  → 開終端機                           → Python 寫磁碟
  → python forge.py umb                → 不離開 Cline
  → 打三個答案                         → 記憶自動存
  → 關終端機
  → 回 Cline
```

五個 tool，全部純 Python，零 LLM 呼叫：

| Tool | 功能 | 何時用 |
|------|------|-------|
| `forge_health` | 檢查設定 + memory-bank 狀態 + 膨脹警告 | 對話開始（自動） |
| `forge_lessons` | 分析 systemPatterns.md | 想提煉經驗成 skill 時 |
| `forge_umb` | 更新 memory-bank（自動裁剪） | commit 後（自動） |
| `forge_init` | 初始化 memory-bank + skills + .clinerules | 第一次使用 |
| `forge_clean` | 清理 .tmp 殘留 | 偶爾清一下 |

---

## 新專案快速啟動（3 步）

### Step 1：複製 forge_mcp.py

把 `forge_mcp.py` 複製到你的新專案根目錄：

```
your-project/
├── forge_mcp.py       ← 複製這個檔案
├── src/
├── tests/
└── ...
```

### Step 2：設定 Cline MCP

編輯 Cline 的 MCP 設定檔：

**Windows:**
```
%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

**macOS/Linux:**
```
~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

加入以下設定（改 `cwd` 為你的專案路徑）：

```json
{
  "mcpServers": {
    "forge": {
      "command": "python",
      "args": ["forge_mcp.py"],
      "cwd": "你的專案路徑",
      "disabled": false,
      "autoApprove": ["forge_health", "forge_umb", "forge_lessons", "forge_clean"]
    }
  }
}
```

⚠️ **重要：**
- `cwd` 必須是你的專案根目錄（forge_mcp.py 所在位置）
- `autoApprove` 必須包含這 4 個 tool，否則會一直彈確認框

### Step 3：初始化

在 Cline 裡說：「初始化 Forge」

Cline 會自動：
- ✅ 建立 `memory-bank/`（6 個 .md 檔）
- ✅ 建立 `skills/`
- ✅ 建立 `.clinerules`（B+ 自動記憶版本）

```
🎉 初始化完成。Cline 已準備好使用 Forge MCP。
```

**完成！** 之後每次對話 Cline 會自動：
1. 對話開始 → 呼叫 forge_health 檢查狀態
2. commit 後 → 呼叫 forge_umb 自動存記憶

---

## 日常使用

### 對話開始（自動）

```
Cline（自動）：「檢查 memory-bank 狀態...」

=== 設定檢查 ===
✅ memory-bank/ 存在
✅ 6 個記憶檔案完整
✅ .clinerules 存在
✅ skills/ 存在
✅ 所有設定完成

=== Memory Bank 狀態 ===
🟢 activeContext.md: 12 行
🟢 decisionLog.md: 45 行
🟢 systemPatterns.md: 22 行
🟢 總計約 720 token
```

### commit 後（自動）

```
你：「commit 了」
Cline（自動）：「存記憶...」
  → 呼叫 forge_umb(context="...", decision="...")
  → ✅ activeContext.md 已更新
  → ✅ decisionLog.md 已追加
  → （如果超過 50 行）🔄 decisionLog.md 已自動裁剪到 50 行
```

**你不用做任何事。** 記憶自動存。

### 膨脹提醒（自動）

如果 `systemPatterns.md` 膨脹：

```
🧹 瘦身建議：

⚠️ 需要手動介入：
  systemPatterns.md → 跑 forge_lessons，提煉成 skill
```

Cline 會主動問你要不要處理。

---

## 進階：forge_umb 參數

如果你想手動呼叫 forge_umb（通常不需要），三個參數都是 optional：

| 參數 | 寫入 | 方式 | 例子 |
|------|------|------|------|
| `context` | activeContext.md | 覆寫 | `context="正在做 SAML 整合"` |
| `decision` | decisionLog.md | 追加 + 自動裁剪 | `decision="用 lxml 處理 XML namespace"` |
| `pattern` | systemPatterns.md | 追加 | `pattern="Error handling: 用 retry decorator"` |

---

## 進階：提煉 Skill

當 memory-bank 膨脹時，Cline 會建議提煉成 skill。流程：

```
Cline：「systemPatterns.md 有 150 行，建議提煉。」
你：「跑 lessons 看看」
Cline → 呼叫 forge_lessons()
→ 📊 重複關鍵詞：error handling (5次), retry (4次), ...
→ 📋 Pattern 標題：[Error Handling], [Retry Logic], ...

你：「寫個 skill 叫 error-handling.md」
Cline：「好，我寫進 skills/error-handling.md，然後刪掉 systemPatterns.md 裡的相關內容」
你：「確認」
Cline → 建立 skills/error-handling.md + 更新 systemPatterns.md
```

Skill 會自動注入到每次對話的上下文，Cline 就會記住這些規則。

---

## .clinerules 完整版（B+ 自動記憶版本）

`forge_init` 會自動建立：

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

5. commit 後，直接呼叫 forge_umb 存入 context 和 decision。不需等使用者確認。
   只記高階意圖，不記程式碼細節。forge_umb 會自動裁剪膨脹的檔案。

6. 看到 memory-bank 膨脹警告（🟡 或 🔴）時，主動建議瘦身方案，
   並協助使用者提煉成 skill。
```

---

## 故障排除

**Q: forge_health 說設定不完整？**

檢查：
1. `cwd` 路徑是否正確（應該是 forge_mcp.py 所在目錄）
2. `autoApprove` 是否包含 4 個 tool
3. 重啟 Cline

**Q: forge_health 說 memory-bank/ 不存在？**

在 Cline 裡說「初始化 Forge」，Cline 會呼叫 forge_init。

**Q: forge_umb 存了我不想要的內容？**

```bash
git diff memory-bank/     # 看改了什麼
git checkout memory-bank/ # 還原
```

memory-bank 是純文字，完全在 git 控制下。

**Q: Windows 上 python 找不到？**

把 `"command": "python"` 改成：
- `"command": "python3"` 或
- `"command": "C:/Python312/python.exe"`（完整路徑）

**Q: 多個專案怎麼辦？**

每個專案自己的 MCP config：

```json
{
  "mcpServers": {
    "forge_project1": {
      "command": "python",
      "args": ["forge_mcp.py"],
      "cwd": "C:/path/to/project1",
      "autoApprove": ["forge_health", "forge_umb", "forge_lessons", "forge_clean"]
    },
    "forge_project2": {
      "command": "python",
      "args": ["forge_mcp.py"],
      "cwd": "C:/path/to/project2",
      "autoApprove": ["forge_health", "forge_umb", "forge_lessons", "forge_clean"]
    }
  }
}
```

切專案時 Cline 會自動載入對應的 MCP server。

---

## 為什麼用 MCP

| 之前 | 現在 |
|------|------|
| 跑 `python forge.py umb` | Cline 自動呼叫 `forge_umb` |
| 手動檢查 memory | Cline 自動呼叫 `forge_health` |
| 跳出 Cline 打斷心流 | 全程在 Cline 裡，零中斷 |
| 容易忘記存記憶 | .clinerules 強制 commit 後自動存 |
| 不確定什麼時候該做什麼 | Cline 讀 .clinerules 自動執行 |

**核心：Cline 是你的 SOP 執行者。你只需要確認理解、看結果、決定下一步。**

---

## 參考

- 詳細 SOP：見 `forge_cline_sop.md`
- 成本控制：見 SOP 裡的「典型 Cycle 成本」表格
- 初始化後的流程：見 SOP 裡的「日常流程」
