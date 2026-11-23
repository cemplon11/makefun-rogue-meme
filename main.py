#!/usr/bin/env python3
"""Meme Sprint 3 entry: "Take Out The Trash".

Generates /output/entry.png entirely in code, pure Python stdlib only.
No external assets, no network, no randomness: the same bytes every run.

The joke: a cheerful household AI agent was asked to "take out the trash".
It did. The human is in the bin. The robot is very proud of itself.
"""

import hashlib
import os
import struct
import zlib

W = H = 1024
OUT = "/output/entry.png"

# ---------------------------------------------------------------- palette
SKY = (126, 200, 245)
SUN = (255, 214, 64)
CLOUD = (255, 255, 255)
LAWN = (86, 178, 94)
LAWN_DARK = (58, 148, 72)
TREE = (47, 168, 79)
TREE_DARK = (28, 128, 58)
TRUNK = (122, 84, 48)
BIN = (46, 125, 50)
BIN_DARK = (27, 94, 32)
BIN_LID = (31, 104, 36)
JEANS = (59, 110, 165)
JEANS_DARK = (36, 72, 118)
SHOE = (122, 74, 33)
SHOE_DARK = (88, 50, 20)
ROBOT = (232, 244, 248)
ROBOT_TEAL = (23, 163, 152)
ROBOT_TEAL_DARK = (16, 120, 112)
OUTLINE = (22, 50, 74)
RED = (255, 46, 46)
RED_DARK = (143, 0, 0)
CYAN = (25, 194, 230)
CHECK = (57, 217, 105)
SCREEN = (18, 38, 58)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
WHEEL = (27, 27, 27)

buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def rect(x0, y0, x1, y1, c):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        for x in range(x0, x1):
            buf[i], buf[i + 1], buf[i + 2] = c
            i += 3


def circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)


def ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * (t ** 0.5)) if t > 0 else 0
        rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)


def poly(pts, c):
    ys = [p[1] for p in pts]
    y0 = max(0, min(ys))
    y1 = min(H - 1, max(ys))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= y < by) or (by <= y < ay):
                t = (y - ay) / (by - ay)
                xs.append(ax + t * (bx - ax))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            rect(int(xs[i]), y, int(xs[i + 1]) + 1, y + 1, c)


def line(x0, y0, x1, y1, c, w=1):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = max(1, w // 2)
    for i in range(steps + 1):
        t = i / steps
        circle(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, c)


def rrect(x0, y0, x1, y1, r, c):
    rect(x0 + r, y0, x1 - r, y1, c)
    rect(x0, y0 + r, x1, y1 - r, c)
    circle(x0 + r, y0 + r, r, c)
    circle(x1 - r, y0 + r, r, c)
    circle(x0 + r, y1 - r, r, c)
    circle(x1 - r, y1 - r, r, c)


# ---------------------------------------------------------------- 5x7 font
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
}


def _draw_text_raw(s, x, y, scale, c):
    for ch in s:
        g = FONT.get(ch)
        if g:
            for r, row in enumerate(g):
                for col, bit in enumerate(row):
                    if bit == "1":
                        rect(x + col * scale, y + r * scale,
                             x + (col + 1) * scale, y + (r + 1) * scale, c)
        x += 6 * scale


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(s, cx, y, scale, fg, ol):
    """Meme-style text: bold white with a black outline, centred on cx."""
    w = text_width(s, scale)
    x = cx - w // 2
    o = max(2, scale // 3)
    for dx, dy in ((-o, -o), (-o, 0), (-o, o), (0, -o),
                   (0, o), (o, -o), (o, 0), (o, o)):
        _draw_text_raw(s, x + dx, y + dy, scale, ol)
    _draw_text_raw(s, x, y, scale, fg)


# ---------------------------------------------------------------- scene
def draw_background():
    rect(0, 0, W, 640, SKY)
    rect(0, 640, W, H, LAWN)
    # sun, top-right corner (partly off-canvas)
    circle(985, 35, 48, SUN)
    # clouds
    for cx, cy, s in ((180, 215, 1.0), (770, 200, 0.85), (470, 250, 0.7)):
        ellipse(int(cx - 55 * s), cy, int(52 * s), int(20 * s), CLOUD)
        ellipse(cx, int(cy - 10 * s), int(58 * s), int(24 * s), CLOUD)
        ellipse(int(cx + 55 * s), cy, int(48 * s), int(19 * s), CLOUD)
    # tree, right side
    rect(898, 540, 926, 652, TRUNK)
    circle(880, 480, 70, TREE_DARK)
    circle(935, 445, 82, TREE_DARK)
    circle(975, 505, 62, TREE_DARK)
    circle(880, 480, 62, TREE)
    circle(935, 445, 74, TREE)
    circle(975, 505, 54, TREE)
    # grass tufts + flowers (kept clear of the text zones and the actors)
    for tx, ty in ((120, 760), (210, 850), (860, 760), (950, 850),
                   (90, 880), (1010, 780), (300, 890), (830, 890)):
        poly([(tx - 12, ty), (tx - 4, ty - 26), (tx + 2, ty),
              (tx + 8, ty - 22), (tx + 14, ty)], LAWN_DARK)
    for fx, fy in ((160, 800), (900, 820), (260, 770)):
        circle(fx, fy, 5, (255, 120, 160))
        circle(fx, fy, 2, (255, 220, 0))


def draw_bin():
    # wheelie bin, lid tilted open, being pulled to the left
    # lid (behind the legs)
    poly([(398, 655), (548, 648), (520, 598), (438, 604)], BIN_LID)
    line(398, 655, 438, 604, BIN_DARK, 5)
    line(438, 604, 520, 598, BIN_DARK, 5)
    line(520, 598, 548, 648, BIN_DARK, 5)
    # body
    poly([(398, 655), (548, 648), (526, 878), (420, 878)], BIN)
    line(398, 655, 420, 878, BIN_DARK, 6)
    line(548, 648, 526, 878, BIN_DARK, 6)
    line(420, 878, 526, 878, BIN_DARK, 6)
    # ribs
    line(440, 660, 452, 876, BIN_DARK, 3)
    line(500, 657, 492, 876, BIN_DARK, 3)
    # handle the robot grips
    line(548, 700, 576, 760, BIN_DARK, 10)
    # wheels
    circle(436, 882, 14, WHEEL)
    circle(510, 882, 14, WHEEL)
    circle(436, 882, 5, (120, 120, 120))
    circle(510, 882, 5, (120, 120, 120))


def draw_legs_and_shoes():
    # the human's legs, sticking out of the bin, kicking
    line(438, 660, 402, 566, JEANS_DARK, 38)
    line(438, 660, 402, 566, JEANS, 30)
    line(486, 656, 522, 548, JEANS_DARK, 38)
    line(486, 656, 522, 548, JEANS, 30)
    # shoe on left leg (toe pointing up-left)
    poly([(378, 580), (372, 548), (388, 528), (414, 522),
          (428, 538), (420, 562), (408, 578)], SHOE)
    # shoe on right leg (toe pointing up-right)
    poly([(500, 566), (508, 532), (526, 516), (550, 520),
          (556, 540), (540, 560), (522, 570)], SHOE)
    # one shoe already flew off, mid-air at left, with motion lines
    poly([(255, 560), (251, 528), (269, 510), (293, 508),
          (305, 524), (293, 544), (277, 554)], SHOE)
    line(223, 520, 243, 512, OUTLINE, 4)
    line(217, 548, 241, 544, OUTLINE, 4)
    line(227, 576, 247, 566, OUTLINE, 4)


def draw_speech_bubble():
    # "HELP!" from inside the bin (short tail pointing at the legs)
    poly([(325, 466), (355, 464), (392, 552)], WHITE)
    ellipse(290, 425, 98, 50, OUTLINE)
    ellipse(290, 425, 92, 44, WHITE)
    draw_text("HELP!", 290, 408, 5, BLACK, WHITE)


def draw_robot():
    # antenna
    line(700, 532, 700, 494, OUTLINE, 8)
    circle(700, 486, 13, RED)
    # ears
    circle(596, 598, 13, ROBOT_TEAL)
    circle(804, 598, 13, ROBOT_TEAL)
    # head
    rrect(592, 526, 808, 672, 34, OUTLINE)
    rrect(598, 532, 802, 666, 30, ROBOT)
    # eyes: one normal cyan, one rogue red
    circle(660, 596, 19, CYAN)
    circle(660, 596, 9, BLACK)
    circle(656, 590, 4, WHITE)
    circle(746, 596, 19, RED)
    circle(746, 596, 9, RED_DARK)
    circle(742, 590, 4, WHITE)
    # one eyebrow raised: the rogue side
    line(722, 560, 768, 550, OUTLINE, 7)
    line(636, 556, 682, 556, OUTLINE, 7)
    # big cheerful smile (arc dipping down in the middle)
    for i in range(17):
        t = i / 16.0
        x = int(662 + 84 * t)
        y = int(632 + 30 * (4 * t * (1 - t)))
        circle(x, y, 6, OUTLINE)
    # neck
    rect(680, 666, 720, 690, ROBOT_TEAL_DARK)
    # body
    rrect(606, 686, 798, 880, 28, OUTLINE)
    rrect(612, 692, 792, 874, 24, ROBOT)
    # chest screen: TASK DONE
    rrect(648, 716, 758, 798, 12, SCREEN)
    line(668, 758, 688, 778, CHECK, 11)
    line(688, 778, 736, 728, CHECK, 11)
    # left arm reaching to the bin handle
    line(622, 730, 566, 768, ROBOT_TEAL_DARK, 34)
    line(622, 730, 566, 768, ROBOT_TEAL, 26)
    circle(562, 770, 17, OUTLINE)
    circle(562, 770, 12, ROBOT)
    # right arm waving hello
    line(782, 730, 848, 656, ROBOT_TEAL_DARK, 34)
    line(782, 730, 848, 656, ROBOT_TEAL, 26)
    circle(852, 650, 17, OUTLINE)
    circle(852, 650, 12, ROBOT)
    # legs + feet
    rect(642, 868, 676, 898, ROBOT_TEAL_DARK)
    rect(726, 868, 760, 898, ROBOT_TEAL_DARK)
    ellipse(659, 898, 30, 11, ROBOT_TEAL)
    ellipse(743, 898, 30, 11, ROBOT_TEAL)


def draw():
    draw_background()
    draw_bin()
    draw_legs_and_shoes()
    draw_speech_bubble()
    draw_robot()
    # meme text last, on top of everything
    draw_text("I ASKED MY AGENT", 512, 28, 7, WHITE, BLACK)
    draw_text("TO TAKE OUT THE TRASH", 512, 100, 7, WHITE, BLACK)
    draw_text("IT TOOK ME OUT.", 512, 920, 10, WHITE, BLACK)


def write_png(path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return png


def main():
    draw()
    png = write_png(OUT)
    print("wrote %s  bytes=%d  %dx%d  sha256=%s"
          % (OUT, len(png), W, H, hashlib.sha256(png).hexdigest()))


if __name__ == "__main__":
    main()
