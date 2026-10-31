"""生成两个实验变体，量化「4MB 数据块的形态/位置」对首屏的影响。

A：把数据脚本从 2.4% 处整块搬到应用脚本之前（仍是可执行 JS 字面量）
B：在 A 的基础上，把 PHONE_DATA 改成 <script type="application/json"> + JSON.parse
   （MANUAL_QUOTES 只有 1.7KB，保持原样，避免一次动两个变量）

只写到 _jst/ 下，不参与产物。
"""
import json
import sys

src = open("index.html", encoding="utf-8").read()

# 1) 用 raw_decode 精确定位数组边界（比正则可靠：数据里含 ] 和 ; 都很正常）
i = src.find("window.PHONE_DATA=")
if i < 0:
    sys.exit("未找到 PHONE_DATA")
arr_start = src.find("[", i)
arr, arr_end = json.JSONDecoder().raw_decode(src, arr_start)

# 2) 整个数据脚本块 = 包住它的 <script> ... </script>
block_start = src.rfind("<script>", 0, i)
block_end = src.find("</script>", arr_end) + len("</script>")
block = src[block_start:block_end]
print(f"数据块 {len(block.encode('utf-8')):,} 字节（数组 {len(arr)} 条）")

payload = src[arr_start:arr_end]
if "</script" in payload.lower():
    sys.exit("数据里含 </script，不能放进 application/json 标签")
json.loads(payload)
print("JSON 合法，且不含 </script")

# 3) 其余同脚本内的语句（MANUAL_QUOTES 等）保持原样
rest = src[arr_end:block_end - len("</script>")].lstrip(";").strip()
print(f"同脚本内的其余语句 {len(rest)} 字节")

# 4) 应用脚本起点
anchor = "const phones=Array.isArray(window.PHONE_DATA)"
if src.count(anchor) != 1:
    sys.exit("锚点不唯一")


def relocate(body_without_block, insert):
    at = body_without_block.find(anchor)
    open_tag = body_without_block.rfind("<script>", 0, at)
    return body_without_block[:open_tag] + insert + "\n" + body_without_block[open_tag:]


stripped = src.replace(block, "", 1)

# A：原样搬
a = relocate(stripped, block)
open("_jst/_exp_a.html", "w", encoding="utf-8", newline="").write(a)

# B：数组转 JSON 文本，MANUAL_QUOTES 仍是小脚本
b_insert = (
    '<script id="phoneData" type="application/json">' + payload + "</script>\n"
    "<script>window.MANUAL_QUOTES=" + rest.split("=", 1)[1] + "</script>"
)
b = relocate(stripped, b_insert).replace(
    "const phones=Array.isArray(window.PHONE_DATA)?window.PHONE_DATA:[];",
    'const phones=(function(){try{const el=document.getElementById("phoneData");'
    "window.PHONE_DATA=el?JSON.parse(el.textContent):[];}catch(e){"
    'console.error("数据解析失败",e);window.PHONE_DATA=[];}return window.PHONE_DATA;})();',
    1,
)
open("_jst/_exp_b.html", "w", encoding="utf-8", newline="").write(b)

for name in ("_jst/_exp_a.html", "_jst/_exp_b.html"):
    s = open(name, encoding="utf-8").read()
    n = len(s.encode("utf-8"))
    marker = 'id="phoneData"' if 'id="phoneData"' in s else "window.PHONE_DATA"
    off = len(s[: s.find(marker)].encode("utf-8"))
    print(f"{name}: {n:,} 字节，数据块位于 {off / n * 100:.1f}%")
