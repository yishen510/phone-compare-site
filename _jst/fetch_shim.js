/* 测试用 fetch 垫片：把 data/detail/<id>.json 从磁盘读出来喂给页面。
   为什么需要：规格与逐字段溯源已从首屏数据拆到按需文件，
   jsdom 里没有 fetch，详情会拿不到规格（表现为 .spec-group 渲染 0 组）。
   只处理 detail 请求，其余一律 ok:false，避免掩盖真实问题。 */
const fs = require('fs');
const path = require('path');

module.exports = function installFetchShim(w) {
  w.fetch = function (url) {
    const m = String(url).match(/data\/detail\/([^/?#]+)\.json/);
    if (!m) return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve(null) });
    try {
      const file = path.join(process.cwd(), 'data', 'detail', decodeURIComponent(m[1]) + '.json');
      const data = JSON.parse(fs.readFileSync(file, 'utf8'));
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(data) });
    } catch (e) {
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve(null) });
    }
  };
};
