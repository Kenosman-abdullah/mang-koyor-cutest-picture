"""Bunny in a Strawberry Beret.

Entry for the make.fun bounty "Make the cutest picture".
A deterministic program (Python standard library only) that draws one
cute picture and writes it to output/entry.png.

The picture riffs on the leaderboard's top three: a fluffy baby animal
with huge glossy eyes and blush cheeks hugging a tiny yellow chick on
a soft pastel background, in a soft kawaii style. The twist: the animal
is a grey bunny (not a kitten or puppy), and instead of a knitted scarf
or a daisy crown it wears a strawberry beret.
"""

import math
import os
import random
import struct
import zlib
from hashlib import sha256

W = 1024
H = 1024

LILAC_TOP = (206, 194, 232)
LILAC_BOTTOM = (233, 212, 230)
GREY = (228, 228, 235)
GREY_LIGHT = (241, 241, 247)
OUTLINE = (196, 194, 218)
PINK_IN = (246, 183, 196)
PINK = (245, 170, 182)
DARK = (52, 46, 60)
NOSE = (230, 120, 130)
MOUTH = (140, 105, 115)
RED = (228, 72, 92)
RED_DARK = (198, 52, 72)
GREEN = (90, 170, 110)
YELLOW = (255, 214, 92)
YELLOW_DARK = (250, 190, 60)
ORANGE = (255, 150, 60)
WHITE = (255, 255, 255)
CREAM = (255, 244, 214)
SHADOW = (200, 186, 214)

buf = bytearray(W * H * 3)
rng = random.Random(31113)


def lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def set_px(x, y, col):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = col[0]
        buf[i + 1] = col[1]
        buf[i + 2] = col[2]


def blend_px(x, y, col, a):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        b = 1.0 - a
        buf[i] = int(buf[i] * b + col[0] * a)
        buf[i + 1] = int(buf[i + 1] * b + col[1] * a)
        buf[i + 2] = int(buf[i + 2] * b + col[2] * a)


def row_fill(y, col):
    i = y * W * 3
    buf[i:i + W * 3] = bytes(col) * W


def circle(cx, cy, r, col, a=1.0):
    r2 = r * r
    y0 = max(0, int(cy - r))
    y1 = min(H - 1, int(cy + r))
    for y in range(y0, y1 + 1):
        dy = y - cy
        dx = int(math.sqrt(max(0, r2 - dy * dy)))
        x0 = max(0, int(cx - dx))
        x1 = min(W - 1, int(cx + dx))
        if a >= 1.0:
            for x in range(x0, x1 + 1):
                set_px(x, y, col)
        else:
            for x in range(x0, x1 + 1):
                blend_px(x, y, col, a)


def ellipse(cx, cy, rx, ry, col):
    for y in range(max(0, int(cy - ry)), min(H - 1, int(cy + ry)) + 1):
        t = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        for x in range(max(0, int(cx - dx)), min(W - 1, int(cx + dx)) + 1):
            set_px(x, y, col)


def rellipse(cx, cy, rx, ry, angle_deg, col, a=1.0):
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    r = max(rx, ry)
    for y in range(max(0, int(cy - r)), min(H - 1, int(cy + r)) + 1):
        for x in range(max(0, int(cx - r)), min(W - 1, int(cx + r)) + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                if a >= 1.0:
                    set_px(x, y, col)
                else:
                    blend_px(x, y, col, a)


def line(x0, y0, x1, y1, col, width=1):
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy))) + 1
    r = width // 2
    for s in range(steps + 1):
        t = s / steps
        x = int(x0 + dx * t)
        y = int(y0 + dy * t)
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                if ox * ox + oy * oy <= r * r + r:
                    set_px(x + ox, y + oy, col)


def poly(points, col):
    ys = [p[1] for p in points]
    for y in range(max(0, int(min(ys))), min(H - 1, int(max(ys))) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(xs[i])), min(W - 1, int(xs[i + 1])) + 1):
                set_px(x, y, col)


def sparkle(x, y, size, col):
    line(x - size, y, x + size, y, col, 1)
    line(x, y - size, x, y + size, col, 1)


def flower(cx, cy, r, petal, centre):
    for k in range(5):
        ang = 2 * math.pi * k / 5 - math.pi / 2
        circle(int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang)), int(r * 0.62), petal)
    circle(cx, cy, int(r * 0.55), centre)


def background():
    for y in range(H):
        row_fill(y, lerp(LILAC_TOP, LILAC_BOTTOM, y / H))
    for _ in range(42):
        x = rng.randrange(40, W - 40)
        y = rng.randrange(40, H - 40)
        col = rng.choice([(244, 200, 210), (196, 232, 210), (255, 236, 170), (200, 220, 250)])
        circle(x, y, rng.randrange(8, 22), col, a=0.28)


def shadow():
    rellipse(512, 905, 320, 42, 0, SHADOW, a=0.45)


def bunny():
    ellipse(512, 660, 272, 242, OUTLINE)
    ellipse(512, 660, 265, 235, GREY)
    ellipse(512, 700, 185, 165, GREY_LIGHT)
    circle(512, 415, 201, OUTLINE)
    circle(512, 415, 195, GREY)
    circle(345, 470, 50, OUTLINE)
    circle(680, 470, 50, OUTLINE)
    circle(345, 470, 45, GREY)
    circle(680, 470, 45, GREY)
    rellipse(415, 205, 64, 166, -12, OUTLINE)
    rellipse(610, 205, 64, 166, 12, OUTLINE)
    rellipse(415, 205, 58, 160, -12, GREY)
    rellipse(610, 205, 58, 160, 12, GREY)
    rellipse(415, 215, 30, 115, -12, PINK_IN)
    rellipse(610, 215, 30, 115, 12, PINK_IN)


def beret():
    rellipse(605, 250, 120, 58, -18, RED)
    rellipse(605, 268, 118, 20, -18, RED_DARK)
    ang = math.radians(-18)
    ca, sa = math.cos(ang), math.sin(ang)
    for t in [0.4, 1.0, 1.6, 2.2, 2.7, 0.7, 1.3, 1.9, 2.5]:
        lx, ly = 95 * math.cos(t), 35 * math.sin(t)
        x = int(605 + lx * ca - ly * sa)
        y = int(250 + lx * sa + ly * ca)
        ellipse(x, y, 7, 11, CREAM)
    poly([(690, 205), (722, 182), (700, 222)], GREEN)
    poly([(700, 205), (728, 195), (712, 228)], GREEN)


def face():
    for ex in (440, 585):
        circle(ex, 405, 36, DARK)
        circle(ex - 12, 393, 13, WHITE)
        circle(ex + 11, 417, 5, WHITE)
    ellipse(395, 495, 36, 22, PINK)
    ellipse(630, 495, 36, 22, PINK)
    poly([(500, 468), (524, 468), (512, 484)], NOSE)
    line(500, 488, 512, 500, MOUTH, 3)
    line(512, 500, 524, 488, MOUTH, 3)
    for sx, sy, ex, ey in [(350, 455, 420, 470), (352, 480, 420, 485), (355, 505, 420, 498),
                           (675, 455, 605, 470), (673, 480, 605, 485), (670, 505, 605, 498)]:
        line(sx, sy, ex, ey, (180, 170, 185), 2)


def chick():
    circle(640, 715, 88, YELLOW)
    rellipse(598, 735, 34, 58, -25, YELLOW_DARK)
    line(640, 632, 628, 612, YELLOW_DARK, 3)
    line(640, 632, 640, 608, YELLOW_DARK, 3)
    line(640, 632, 652, 612, YELLOW_DARK, 3)
    circle(665, 690, 11, DARK)
    circle(661, 686, 4, WHITE)
    poly([(700, 710), (730, 722), (700, 734)], ORANGE)
    line(618, 800, 612, 814, ORANGE, 3)
    line(664, 800, 670, 814, ORANGE, 3)


def paws():
    ellipse(445, 820, 66, 48, OUTLINE)
    ellipse(600, 828, 66, 48, OUTLINE)
    ellipse(445, 820, 60, 42, GREY)
    ellipse(600, 828, 60, 42, GREY)
    line(425, 800, 425, 838, (200, 200, 212), 2)
    line(445, 798, 445, 840, (200, 200, 212), 2)
    line(580, 808, 580, 846, (200, 200, 212), 2)
    line(600, 806, 600, 848, (200, 200, 212), 2)


def decorations():
    for cx, cy, petal, centre in [
        (120, 820, (255, 183, 197), (255, 214, 92)),
        (880, 860, (255, 255, 255), (255, 190, 120)),
        (150, 300, (255, 255, 255), (255, 214, 92)),
        (880, 320, (255, 183, 197), (255, 255, 255)),
        (250, 920, (196, 232, 210), (255, 255, 255)),
        (790, 930, (255, 236, 170), (255, 150, 60)),
    ]:
        flower(cx, cy, 26, petal, centre)
    for sx, sy in [(300, 150), (760, 180), (830, 600), (180, 620), (512, 120)]:
        sparkle(sx, sy, 7, WHITE)


def write_png(path):
    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return png


def preview():
    chars = " .:-=+*#%@"
    print("preview 64x40 (brightness):")
    for row in range(40):
        out = []
        for col in range(64):
            x = col * W // 64 + 8
            y = row * H // 40 + 12
            i = (y * W + x) * 3
            lum = (buf[i] * 30 + buf[i + 1] * 59 + buf[i + 2] * 11) // 100
            out.append(chars[min(9, lum * 10 // 256)])
        print("".join(out))


def main():
    background()
    shadow()
    bunny()
    beret()
    face()
    chick()
    paws()
    decorations()
    png = write_png("output/entry.png")
    print("PNG bytes:", len(png))
    print("SHA256:", sha256(png).hexdigest())
    print("limit: 1048576 bytes, 1024x1024")
    preview()


if __name__ == "__main__":
    main()
