"""生成 PWA 图标（纯标准库，不依赖 Pillow）。

图形：蓝渐变圆角方块 + 白色手机轮廓。没有文字——中文字形需要字体文件，
用几何图形反而在各种尺寸下都清晰。

用法：python scripts/make_icons.py
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "icons"
SS = 4  # 超采样倍数，用于抗锯齿


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def in_round_rect(x, y, w, h, r, left, top):
    """点是否落在圆角矩形内（坐标已归一化到 0..1 的局部空间）"""
    cx = min(max(x, left + r), left + w - r)
    cy = min(max(y, top + r), top + h - r)
    if left <= x <= left + w and top <= y <= top + h:
        if (x < left + r or x > left + w - r) and (y < top + r or y > top + h - r):
            return (x - cx) ** 2 + (y - cy) ** 2 <= r * r
        return True
    return False


def render(size: int, pad: float = 0.0) -> bytes:
    """pad：四周留白比例（maskable 图标要留出安全区）"""
    top_c = (59, 118, 234)      # #3b76ea
    bot_c = (30, 64, 175)       # #1e40af
    white = (255, 255, 255)
    px = bytearray()

    # 图形在留白后的可用区域内绘制
    box = 1.0 - pad * 2
    for y in range(size):
        px.append(0)  # filter: none
        for x in range(size):
            acc = [0.0, 0.0, 0.0, 0.0]
            for sy in range(SS):
                for sx in range(SS):
                    u = (x + (sx + 0.5) / SS) / size
                    v = (y + (sy + 0.5) / SS) / size
                    # 归一化到图形区域
                    uu = (u - pad) / box
                    vv = (v - pad) / box
                    if not (0 <= uu <= 1 and 0 <= vv <= 1):
                        continue  # 透明
                    bg = lerp(top_c, bot_c, vv)
                    color = bg
                    if in_round_rect(uu, vv, 1, 1, 0.22, 0, 0):
                        # 手机机身：中间偏上的圆角矩形
                        if in_round_rect(uu, vv, 0.40, 0.62, 0.09, 0.30, 0.19):
                            color = white
                            # 挖空屏幕，形成描边
                            if in_round_rect(uu, vv, 0.32, 0.52, 0.07, 0.34, 0.24):
                                color = lerp(top_c, bot_c, vv * 0.9)
                        # 屏幕内的 Home 指示条：给"手机"一个身份，不然只是个空心框
                        elif in_round_rect(uu, vv, 0.16, 0.028, 0.014, 0.42, 0.705):
                            color = white
                    else:
                        continue  # 圆角外透明
                    acc[0] += color[0]
                    acc[1] += color[1]
                    acc[2] += color[2]
                    acc[3] += 255
            n = SS * SS
            if acc[3] == 0:
                px += bytes((0, 0, 0, 0))
            else:
                a = acc[3] / n
                px += bytes((round(acc[0] / (acc[3] / 255)), round(acc[1] / (acc[3] / 255)),
                             round(acc[2] / (acc[3] / 255)), round(a)))
    return png_bytes(size, size, bytes(px))


def png_bytes(w: int, h: int, raw: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)  # 8bit RGBA
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    jobs = [
        ("icon-192.png", 192, 0.02),
        ("icon-512.png", 512, 0.02),
        ("icon-maskable-512.png", 512, 0.14),   # maskable 需要安全区
        ("apple-touch-icon.png", 180, 0.02),
    ]
    for name, size, pad in jobs:
        (OUT / name).write_bytes(render(size, pad))
        print(f"{name}  {size}×{size}")
