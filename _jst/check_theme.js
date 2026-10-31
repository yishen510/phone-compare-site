/* 配色可读性自检：从 index.html 读出两套主题的令牌，按 WCAG 算对比度。
   关键点：玻璃是半透明的，文字压在 blend(tint, bg) 之后的"有效面"上，
   所以不能只对 --bg 算——那会高估对比度（透明化之后尤其危险）。
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
const rawTok = (b, name) => {
  const m = b.match(new RegExp(`--${name}\\s*:\\s*([^;]+);`));
  return m ? m[1].trim() : null;
};
function hex2rgb(h) {
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
}
function parseColor(v) {
  if (v.startsWith('#')) return { rgb: hex2rgb(v), a: 1 };
  const m = v.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)/);
  if (!m) return null;
  return { rgb: [+m[1], +m[2], +m[3]], a: m[4] === undefined ? 1 : +m[4] };
}
const toHex = t => '#' + t.map(v => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('');
const blend = (fg, bg) => toHex(fg.rgb.map((v, i) => fg.a * v + (1 - fg.a) * bg[i]));
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

for (const [label, sel] of [['暗色', ':root{'], ['浅色', 'html[data-theme="light"]{']]) {
  const b = block(sel);
  const bg = rawTok(b, 'bg');
  const ink = rawTok(b, 'ink');
  const muted = parseColor(rawTok(b, 'muted'));
  const faint = parseColor(rawTok(b, 'faint'));
  const aText = rawTok(b, 'accent-text');
  const g1 = parseColor(rawTok(b, 'glass-1'));
  const g4 = parseColor(rawTok(b, 'glass-4'));

  /* 玻璃压在底色上的"实际看到的那层颜色" */
  const surf1 = blend(g1, hex2rgb(bg));
  const surf4 = blend(g4, hex2rgb(bg));
  const mutedOn1 = blend(muted, hex2rgb(surf1));
  const faintOn1 = blend(faint, hex2rgb(surf1));

  chk(`${label}：正文压卡片面 ≥ 7`, contrast(ink, surf1) >= 7,
    `${surf1} = ${contrast(ink, surf1).toFixed(2)}`);
  chk(`${label}：次要文字压卡片面 ≥ 4.5`, contrast(mutedOn1, surf1) >= 4.5,
    contrast(mutedOn1, surf1).toFixed(2));
  chk(`${label}：最淡文字压卡片面 ≥ 4.5`, contrast(faintOn1, surf1) >= 4.5,
    contrast(faintOn1, surf1).toFixed(2));
  chk(`${label}：强调字压卡片面 ≥ 4.5`, contrast(aText, surf1) >= 4.5,
    contrast(aText, surf1).toFixed(2));
  chk(`${label}：正文压弹层 ≥ 7`, contrast(ink, surf4) >= 7,
    `${surf4} = ${contrast(ink, surf4).toFixed(2)}`);
  chk(`${label}：玻璃真的半透明（L1 alpha ≤ 0.60）`, g1.a <= 0.60, `alpha ${g1.a}`);
  chk(`${label}：透明但仍不糊（L1 alpha ≥ 0.50）`, g1.a >= 0.50, `alpha ${g1.a}`);

  const acc = rawTok(b, 'accent'), acc2 = rawTok(b, 'accent-2'), deep = rawTok(b, 'accent-deep');
  chk(`${label}：白字压 accent ≥ 4.5`, contrast('#ffffff', acc) >= 4.5, `${acc} = ${contrast('#ffffff', acc).toFixed(2)}`);
  chk(`${label}：白字压 accent-2 ≥ 4.5`, contrast('#ffffff', acc2) >= 4.5, `${acc2} = ${contrast('#ffffff', acc2).toFixed(2)}`);
  chk(`${label}：白字压 accent-deep ≥ 4.5`, contrast('#ffffff', deep) >= 4.5, contrast('#ffffff', deep).toFixed(2));
}

/* 主色必须留在冷色区间，别又飘回暖色 */
const dark = block(':root{');
const [ar, ag, ab] = hex2rgb(rawTok(dark, 'accent'));
const hue = (() => {
  const r = ar / 255, g = ag / 255, bl = ab / 255;
  const mx = Math.max(r, g, bl), mn = Math.min(r, g, bl), d = mx - mn;
  if (d === 0) return 0;
  let h;
  if (mx === r) h = ((g - bl) / d) % 6;
  else if (mx === g) h = (bl - r) / d + 2;
  else h = (r - g) / d + 4;
  return (h * 60 + 360) % 360;
})();
chk('主色色相落在冷色区间（160°–300°）', hue >= 160 && hue <= 300, `${hue.toFixed(0)}°`);

const stale = ['#b02a35', '#c94850', '#78171f', '#9c2b33', '#96262f', '#e9a09c',
               '#266571', '#367f8b', '#79d5e0', '#0f1319', '#345e95'];
const found = stale.filter(c => html.toLowerCase().includes(c));
chk('没有残留旧版本主色', found.length === 0, found.join(',') || '干净');

console.log(`\n${ok} 通过 / ${bad} 失败`);
process.exit(bad ? 1 : 0);
