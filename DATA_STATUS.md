# 数据库完整度与逐条复核清单

> 最后更新：2026-10-18。此页已校正为当前目录快照口径；历史批次数据保留在下文，仅作历史记录。

- 当前主数据库：155 条记录、11 个品牌，ID 唯一。
- 当前字段级审核报告：566 条字段记录，覆盖 61 款 2025—2026 年机型。
- `index.html` 与 `phone-compare-demo.html` 内嵌目录均为 155 条且 ID 顺序与 `data/phones.json` 一致；2026-10-19 本地实测 155 张卡片、155 行表格渲染无 JS 报错（Edge 无头）。
- 目录记录数不等于已审核或可排名机型数。荣耀 Magic9 超能版与 vivo X500 Pro Max 均保留待审核状态；后者 12GB+256GB 官方首发价 6999 元已核实，但整机资格仍关闭。
- 当前没有机型满足九字段整机准入条件；正式排名与推荐资格继续关闭。
- HUAWEI Pura 90 Pro Max 已完成九字段官方来源预审，但官方 SKU 首发价逐档映射仍缺直接证据；媒体价格仅作交叉线索，未新增目录记录，未开放排名/推荐。详见 `reports/model_missing_duplicate_audit_2026-10-18.json`。
- 本轮仅确认远程静态一致性；不将其表述为浏览器 E2E、生产站点实测或所有参数的独立事实核验。

## 历史审计批次说明

下文中的“本轮 25 款”及早期 53 款目录口径属于历史批次，不代表当前完整度。当前事实以 `data/phones.json`、`reports/flagship_catalog_field_audit_2026-10-17.json`、`reports/catalog_sync_validation_2026-10-18.json` 和 `reports/release_gate_static_check_2026-10-18.json` 为准。

## 本轮 25 款逐条清单

| 机型 | 上市月份 | 录入大陆存储组合 | 核验状态与重点 | 官方规格/支持来源 | 发布/首发价来源 |
|---|---|---|---|---|---|
| Apple iPhone 15 Pro Max | 2023年09月 | 256GB、512GB、1TB | 已关联型号级来源：Apple 技术规格页确认容量、221g、屏幕、A17 Pro 与相机；发布稿确认大陆首发价 9999 元和容量组合。 本条的首发价来自发布稿；官方规格页不提供当前第三方渠道成交价。 | [规格/支持页](https://support.apple.com/zh-cn/111828) | [发布/价格来源](https://www.apple.com.cn/newsroom/2023/09/apple-unveils-iphone-15-pro-and-iphone-15-pro-max/) |
| Apple iPhone 14 Pro Max | 2022年09月 | 128GB、256GB、512GB、1TB | 已关联型号级来源：技术规格页确认大陆版容量、尺寸重量、屏幕、芯片与摄像头；发布稿确认 8999 元首发起价。 本条的首发价来自发布稿；官方规格页不提供当前第三方渠道成交价。 | [规格/支持页](https://support.apple.com/zh-cn/111846) | [发布/价格来源](https://www.apple.com.cn/newsroom/2022/09/apple-debuts-iphone-14-pro-and-iphone-14-pro-max/) |
| Apple iPhone 13 Pro Max | 2021年09月 | 128GB、256GB、512GB、1TB | 已关联型号级来源：官方规格页确认容量、屏幕、重量；Apple 发布稿确认大陆 8999 元首发起价。 本条的首发价来自发布稿；官方规格页不提供当前第三方渠道成交价。 | [规格/支持页](https://support.apple.com/zh-cn/111870) | [发布/价格来源](https://www.apple.com.cn/newsroom/2021/09/apple-unveils-iphone-13-pro-and-iphone-13-pro-max-more-pro-than-ever-before/) |
| Honor 荣耀 Magic5 Pro | 2023年03月 | 8GB+256GB、12GB+256GB、16GB+512GB | 已关联型号级来源：荣耀官方规格页与 Magic5 国内发布稿已关联；发布稿确认 Magic5 Pro 5199 元起、2023-03-10 开售，配置组合按大陆型号页校对。 | [规格/支持页](https://www.honor.com/cn/phones/honor-magic5-pro/spec/) | [发布/价格来源](https://www.honor.com/cn/news/honor-magic-5-product-launch/) |
| Honor 荣耀 Magic4 Pro | 2022年03月 | 8GB+256GB、12GB+256GB、12GB+512GB | 已关联型号级来源：荣耀官网国内发布稿确认 Magic4 Pro 5499 元起、3 月 25 日开售；容量组合以荣耀大陆规格页为准。 | [规格/支持页](https://www.honor.com/cn/phones/honor-magic4-pro/spec/) | [发布/价格来源](https://www.honor.com/cn/news/honor-announces-magic4-series/) |
| Honor 荣耀 Magic3 Pro | 2021年08月 | 8GB+256GB、12GB+256GB、12GB+512GB | 已关联型号级来源：荣耀官方系列发布稿确认 Magic3 Pro 8GB+256GB 5999 元、12GB+512GB 6799 元；型号页及官方产品入口同时列有 12GB+256GB，故数据库将该容量加入可选列表。 | [规格/支持页](https://www.honor.com/cn/phones/honor-magic3-pro/spec/) | [发布/价格来源](https://www.honor.com/cn/news/magic/) |
| Huawei HUAWEI Pura 70 Ultra | 2024年04月 | 16GB+512GB、16GB+1TB、12GB+512GB | 已关联型号级来源：华为官方产品指南列出大陆双卡 16GB+512GB/1TB；另一官方支持内容也列出 12GB+512GB。首发价 9999 元对应发布期 16GB+512GB 起售价参考，当前价需另查渠道。 | [规格/支持页](https://consumer.huawei.com/cn/support/content/zh-cn16021601/) | [发布/价格来源](https://consumer.huawei.com/cn/support/content/zh-cn16021601/) |
| Huawei HUAWEI Mate 60 Pro | 2023年08月 | 12GB+256GB、12GB+512GB、12GB+1TB | 已关联型号级来源：按华为大陆型号规格页及发布期公示信息整理；Mate 60 Pro 实际芯片标识存在批次/命名差异，未将性能相关字样作更强断言，价格为最低版本首发参考。 | [规格/支持页](https://consumer.huawei.com/cn/phones/mate60-pro/specs/) | [发布/价格来源](https://consumer.huawei.com/cn/press/) |
| Huawei HUAWEI Mate 50 Pro | 2022年09月 | 8GB+256GB、8GB+512GB | 已关联型号级来源：华为规格页确认 6.74 英寸屏幕、处理器、影像和 8GB+256/512GB 主要配置；发布会页确认发布日期。去除之前疑似无根据的 1TB 容量。 | [规格/支持页](https://consumer.huawei.com/cn/phones/mate50-pro/specs/) | [发布/价格来源](https://consumer.huawei.com/cn/press/events/2022/huawei-mate50-series-and-all-scenario-new-product-autumn-launch-event/) |
| Huawei HUAWEI P50 Pro | 2021年07月 | 8GB+128GB、8GB+256GB、8GB+512GB、12GB+512GB | 已关联型号级来源：华为官方支持资料显示 P50 Pro 存在不同芯片与容量型号；本数据库按大陆公开组合列示，不将所有版本视为同一芯片版本。价格为系列发布期参考起售价。 | [规格/支持页](https://consumer.huawei.com/cn/phones/p50-pro/) | [发布/价格来源](https://consumer.huawei.com/hk/press/news/2021/p50_series_global/) |
| OnePlus 一加 15 | 2025年10月 | 12GB+256GB、16GB+256GB、12GB+512GB、16GB+512GB、16GB+1TB | 已关联型号级来源：一加官方产品页确认国行第五代骁龙 8 至尊版、165Hz 屏幕、7300mAh、120W 有线/50W 无线；首发各容量售价根据发布期媒体对公开定价的记录，当前零售价已变动。 | [规格/支持页](https://www.oneplus.com/cn/15) | [发布/价格来源](https://www.ithome.com/0/892/832.htm) |
| OnePlus 一加 11 | 2023年01月 | 12GB+256GB、16GB+256GB、16GB+512GB | 已关联型号级来源：一加官方规格页确认国行配置为 12GB+256GB、16GB+256GB、16GB+512GB；纠正数据库中重复的 12GB+256GB 与不准确的 8GB+128GB。 | [规格/支持页](https://www.oneplus.com/cn/11/specs) | [发布/价格来源](https://www.oneplus.com/cn/11) |
| Samsung Galaxy S24 Ultra | 2024年01月 | 12GB+256GB、12GB+512GB、12GB+1TB | 已关联型号级来源：三星中国大陆规格/购买页列出 12GB+256GB、12GB+512GB、12GB+1TB 三档，型号参数和存储组合已核对；首发价格为公开大陆参考起价。 | [规格/支持页](https://www.samsung.com.cn/smartphones/galaxy-s24-ultra/specs/) | [发布/价格来源](https://www.samsung.com.cn/smartphones/galaxy-s24-ultra/buy/) |
| Samsung Galaxy S23 Ultra | 2023年02月 | 8GB+256GB、12GB+256GB、12GB+512GB、12GB+1TB | 已关联型号级来源：三星中国大陆购买/规格页面列出 8GB+256GB、12GB+256GB、12GB+512GB、12GB+1TB 可选配置；首发起价按上市公开定价 9499 元记录，价格非现价。 | [规格/支持页](https://www.samsung.com.cn/smartphones/galaxy-s23-ultra/specs/) | [发布/价格来源](https://www.samsung.com.cn/smartphones/galaxy-s23-ultra/) |
| Samsung Galaxy S22 Ultra | 2022年02月 | 12GB+256GB、12GB+512GB、12GB+1TB | 已关联型号级来源：三星中国大陆规格页列出 12GB+256GB、12GB+512GB、12GB+1TB；不把普通版 Galaxy S22 的 8GB+128GB 混入 Ultra。首发起价为 9699 元。 | [规格/支持页](https://www.samsung.com.cn/smartphones/galaxy-s22-ultra/specs/) | [发布/价格来源](https://www.samsung.com.cn/smartphones/galaxy-s22-ultra/) |
| Samsung Galaxy S21 Ultra | 2021年01月 | 12GB+256GB、16GB+512GB、16GB+1TB | 已关联型号级来源：中国移动官方网上营业厅旧商品页可核对国行版本、12GB+256GB/16GB+512GB 和 9699 元参考价格；三星历史规格页链接保留为官方补充来源。 | [规格/支持页](https://www.samsung.com.cn/smartphones/galaxy-s21-ultra-5g/specs/) | [发布/价格来源](https://shop.10086.cn/goods/891_891_1084371_1070915.html) |
| Xiaomi 小米 15 Ultra | 2025年02月 | 12GB+256GB、16GB+512GB、16GB+1TB | 已关联型号级来源：按中国大陆版规格页与发布期容量/价格报道核对；首发组合为 12+256、16+512、16+1TB，海外版电池/规格不用于此记录。 | [规格/支持页](https://www.mi.com/xiaomi-15-ultra/specs) | [发布/价格来源](https://m.ithome.com/html/834153.htm) |
| Xiaomi 小米 17 Ultra | 2025年12月 | 12GB+512GB、16GB+512GB、16GB+1TB | 已关联型号级来源：小米官方发布稿确认 2025-12-25 发布、12+512GB 6999 元起、16+512GB 与 16GB+1TB 档位；官方商城中国大陆购买页已关联。已将原库占位参数替换为正式规格方向。 | [规格/支持页](https://www.mi.com/shop/buy/detail?product_id=1230801368) | [发布/价格来源](https://www.mi.com/global/discover/article?id=5825) |
| Xiaomi 小米 14 Ultra | 2024年02月 | 12GB+256GB、16GB+512GB、16GB+1TB | 已关联型号级来源：官方大陆规格页与发布期报价报道已关联；基础容量、处理器代际、屏幕和影像参数核对完成。 | [规格/支持页](https://www.mi.com/xiaomi-14-ultra/specs) | [发布/价格来源](https://www.autohome.com.cn/news/202402/1293605.html) |
| Xiaomi 小米 13 Ultra | 2023年04月 | 12GB+256GB、16GB+512GB、16GB+1TB | 已关联型号级来源：官方规格页核对屏幕、芯片、相机和机身；发布期报道确认大陆三个容量版本与 5999 元起价。价格引用为新闻报道，非实时价格。 | [规格/支持页](https://www.mi.com/xiaomi-13-ultra/specs) | [发布/价格来源](https://www.ithome.com/0/687/322.htm) |
| Xiaomi 小米 12S Ultra | 2022年07月 | 8GB+256GB、12GB+256GB、12GB+512GB | 历史页面可访问性待复核：按 2022 年小米 12S Ultra 大陆版公开规格与首发配置整理；小米旧活动入口不是永久商品报价页，价格为历史首发价。老款官方直链可能重定向，已保留历史参数与发布期来源，并明确标注链接可访问性待复核。 | [规格/支持页](https://www.mi.com/xiaomi-12s-ultra/specs/) | [发布/价格来源](https://www.mi.com/event) |
| Xiaomi 小米 11 Ultra | 2021年03月 | 8GB+256GB、12GB+256GB、12GB+512GB | 历史页面可访问性待复核：按小米 11 Ultra 大陆版发布资料与历史规格整理；由于厂商老款商品页存在下架/跳转，首发价与容量保留为历史资料，非现价。老款官方直链可能重定向，明确标注后续需补可访问的官方存档来源。 | [规格/支持页](https://www.mi.com/mi11ultra/specs/) | [发布/价格来源](https://www.mi.com/) |
| realme 真我 GT7 Pro | 2024年11月 | 12GB+256GB、16GB+256GB、12GB+512GB、16GB+512GB、16GB+1TB | 已关联型号级来源：官方规格页确认骁龙 8 至尊版、6500mAh、120W 和最高 16GB+1TB；价格字段改为 3699 元官方定价起价，3599 元属于首发优惠，不混作常规定价。 | [规格/支持页](https://www.realme.com/cn/realme-gt-7-pro/specs) | [发布/价格来源](https://www.ithome.com/0/807/768.htm) |
| realme 真我 GT5 Pro | 2023年12月 | 12GB+256GB、16GB+256GB、16GB+512GB、16GB+1TB | 已关联型号级来源：官方规格页确认 5400mAh、100W/50W 及至高 16GB+1TB；首发起价以厂商发布期商品页为历史参考。 | [规格/支持页](https://www.realme.com/cn/realme-gt-5-pro/specs) | [发布/价格来源](https://www.realme.com/cn/realme-gt-5-pro) |
| vivo vivo X90 Pro+ | 2022年11月 | 12GB+256GB、12GB+512GB | 已关联型号级来源：vivo 官方型号参数页直接给出 2022 年 11 月上市、12+256GB 建议零售价 6499 元、12+512GB 6999 元及主要参数；该项可视为高置信度官方校验。 | [规格/支持页](https://www.vivo.com.cn/vivo/param/x90proplus) | [发布/价格来源](https://www.vivo.com.cn/vivo/param/x90proplus) |

## 本轮修订摘要

- 核对 iPhone 13 Pro Max、14 Pro Max、15 Pro Max 的容量/屏幕/重量与 A 系列芯片信息；将苹果电池容量继续按“官方未按 mAh 公布”处理，不编造 mAh。
- 核对荣耀 Magic3 Pro、Magic4 Pro、Magic5 Pro 的发布期价格与公开容量组合；发布期价与当前渠道价分开。
- 核对华为 Pura 70 Ultra、Mate 60 Pro、Mate 50 Pro、P50 Pro 的可确认大陆版存储组合。Pura 70 Ultra 保留 16GB+512GB、16GB+1TB 和华为支持内容列出的 12GB+512GB；首发起价对应发布期 16GB+512GB 版本。Mate 50 Pro 当前仅列本轮可确认的 8GB+256GB/512GB 常规组合。
- 核对一加 15、一加 11 的公开容量与规格；修正一加 11 存储字段中的重复/不匹配组合。
- 核对三星 S24 Ultra、S23 Ultra、S22 Ultra、S21 Ultra 的大陆版容量组合；S23 Ultra 纳入三星中国商城公开展示的 8GB+256GB 配置；S22 Ultra 明确只列 12GB+256GB/512GB/1TB，避免把普通版 Galaxy S22 的 8GB+128GB 混入。
- 核对小米 13 Ultra、14 Ultra、15 Ultra、17 Ultra 的大陆版本/上市期资料；小米 17 Ultra 不再使用占位参数。小米 12S Ultra 与小米 11 Ultra 的旧商品页可能重定向，故保留历史数据并在站内提示继续复核。
- 核对真我 GT5 Pro、GT7 Pro 的处理器、电池、充电与容量；GT7 Pro 的 3699 元设为发布期指导起价参考，3599 元首发促销不混入标准起售价字段。
- 核对 vivo X90 Pro+ 官方参数页，明确 2022 年 11 月上市、12GB+256GB/512GB 与对应建议零售价。

## 实时报价接口

- 本段是早期方案的历史记录，已被新版适配器取代。当前使用海纳开放平台「好价检索 Pro v2」：`POST https://gw-openapi.zhidemai.com/hj-search/discount/v2`，由服务端在 `x-api-key` 请求头发送 `HAINAN_API_KEY`，响应从 `data.rows[]` 解析。
- 当前密钥仅在本机/服务器 `.env` 中配置，不写入浏览器包。未配置时返回 `needs_credentials`；没有满足型号+存储精确匹配的商品时返回 `no_exact_offers`，不以模糊标题猜价。
- 默认目标容量为各机型 `storageOptions` 的首个大陆版组合，并显示在 UI 中。代码排除二手/翻新/配件与常见海外版标题，要求 HTTPS 直达商品 URL。
- 查询结果默认缓存 30 分钟；无匹配缓存 10 分钟。这是商品检索报价，不承诺最终下单价。用户仍需检查商品新旧、国行版本、颜色、库存、优惠券、会员与以旧换新资格。
- 当前项目没有放入真实密钥。维护者提供了新版控制台文档截图，但其中的 Key 可见，因此本次没有使用已暴露的 Key 发起请求；建议先轮换，再仅在本机 `.env` 配置新 Key。真实报价和四项实测指标仍需在有效授权下跑完验收。

## 相关数据源与技术说明

- [值得买开放平台商品检索 API 文档](https://openapi.zhidemai.com/pages/aiagent/1.%E5%95%86%E5%93%81%E6%A3%80%E7%B4%A2%E6%8E%A5%E5%8F%A3.html)
- [值得买开放平台 API 调用方法与签名规则](https://openapi.zhidemai.com/pages/rookie/2.API%E8%B0%83%E7%94%A8%E6%96%B9%E6%B3%95%E8%AF%A6%E8%A7%A3.html)
- [README.md](README.md)：启动步骤、凭据配置与接口响应说明。

## 2025—2026 旗舰机型补录（2026-10-17）

本次在 `data/phones.json` 中新增 12 条记录，总量从 53 条增加到 65 条，并同步更新独立演示页 `phone-compare-demo.html` 的内嵌数据。新增代表机型包括：Xiaomi 17 Pro / 17 Pro Max、vivo X300 / X300 Pro、OPPO Find X9 / Find X9 Pro、荣耀 Magic8、REDMI K90 Pro Max、iQOO 15、Xiaomi 18 Pro、vivo X500 / X500 Pro。

### 新增数据源（优先厂商官方页面）
- 荣耀 Magic8 系列发布信息：https://www.honor.com/cn/news/honor-magic8-launch/
- vivo X300 系列发布信息：https://www.vivo.com.cn/brand/news/detail?id=1336
- vivo X300 Pro 规格与建议零售价：https://www.vivo.com.cn/vivo/param/x300pro
- OPPO Find X9：https://www.oppo.com/cn/smartphones/series-find-x/find-x9/
- OPPO Find X9 Pro 参数：https://www.oppo.com/cn/smartphones/series-find-x/find-x9-pro/specs/
- Xiaomi 17 Pro 系列资料：https://ir.mi.com/static-files/e4830480-8ce9-45f8-a09d-64e40b2bdfac
- Xiaomi 17 Ultra 发布信息：https://www.mi.com/global/discover/article?id=5825
- vivo X500 Pro 参数：https://www.vivo.com.cn/vivo/param/x500pro
- Xiaomi 18 Pro 商品页：https://www.mi.com/shop/buy/detail?cfrom=search&product_id=1230809262

### 数据质量说明
- 本次目标是补齐代表机型，不宣称覆盖 2025—2026 年所有旗舰、折叠屏、性能子系列及各存储 SKU。
- 无法从可用官方页面可靠核验首发价的新增机型，`priceCN` 留空，不用当前零售价或媒体传闻填充。
- 部分新增条目的详细参数仍标注“官方规格页待复核”；上线前应继续逐字段核对大陆版本、上市时间、完整存储组合及官方首发价。
- `priceCN` 是首发价/官方建议价参考，不代表当前渠道成交价；实时渠道报价仍须独立验证。
- 更新明细：`reports/flagship_catalog_update_2026-10-17.json`。


## 2025–2026 旗舰机型系统排查（2026-10-17）

- 数据库由 65 条扩充至 100 条；本轮新增 35 条候选/已发布旗舰记录。
- 覆盖 Apple、Samsung、小米、华为、荣耀、OPPO、vivo、一加、iQOO、realme、nubia 等品牌。
- 对首发价与当前渠道价分开处理；没有足够来源的首发价保留 null。
- 新增记录的参数核验状态默认为 partial_verified，任何“待复核”字段不可视为已确认。
- 详细清单见 `reports/flagship_catalog_audit_2026-10-17.json`。


## 2025—2026 旗舰机型逐字段审核（2026-10-17）

- 审核清单：`reports/flagship_catalog_field_audit_2026-10-17.json` 与 `.csv`。每款逐项记录屏幕、处理器、影像、电池、充电、重量、容量组合、发布/开售日期、官方首发价及对应来源 URL。
- 新增字段：每条机型记录包含 `fieldAudit`、`auditStatus`、`parameterAuditStatus`、`priceAuditStatus`、`eligibleForRanking`、`eligibleForRecommendation`。
- **审核策略：**仅当一条记录所有要求字段都在官方来源中逐项核对后，才允许 `auditStatus=verified` 且 `eligibleForRanking/eligibleForRecommendation=true`。官方 URL 存在但没有逐项核对页面原文，仍不算通过。
- 当前审计范围内记录全部处于 `pending_review`；因此它们应被视为候选资料，不得作为最终排名或购买推荐依据。
- 本轮发现并纠正“小米 15 / 小米 15 Pro”年份错误：两款应归入 2024 年，而不是 2025 年；具体发布日期仍需补入官方发布稿作为证据。
- 部分来源只提供品牌首页、客服维修页、其他型号页面或媒体链接，不能证明对应字段，审计清单会明确标注来源不足。


## 2025–2026 旗舰机型逐字段审计第二轮（2026-10-17）

- 审计报告已按唯一机型重建：重复的 `realme-gt8p` 占位记录已移除，保留带官方规格页的 `realme-gt8-pro`，避免同一机型重复参与比较。
- 对华为 Mate 90、OPPO Find X10、真我 GT8 Pro 的官方规格页逐项录入了屏幕、芯片、影像、电池、充电、重量和容量组合；华为 Mate 90 的开售时间/首发价按官方购买指引核实。
- 对 iPhone 17 的官方发布稿确认了屏幕概述、芯片、影像、容量、发布/开售日期和首发价；iPhone Air 的部分字段仍需规格页复核。
- 对荣耀 Magic9 和 vivo X500 更新了官方发布稿能直接支持的发布/开售日期与起售价；未从发布稿直接支持的详细硬件字段不作推断。
- **所有 2025–2026 机型仍保持 `eligibleForRanking=false`、`eligibleForRecommendation=false`。** 部分字段通过不等于整机通过审核。
- 最新字段审计文件：`reports/flagship_catalog_field_audit_2026-10-17.csv` 与同名 JSON。


### 本轮审计统计（第三轮最终）

- 唯一机型：59 款；字段审计：531 项（每款 9 项）。已移除一个重复的真我 GT8 Pro 占位记录。
- 字段状态：已核实 103 项；有官方链接待逐字段确认 224 项；值不完整 189 项；官方证据不足 15 项。
- 本轮新增逐字段录入：华为 Pura 80、华为 Mate 90 Pro、三星 Galaxy S26 / S26+；前一轮已处理华为 Mate 90、OPPO Find X10、真我 GT8 Pro、iPhone 17 / Air、荣耀 Magic9、vivo X500 的部分字段。
- 整机通过准入：0 款。全部 2025–2026 记录的 `eligibleForRanking` 与 `eligibleForRecommendation` 均为 `false`。
- **实现限制：**本轮已将禁入标志写入 JSON 数据层，但尚未验证网站前端是否读取并执行这两个标志；不要把当前演示页视为已具备完整的排名/推荐隔离。上线前必须在前端候选集、排序和推荐器中强制过滤 `eligibleForRanking === true` / `eligibleForRecommendation === true`。


## 第四轮逐字段官方来源核验（2026-10-17）

本轮直接核对了 Apple iPhone 17、iPhone Air、华为 Pura 80、Mate 80、Mate 80 Pro、Mate 80 Pro Max、Mate X7、Mate 90、OPPO Find N5、OPPO Find X8 Ultra 的官方规格页或官方发布/购买指引。仅对来源直接支持的字段标记已核实；华为 Pura 80 芯片、若干机型首发价/正式开售日期、折叠机容量组合等仍保留待审。所有候选机型继续禁止进入最终排名和购买推荐。
本轮审计状态统计：official_source_linked_needs_field_confirmation=204, unverified_missing_or_insufficient_official_evidence=24, unverified_value_incomplete=172, verified_official_page_reviewed=151。

### 第四轮统计校正与执行边界

第四轮最终审计表固定为每款 9 个字段，59 款共 531 项（避免将 `launchDate` 与 `launchDateDisplay`、`price` 与 `priceCN` 两套兼容字段重复计数）。当前统计为：已核实 143 项；有官方链接待逐字段确认 197 项；值不完整 169 项；官方证据不足 22 项。整机九字段全部标记已核实的记录有 4 款，但这不代表网站端已完成准入隔离。

本轮补核 10 款：iPhone 17、iPhone Air、HUAWEI Pura 80、Mate 80、Mate 80 Pro、Mate 80 Pro Max、Mate X7、Mate 90、OPPO Find N5、OPPO Find X8 Ultra，共 90 个字段。对华为 Mate 90，官方购买指引明确写明 12GB+256GB 首发价 5999 元、2026年10月1日12:08正式开售；对 iPhone 17 与 iPhone Air，Apple 官方发布稿分别明确了 5999 元与 7999 元起售价及容量/上市信息。Pura 80 的芯片型号未在所用官方规格页中列出，未据此推测；Mate 80 系列、Mate X7、Find N5、Find X8 Ultra 的历史首发价或大陆首销日期若没有直接的官方首发证据，继续留空或标记待核，不把商城当前售价冒充首发价。

**重要限制：**`app.js` 当前不在项目目录内，而 `index.html` 仍引用它。因此本轮虽在数据层将 2025—2026 候选机型设置为 `eligibleForRanking=false` / `eligibleForRecommendation=false`，但不能声称前端已执行过滤。修复并验证前端脚本前，不应把演示页当成可用的正式排名/推荐工具。


2026-10-18 补录 vivo X500 Pro Max（`vivo-x500pm`）：主要硬件、容量 SKU 和上市月份已按中国大陆官方规格页记录；官网建议零售价不视作首发价，`priceCN` 保持 null，排名与推荐资格关闭。

## 2026-10-19 中高端机型补录（54 款）

本轮针对“2021—2026 各品牌中高端产品线”做缺口排查，`data/phones.json` 由 102 条扩至 **155 条**（合并重复的 realme-gt8p 后净增 53 条），品牌仍为 11 个。明细见 `reports/midhigh_backfill_2026-10-19.json`，可复现脚本为 `scripts/add_midhigh_models_2026-10-19.py`。

### 补录后的覆盖矩阵

| 品牌 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | 合计 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Huawei | 1 | 1 | 3 | 7 | 10 | 3 | 25 |
| Xiaomi | 1 | 3 | 4 | 5 | 10 | 1 | 24 |
| Samsung | 1 | 1 | 3 | 5 | 6 | 3 | 19 |
| OPPO | 0 | 2 | 3 | 4 | 6 | 2 | 17 |
| vivo | 1 | 1 | 2 | 5 | 4 | 4 | 17 |
| Honor | 1 | 1 | 2 | 5 | 3 | 4 | 16 |
| Apple | 1 | 2 | 3 | 3 | 4 | 2 | 15 |
| OnePlus | 0 | 1 | 2 | 3 | 2 | 0 | 8 |
| iQOO | 0 | 0 | 2 | 2 | 1 | 1 | 6 |
| realme | 0 | 0 | 1 | 2 | 2 | 0 | 5 |
| nubia | 0 | 0 | 1 | 2 | 0 | 0 | 3 |

### 本轮新增机型

- **Apple（6）**：iPhone 17 Pro、16 Pro、16、15 Pro、15、14 Pro。
- **Samsung（7）**：Galaxy S24、S24+、Z Fold6、Z Flip6、Z Fold5、Z Flip5、S25 Edge。
- **Xiaomi（9）**：小米 14、14 Pro、13、13 Pro、MIX Fold 4、MIX Fold 3、MIX Flip、REDMI K80 Pro、K80。
- **Huawei（7）**：Mate 70、Mate 70 Pro+、Mate X6、Mate X5、Pura 70、Pura 70 Pro、Pura X。
- **Honor（4）**：Magic7、Magic6、Magic V3、Magic V2。
- **OPPO（6）**：Find X8、X8 Pro、X7、Find N3、N3 Flip、N2。
- **vivo（7）**：X200、X200 Pro、X200 Pro mini、X100、X100 Pro、X Fold5、X Fold3 Pro。
- **OnePlus（2）**：一加 Ace 5 Pro、Ace 5。
- **iQOO（3）**：iQOO 12、12 Pro、Neo10 Pro。
- **realme（2）**：真我 GT6、GT7。
- **nubia（1）**：红魔 9 Pro。

### 录入口径

- 字段集合与既有记录一致（41 键）；`storage` 由 `storageOptions` 拼接生成，避免两处不一致。
- `priceCN` 只在有把握对应官方首发价时填写，其余留空；不写渠道现价。
- 新增记录一律 `auditStatus=needs_parameter_price_audit`、`parameterAuditStatus=needs_source_crosscheck`，`eligibleForRanking/Recommendation` 视为 false，详情页显示“待核验”。
- 苹果电池沿用既有口径“官方未按 mAh 公布”，不写 mAh 数值。

### 未补录与原因

- **2026 年未见于现有目录的兄弟机型**（如 iPhone 18 基础款、各家 2026 折叠）：无法核对官方规格与上市信息，不按命名规律推断存在性。
- **Motorola / 魅族 / 中兴 Axon / ROG 等品牌**：目录现为 11 品牌，新增品牌会改变筛选口径，且缺少可核验的大陆官方规格页，暂不引入。
- **非基础存储 SKU**：一款机型一条记录，容量差异写入 `storageOptions`。

### 已知问题

- ~~`realme-gt8p` 与 `realme-gt8-pro` 重复~~：已于 2026-10-19 合并，保留带官方规格页的 `realme-gt8-pro`，`realme-gt8p` 已从 JSON 与两个页面内嵌数据中移除。

## 2026-10-19 字段核验第一批（华为 3 款）

- 已按华为中国大陆官方规格页逐项核对 **HUAWEI Mate 70、Mate 70 Pro+、Mate X6** 的屏幕、影像、电池、充电、重量、容量组合，共 **18 个字段**，全部标记 `verified_official_page_reviewed` 并附证据原文与来源链接。
- 三款的处理器、上市日期、官方首发价不在规格页内，**保持未核验**；`auditStatus` 仍为 `needs_parameter_price_audit`，排名与推荐资格继续关闭。核验明细见 `reports/field_audit_batch1_huawei_2026-10-19.json`。
- 未能核验：**Pura 70 / Pura 70 Pro** 的官方规格页已下线（跳回产品总览），**Mate X5** 本轮未取得可用规格内容。老机型需要改用官方存档页作为证据来源，不能拿媒体参数冒充实测。
- 同轮修正前端缺陷：详情页 `field()` 原以英文键（`fieldAudit['display']`）查询，而数据中的 `fieldAudit` 是中文名字段数组，导致**所有机型**（含此前已核验的 vivo X500 Pro Max）一律显示“待核验”。现已兼容两种结构，已核验字段正确显示“已核验 + 证据 + 字段来源”。

## 2026-10-19 字段核验第二批（Apple 5 款）

- iPhone 17 Pro、16 Pro、16、15 Pro、14 Pro 各核验 7 个字段（屏幕、处理器、影像、电池、充电、重量、容量组合），共 **35 项**，全部附官方页面证据与来源链接。明细见 `reports/field_audit_batch2_apple_2026-10-19.json`。
- 按官方页修正 iPhone 17 Pro 重量 206 g → **204 g**，影像口径改为「4800 万融合式主摄 + 4800 万融合式超广角 + 4800 万融合式长焦（4×/8×）」，电池改按官方「视频播放最长 31 小时」表述。
- 来源：iPhone 16 用 apple.com.cn 在售规格页；16 Pro / 15 Pro / 14 Pro 的在售页已下架，改用 support.apple.com 官方技术规格页（长期保留）。
- **iPhone 15 标准版**的支持页编号未确认，本轮未纳入；上市日期与首发价仍无官方直接证据，整机准入继续关闭。
- **华为老机型**：计划中的官方存档页方案因 archive.org 在当前网络不可达而无法执行，Pura 70 / Pura 70 Pro / Mate X5 仍未核验，不以媒体参数替代。

## 2026-10-19 字段核验第三批（小米 4 款）与进度

- 小米 14、14 Pro、13、13 Pro 按 mi.com 官方规格页核对屏幕、处理器、影像（14/14 Pro）、电池、充电、重量，共 **22 项**。明细见 `reports/field_audit_batch3_xiaomi_2026-10-19.json`。
- 累计已核验 **12 款**：华为 Mate 70 / Mate 70 Pro+ / Mate X6，Apple iPhone 17 Pro / 16 Pro / 16 / 15 Pro / 14 Pro，小米 14 / 14 Pro / 13 / 13 Pro。
- 自动化解析只作线索，**不直接入库**：试跑时曾把 vivo X100 电池误读为 2500mAh、把 100W 误读为 04W，说明正则抽取不可靠，最终值均由页面原文人工确认。
- 剩余机型的官方规格页多数已下架（Pura 70 系列、Z Fold5 / Flip5、MIX Fold / Flip、REDMI K80 系列、iQOO 12 系列、红魔 9 Pro 等），需改用官方存档或其他官方文档，才能继续核验。
- 本地提交 `25b559a` 因 GitHub 网络中断暂未推送，线上仍停留在 `b7db3bf`（8 款已核验版本）。

## 2026-10-19 字段核验第五批（官方页 21 款）

- 荣耀 Magic7 / Magic6 / Magic V3 / Magic V2、OPPO Find X8 / X8 Pro / X7 / N3 / N3 Flip / N2、vivo X200 / X200 Pro / X200 Pro mini / X100 / X100 Pro / X Fold5 / X Fold3 Pro、三星 Galaxy S24 / Z Fold6 / Z Flip6 / S25 Edge，共 **21 款**。
- 每款核验屏幕、电池（区分典型值/额定值）、充电、重量、容量组合中页面明确列出的项目，状态为 `verified_official_page_reviewed`。
- 通用回填器 `scripts/apply_field_audit.py` + 结构化数据 `.workbuddy/tmp/batch5.json`，便于后续批次复用。
- 累计：官方核验 **33 款**、第三方核验 **1 款**；仍待核验 18 款（一加 2、realme 2、iPhone 15、Galaxy S24+ 及官方页已下架的 13 款）。

## 2026-10-20 官方首发价回填（26 款）与价格标签分层

- 目标：把 2024—2026 年「只挂厂商页、页面不写价」的机型补上可追溯的首发价。本轮写入 **26 款**，目录有价记录由 172 条增至 **198 / 213**。
- 三档记账方式（已写入 `AUDIT_POLICY.md`）：
  - `official_launch_msrp`（21 款）：价格与容量 SKU 双确认，卡片标签「官方首发参考价」。
  - `official_starting_price`（5 款）：只有「XX 元起」，卡片标签强制显示「官方起售价（容量待核）」——MIX Flip 2、Pura 80 Pro+、Magic9 Pro Max、Magic9 超能版、一加 13T；另把原有 Magic8 Pro 一并归入此类，共 6 条。
  - `third_party_reference`（46 条，既有）：中关村在线参考价，标签「参考价（第三方）」。
- 官方页直证（`verified_official_page_reviewed`）：
  - 华为官网发布会页确认 Pura 80「￥4699 起」，配合官方档位 12GB+256GB 4699 / 12+512 5199 / 12+1TB 6199。
  - 荣耀官网发布稿确认 Magic9 Pro Max 6499 元起、Magic9 超能版 4499 元起。
  - 三星中国官网发布稿 + 官方促销页确认 Z Flip7 12+256 ￥7,999、S25 Edge 12+256 ￥7,999。
  - vivo 官网参数页「建议零售价」确认 X500 12+256 5499 元、iQOO 13 12+256 3999 元（后者与中国新闻网报道五档价格完全一致）。
  - 中兴（努比亚）官网发布稿确认 Z70 Ultra 12+256 4599 元。
- 权威媒体交叉核对（`cross_checked_secondary_source`）：小米 15 / 15 Pro / 15S Pro、Pura 80 Pro+、Find X8s / X8s+ / N5 / X10 / X9 Ultra、一加 15、iQOO 15、Mate 80 Pro、S26+ / S26 Ultra、真我 GT8 Pro / GT7、红魔 10 Pro。
- **已知冲突（未掩盖）**：HUAWEI Mate 80 Pro 发布当时（2025-11-25）中国证券网、黄浦区政府新闻、无锡市科技局简报均报 **5999 元起**，华为官网发布会页面当前标 **￥6999 起**，相差 1000 元。以发布当时价 5999 元（12GB+256GB）入库，并在 `evidenceText` 写明差异与「SKU 归属待复核」。同类现象见于 Galaxy S26 系列（2026-10 官方整体调价 +1000～2000 元），首发价仍按发布时价记录。
- 顺带修正两条历史数据：`honor-magic8-pro` 价格类型由 `unknown` 改为 `official_starting_price` 并补建价格审计条目；`op-15` 原 `priceSourceName` 写「暂无可靠的首发价格来源」却已填 3999，按 IT之家五档官方定价改为 `official_launch_msrp`（12GB+256GB 3999 元）。
- 仍缺价格 **15 款**，全部为 2021—2023 年机型（iPhone 13 / 13 mini / 13 Pro / 14 / 14 Plus / 15 Plus、Galaxy Z Fold5 / Z Flip5、Mate X5、REDMI K70 / K70 Pro / K60 Pro、vivo X90 / X Fold2、OPPO Find X6），官方产品页均已下架，需中关村在线链接。清单见 `reports/missing_price_models.md`。
- 修复一处同步缺陷：此前 HTML 内嵌数据用「保留旧数组 + 追加新数组」的方式拼接，重复执行会让数据成倍膨胀（本轮曾出现 213→639 条）。现改为整体替换 `window.PHONE_DATA=[...]` 块并在写盘前自检条数与内容，`scripts/backfill_launch_prices_2026-10-20.py` 已同步修正。

## 2026-10-20 价格覆盖收口：213 / 213

- 用户填写《待补价格机型填写表》后，最后 15 款 2021—2023 年机型补入价格，**目录 213 条全部有价**。
- 记账口径：用户只提供参考价与容量、未附中关村参数页链接，统一记 `priceType=third_party_reference`、`priceAuditStatus=secondary_source_reference`、`priceSource=""`，字段证据状态 `unverified_missing_or_insufficient_official_evidence`（详情页显示「待核验」）。不冒充官方首发价。
- 当前分布：`official_launch_msrp` 147、`third_party_reference` 59、`official_starting_price` 6、`official_retail_msrp` 1。
- **三星两条已核对**：
  - Galaxy Z Fold5（512GB / 12999 元）**正确**。国行 2023-08-03 发布时大陆只有 12GB+512GB（12999 元）与 12GB+1TB（14999 元），无 256GB 版本。该条已升级为 `official_launch_msrp`。
  - Galaxy Z Flip5（**512GB** / 8499 元）**已确认**。用户确认看到的是 512GB 版本；国行首发 8GB+256GB 为 7499 元、8GB+512GB 为 8499 元，与官方首发价吻合，已升级为 `official_launch_msrp`。
- ⚠ 修正记录：本文件与 `reports/missing_price_models.md` 初稿曾写「官方 12999 元对应 256GB、512GB 为 13999 元」，经中关村在线与三星中国商城页核对后证伪，已改正。教训：不要凭对海外版本 SKU 的印象推断国行版本序列。
- 后续若要升级这 15 条的来源等级，只需补中关村 `param.shtml` 地址，脚本 `scripts/apply_filled_prices_2026-10-20.py` 可按同一口径改写。
