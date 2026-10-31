"""生成首屏 CPU 成本的对照变体，定位 Layout 那 2 秒花在哪。

V1：卡片去掉 content-visibility:auto
V2：首屏骨架屏去掉（40 个带流光动画的元素）
V3：两者都去掉
"""
import re

src = open("index.html", encoding="utf-8").read()

# V1：在 </style> 前追加覆盖规则
v1 = src.replace(
    "</style>",
    ".phone-card{content-visibility:visible!important;contain-intrinsic-size:none!important}\n</style>",
    1,
)
open("_jst/_v1_nocv.html", "w", encoding="utf-8", newline="").write(v1)

# V2：清空骨架屏内容
m = re.search(r'<div class="skeleton-grid" aria-hidden="true">.*?</div>\s*</div>\s*(<div id="pagerBar")', src, re.S)
if not m:
    raise SystemExit("未匹配到骨架屏结构")
# 骨架屏自身是 <div class="skeleton-grid"> 内含多个 skeleton-card，再闭合
start = src.find('<div class="skeleton-grid" aria-hidden="true">')
# 找到与之配对的结束标签：按 div 计数
i = start
depth = 0
while i < len(src):
    nxt_open = src.find("<div", i)
    nxt_close = src.find("</div>", i)
    if nxt_close < 0:
        raise SystemExit("div 不闭合")
    if 0 <= nxt_open < nxt_close:
        depth += 1
        i = nxt_open + 4
    else:
        depth -= 1
        i = nxt_close + 6
        if depth == 0:
            break
block = src[start:i]
v2 = src.replace(block, '<div class="skeleton-grid" aria-hidden="true"></div>', 1)
open("_jst/_v2_noskel.html", "w", encoding="utf-8", newline="").write(v2)

# V3：两者叠加
v3 = v2.replace(
    "</style>",
    ".phone-card{content-visibility:visible!important;contain-intrinsic-size:none!important}\n</style>",
    1,
)
open("_jst/_v3_both.html", "w", encoding="utf-8", newline="").write(v3)

for n in ("_v1_nocv", "_v2_noskel", "_v3_both"):
    p = f"_jst/{n}.html"
    print(p, f"{len(open(p, encoding='utf-8').read().encode('utf-8')):,} 字节")
