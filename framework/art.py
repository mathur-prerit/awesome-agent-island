#!/usr/bin/env python3
"""Cycling-route pixel art generator for the agent-island data theme.

A scrolling forest meadow (parallax mountains, pine trees, grass) that shifts
day -> golden -> dusk -> night with token usage. The moving characters (the
cyclist, the flying critter, the running critter) are loaded from generated
PNG sprites in sources/pokemon_emerald/, auto-cropped, downscaled onto the
pixel grid, and tinted per tier so they sit in the scene's lighting.
"""
import collections
import math
import os
import struct
import zlib


# ---------- tiny PNG writer (RGBA, 8-bit, no interlace) ----------
class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0, 0)):
        self.w, self.h = w, h
        if len(bg) == 3:
            bg = (bg[0], bg[1], bg[2], 255)
        self.buf = bytearray(bytes(bg) * (w * h))

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            if len(c) == 3:
                c = (c[0], c[1], c[2], 255)
            if c[3] == 0:
                return
            i = (y * self.w + x) * 4
            if c[3] == 255:
                self.buf[i:i + 4] = bytes(c)
            else:
                a = c[3] / 255.0
                for k in range(3):
                    self.buf[i + k] = int(c[k] * a + self.buf[i + k] * (1 - a))
                self.buf[i + 3] = max(self.buf[i + 3], c[3])

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, c)

    def fill(self, c):
        self.rect(0, 0, self.w, self.h, c)

    def blit(self, other, dx, dy):
        for y in range(other.h):
            for x in range(other.w):
                i = (y * other.w + x) * 4
                self.px(dx + x, dy + y, tuple(other.buf[i:i + 4]))

    def write_png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            raw += self.buf[y * self.w * 4:(y + 1) * self.w * 4]

        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(png)


# ---------- PNG reader (RGBA, 8-bit, all filters) ----------
def read_png(p):
    d = open(p, "rb").read()
    i = 8
    w = h = 0
    idat = b""
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        tag = d[i + 4:i + 8]
        data = d[i + 8:i + 8 + ln]
        i += 12 + ln
        if tag == b"IHDR":
            w, h = struct.unpack(">II", data[:8])
        elif tag == b"IDAT":
            idat += data
    raw = zlib.decompress(idat)
    bpp = 4
    off = 0
    prev = bytearray(w * bpp)
    out = bytearray()
    for _y in range(h):
        ft = raw[off]
        off += 1
        line = bytearray(raw[off:off + w * bpp])
        off += w * bpp
        if ft == 1:
            for x in range(bpp, len(line)):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif ft == 2:
            for x in range(len(line)):
                line[x] = (line[x] + prev[x]) & 255
        elif ft == 3:
            for x in range(len(line)):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(len(line)):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line
        prev = line
    return w, h, out


# Pixel-map (rows of palette-key chars) -> Canvas. Kept so map-based theme
# generators (e.g. the mario theme) still build on this shared engine.
def sprite(rows, pal, scale=1):
    h = len(rows) * scale
    w = max(len(r) for r in rows) * scale
    c = Canvas(w, h)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            col = pal.get(ch)
            if col is None:
                continue
            for sy in range(scale):
                for sx in range(scale):
                    c.px(x * scale + sx, y * scale + sy, col)
    return c


def _strip_checker_bg(w, h, buf):
    """Generated PNGs bake the transparency checkerboard in as opaque pixels.
    Detect the two checker colours from the border and flood-fill them away
    (border-connected only, so interior subject pixels are never touched)."""
    cnt = collections.Counter()
    for x in range(w):
        for y in (0, h - 1):
            i = (y * w + x) * 4
            cnt[(buf[i], buf[i + 1], buf[i + 2])] += 1
    for y in range(h):
        for x in (0, w - 1):
            i = (y * w + x) * 4
            cnt[(buf[i], buf[i + 1], buf[i + 2])] += 1
    common = cnt.most_common()
    c1 = common[0][0]
    c2 = c1
    for col, _ in common[1:]:
        if sum(abs(col[k] - c1[k]) for k in range(3)) > 40:
            c2 = col
            break
    l1, l2 = sum(c1) / 3, sum(c2) / 3
    lo, hi = min(l1, l2) - 12, max(l1, l2) + 10

    def is_bg(i):
        r, g, b = buf[i], buf[i + 1], buf[i + 2]
        if max(r, g, b) - min(r, g, b) > 16:   # only near-neutral checker grays
            return False
        return lo <= (r + g + b) / 3 <= hi

    seen = bytearray(w * h)
    dq = collections.deque()
    for x in range(w):
        for y in (0, h - 1):
            dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            dq.append((x, y))
    while dq:
        x, y = dq.popleft()
        if x < 0 or x >= w or y < 0 or y >= h:
            continue
        p = y * w + x
        if seen[p]:
            continue
        seen[p] = 1
        i = p * 4
        if not is_bg(i):
            continue
        buf[i + 3] = 0
        dq.append((x + 1, y)); dq.append((x - 1, y))
        dq.append((x, y + 1)); dq.append((x, y - 1))
    return buf


# ---------- load a generated sprite: strip bg + crop + area-downscale ----------
def load_sprite(path, target_h, athr=40, afloor=30):
    w, h, buf = read_png(path)
    # Raw generator PNGs arrive fully opaque (checkerboard baked in); cleaned sources
    # already carry alpha, so only flood the checkerboard when there's none yet.
    if not any(buf[k * 4 + 3] == 0 for k in range(w * h)):
        buf = _strip_checker_bg(w, h, buf)
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        base = y * w * 4
        for x in range(w):
            if buf[base + x * 4 + 3] > athr:
                minx = min(minx, x); maxx = max(maxx, x)
                miny = min(miny, y); maxy = max(maxy, y)
    if maxx < 0:
        return Canvas(1, target_h)
    sw, sh = maxx - minx + 1, maxy - miny + 1
    th = target_h
    tw = max(1, round(sw * th / sh))
    acc = [[0.0, 0.0, 0.0, 0.0, 0] for _ in range(tw * th)]
    for sy in range(miny, maxy + 1):
        ty = min(th - 1, int((sy - miny) * th / sh))
        base = sy * w * 4
        for sx in range(minx, maxx + 1):
            i = base + sx * 4
            a = buf[i + 3]
            tx = min(tw - 1, int((sx - minx) * tw / sw))
            cell = acc[ty * tw + tx]
            cell[0] += buf[i] * a
            cell[1] += buf[i + 1] * a
            cell[2] += buf[i + 2] * a
            cell[3] += a
            cell[4] += 1
    out = Canvas(tw, th)
    for k in range(tw * th):
        ra, ga, ba, asum, cnt = acc[k]
        if asum > 0:
            alpha = int(asum / cnt)
            if alpha < afloor:      # drop faint generator-watermark ghosts
                continue
            j = k * 4
            out.buf[j] = int(ra / asum)
            out.buf[j + 1] = int(ga / asum)
            out.buf[j + 2] = int(ba / asum)
            out.buf[j + 3] = alpha
    return out


def tint(src, amb):
    """Return a copy of src with rgb multiplied by ambient colour (alpha kept)."""
    if amb == (255, 255, 255):
        return src
    out = Canvas(src.w, src.h)
    for k in range(src.w * src.h):
        j = k * 4
        a = src.buf[j + 3]
        if a == 0:
            continue
        out.buf[j] = src.buf[j] * amb[0] // 255
        out.buf[j + 1] = src.buf[j + 1] * amb[1] // 255
        out.buf[j + 2] = src.buf[j + 2] * amb[2] // 255
        out.buf[j + 3] = a
    return out


# ---------- geometry ----------
AS = 2
ART_W, ART_H = 288, 40
FRAME_W, FRAME_H = ART_W * AS, ART_H * AS
GROUND_TOP = 27           # grass starts here
N = 36

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "themes", "pokemon_emerald"))
SRC = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "sources", "pokemon_emerald"))

WHT = (246, 250, 255, 255)
RED = (226, 54, 66, 255)
POLE = (110, 116, 126, 255)


def lerp(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(min(len(a), len(b))))


TIER_CFG = {
    "day": {
        "sky": (118, 196, 236), "sky2": (206, 234, 246),
        "mtn_far": (150, 176, 168), "mtn_near": (96, 150, 104),
        "tree": (58, 124, 64), "tree_d": (38, 92, 50), "trunk": (96, 70, 48),
        "grass": (120, 196, 96), "grass_d": (78, 158, 76), "blade": (150, 220, 120),
        "cloud": (250, 254, 255), "amb": (255, 255, 255), "night": False,
    },
    "golden": {
        "sky": (250, 196, 116), "sky2": (255, 226, 168),
        "mtn_far": (196, 174, 150), "mtn_near": (158, 146, 92),
        "tree": (96, 112, 56), "tree_d": (62, 80, 44), "trunk": (92, 66, 44),
        "grass": (180, 192, 96), "grass_d": (134, 162, 72), "blade": (212, 214, 120),
        "cloud": (255, 238, 206), "amb": (255, 222, 176), "night": False,
    },
    "dusk": {
        "sky": (108, 84, 150), "sky2": (240, 138, 108),
        "mtn_far": (112, 96, 138), "mtn_near": (78, 70, 112),
        "tree": (58, 70, 84), "tree_d": (38, 46, 62), "trunk": (66, 54, 56),
        "grass": (86, 110, 96), "grass_d": (58, 82, 74), "blade": (118, 136, 116),
        "cloud": (206, 176, 206), "amb": (198, 168, 196), "night": False,
    },
    "night": {
        "sky": (16, 24, 58), "sky2": (40, 56, 102),
        "mtn_far": (42, 52, 88), "mtn_near": (28, 38, 68),
        "tree": (30, 46, 56), "tree_d": (18, 30, 42), "trunk": (44, 40, 50),
        "grass": (40, 72, 72), "grass_d": (28, 54, 60), "blade": (70, 110, 100),
        "cloud": (92, 112, 162), "amb": (120, 142, 198), "night": True,
        "moon": (240, 236, 200),
    },
}

# layer scroll: (period, advance-per-frame); 36*adv is a multiple of period -> seamless loop.
# Scenery scrolls right (offset grows with i, added to x) because the riders face/travel left.
# advance < period/2 on every layer so the direction is unambiguous, and 36*adv % period == 0
# keeps the N-frame sheet a seamless loop.
LYR = {"far": (36, 1), "near": (72, 2), "tree": (48, 4), "grass": (32, 8)}


# ---------- background layers ----------
def paint_sky(c, tier):
    cfg = TIER_CFG[tier]
    for y in range(GROUND_TOP):
        c.rect(0, y, ART_W, 1, lerp(cfg["sky"], cfg["sky2"], y / max(1, GROUND_TOP - 1)))


def paint_sky_decor(c, tier):
    cfg = TIER_CFG[tier]
    if cfg["night"]:
        for sx, sy in ((22, 4), (54, 9), (92, 3), (138, 7), (176, 5), (210, 10), (248, 4), (268, 8)):
            c.px(sx, sy, cfg["moon"])
        c.rect(236, 3, 8, 8, cfg["moon"])
        c.rect(240, 2, 3, 3, cfg["sky"])            # sky-coloured bite carves the crescent
        c.px(243, 4, cfg["sky"])
    else:
        for x, y, w in ((30, 5, 16), (150, 7, 12), (224, 4, 18)):
            c.rect(x, y + 1, w, 2, cfg["cloud"])
            c.rect(x + 3, y, max(4, w - 7), 4, cfg["cloud"])


def _hump(c, off, base, amp, period, color):
    for x in range(ART_W):
        top = int(round(base - amp * (0.5 + 0.5 * math.cos(2 * math.pi * (x - off) / period))))
        c.rect(x, top, 1, GROUND_TOP - top, color)


def draw_mountains(c, tier, i):
    cfg = TIER_CFG[tier]
    pf, af = LYR["far"]
    pn, an = LYR["near"]
    _hump(c, i * af, base=19, amp=6, period=pf, color=cfg["mtn_far"] + (255,))
    _hump(c, i * an, base=25, amp=8, period=pn, color=cfg["mtn_near"] + (255,))


def draw_pine(c, cx, tier):
    cfg = TIER_CFG[tier]
    tree, tree_d, trunk = cfg["tree"] + (255,), cfg["tree_d"] + (255,), cfg["trunk"] + (255,)
    c.rect(cx, GROUND_TOP - 3, 2, 4, trunk)
    tiers = [(GROUND_TOP - 4, 7), (GROUND_TOP - 8, 6), (GROUND_TOP - 11, 4)]
    for ty, half in tiers:
        for r in range(half):
            w = (half - r) * 2
            c.rect(cx + 1 - (w // 2), ty - r, w, 1, tree if r else tree_d)
    c.px(cx + 1, tiers[-1][0] - tiers[-1][1], tree_d)


def draw_trees(c, tier, i):
    p, a = LYR["tree"]
    off = (i * a) % p
    for tx in range(-1, ART_W // p + 2):
        draw_pine(c, tx * p + p // 2 + off, tier)


def draw_grass(c, tier, i):
    cfg = TIER_CFG[tier]
    c.rect(0, GROUND_TOP, ART_W, ART_H - GROUND_TOP, cfg["grass"] + (255,))
    c.rect(0, GROUND_TOP, ART_W, 1, cfg["blade"] + (255,))
    c.rect(0, GROUND_TOP + 5, ART_W, ART_H - GROUND_TOP - 5, cfg["grass_d"] + (255,))
    p, a = LYR["grass"]
    off = (i * a) % p
    x = -p
    while x < ART_W + p:
        bx = x + p // 2 + off
        c.px(bx, GROUND_TOP + 2, cfg["blade"] + (255,))
        c.px(bx, GROUND_TOP + 1, cfg["blade"] + (255,))
        c.px(bx + 4, GROUND_TOP + 3, cfg["grass_d"] + (255,))
        x += p


def fireflies(c, tier, i):
    if not TIER_CFG[tier]["night"]:
        return
    glow = (255, 240, 150, 200)
    for k, (bx, by) in enumerate(((70, 20), (118, 16), (150, 22), (196, 18), (210, 24))):
        if (i + k * 5) % 12 < 7:
            c.px(bx + (i % 3), by - (i % 2), glow)


def background(tier, i):
    c = Canvas(ART_W, ART_H)
    paint_sky(c, tier)
    paint_sky_decor(c, tier)
    draw_mountains(c, tier, i)
    draw_trees(c, tier, i)
    draw_grass(c, tier, i)
    return c


# ---------- sprites (loaded once) ----------
SPRITES = {}


def load_all():
    if SPRITES:
        return
    SPRITES["biker1"] = load_sprite(os.path.join(SRC, "biker1.png"), 22)
    SPRITES["biker2"] = load_sprite(os.path.join(SRC, "biker2.png"), 22)
    SPRITES["biker_rest"] = load_sprite(os.path.join(SRC, "biker_rest.png"), 22)
    SPRITES["bug1"] = load_sprite(os.path.join(SRC, "bug1.png"), 14)
    SPRITES["bug2"] = load_sprite(os.path.join(SRC, "bug2.png"), 14)
    SPRITES["runner1"] = load_sprite(os.path.join(SRC, "runner1.png"), 14)
    SPRITES["runner2"] = load_sprite(os.path.join(SRC, "runner2.png"), 14)


def place(c, spr, cx, bottom, amb):
    """Blit sprite centred at cx with its feet on `bottom`, tinted by amb."""
    s = tint(spr, amb)
    c.blit(s, cx - s.w // 2, bottom - s.h)


# ---------- working sheet ----------
def scale_canvas(fr):
    dev = Canvas(FRAME_W, FRAME_H)
    for y in range(ART_H):
        for x in range(ART_W):
            idx = (y * ART_W + x) * 4
            col = tuple(fr.buf[idx:idx + 4])
            for sy in range(AS):
                for sx in range(AS):
                    dev.px(x * AS + sx, y * AS + sy, col)
    return dev


def working_sheet(tier="day"):
    cfg = TIER_CFG[tier]
    amb = cfg["amb"]
    sheet = Canvas(FRAME_W * N, FRAME_H)
    for i in range(N):
        fr = background(tier, i)
        # sin args use integer multiples of i/N so the motion closes its loop over the N-frame sheet
        bug = SPRITES["bug1"] if (i // 2) % 2 == 0 else SPRITES["bug2"]
        bug_x = 120 + int(round(16 * math.sin(2 * math.pi * 2 * i / N)))
        bug_y = 12 + int(round(3 * math.sin(2 * math.pi * 4 * i / N)))
        place(fr, bug, bug_x, bug_y, amb)
        run = SPRITES["runner1"] if (i // 2) % 2 == 0 else SPRITES["runner2"]
        run_hop = -1 if (i // 2) % 2 else 0
        place(fr, run, 96, GROUND_TOP + 2 + run_hop, amb)
        bike = SPRITES["biker1"] if (i // 3) % 2 == 0 else SPRITES["biker2"]
        bob = -1 if (i // 3) % 2 else 0
        place(fr, bike, 44, GROUND_TOP + 3 + bob, amb)
        fireflies(fr, tier, i)
        sheet.blit(scale_canvas(fr), FRAME_W * i, 0)
    return sheet


# ---------- blocky text for banners ----------
def text_blocky(c, s, x, y, col, sc=1):
    F = {
        'A': ["111", "101", "111", "101", "101"], 'C': ["111", "100", "100", "100", "111"],
        'D': ["110", "101", "101", "101", "110"], 'E': ["111", "100", "111", "100", "111"],
        'G': ["111", "100", "101", "101", "111"], 'L': ["100", "100", "100", "100", "111"],
        'M': ["101", "111", "111", "101", "101"], 'N': ["101", "111", "111", "111", "101"],
        'O': ["111", "101", "101", "101", "111"], 'R': ["111", "101", "111", "110", "101"],
        'T': ["111", "010", "010", "010", "010"], 'V': ["101", "101", "101", "101", "010"],
        'W': ["101", "101", "111", "111", "101"], 'Y': ["101", "101", "010", "010", "010"],
        'Z': ["111", "001", "010", "100", "111"], '!': ["1", "1", "1", "0", "1"],
        '?': ["111", "001", "011", "000", "010"], ' ': ["00", "00", "00", "00", "00"],
    }
    cx = x
    for ch in s:
        g = F.get(ch, F[' '])
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == '1':
                    for sy in range(sc):
                        for sx in range(sc):
                            c.px(cx + gx * sc + sx, y + gy * sc + sy, col)
        cx += (len(g[0]) + 1) * sc


def signpost(c, x, label_col):
    c.rect(x, GROUND_TOP - 13, 2, 13, (120, 92, 60, 255))
    c.rect(x - 6, GROUND_TOP - 14, 14, 6, label_col)
    c.rect(x - 6, GROUND_TOP - 14, 14, 1, WHT)


# ---------- banners ----------
def banner_wait_perm():
    fr = background("golden", 0)
    amb = TIER_CFG["golden"]["amb"]
    bar, stripe = RED, (240, 200, 80, 255)
    fr.rect(ART_W // 2 + 8, GROUND_TOP - 9, 40, 3, bar)
    for k in range(0, 40, 8):
        fr.rect(ART_W // 2 + 8 + k, GROUND_TOP - 9, 4, 3, stripe)
    fr.rect(ART_W // 2 + 6, GROUND_TOP - 12, 3, 12, POLE)
    place(fr, SPRITES["biker_rest"], ART_W // 2 - 24, GROUND_TOP + 3, amb)
    text_blocky(fr, "!", ART_W // 2 - 6, 4, RED, 2)
    return scale_canvas(fr)


def banner_wait_turn():
    fr = background("dusk", 0)
    amb = TIER_CFG["dusk"]["amb"]
    place(fr, SPRITES["biker_rest"], ART_W // 2, GROUND_TOP + 3, amb)
    place(fr, SPRITES["runner1"], ART_W // 2 + 34, GROUND_TOP + 2, amb)
    text_blocky(fr, "Z", ART_W // 2 + 14, 8, WHT, 1)
    text_blocky(fr, "Z", ART_W // 2 + 21, 3, WHT, 1)
    return scale_canvas(fr)


def banner_finished():
    fr = background("day", 0)
    amb = TIER_CFG["day"]["amb"]
    signpost(fr, ART_W // 2 + 84, (58, 194, 104, 255))
    place(fr, SPRITES["runner1"], ART_W // 2 + 44, GROUND_TOP + 2, amb)
    place(fr, SPRITES["biker1"], ART_W // 2 + 4, GROUND_TOP + 3, amb)
    text_blocky(fr, "DONE", 14, 6, WHT, 2)
    return scale_canvas(fr)


def banner_failed():
    fr = background("night", 0)
    amb = TIER_CFG["night"]["amb"]
    fr.rect(ART_W // 2 + 30, GROUND_TOP - 12, 3, 12, POLE)
    fr.rect(ART_W // 2 + 26, GROUND_TOP - 14, 12, 3, RED)
    place(fr, SPRITES["biker_rest"], ART_W // 2 - 30, GROUND_TOP + 3, amb)
    fireflies(fr, "night", 0)
    text_blocky(fr, "ERROR", ART_W // 2 - 28, 6, RED, 2)
    return scale_canvas(fr)


def banner_idle():
    fr = background("night", 0)
    amb = TIER_CFG["night"]["amb"]
    place(fr, SPRITES["biker_rest"], ART_W // 2, GROUND_TOP + 3, amb)
    fireflies(fr, "night", 6)
    return scale_canvas(fr)


# ---------- output ----------
TIERS = [
    ("day", "ride_day.png"),
    ("golden", "ride_golden.png"),
    ("dusk", "ride_dusk.png"),
    ("night", "ride_night.png"),
]


def main():
    load_all()
    sheets = {}
    for tier, fname in TIERS:
        s = working_sheet(tier=tier)
        s.write_png(os.path.join(ROOT, "sprites", fname))
        sheets[tier] = s
    banner_wait_perm().write_png(os.path.join(ROOT, "images", "wait_permission.png"))
    banner_wait_turn().write_png(os.path.join(ROOT, "images", "wait_turnend.png"))
    banner_finished().write_png(os.path.join(ROOT, "images", "finished.png"))
    banner_failed().write_png(os.path.join(ROOT, "images", "failed.png"))
    banner_idle().write_png(os.path.join(ROOT, "images", "idle.png"))
    print("frames:", N, "frame:", FRAME_W, "x", FRAME_H, "tiers:", [t for t, _ in TIERS])

    pad = 6
    prev = Canvas(FRAME_W + 2 * pad, (FRAME_H + pad) * 9 + pad, (40, 40, 40, 255))
    y = pad

    def put(canv):
        nonlocal y
        prev.blit(canv, pad, y)
        y += FRAME_H + pad

    for tier, _ in TIERS:
        f = Canvas(FRAME_W, FRAME_H)
        f.blit(sheets[tier], -FRAME_W * 10, 0)
        put(f)
    put(banner_wait_perm())
    put(banner_wait_turn())
    put(banner_finished())
    put(banner_failed())
    put(banner_idle())
    prev.write_png(os.path.join(os.path.dirname(__file__), "_preview.png"))
    print("preview written")


if __name__ == "__main__":
    main()
