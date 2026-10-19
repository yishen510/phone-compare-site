# 2025—2026 旗舰机型审核与排名准入规则

审计日期：2026-10-17

## 适用范围
数据库中 `year` 为 2025 或 2026 的记录。逐字段审查屏幕、处理器、影像、电池、充电、重量、容量组合、正式发布/开售日期、官方首发价。

## 状态定义
- `verified_official_page_reviewed`：字段值非占位文本，且本轮已读取相应官方规格页/发布稿并确认。
- `official_source_linked_needs_field_confirmation`：存在厂商域名链接，但还没有逐项核对页面原文；不得当作已验证。
- `unverified_value_incomplete`：字段缺失或仍是“待复核/待录入/以官方为准”等占位值。
- `unverified_missing_or_insufficient_official_evidence`：缺少足以支持该字段的官方来源，或链接并非具体型号的规格/发布页面。

## 排名/推荐准入
只有当九个字段全部为 `verified_official_page_reviewed`，`auditStatus` 才能设为 `verified`，并将 `eligibleForRanking` 与 `eligibleForRecommendation` 设为 `true`。否则必须保持 `pending_review` 和两个 `false` 标志。当前审核范围中通过整条准入规则的机型为 0 款。

## 首发价规则
首发价必须能追溯到厂商发布稿或官方购买指引，并且能对应中国大陆版本及具体容量组合。当前商城价、促销价、媒体报道的传闻价不得直接写作官方首发价。厂商页面只展示当前起售价时，应标注为当前官网价，不能据此推断历史首发价。

## 文件
- `reports/flagship_catalog_field_audit_2026-10-17.json`：结构化审计记录及字段级来源链接。
- `reports/flagship_catalog_field_audit_2026-10-17.csv`：便于人工逐项复核的表格。
- `data/phones.json`：机型记录中的 `fieldAudit` 和准入标志。

## 重要限制
来源链接不等于字段已核验。报告中标为“有官方链接、待确认”的项目仍需人工打开链接，对照型号、地区、容量版本和页面原文后才能升级状态。


## 前端强制过滤要求

数据字段本身不等于运行时保护。正式排名候选集必须调用 `PhoneEligibility.rankingCandidates()`，正式推荐候选集必须调用 `PhoneEligibility.recommendationCandidates()`；两个入口均要求整机状态、双重资格标志以及九个必需字段的字段级证据同时满足。一般目录浏览和用户手动对比可以展示待审核机型，但不得把它们称为正式推荐或排名结果。

## Fail-closed eligibility gate（2026-10-17）
- `index.html` 与 `phone-compare-demo.html` 内嵌 `PhoneEligibility` 审核门槛；字段级证据从 `reports/flagship_catalog_field_audit_2026-10-17.json` 同步至 `data/phones.json` 的 `fieldAudit`。
- 必需字段为屏幕、处理器、影像、电池、充电、重量、容量组合、正式发布/开售日期、官方首发起售价。每个字段都必须具备已核验状态、HTTPS 来源、非空证据文字和非占位值。
- 历史说明中提及的 `sync_audit_fields.py`、`verify_eligibility.py` 与 `tests_browser.py` 在本轮仓库检查中未确认存在于当前文件树，因此本轮不将这些脚本或浏览器 E2E 结果视为已重新执行。
- 最近一次可复核的验证是 `reports/catalog_sync_validation_2026-10-18.json` 与 `reports/release_gate_static_check_2026-10-18.json` 中的远程静态一致性检查，各记录 10/10 通过；范围仅包括 JSON/HTML/报告静态内容，不包括 Chromium 浏览器交互测试、生产站点实测或所有参数的独立事实核验。
- 当前有 155 款目录记录，其中 61 款有九字段审计行；2026-10-19 补录的 54 款中高端机型尚未建立 `fieldAudit`，一律为 `auditStatus=needs_parameter_price_audit`、`eligibleForRanking=false`。荣耀 Magic9 超能版与 vivo X500 Pro Max 均仍待整机终审，后者首发价与 SKU 映射已核实，但九字段整体准入未全部通过。没有机型满足整机准入条件，正式排名与推荐继续关闭。

## 日期与容量口径
- `launchMonth` 记录上市月份；`launchDateDisplay` 可记录具体开售日期，也可明确标注“官方仅核实到月份”。不得将发布会日期、海外上市日期和中国大陆开售日期混为一谈。
- 对可核实的电池参数，分别保留典型容量与额定容量；不允许只存一个 mAh 数字而让读者误以为是唯一容量。
- 存储组合必须来自目标市场官方规格/商城页面；卫星通信版、摄影师套装等独立 SKU 应单独标注，不要把不同地区或不同版本混在一起。


目录更新（2026-10-18）：vivo X500 Pro Max 已加入待审核目录。官方发布稿已核实其 12GB+256GB SKU 首发价为 6999 元，`priceCN` 已填为 6999；整机仍为 `pending_review`，排名/推荐资格关闭。

## 价格类型与「只有起售价」的处置（2026-10-20）

- `priceType=official_launch_msrp`：已确认「中国大陆版 + 具体容量组合 + 价格」三要素，卡片标签显示「官方首发参考价」，字段状态为 `verified_official_page_reviewed` 或 `cross_checked_secondary_source`。
- `priceType=official_starting_price`：官方只公布「XX 元起」，拿不到该价位对应的容量 SKU。此类记录仍写入 `priceCN` 以便展示，但卡片标签强制显示「**官方起售价（容量待核）**」，`fieldAudit` 状态为 `starting_price_only_sku_mapping_unverified`，不得计入已核验首发价，也不满足准入条件。
- `priceType=third_party_reference`：价格来自中关村在线等第三方聚合页，标签显示「参考价（第三方）」。
- 发布会现场公布的价格若只能追溯到权威媒体报道（央广网、新华网、证券时报、中国新闻网、中国经济网等），按 `cross_checked_secondary_source` 记账，并在 `evidenceText` 写清媒体名称与档位；不得写成「官网已核验」。
- 同一机型若出现「发布当时媒体价」与「厂商页面现价」不一致（如 2026 年存储涨价后的调价），以**发布当时价**作为首发价，并在 `evidenceText` 中显式标注差异与待复核项。
