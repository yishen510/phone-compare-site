# 机型命名统一报告（2026-10-31）

## 背景
数据库 485 台机型的 `name` 字段存在品牌前缀写法不一致，影响卡片/详情展示统一性，且部分「品牌词重复」（`华为HUAWEI`）看起来像 bug：

| 品牌 | 现有写法冲突 |
| --- | --- |
| 华为 | `HUAWEI`（57）vs `华为` / `华为HUAWEI`（5） |
| 三星 | `Galaxy`（21，无品牌）vs `三星Galaxy`（16） |
| 小米 | `Xiaomi`（9）vs `小米`（20）vs `MIX`（4 无前缀）vs `REDMI`（27） |
| 华硕 | `ROG`（4 无品牌）vs `华硕`（1） |
| 魅族/努比亚/一加/真我/荣耀 | 品牌词后缺空格（如 `魅族Lucky 08`） |

## 规则（已与用户确认）
1. **三星** → `三星 Galaxy`（W 系列「心系天下」不加 Galaxy，仅补空格）
2. **小米英系** → `小米`（Xiaomi 数字旗舰、MIX 折叠中文化，与「小米 15」统一）
3. **华硕 ROG** → `华硕 ROG`
4. **华为** → 统一 `HUAWEI`（去重复词「华为HUAWEI」）
5. **红米** → 保持 `REDMI`（`红米Redmi` 重复词修正）
6. **通用兜底** → 所有已知品牌词后紧接字母/数字时补一个空格

## 变更规模
共 **106 条** `name` 变更；改名后 `name` **零冲突**、**零残留**（无「品牌词直接连型号无空格」样本）。

典型对照：

| 旧 | 新 |
| --- | --- |
| Galaxy S25 | 三星 Galaxy S25 |
| 三星Galaxy Z Flip4 | 三星 Galaxy Z Flip4 |
| 三星W25 | 三星 W25 |
| Xiaomi 17 Pro | 小米 17 Pro |
| MIX Fold 4 | 小米 MIX Fold 4 |
| 华为HUAWEI Mate 60 | HUAWEI Mate 60 |
| 华为 畅享 80 | HUAWEI 畅享 80 |
| 红米Redmi K70至尊版 | REDMI K70至尊版 |
| ROG 游戏手机 9 | 华硕 ROG 游戏手机 9 |
| 魅族Lucky 08 | 魅族 Lucky 08 |

**只改 `name` 展示字段**，不动参数 / 价格 / 审计 / 规格表。搜索归一化已剥品牌前缀与空格，改名不影响命中。

## 验证
- 改名后 `name` 唯一性：485 全唯一 ✓
- 回归（全过）：
  - check_search 8/8、check_notes 4/4、check_placeholder 0 漏网
  - check_batch 22/22（修了一处 hardcode 旧名的断言，改用 id 查找更稳）
  - smoke：卡片 / 表格各 485 行，0 脚本错误
  - smoke_func 15/15、probe_features 11/11、probe_url 9 用例无崩溃（XSS 输入被转义展示）

## 文件改动（diff 极小）
- `data/phones.json`：108 行（106 条 name + 少量相邻）
- `index.html` / `_site/index.html`：各 2 行（内嵌 PHONE_DATA 单行）
- 新增 `scripts/rename_names_20261031.py`（含 `--dry` 预演、唯一性兜底、保留源换行符/缩进避免整文件 diff）
- 修正 `_jst/check_batch.js`（用 id 而非 hardcode 旧名）
