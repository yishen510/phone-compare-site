# 报价 API 接入状态（2026-10-18）

## 已写入代码
- 服务端报价适配器已切换到海纳好价检索 Pro v2：`POST https://gw-openapi.zhidemai.com/hj-search/discount/v2`。
- 鉴权通过请求头 `x-api-key` 发送；密钥只从服务端环境变量 `HAINAN_API_KEY` 读取，不应放进 HTML、浏览器脚本或 Git。
- 请求体支持 `request_from`、唯一 `question_id`、`product_query`、`query_process`、`size` 和 `fields`。
- 返回字段映射覆盖 `data.rows[]` 中的标题、数字价格、商品直达链接、商城与优惠信息；记录实际使用的价格字段。
- 保留型号别名、容量 SKU 匹配、HTTPS 链接校验、二手/翻新/配件/非大陆版本过滤、错误提示与缓存。
- `/api/health` 用于检查后端是否配置凭据；`/api/prices?ids=...` 用于查询指定机型。单次最多处理 5 款，并按配置限制请求间隔。
- 网页已接入后端探测与报价渲染；首次只抽查 9 款代表机型，避免未经质量验收就消耗整个目录的调用配额。
- 新增 `.env.example` 和 `.gitignore`，防止本地凭据文件被误提交。

## 仍待完成（不能标记为已上线）
- **没有在当前执行环境发起真实的海纳授权请求**：环境中没有项目所有者的密钥，也无法访问其本机部署进程。
- 请在海纳控制台轮换任何曾出现在聊天或截图中的 Key，然后仅在部署服务器配置新的 `HAINAN_API_KEY`。
- 本地 `/api/health` 返回 `credentialsConfigured=true` 仅表示环境变量存在，不代表 Key 有效或已开通 Pro 权限。
- 真实调用成功后，才可以确认鉴权连通；接着运行 `python quote_quality_check.py` 并人工抽查商品页，再决定是否扩大到全部机型。
- 如果网站只部署在 GitHub Pages 等纯静态托管环境，`/api/health` 不会自动存在；必须另外部署 Python 后端并将前端 API 路径配置到该后端域名。不要将 Key 暴露给前端来绕过此限制。

## 在本机启动
1. 复制 `.env.example` 为 `.env`，把占位值替换成轮换后的 Key。
2. 安装 Python 3.10+（代码使用标准库，无需额外 Python 包）。
3. 在项目目录运行 `python price_server.py`。
4. 打开 `http://127.0.0.1:8000/api/health` 确认服务启动。
5. 运行 `python quote_quality_check.py`，检查 `apiWasActuallyTested`、`apiStatus`、覆盖率与自动规则通过率。
6. 在 `reports/quote_quality_manual_review.csv` 人工记录商品页实价、国行全新状态、精确容量与库存；人工核验指标不得与 API 自动指标混算。

## 价格口径
- API 搜索报价不是订单最终结算承诺。下单前必须重新打开商品页，确认商品新旧、国行版本、容量、库存、地区与优惠资格。
- 当前渠道报价不得覆盖 `priceCN` 或冒充官方首发价；API 未返回精确型号/容量匹配时保持“待核验”。
- 未完成真实授权请求与页面抽检前，API 报价质量指标保持 N/A。
