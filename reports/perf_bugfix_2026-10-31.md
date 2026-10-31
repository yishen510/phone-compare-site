# 效率优化与缺陷修复报告（2026-10-31）

## 〇、上下文与适用范围

- 技术栈：纯静态单文件站点（HTML + 原生 JS + 内联 CSS），无框架、无后端；`data/phones.json` 为数据真值，`scripts/*.py` 为数据管线，`_jst/*.js` 为 jsdom / Edge-CDP 测试。
- 规模：485 条机型，`index.html` 4.06 MB（内嵌 `PHONE_DATA` 约 2.8 MB）。
- 基线：移动端 390×844 + CPU 4× 降速（`_jst/ux_bench.js`）。
- **不适用维度（明确标注，非漏查）**：无数据库 → 无「数据库查询」；无服务端 → 无「网络 I/O 热点」（仅可选报价 API，且未配置后端时不发请求）；数据内嵌 → 无运行时磁盘 I/O。

---

## 一、结论摘要

| 指标（移动端 CPU 4×） | 修复前 | 修复后 | 变化 |
| --- | --- | --- | --- |
| 首屏到卡片画完 | 7820 ms | **5393 ms** | **-31%** |
| 切换到表格视图 | 2465 ms | **1367 ms** | **-45%** |
| 表格点击排序 | 2692 ms | **1643 ms** | **-39%** |
| 搜索「骁龙」到结果画完 | 90 ms | 82 ms | -9% |
| 清空搜索恢复全部 | 90 ms | 83 ms | -8% |

修复 7 处；新增 17 项「行为不变」测试；全部 10 个测试通过。

---

## 二、问题清单（按严重级别）

| # | 级别 | 位置 | 问题 | 触发条件 | 影响范围 |
| --- | --- | --- | --- | --- | --- |
| 1 | **P0 高** | `index.html` `syncCardMotion()` + `MutationObserver`（约 2673–2690 行） | observer 每次 `childList` mutation 都**全量** `querySelectorAll('.phone-card')` 并逐张写样式 | 首屏 / 筛选后分批插入（48 + 96×N 批） | O(n²)：485 张卡片被反复扫描；首屏与重绘卡顿（实测主要热点） |
| 2 | **P0 高** | `index.html` `filtered()` 排序比较器（约 1568–1582 行） | 比较器内重复调用 `priceOf`/`batKeyOf`/`wtKeyOf`/`recScreen` | 任意排序 | 485 条排序约 **8000 次**重复解析正则；`recScreen`→`specFind`→`specList` 每台线性扫 50~80 条字段 |
| 3 | **P0 高** | `index.html` `specList()`（约 1799 行） | 每次调用都 `p.specs.filter()` **重建数组**，无缓存 | 所有 `specFind` 调用（排序/详情/对比/推荐） | 重复分配 + 重复遍历，是 #2 的成本放大器 |
| 4 | P1 中 | `index.html` 搜索二次排序 + `relScore()`（约 1583–1590 / 1966 行） | 比较器每对比较都跑 `relScore`，内部含 `tighten()` 全角转换正则 | 搜索时 | 约 8000 次 `tighten`；搜索响应可再降 |
| 5 | P1 中 | `index.html` `ensureDetailList()`（约 1979 行） | 打开详情时重新 `filtered()` 全量过滤 + 排序 | 每次打开详情/翻页 | 重复计算 485 条；移动端详情打开延迟 |
| 6 | P2 低 | `index.html` `setText()`（约 1478 行） | `if($(id))$(id).textContent=v` 两次 `getElementById` | 每次 `render()` 多次调用 | 微量冗余 DOM 查询 |
| 7 | P2 低 | `index.html` `render()`（约 1780 行） | `new Set(phones.map(p=>p.brand)).size` 每次重算 | 每次 `render()` | 冗余 map 485 条（值恒定） |

---

## 三、根因分析

1. **#1 分批绘制与 observer 叠加**：分批本身是为首帧收益；但 observer 回调没有合并/去重，`paintGrid` 每插一批触发一次 mutation → 每批都全量重扫。插入 N 批使总工作量从 O(n) 放大到 O(n²)。这是「首屏 7.8s」的最大可控成分。
2. **#2 比较器无 key 缓存**：JS `Array.sort` 的比较器被调用 O(n log n) 次，而排序 key 只依赖**单条记录**，天然可预计算；当前实现每次比较都重新跑正则/扫描参数表。
3. **#3 specList 无缓存**：`p.specs` 是只读数据，`filter` 结果对同一 id 恒定，却被反复重建。
4. **#4 relScore 无缓存**：相关性分数只依赖（记录, 查询词），可在排序前一次算好。
5. **#5 详情列表重复计算**：`render()` 已算过当前结果集，`ensureDetailList()` 未复用。

---

## 四、修复与优化方案（最小改动原则）

| # | 修复 | 改动量 | 权衡 / 可观测行为 |
| --- | --- | --- | --- |
| 1 | observer 回调改 **rAF 合并**；`syncCardMotion` 只处理 `:not([data-motion])` 的新增卡片并打标记 | ~15 行 | 新增内部属性 `data-motion`（不影响可见/可访问）；`--card-index` 前 8 张仍为 0…8，其余 8；`tabindex=-1` 不变 |
| 2 | 排序前按 id 预计算 key（`kOf`），每台只算一次 | ~12 行 | 排序结果**完全不变**（key 计算方式未改，只是缓存） |
| 3 | `specList` 加 `Map` 缓存 | ~8 行 | 返回内容不变；依赖 specs 只读（已确认） |
| 4 | 搜索排序前预计算 `relScore` Map | ~8 行 | 相关性排序结果不变 |
| 5 | `render()` 存 `state.lastArr`；`ensureDetailList` 优先复用 | ~2 行 | 详情列表内容不变（render 同步，lastArr 始终最新） |
| 6 | `setText` 单次查询 | 1 行 | 不变 |
| 7 | `BRAND_COUNT` 常量预计算 | 2 行 | 数值不变 |

**新增缓存的内存代价**：4 个 Map/Set 合计约 485 条记录的引用级开销（几十 KB 量级），可忽略。

**明确未做的优化及原因**：
- 拆分外部 JSON / 分片加载：首屏收益最大，但会把「单文件站点」改成多文件，违反既有结构约束；建议作为独立议题评估。
- 表格虚拟滚动：改动远大于收益，当前一次性插入已足够。
- 合并两个 `scroll` 监听（导航态 + 阅读进度）：各自已用 rAF 节流，每帧至多 2 次回调，收益可忽略，不做。

---

## 五、涉及文件

| 文件 | 改动 |
| --- | --- |
| `index.html` | 7 处修复（见上表） |
| `_site/index.html` | `build_pages.py` 重新生成的产物 |
| `_jst/check_perf_fix.js` | **新增** 17 项「行为不变」测试 |
| `reports/perf_bugfix_2026-10-31.md` | 本报告 |

---

## 六、验证方式

### 1）行为不变（新增测试 `_jst/check_perf_fix.js`，17/17 通过）
- 品牌统计 = 数据实际品牌数（`BRAND_COUNT`）
- 485 张卡片全部带 `data-motion` 标记、`tabindex=-1`、前 9 张入场序号 0…8
- 价格升序：非空价格单调不减、缺价排最后
- 电池降序：数值单调不增、缺值排最后
- 表格重量升序：非空单调不减、缺值最后；切表格与排序后行数均为 485
- 搜索「小米15」有 5 条且首条为「小米 15」
- 详情可打开、`ArrowRight` 可翻到下一台

### 2）全量回归（全部通过）
`smoke`（485 行、0 脚本错误）、`smoke_func` 15/15、`check_search` 8/8、`check_notes` 4/4、`check_placeholder` 0 漏网、`check_batch` 22/22、`probe_features` 11/11、`probe_relevance` 无异常、`probe_url` XSS 安全、`check_perf_fix` 17/17。

### 3）性能复测（`_jst/ux_bench.js`，Edge headless + CDP，390×844 + CPU 4×）
见「一、结论摘要」。

---

## 七、已排查但未发现问题的项（避免误以为漏查）

- `localStorage` 读写全部包 `try/catch`（隐私模式不会抛错中断）✓
- `JSON.parse`（收藏、最近浏览、文件导入）均有 `try/catch` ✓
- 无 `setInterval` → 无定时器泄漏 ✓
- `fetchJson` 有 `AbortController` + `setTimeout` 超时 + `finally clearTimeout` ✓
- 报价批量查询有 `quoteRunToken` 竞态保护 + 停止逻辑（换查询会丢弃旧响应）✓
- `URL.createObjectURL` 有 `revokeObjectURL`（1s 后）✓
- 所有插值输出经 `esc()` 转义（`probe_url` XSS 用例通过）✓
- 排序缺值（价格 `null`、电池「未公布」）统一排最后，不会把「待核」当 0 元 ✓
- `IntersectionObserver` 用 `unobserve` 逐个释放；观察目标有限，不构成泄漏（可选 `disconnect`，收益极低，未做）✓
