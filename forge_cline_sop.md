# Forge (Cline) — MCP-Native SOP

## 核心理念

**Opus 是你的 SOP 執行者。** 不是你記住 SOP，而是 Opus 讀 `.clinerules` 自動執行。

- `.clinerules` = Opus 的行為規則（每次對話都讀）
- `forge_*` MCP tools = 記憶管理的原子操作
- 你的工作 = 確認 Opus 的理解，看測試結果，決定下一步

---

## 日常流程

```
┌─────────────────────────────────────────────┐
│  開工                                        │
│  Opus 自動呼叫 forge_health                  │
│  ↓ 看膨脹警告 + 讀 memory-bank/ + skills/   │
└──────────┬──────────────────────────────────┘
           │
     這次要做什麼？
           │
     ├─ 一句話講得完 ──────────────── 直接 ③
     │  （改 typo、加 log、已知步驟）
     │
     └─ 一句話講不完 ──────────────── 從 ① 開始
        （新功能、架構、不確定怎麼拆）


① Plan（Opus）── 規劃
   你描述要做的事
   Opus 拆成原子步驟
   你看一眼計畫合不合理
   └─ 不合理 → 繼續在 Plan 裡修正
   └─ 合理 → 切模型 → ②

② Act（Haiku）── 執行 + 測試
   「照 Plan 做第 X 步，做完跑測試」 ← 一句話講完
   Haiku 執行 → 自動跑測試 → 你看結果
   │
   ├─ 測試過 → ③
   │
   ├─ 小問題（typo、少個 import）
   │  → 留在 Act：「修一下 X，修完跑測試」 → 看結果
   │
   ├─ 改兩次沒過
   │  → 切 Plan（Opus）分析原因 → 回 ①
   │
   └─ 方向錯了（Plan 拆的步驟有問題）
      → 切 Plan（Opus）重新規劃 → 回 ①

③ 收尾
   git add + commit（Cline 做或你做）
   Opus 自動總結改動，詢問是否存進 memory-bank
   你確認 → Opus 呼叫 forge_umb
   ↓
   ├─ 還有下一個任務 → 回最上面
   └─ 收工
```

---

## Forge MCP Tools

| Tool | 功能 | 何時呼叫 |
|------|------|--------|
| `forge_health` | 檢查 memory-bank 狀態 + 膨脹警告 | 對話開始（Opus 自動） |
| `forge_umb` | 更新 memory-bank（context / decision / pattern） | commit 後，使用者確認 |
| `forge_lessons` | 分析 systemPatterns.md，找重複關鍵詞 | 想提煉經驗成 skill 時 |
| `forge_init` | 初始化 memory-bank + skills + .clinerules | 第一次使用 |
| `forge_clean` | 清理 .tmp 殘留 | 偶爾清一下 |

---

## 什麼時候用什麼

| 情境 | 用 | 模型 | 花費 |
|---|---|---|---|
| 規劃、拆步驟 | Plan | Opus | ~$0.30 |
| 分析失敗原因 | Plan | Opus | ~$0.30 |
| 重新規劃（方向錯了）| Plan | Opus | ~$0.30 |
| 執行明確步驟 + 跑測試 | Act | Haiku | $0.07 |
| 修小 bug + 跑測試 | Act | Haiku | $0.07 |
| 看測試結果、判斷要不要繼續 | **你自己** | — | **$0** |
| 存記憶（forge_umb） | **Opus 呼叫** | — | **$0** |

**關鍵：Act 指令結尾永遠加「做完跑測試」。** 不要分兩次對話——一次講完，Haiku 做完自動跑，你看結果就好。

---

## ❌ 不要做的事

| 不要 | 為什麼 | 改成 |
|---|---|---|
| Act 指令不提測試 | Haiku 可能做完就停，不跑測試 | 指令結尾加「做完跑測試」|
| 問「你測試了沒？」| Haiku 可能用文字回答「有」但沒實際跑 | 說「跑測試」（指令，不是問句）|
| Act 完切 Plan 檢查 | 多花 $0.30/cycle，測試過就夠了 | 看測試結果，有問題才切 Plan |
| Act 改三次以上沒過 | Haiku 在繞圈子，燒錢 | 切 Plan 讓 Opus 分析根本原因 |
| 用 Act 做規劃 | Haiku 規劃品質不夠 | 切 Plan 用 Opus |
| 用 Plan 跑測試 | Opus 跑測試浪費錢 | Act 指令裡帶「做完跑測試」|
| 手動跑 forge.py | 打斷心流，Opus 無法自動化 | 讓 Opus 呼叫 forge_* tools |

---

## 典型 Cycle 成本

| 情境 | 步驟 | 花費 |
|---|---|---|
| **順利（最常見）** | Plan → Act「做X，做完跑測試」→ 過 → commit → forge_umb | $0.30 + $0.07 = **$0.37** |
| 小修不用規劃 | Act「改X，做完跑測試」→ 過 → commit → forge_umb | **$0.07** |
| Act 修一次 | Plan → Act → 沒過 → Act「修X，跑測試」→ 過 | $0.30 + $0.07 + $0.07 = **$0.44** |
| Act 修兩次沒過 | Plan → Act → 修 → 修 → 切 Plan 分析 → Act → 過 | $0.30 + $0.21 + $0.30 + $0.07 = **$0.88** |
| 純問問題 | Plan 裡 Chat 問一下 | **~$0.30** |

**大部分 cycle 是 $0.37（一次 Plan + 一次 Act）。**

---

## 一日範例

```
09:00  開工
       Opus 自動呼叫 forge_health
       → 🟢 memory 正常，讀取 activeContext.md
       → 「繼續昨天的認證模組」

09:05  你：「幫我規劃 SAML 整合，要支援 IdP metadata 自動解析」
       Opus（Plan）：拆成 4 個步驟

09:08  切 Act（Haiku）
       你：「做第 1 步：建 SAML config model，做完跑測試」
       → Haiku 建完 → 跑 pytest → 過 ✅

09:12  你：「繼續第 2 步：寫 metadata parser，做完跑測試」
       → Haiku 做完 → 跑 pytest → 失敗 ❌（XML namespace error）

09:15  你：「修 XML namespace 的問題，修完跑測試」  ← 留在 Act，不用切 Plan
       → Haiku 修好 → pytest → 過 ✅

09:18  git commit
       Opus（自動）：「這次改動：完成 SAML metadata parser，用 lxml 處理 namespace。
                    要存進 memory-bank 嗎？」
       你：「存」
       Opus → 呼叫 forge_umb(
           context="SAML 整合，step 1-2 完成",
           decision="用 lxml 而非 xml.etree 因為要處理 namespace"
       )
       ✅ memory-bank 已更新

09:20  你：「繼續第 3 步：...，做完跑測試」
       ...

12:00  4 個步驟都完成
       git commit
       Opus：「SAML 整合全部完成。要更新 activeContext 嗎？」
       你：「更新」
       Opus → forge_umb(context="SAML 整合全部完成")

       今天花費：Plan $0.30 + Act ×6 $0.42 = $0.72
       （6 次 Act 中含 1 次 retry，全程沒離開 Cline）
```

---

## .clinerules 完整版（MCP-native）

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

---

## Cheat Sheet（貼在螢幕旁邊）

```
Plan（Opus $0.30）：規劃、分析、卡住時
Act （Haiku $0.07）：執行 + 測試、小修
forge_umb（$0）：  Opus 自動呼叫，你確認

Act 指令公式：
  「做 ___，做完跑測試」

規則：
  ✅ Act 指令結尾永遠帶「做完跑測試」
  ✅ 測試過才 commit
  ✅ commit 後 Opus 自動提議 forge_umb
  ✅ 對話開始 Opus 自動呼叫 forge_health
  ❌ Act 改兩次沒過 → 切 Plan
  ❌ 別用 Plan 做 Act 的事
  ❌ 別用 Act 做 Plan 的事
  ❌ 別手動跑 forge.py（讓 Opus 呼叫 tools）
```

---

## 為什麼這樣設計

### 確定性（Consistency）

**問題：** 人容易忘記 SOP，Cline 的行為不一致。

**解決：** 把 SOP 寫進 `.clinerules`，Opus 每次對話都讀。Opus 的行為就是 SOP 的執行者。

- `.clinerules` 第 1 條 → Opus 自動呼叫 `forge_health`
- `.clinerules` 第 5 條 → Opus 自動提議 `forge_umb`
- `.clinerules` 第 6 條 → Opus 看到膨脹自動建議瘦身

**結果：** 你不用記住 SOP，Opus 自己就是 SOP。

### 零中斷（Zero Friction）

**問題：** 跑 `python forge.py umb` 需要跳出 Cline，打斷心流。

**解決：** 所有操作都是 MCP tools，Opus 直接呼叫，不離開 Cline。

### 成本控制

**問題：** 不知道什麼時候該用 Plan vs Act，容易燒錢。

**解決：** 表格清楚列出每個情境的成本。大部分 cycle 是 $0.37。

---

## 初始化

第一次使用時，Opus 會呼叫 `forge_init`：

```
你：「初始化 Forge」
Opus → 呼叫 forge_init()
→ ✅ 建立 memory-bank/
→ ✅ 建立 skills/
→ ✅ 建立 .clinerules（MCP-native 版本）
→ 🎉 初始化完成
```

之後就不用再跑 `python forge.py init` 了。

---

## 故障排除

**Q: Opus 沒有自動呼叫 forge_health？**
確認 `.clinerules` 存在且第 1 條寫著「呼叫 forge_health」。如果沒有，手動說「檢查 memory」。

**Q: forge_umb 存了我不想要的內容？**
`git diff memory-bank/` 看改了什麼，`git checkout memory-bank/` 還原。memory-bank 是純文字，完全在 git 控制下。

**Q: 怎麼知道什麼時候該切 Plan vs Act？**
看「什麼時候用什麼」表格。簡單說：不確定怎麼拆 → Plan；明確步驟 → Act。

**Q: Act 改了三次還沒過，怎麼辦？**
切 Plan，讓 Opus 分析根本原因。不要在 Act 裡繞圈子。

---

## 進階：提煉 Skill

當 memory-bank 膨脹時，Opus 會建議提煉成 skill。流程：

```
Opus：「systemPatterns.md 有 150 行，建議提煉。」
你：「跑 lessons 看看」
Opus → 呼叫 forge_lessons()
→ 📊 重複關鍵詞：error handling (5次), retry (4次), ...
→ 📋 Pattern 標題：[Error Handling], [Retry Logic], ...
→ 💡 這些值得寫成 skill 嗎？

你：「寫個 skill 叫 error-handling.md」
Opus：「好，我寫進 skills/error-handling.md，然後刪掉 systemPatterns.md 裡的相關內容」
你：「確認」
Opus → 建立 skills/error-handling.md + 更新 systemPatterns.md
```

Skill 會自動注入到每次對話的上下文，Opus 就會記住這些規則。

---

## 總結

| 之前 | 現在 |
|------|------|
| 你記住 SOP | Opus 讀 .clinerules 執行 SOP |
| 跑 `python forge.py umb` | Opus 呼叫 `forge_umb` |
| 手動檢查 memory | Opus 自動呼叫 `forge_health` |
| 不確定什麼時候該做什麼 | 表格清楚列出每個情境 |
| 容易忘記測試 | .clinerules 強制「做完跑測試」 |

**核心：Opus 是你的 SOP 執行者。你只需要確認理解、看結果、決定下一步。**
