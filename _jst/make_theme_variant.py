"""生成配色变体：只换颜色，不动结构与逻辑。

用法：python _jst/make_theme_variant.py <方案名> <acc> <acc2> <deep> <text>
颜色都是暗色主题的令牌值，浅色按同一色相自动派生。

改色的两个坑（写在这里免得下次忘）：
1) 同一个十六进制值在两套主题里可能是不同角色，必须按主题块精确替换；
2) 组件里有大量写死的 rgba(...)，只改变量会在渐变/阴影/描边里留旧色。
"""
import colorsys
import sys

name, acc, acc2, deep, text = sys.argv[1:6]


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexof(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def to_hls(h):
    r, g, b = [v / 255 for v in rgb(h)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, s, l


def lum(h):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + .05) / (min(la, lb) + .05)


def shift(h, ds, dl):
    hh, s, l = to_hls(h)
    return hexof(hh, max(0, min(1, s + ds)), max(0, min(1, l + dl)))


# 浅色主题令牌：同色相，按浅底反推可读的深度
acc_l = shift(acc, 0.02, -0.10)
acc2_l = shift(acc2, 0.0, -0.09)
deep_l = shift(deep, 0.04, -0.06)
text_l = shift(acc, 0.03, -0.12)

src = open("index.html", "rb").read().decode("utf-8")

pairs = [
    # 暗色令牌
    ("--accent:#266571;", f"--accent:{acc};"),
    ("--accent-2:#367f8b;", f"--accent-2:{acc2};"),
    ("--accent-deep:#16424d;", f"--accent-deep:{deep};"),
    ("--accent-text:#79d5e0;", f"--accent-text:{text};"),
    # 浅色令牌
    ("--accent:#1c6373;", f"--accent:{acc_l};"),
    ("--accent-2:#2a6f80;", f"--accent-2:{acc2_l};"),
    ("--accent-deep:#12414d;", f"--accent-deep:{deep_l};"),
    ("--accent-text:#1c5a6b;", f"--accent-text:{text_l};"),
    # 首屏标题渐变
    ("linear-gradient(96deg,#ffffff 6%,#a9e6ee 34%,#4aa5b4 68%,#2f8fa0 100%)",
     f"linear-gradient(96deg,#ffffff 6%,{text} 40%,{acc2} 100%)"),
    ("linear-gradient(96deg,#0d1626 4%,#0f7d8e 48%,#155f6d 94%)",
     f"linear-gradient(96deg,#0d1626 4%,{acc_l} 48%,{deep_l} 94%)"),
]
for old, new in pairs:
    if src.count(old) != 1:
        sys.exit(f"锚点不唯一或缺失: {old} -> {src.count(old)}")
    src = src.replace(old, new, 1)

# 组件级：按 RGB 替换，保留原 alpha
ar, ag, ab = rgb(acc)
tr, tg, tb = rgb(text)
al, alg, alb = rgb(acc_l)
comp = [
    ("rgba(38,101,113,", f"rgba({ar},{ag},{ab},"),
    ("rgba(121,213,224,", f"rgba({tr},{tg},{tb},"),
    ("rgba(28,99,115,", f"rgba({al},{alg},{alb},"),
    ("#266571", acc), ("#367f8b", acc2), ("#16424d", deep), ("#79d5e0", text),
    ("#1c6373", acc_l), ("#2a6f80", acc2_l), ("#12414d", deep_l), ("#1c5a6b", text_l),
]
for old, new in comp:
    src = src.replace(old, new)

out = f"_jst/_theme_{name}.html"
open(out, "wb").write(src.encode("utf-8"))
print(f"{out}  暗[{acc} {acc2} {deep} {text}] 浅[{acc_l} {acc2_l}]")
print(f"  白字压最浅端 {contrast('#ffffff', acc2):.2f} · 强调字在暗底 {contrast(text, '#171b21'):.2f}"
      f" · 浅底强调字 {contrast(acc_l, '#e8e9ec'):.2f}")
