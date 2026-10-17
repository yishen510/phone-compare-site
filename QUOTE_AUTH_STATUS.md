# 报价 API 接入状态（2026-10-17）

## 已完成

- 已根据控制台文档截图切换到新版接口：`POST https://gw-openapi.zhidemai.com/hj-search/discount/v2`。
- 新版鉴权使用 `x-api-key`；移除了旧版 `app_key + timestamp + sign + app_secret` 的运行依赖。
- 请求体包含 `request_from`、唯一 `question_id`、`product_query`、`query_process`、`size`、`fields`；结果从 `data.rows[]` 解析。
- 映射 `title`、`content`、`direct_link`、`url`、`price`、`digital_price`、`page_price`、`coupon`、`activity`、`mall_name`、`brand_name` 等字段。会记录使用的价格字段并提示 API 报价不等于最终结算价。
- 增加 401/403/422/429/502/504 错误解释；按保守频率调用，每次响应最多查询 5 款，前端自动分批轮询，以降低触发 QPS 的概率。
- Key 只在服务端 `.env`，未写入 HTML、演示版或项目包。

## 尚待完成

- **真实授权请求尚未执行**：Key 在聊天消息/截图中可见，出于安全考虑不使用这把已暴露的 Key。请在海纳控制台轮换后，在本机 `.env` 中填写新 Key。
- `/api/health` 检测到 Key 只能证明配置存在，不证明平台权限有效；首次真实 API 请求成功后才能确认鉴权连通。
- 四项真实报价指标仍应标记 N/A，直到成功调用并完成商品页人工抽检。

## 建议步骤

1. 在海纳控制台轮换已公开的 Key。
2. 本机将 `.env.example` 复制为 `.env`，只设置 `HAINAN_API_KEY=新Key`。
3. `python price_server.py`，然后检查 `http://127.0.0.1:8000/api/health`。
4. 运行 `python quote_quality_check.py`；核实 JSON 报告中的 `apiWasActuallyTested`、`apiStatus` 和四项指标。
5. 手工核对 `reports/quote_quality_manual_review.csv`，再报告页面价格一致率和有效可购买链接率。
