/* 机选 Service Worker
 *
 * 目标：手机"添加到主屏幕"后像 App 一样打开；二次打开从本地读，接近瞬开；
 * 没网也能看已经打开过的机型。
 *
 * 三种策略各有理由：
 *  1) 页面导航 → 网络优先。内容会持续更新，缓存优先会让人看到旧数据；
 *     断网时才回落到缓存。
 *  2) detail/<id>.json → 缓存优先 + 后台更新。一台手机的规格几乎不变，
 *     二次看立刻出，同时在后台悄悄刷新。
 *  3) 其它同源 GET（图标、配置）→ 同上。
 *
 * 版本号变了才会重建 shell 缓存；改代码时请一起改 VERSION。
 */
const VERSION = 'v1';
const SHELL = `shell-${VERSION}`;
const RUNTIME = `runtime-${VERSION}`;

const SHELL_ASSETS = [
  './',
  './manifest.webmanifest',
  './api-config.js',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(SHELL).then((c) => c.addAll(SHELL_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== SHELL && k !== RUNTIME).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // 报价 API 等跨域请求不接管

  /* 页面导航：先网络，失败再吃缓存 */
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(SHELL).then((c) => c.put('./', copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match('./').then((r) => r || caches.match(req)))
    );
    return;
  }

  /* 其余：缓存优先，后台更新 */
  e.respondWith(
    caches.open(RUNTIME).then(async (cache) => {
      const hit = await cache.match(req);
      const network = fetch(req)
        .then((res) => {
          if (res && res.ok) cache.put(req, res.clone()).catch(() => {});
          return res;
        })
        .catch(() => null);
      if (hit) return hit;
      const res = await network;
      return res || new Response('', { status: 504, statusText: 'offline' });
    })
  );
});
