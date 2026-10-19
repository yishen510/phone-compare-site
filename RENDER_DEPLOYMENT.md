# 报价 API 后端部署指南（Render + GitHub Pages）

## 为什么要单独部署
GitHub Pages 只能托管静态网页，不能执行 `price_server.py`。本项目通过 Render 部署 Python API，GitHub Pages 继续托管前端；API Key 只保存在 Render 环境变量中。

## 部署步骤
1. 打开 Render，选择 **New → Blueprint**，连接 GitHub 仓库 `yishen510/phone-compare-site`，选择分支 `main`。仓库根目录的 `render.yaml` 已定义 Web Service、Python 语法检查、启动命令与健康检查。
2. 创建服务时，在 Render 的 Environment 页面设置 `HAINAN_API_KEY` 为已经轮换的有效 Key。不要把 Key 写进仓库文件、`api-config.js`、前端 HTML 或聊天记录。
3. 等待部署完成，复制 Render 分配的 HTTPS 服务域名，例如 `https://<your-service>.onrender.com`。
4. 在仓库的 `api-config.js` 中设置：
   ```js
   window.PHONE_API_BASE_URL = "https://<your-service>.onrender.com";
   ```
   只填写后端公开域名，不要在此处放任何密钥。
5. 检查 `render.yaml` 的 `PHONE_CORS_ORIGIN` 与 Pages 前端的 **Origin** 一致。当前默认值是 `https://yishen510.github.io`；如果 Pages 使用了自定义域名，请在 Render 环境变量里改成那个域名的 origin（只写协议和主机，不带路径）。
6. 提交 `api-config.js` 的更改，等待 GitHub Pages 部署完成。
7. 先访问 `https://<your-service>.onrender.com/api/health`。预期 JSON 中 `status` 为 `ok`、`credentialsConfigured` 为 `true`。这只说明后端运行且检测到 Key，并不证明上游授权成功。
8. 再通过本地运行的 `python quote_quality_check.py` 做真实 API 请求与规则评估。只有真实请求成功、且商品标题/容量/价格/HTTPS 链接通过规则，才计入 API 报价指标。
9. 打开 Pages 网站，确认状态栏、前 10 款抽查报价和商品跳转链接。人工打开商品页，核对全新国行、精确容量、库存、地区和优惠条件后，再登记到 `reports/quote_quality_manual_review.csv`。

## 本地先验证（可选，不消耗真实配额）
1. `.env` 里取消注释 `HAINAN_API_KEY=mock-test-key` 与 `HAINAN_API_URL=http://127.0.0.1:8899/hj-search/discount/v2`。
2. 终端 A：`python _mock_upstream.py`；终端 B：`python price_server.py`。
3. 打开 `http://127.0.0.1:8000/index.html`，卡片应出现「渠道报价 ¥4,299 · 京东 · 12GB+256GB · 商品页 ↗」。
4. 验证完把这两行重新注释掉，再填真实 Key。

## 重要说明
- Render 免费服务可能休眠，第一次请求可能需要等待冷启动。
- 如果上游返回 401/403/429，先检查 Key 是否轮换、是否开通好价检索 Pro 权限及剩余额度；不要将 Key 暴露给前端来绕过错误。
- API 返回的是搜索候选报价，不保证结算价。不能把渠道参考价覆盖为官方首发价，也不能把 API 候选标记成“人工已核验”。
- 如果后端服务尚未部署或 `api-config.js` 仍为空，GitHub Pages 上会显示“报价 API 状态：未接入”，且**不会发出任何 /api 请求**（前端已加未配置守卫，避免每次打开都 404）。
- Render 免费实例休眠后首次访问需要 30—60 秒冷启动，前端对 `/api/health` 已做 25 秒超时 + 1 次重试，仍失败才显示“后端未连接”。
