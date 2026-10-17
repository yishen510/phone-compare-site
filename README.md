# 机选 · 中国大陆旗舰手机选购与对比

这是一个原生 HTML/CSS/JavaScript 前端 + Python 标准库服务端的手机选购对比网站。主库有 **53 款代表机型、9 个品牌，覆盖 2021—2026 年**。它关注大陆正式销售的主流旗舰，不宣称穷尽每个品牌的全部版本。

## 快速运行

1. 安装 Python 3.10+（不需要额外 Python 包）。
2. 在本目录复制 `.env.example` 为 `.env`。尚未申请开放平台授权时可以先跳过这一步。
3. 在项目目录运行：

   ```bash
   python price_server.py
   ```

4. 浏览器打开 `http://127.0.0.1:8000`。

也可以双击 `phone-compare-demo.html` 浏览单文件演示。该文件内嵌 53 款机型与当前可用的限期人工商品页快照，不需要 API Key；它不会实时刷新页面价格。

## 功能

- 按品牌、年份、关键词、旗舰定位筛选，支持卡片与表格视图。
- 最多 4 款机型横向对比；展示上市月份、首发参考价、存储版本、屏幕、处理器、影像、电池、充电与重量。
- 关联厂商大陆规格/支持/发布页面，并记录逐条复核说明。
- 透明的规则评分：性能 25%、影像 25%、屏幕 15%、续航/充电 15%、系统/生态 20%。评分与分项理由展示在页面上，是启发式初评，不是统一实验室排名。
- 按影像、游戏、续航、小屏、大屏办公、苹果生态、AI 等需求推荐候选机型。
- 提供京东、天猫/淘宝、拼多多、苏宁直达搜索入口。
- 报价支持两种明确分开的来源：获得授权后调用海纳好价检索 Pro v2；暂时没有 API Key 时展示少量限期公开商品页人工快照。两类来源均显示 SKU、页面链接与时间，人工快照不会被算作 API 报价或参与预算过滤。

## 数据库完整度

- `data/phones.json`：53 款机型；本轮对 25 款历史/待复核机型逐条检查官方规格或支持页、存储版本、上市月份与首发价格来源。23 条绑定可用的型号级来源；小米 12S Ultra 和小米 11 Ultra 的历史页面可能重定向，保留历史规格来源，但 UI 会继续提示复核，不夸称永久可访问。
- `data/price-config.json`：报价 API 的公开字段配置，不含任何密钥。
- `DATA_STATUS.md`：25 条复核记录与来源清单。
- `priceCN`：首发价/上市期参考起价，不是现在的实际售价。
- `quoteTargetStorage`：报价默认匹配的大陆版容量。本版默认采用该机 `storageOptions` 列表中的第一个组合，例如 iPhone 的入门容量或安卓的入门 RAM/ROM；报价必须匹配此容量，未匹配时不显示数字。后续可增加容量选择控件。

## 实时报价：授权与准确性边界

当前已完成**服务端 API 适配器、无密钥人工快照备用模式、人工核价导入工具及离线回归测试**。本项目不包含任何平台密钥。截图中曾可见的 Key 不应继续使用；请轮换并仅在本地 `.env` 配置新 Key。无有效 API 凭据时，服务器仍能显示 `data/manual-quotes.json` 中少量尚未过期的公开商品页人工快照；卡片会明确标记为“公开商品页快照价”，不是实时成交价，且不计入 API 质量指标。

### 没有 API Key 时如何维护价格

1. 网站会暂时展示 `data/manual-quotes.json` 中 4 条有来源的公开商品页价格快照。它们来自 2026-10-17 的初步页面抽检，部分页面信息可能由搜索索引提供；不是当日已保证可下单的库存或最终结算价。快照在记录时间起 72 小时后自动隐藏。
2. 打开 `reports/manual_page_quote_template.csv`，对待更新行逐一打开商品直链，重新核对国行/全新、精确存储容量、库存和优惠条件。只在全部确认后填 `productPageOpened=Yes`、`mainlandNewUnitConfirmed=Yes`、`exactStorageConfirmedOnPage=Yes`、`stockConfirmed=Yes`、`promotionConditionsClear=Yes`，将 `reviewerVerdict` 改为 `manual_verified`，并填写实际核验时间（含时区，例如 `2026-10-17T14:30:00+08:00`）。不要把搜索结果摘要当作完成了商品页复核。
3. 运行下面命令预检查并导入最近 72 小时内的合格记录：

   ```bash
   python update_manual_quotes.py --dry-run
   python update_manual_quotes.py
   ```

   只有精确 SKU 属于数据库、价格为有效数值、URL 为 HTTPS，且所有人工核验字段通过的行才会导入。脚本不会爬取零售网站，不需要 API Key。
4. 在本机复制 `.env.example` 为 `.env`，并填入**已轮换、没有再公开过的**海纳 Key：

   ```dotenv
   HAINAN_API_KEY=你在本机获得并保管的新Key
   ```

5. 重启 `python price_server.py`。服务端按截图中的新版接口发送 `POST https://gw-openapi.zhidemai.com/hj-search/discount/v2`，在 `x-api-key` 请求头传入 Key，JSON 请求体包含 `request_from`（默认与控制台示例一致为 `test_client`）、唯一 `question_id`、`product_query`、`query_process`、`size`、`fields`；旧版 `app_key/app_secret/sign` 签名协议不再使用。Key 只从服务端环境读取，不会发送到浏览器。
6. 查看 `http://127.0.0.1:8000/api/health`。`credentialsConfigured=true` 只表示检测到 Key，不代表该 Key 已获授权。再运行 `python quote_quality_check.py`，进行 9 个品牌代表机型的真实请求和四项指标验收；样本通过后可运行 `python quote_quality_check.py --all`。API 每次响应最多查询 5 款，网站会自动轮询分批填价以降低 QPS 风险。结果缓存默认 30 分钟；无报价结果缓存 10 分钟。
7. 详见 [API_ACCESS_AND_QA.md](API_ACCESS_AND_QA.md)。脚本生成 `reports/quote_quality_latest.json` 和 `reports/quote_quality_manual_review.csv`；后者需人工打开真实商品页，复核页面价格、国行新机、精确容量、库存和优惠条件。

**报价口径：**平台 API 是商品检索结果，包含标题、价格、商城名、促销信息与商品 URL。它不是平台订单的最终结算承诺。代码会排除二手、翻新、配件、海外版本等明显不合适的标题，并要求产品型号、容量版本和 HTTPS 直链均通过检查；购买前仍需打开商品页确认是否国行、新机、具体颜色/容量/库存，以及优惠券、以旧换新和会员资格。个别平台标题信息缺失时宁可不显示报价，也不进行模糊猜测。

## 常用接口和手工快照工具

- `python update_manual_quotes.py --dry-run`：在无 API Key 模式下校验人工核价 CSV；`python update_manual_quotes.py` 则导入合格记录，快照 72 小时后自动隐藏。
- `python build_demo.py`：将站点样式、脚本、机型数据库和人工快照重新打包到单文件演示版。
- `GET /api/health`：服务器和是否配置凭据的状态（不验证密钥有效性）。
- `GET /api/prices?ids=apple-15pm,op-11`：查询指定机型的最新可匹配报价。
- `quote_quality_check.py`：真实授权后的跨品牌样本/全库报价质量验收脚本。
- `test_price_server.py`：离线测试新版 API 请求体与鉴权头、响应字段映射、精确容量匹配、排除词、价格解析及 HTTPS 链接；运行 `python -m unittest -v test_price_server.py`。
- `API_ACCESS_AND_QA.md`：申请步骤、凭据安全及自动/人工验收口径。
- `API_ACCESS_REQUEST_DRAFT.md`：海纳测试授权申请文字草稿，当前接口的字段口径、调用配额与公开展示规范确认问题。
- `test_quote_quality_check.py`：四项指标的离线单元测试。
- `reports/retailer_page_smoke_test_2026-10-17.json` / `.csv`：公开零售页快照抽检，与授权 API 指标严格分开。
- `QUOTE_AUTH_STATUS.md`：本轮真实授权/报价验收状态和明确阻塞项。
- 无密钥时示例响应：

  ```json
  {
    "provider": "hainan_discount_v2",
    "status": "needs_credentials",
    "message": "报价 API 尚未配置；当前展示限期人工商品页快照（非 API 实时报价）……",
    "items": [{"status": "manual_page_snapshot", "sourceType": "manual_public_page_snapshot"}]
  }
  ```

## 数据源参考

- 海纳开放平台好价检索 Pro v2：`https://gw-openapi.zhidemai.com/hj-search/discount/v2`（按项目维护者提供的控制台文档截图接入）
- 海纳开放平台入口：<https://ai.zhidemai.com/>

## 目录结构

```text
phone-compare-site/
├── index.html                 # 主站；内嵌数据、样式、交互和准入门槛
├── phone-compare-demo.html    # 单文件演示版
├── data/phones.json           # 100 款大陆市场机型与字段级证据
├── reports/                   # 逐字段审核 JSON/CSV、报价检查报告
├── sync_audit_fields.py       # 将审核报告同步到数据库 fieldAudit
├── sync_catalog.py            # 将 canonical 数据同步到两个 HTML 入口
├── verify_eligibility.py      # 静态数据/报告一致性与 fail-closed 检查
├── tests_browser.py           # Chromium 浏览器交互测试（Playwright）
├── price_server.py            # 静态文件服务器 + 服务端报价 API 适配器
├── quote_quality_check.py     # 授权 API 报价质量验收脚本
├── API_ACCESS_AND_QA.md       # API 申请与验收说明
├── AUDIT_POLICY.md            # 字段审核与排名/推荐准入规则
└── DATA_STATUS.md             # 数据复核清单（含历史批次记录）
```

## Catalog rebuild and audit checks (2026-10-17)

- Edit the canonical dataset at `data/phones.json`.
- Run `python sync_catalog.py` to regenerate the embedded catalog in both `index.html` and `phone-compare-demo.html`.
- Run `python verify_eligibility.py` for a static fail-closed check of eligibility flags, duplicate IDs, and audit-report counts.
- `verify_eligibility.py` does **not** validate the truth of hardware specifications and is not a browser end-to-end test. Keep all ranking/recommendation eligibility flags closed until the full data review and browser interaction tests pass.
- The Huawei Mate 80 Pro / Pro Max / Mate X7 price fields currently represent the official China website's displayed starting price as checked on 2026-10-17; they are explicitly not historical launch prices or complete SKU price lists.


## Current verification workflow (2026-10-17)

```bash
python sync_audit_fields.py
python sync_catalog.py
python verify_eligibility.py
python tests_browser.py
```

`tests_browser.py` runs Chromium via Playwright and checks search, year/brand filters, card/table view, compare flow, and fail-closed recommendation eligibility. It is not a factual audit of every specification. Keep formal ranking and purchase recommendations disabled until all nine required fields for each candidate are verified and a separate review explicitly grants model-level eligibility.

## 本轮高优先级字段复核与发布门禁（2026-10-17）

- `data/phones.json`、`index.html` 和 `phone-compare-demo.html` 已同步更新。
- 已优先复核一加 15 的典型/额定等效电池容量和充电功率；华为 Mate 80 RS 的电池、充电、存储组合；iPhone 17 Pro Max 的正式发售日、完整存储列表和起售价；荣耀 Magic8 系列的正式启售日。
- Apple 官方没有按 mAh 公布 iPhone 17 Pro Max 电池容量，因此继续保留“官方未按 mAh 公布”，不填第三方推算值。
- 对于有起售价但无法确认其对应具体 RAM/ROM SKU 的机型，保留 `launchStartingPrice` 作为待核参考，`priceCN` 暂置空并隐藏网页价格，禁止把起售价错误绑定到某一容量版本。
- `verify_release_gate.py` 是静态一致性检查，不等同于参数事实审核或浏览器测试。
- `tests/browser_e2e.py` 会启动本地 HTTP 服务并使用 Chromium 测试搜索、筛选、对比、推荐准入；当前执行环境的 Chromium 导航被 `ERR_BLOCKED_BY_ADMINISTRATOR` 阻止，因此本轮没有把 E2E 标记为通过。请在允许 localhost/file 导航的部署或开发环境运行：`python tests/browser_e2e.py`。
- 排名和购买推荐继续关闭。任何机型需通过字段证据、具体价格-SKU映射、整机准入复核和部署端 E2E 后才可考虑开放。


## 2026-10-18 审核续批与浏览器验证

- 本轮对 HUAWEI Mate 80 Pro 补录官方规格证据：5750mAh 典型 / 5620mAh 额定、最高 100W 有线 / 80W 无线（需指定套装），以及官方列出的存储组合。
- 华为发布活动页的 6999 元起未证明历史首发价与具体 SKU 对应关系；`priceCN` 保持空值，`launchPriceMappingStatus=unmapped_starting_price_hidden`。发布日不当作正式开售日。
- 浏览器测试脚本使用 Chromium `page.set_content` 加载项目实际 HTML 并执行原始内联脚本；2026-10-18 共 8 项断言通过。由于沙箱禁止 localhost/file 导航，这不是部署域名、TLS/CDN 或生产环境端到端验收。
- 2025—2026 年机型正式排名和购买推荐仍保持关闭；字段审核、整机准入、价格-SKU映射及生产部署验证均未整体放行。

- 本轮另完成荣耀 Magic8 Pro：中国大陆版典型 7200mAh、额定 7020mAh，最高 120W 有线 / 80W 无线（需荣耀原装充电器），官方确认 2025-10-23 启售。5699 元起未映射到精确 RAM/ROM SKU，首发价格仍隐藏。
- 最新 Chromium 交互测试报告：`reports/deployment_e2e_test_2026-10-18.json`；独立整机审查：`reports/independent_whole_device_admission_review_2026-10-18.json`；静态发布门禁：`reports/release_gate_static_check_2026-10-18.json`。


## 2026-10-18 官方字段复核批次

- 已将 vivo X300 / X300 Pro 的电池典型/额定容量、充电功率、机身重量、存储组合、正式发售日期及官方发布稿逐档首发价写入 `data/phones.json` 与字段审核报告。
- X300 Pro 的卫星通信版与摄影师套装独立记录；官网当前建议零售价与历史首发价分开。
- 执行 `python sync_catalog.py` 同步两个独立 HTML 入口，执行 `python verify_release_gate.py` 与 `python independent_admission_review.py` 检查发布门禁。
- 此批次不授予排名或购买推荐资格；其他机型和部署环境仍需逐项审核。
