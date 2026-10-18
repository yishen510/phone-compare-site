# GitHub Pages 部署与验收

## 当前状态

GitHub Actions 工作流为 `.github/workflows/static.yml`，会在 `main` 分支推送或手动触发时执行 Python 语法检查、报价规则单元测试，再运行 `scripts/build_pages.py` 生成最小静态产物，并通过官方 Pages Actions 部署。工作流只发布 `_site/` 中的 `index.html`、`phone-compare-demo.html` 与公开配置 `api-config.js`，不会把原始机型 JSON、审核报告、Python 脚本或 API 配置说明整个项目目录公开。

**注意：**本地准备好工作流不等于已发布。必须先将项目推送到用户有权限的 GitHub 仓库，并在仓库 Settings → Pages 中确认 Build and deployment 的 Source 为 **GitHub Actions**。首个部署完成后，以 Actions 的 deployment 输出 URL 为准。

## 部署步骤

1. 将本项目提交并推送至自己的 GitHub 仓库，默认分支使用 `main` 或 `master`。
2. 打开仓库 Settings → Pages，将 Source 设为 **GitHub Actions**。
3. 在 Actions 页确认 `Build and deploy GitHub Pages` 工作流成功完成；如仓库要求审批，完成对应审批。
4. 复制部署任务输出的 `page_url`，在浏览器无登录状态下打开首页及 `phone-compare-demo.html`。确认 `api-config.js` 也能加载；在 Render 后端部署前，它保持空字符串是预期状态。
5. 将真实 URL 提供给验收流程，执行线上 HTTP/TLS/资源加载、控制台错误、搜索、品牌/年份筛选、对比、准入门禁和窄屏交互测试。

## 生产验收口径

只有实际目标 URL 已访问且逐项验证通过，才可把生产部署验收标记为通过。以下均不算生产验收：本地 HTTP 200、`page.set_content` 浏览器测试、工作流文件存在、ZIP 可解压或 GitHub Actions 工作流尚未执行。

构建脚本已在本地执行通过；这仅验证源目录与产物生成，不代表 GitHub Actions 或生产环境通过。当前项目中的外部 Google Fonts 为增强性资源；即使字体服务不可用，页面也应保持可读。线上测试需检查字体请求失败是否影响布局，但不把第三方字体加载成功当作核心交互前置条件。
