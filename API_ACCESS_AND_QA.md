# 海纳好价检索 Pro v2：授权与报价质量验收

## 当前接入协议（控制台提供的海纳好价检索 Pro v2）

根据项目维护者提供的控制台文档截图，接口为：

- 方法：`POST`
- 地址：`https://gw-openapi.zhidemai.com/hj-search/discount/v2`
- Headers：`x-api-key: <你的Key>`、`Content-Type: application/json`
- Body：`request_from`、`question_id`、`product_query`、`query_process`、`size`、`fields`
- 返回报价列表：`data.rows[]`

文档所列的行字段包括商品信息 `title/url/direct_link/focus_pic_url/content`，价格信息 `price/digital_price/page_price/coupon/activity`，商城/品牌信息 `mall_id/mall_name/brand_id/brand_name`，以及 `bl_reason/haojia_dplink/pubdate/article_id/product_buy_step` 等业务字段。代码将这些字段映射到内部报价结构，优先使用 `direct_link` 作为商品跳转链接，并记录采用的价格字段。

## 密钥安全

1. API Key 曾出现在聊天消息和截图中；按安全最佳实践，应在海纳控制台轮换该 Key。
2. 将轮换后的 Key **只在自己的服务器或本地 `.env`** 中配置：`HAINAN_API_KEY=...`。不要贴回聊天、写进 HTML/JavaScript、打进前端演示版或提交到 Git。
3. 本项目只从服务端读取 `HAINAN_API_KEY`，浏览器仅请求本地 `/api/prices`。`.env` 和 `price_server.py` 不通过静态站点暴露。

## 请求参数

默认请求体示例（Key 只在 Header，不出现在 JSON 内）：

```json
{
  "request_from": "phone_compare_site",
  "question_id": "phonecompare-unique-id",
  "product_query": "小米 17 Ultra 16GB+512GB",
  "query_process": 1,
  "size": 20,
  "fields": ""
}
```

可在 `.env` 设置 `HAINAN_REQUEST_FROM`、`HAINAN_QUERY_PROCESS`、`HAINAN_RESULT_SIZE`、`HAINAN_FIELDS`、`HAINAN_MIN_REQUEST_INTERVAL_SECONDS` 与 `HAINAN_MAX_QUERIES_PER_RESPONSE`。默认每次 `/api/prices` 最多发 5 条商品词请求，间隔至少 0.6 秒，前端轮询继续补齐报价；这只是保守默认值，实际需以平台授予的 QPS 配额为准。

## 授权与错误响应

- `401`：检查 `x-api-key` 是否存在、有效，以及是否已被轮换/撤销。
- `403`：Key 可能未开通接口、过期或停用。
- `422`：请求体字段或值校验失败。
- `429`：超过 QPS 上限；降低频率，不要立即高频重试。
- `502/504`：上游服务不可用或超时，稍后重试。
- `/api/health` 的 `credentialsConfigured=true` 只说明后端检测到 Key，不证明平台授权已通过。只有成功的真实 `/api/prices` 请求才是授权连通证据。静态前端若单独部署，请在 `api-config.js` 配置 `window.PHONE_API_BASE_URL`，并在后端 `.env` 将 `PHONE_CORS_ORIGIN` 限定为前端确切来源；不要使用通配 CORS。

## 价格匹配规则

- 首先要求商品标题/内容匹配本库机型别名与 `quoteTargetStorage`。
- 排除明显的二手、翻新、配件、海外版等结果。
- 必须具备合理数值价格和 HTTPS 直达链接。
- 价格字段按 `digital_price`、`price`、`page_price` 顺序尝试，且记录使用的字段；若各字段含义/优惠口径与页面实际展示不一致，人工核价时应判为不一致，不可直接当到手价。`coupon`、`activity` 仅作优惠提示，不擅自估算折后价。
- `direct_link` / `haojia_dplink` 优先作为购买链接，`url` 作为备用来源文章链接；要确认它是否最终到达零售商品页。
- API 返回的是好价内容检索快照，不是订单结算承诺。必须人工核对全新国行、精确容量、库存、地区与优惠资格。

## 运行与验收

```bash
# 复制 .env.example 为 .env，填入轮换后的 Key 后启动服务
python price_server.py

# 先抽查 9 个品牌代表机型
python quote_quality_check.py

# 样本通过后再查全部机型（会消耗更多配额）
python quote_quality_check.py --all
```

四项指标分别为：

1. **报价覆盖率**：返回精确型号+目标容量的 API 报价机型数 / 本轮请求机型数。
2. **自动规则通过率**：通过机型、容量、有效价格、HTTPS、商城、时间与排除规则的报价数 / 返回报价数。
3. **页面价格一致率**：24 小时内人工核对的 API 价格与页面实价差额不超过 ¥1 的条数 / 有可比较页面实价的条数。
4. **有效可购买链接率**：24 小时内确认页面可访问、国行全新机、存储准确、有库存/购买路径的链接数 / 已审核链接数。

未完成真实授权请求时，API 指标应为 `null`/N/A，不要显示为 0%。人工页面快照不能混入 API 报价指标。
