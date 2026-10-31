/* 配色可读性自检：从 index.html 里读出两套主题的令牌，按 WCAG 算对比度。
   调色时最容易犯的错是把主色提亮后按钮白字/小字看不清，这个脚本把那条线守住。
   用法：node _jst/check_theme.js */
const fs = require('fs');

const html = fs.readFileSync('index.html', 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));

function block(selector) {
  const i = css.indexOf(selector);
  if (i < 0) throw new Error('找不到 ' + selector);
  const open = css.indexOf('{', i);
  const close = css.indexOf('}', open);
  return css.slice(open + 1, close);
}
function token(blockText, name) {
  const m = blockText.match(new RegExp(`--${name}\\s*:\\s*(#[0-9a-fA-F]{3,8})`));
  return m ? m[1] : null;
}
function hex2rgb(h) {
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
}
function lum(hex) {
  const [r, g, b] = hex2rgb(hex).map(v => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
const contrast = (a, b) => {
  const la = lum(a), lb = lum(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
};

let ok = 0, bad = 0;
const chk = (name, cond, extra = '') => {
  cond ? ok++ : bad++;
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra ? '  → ' + extra : ''}`);
};

const dark = block(':root{');
const light = block('html[data-theme="light"]{');

/* 两个 #fff 压在最浅的那档 accent-2 上（.button-dark 的渐变起点就是它）；
   小字 12.5px 属正文级别，AA 要求 4.5。 */
for (const [label, blk] of [['暗色', dark], ['浅色', light]]) {
  const a2 = token(blk, 'accent-2');
  const a = token(blk, 'accent');
  const txt = token(blk, 'accent-text');
  const bg = token(blk, 'bg');
  const deep = token(blk, 'accent-deep');
  chk(`${label}：按钮白字压 accent-2 ≥ 4.5`, contrast('#ffffff', a2) >= 4.5,
    `${a2} = ${contrast('#ffffff', a2).toFixed(2)}`);
  chk(`${label}：按钮白字压 accent ≥ 4.5`, contrast('#ffffff', a) >= 4.5,
    `${a} = ${contrast('#ffffff', a).toFixed(2)}`);
  chk(`${label}：按钮白字压 accent-deep ≥ 4.5`, contrast('#ffffff', deep) >= 4.5,
    `${deep} = ${contrast('#ffffff', deep).toFixed(2)}`);
  chk(`${label}：accent-text 在底色上 ≥ 4.5`, contrast(txt, bg) >= 4.5,
    `${txt} on ${bg} = ${contrast(txt, bg).toFixed(2)}`);
  chk(`${label}：正文 --ink 在底色上 ≥ 4.5`, contrast(token(blk, 'ink'), bg) >= 4.5,
    `${contrast(token(blk, 'ink'), bg).toFixed(2)}`);
}

/* 主色必须真的"凉"下来：色相在青蓝区间，别又飘回暖色 */
const [ar, ag, ab] = hex2rgb(token(dark, 'accent'));
const hue = (() => {
  const r = ar / 255, g = ag / 255, b = ab / 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (d === 0) return 0;
  let h;
  if (mx === r) h = ((g - b) / d) % 6;
  else if (mx === g) h = (b - r) / d + 2;
  else h = (r - g) / d + 4;
  return (h * 60 + 360) % 360;
})();
chk('主色色相在青蓝区间（160°–220°）', hue >= 160 && hue <= 220, `${hue.toFixed(0)}°`);

/* 页面上不该再出现旧的品牌红 */
const stale = ['#b02a35', '#c94850', '#78171f', '#9c2b33', '#96262f', '#e9a09c'];
const found = stale.filter(c => html.toLowerCase().includes(c));
chk('没有残留旧品牌红', found.length === 0, found.join(',') || '干净');

console.log(`\n${ok} 通过 / ${bad} 失败`);
process.exit(bad ? 1 : 0);
