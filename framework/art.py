#!/usr/bin/env python3
"""Original NES-style pixel art generator for the agent-island "Super Mario" data theme.

All art is hand-authored pixel maps (original, not traced from any sprite). Output is a set of
sprite sheets / banners sized for the theme's 288x28pt banner box, authored at 2x (576x56 device
px) so it stays crisp on Retina. Pure stdlib (own PNG encoder) so no Pillow dependency.
"""
import zlib, struct, math, os

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
            else:  # alpha-over
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
                c = tuple(other.buf[i:i + 4])
                self.px(dx + x, dy + y, c)

    def write_png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            raw += self.buf[y * self.w * 4:(y + 1) * self.w * 4]
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)


# ---------- sprite from text rows ----------
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


# ---------- palette ----------
K = (0, 0, 0, 255)            # outline black
RED = (224, 56, 40)           # cap / shirt
RED_D = (168, 32, 24)
SKIN = (252, 200, 156)
SKIN_D = (208, 140, 100)
HAIR = (96, 56, 24)
OVR = (40, 92, 220)           # overalls blue
OVR_D = (24, 56, 156)
SHOE = (96, 56, 24)
WHT = (252, 252, 252)
SKY = (92, 148, 252)
GRN = (88, 184, 72)           # hill green
GRN_D = (24, 120, 44)
PIPE = (16, 176, 64)
PIPE_D = (8, 112, 40)
PIPE_H = (160, 240, 170)
GND = (224, 132, 56)          # ground tan/orange
GND_D = (150, 78, 24)
GND_K = (96, 44, 8)
BRK = (200, 92, 48)           # brick
BRK_D = (132, 52, 24)
QY = (252, 200, 64)           # question block yellow
QY_D = (196, 132, 16)
MSH = (228, 48, 40)           # mushroom cap
MSH_D = (160, 28, 24)
MSTEM = (252, 224, 176)
GRY = (188, 188, 188)
GRY_D = (110, 110, 110)
GOLD = (252, 208, 72)

PAL = {
    'k': K, 'R': RED, 'r': RED_D, 's': SKIN, 'S': SKIN_D, 'h': HAIR,
    'B': OVR, 'b': OVR_D, 'E': SHOE, 'w': WHT, 'y': QY, 'Y': QY_D,
    'M': MSH, 'm': MSH_D, 'e': MSTEM, 'G': PIPE, 'g': PIPE_D, 'p': PIPE_H,
    'n': GRN, 'N': GRN_D, 'x': BRK, 'X': BRK_D, 'H': (168, 112, 64), 'F': (120, 72, 32),
    '.': None, ' ': None,
}

# Token-band powerup palettes (overlay onto PAL). small=classic, super=classic+flair,
# fire=white overalls + fireball, star=cycling bright recolor (flashing invincibility).
def _merge(over):
    d = dict(PAL); d.update(over); return d
FIRE_PAL = _merge({'B': (252, 252, 252), 'b': (196, 196, 196)})        # fire Mario: white overalls
STAR_PALS = [
    _merge({'R': (252, 232, 88), 'r': (212, 176, 36), 'B': (252, 232, 88), 'b': (212, 176, 36)}),
    _merge({'R': (120, 224, 255), 'r': (52, 156, 220), 'B': (120, 224, 255), 'b': (52, 156, 220)}),
    _merge({'R': (252, 252, 252), 'r': (200, 200, 200), 'B': (252, 252, 252), 'b': (200, 200, 200)}),
]
TIER_EXTRA_COINS = {"small": 0, "super": 1, "fire": 3, "star": 5}

# ---------- Mario (13 x 16 art) -- original plumber, two run frames ----------
MARIO_A = [
    "...kkkkk.....",
    "..kRRRRRk....",
    "..kRRRRRk....",
    ".khhhsssk....",
    ".khsshssssk..",
    ".khsshhsssk..",   # mustache row
    ".khssssssk...",
    "..kssssk.....",
    ".kRRbRRRk....",   # body w/ overall strap + arms
    "ksRRbbRRRsk..",
    "ssRRbbbRRss..",
    "ssBBbbbBBss..",
    "..BBBBBBB....",
    "..BBB.BBB....",
    "..kkk..kk....",   # legs split (run A)
    ".kkk....kkk..",
]
MARIO_B = [
    "...kkkkk.....",
    "..kRRRRRk....",
    "..kRRRRRk....",
    ".khhhsssk....",
    ".khsshssssk..",
    ".khsshhsssk..",
    ".khssssssk...",
    "..kssssk.....",
    "..kRRbRRRk...",
    ".ksRRbbRRRsk.",
    ".ssRRbbbRRss.",
    "..BBbbbBB....",
    "..BBBBBB.....",
    "...BBBBB.....",
    "...kkkkk.....",   # legs together (run B)
    "...kkk.kk....",
]
MARIO_LOOK = [   # looking up at the block (waiting)
    "....kkkkk....",
    "...kRRRRRk...",
    "...kRRRRRk...",
    "...ksssssk...",
    "..kshsshsk...",
    "..ksshhssk...",
    "..ksssssk....",
    "...kssk......",
    "..kRRbRRk....",
    ".ksRbbRRsk...",
    ".ssRbbbRss...",
    "..BBbbbBB....",
    "..BBBBBBB....",
    "..BBB.BBB....",
    "..kk...kk....",
    ".kkk...kkk...",
]

GOOMBA = [
    "..kkkkkk..",
    ".kHHHHHHk.",
    "kHHHHHHHHk",
    "kwwHHHHwwk",
    "kkwHHHHwkk",
    "kHHHHHHHHk",
    "kHkkkkkkHk",
    "kHHHHHHHHk",
    ".kHHHHHHk.",
    ".FFk..kFF.",
    ".FF....FF.",
]

COIN = [
    "..yyyy..",
    ".yYwwYy.",
    "yYwYYwYy",
    "yYwYYwYy",
    "yYwYYwYy",
    "yYwYYwYy",
    "yYwYYwYy",
    "yYYYYYYy",
    ".yYYYYy.",
    "..yyyy..",
]

MARIO_JUMP = [
    "...kkkkk..k",
    "..kRRRRRkkk",
    "..kRRRRRkk.",
    ".khhhsssk..",
    ".khsshsssk.",
    ".khsshhssk.",
    ".khssssssk.",
    "..kssssk...",
    "..kRRbRRk..",
    ".ksRbbRRsk.",
    ".ssRbbbRss.",
    "..BBbbbBB..",
    "..BBBBBBB..",
    "...kkkkk...",
    "..kEEEEEk..",
    "...kkkkk...",
]


def mush(rise):  # mushroom, 'rise' 0..10 reveals from bottom
    rows = [
        "..kkkkk..",
        ".kMMMMMk.",
        "kMwwMwwMk",
        "kMwwMwwMk",
        "kMMMMMMMk",
        ".kkeeekk.",
        "..keeek..",
        "..keeek..",
        "..kkkkk..",
    ]
    c = sprite(rows, PAL, 1)
    out = Canvas(c.w, c.h)
    show = min(c.h, rise)
    out.blit_region = None
    for y in range(c.h - show, c.h):
        for x in range(c.w):
            i = (y * c.w + x) * 4
            out.px(x, y, tuple(c.buf[i:i + 4]))
    return out

QBLOCK = [
    "kkkkkkkk",
    "kYYYYYYk",
    "kYkwwkYk",
    "kYwkkwYk",
    "kYYkwYYk",
    "kYYkYYYk",
    "kYYkYYYk",
    "kYwwwYYk",
    "kkkkkkkk",
]
BRICK = [
    "kkkkkkkk",
    "xxxXxxxX",
    "xxxXxxxX",
    "XXXXXXXX",
    "xXxxxXxx",
    "xXxxxXxx",
    "XXXXXXXX",
    "xxxXxxxX",
]
PIPE_TOP = [
    "kGGGGGGGGGGk",
    "kpGGGGGGGgGk",
    "kpGGGGGGGgGk",
    "kkkkkkkkkkkk",
    ".kGGGGGGGGk.",
    ".kpGGGGGgGk.",
    ".kpGGGGGgGk.",
    ".kpGGGGGgGk.",
    ".kpGGGGGgGk.",
    ".kkkkkkkkkk.",
]
CLOUD = [
    "...wwww....",
    ".wwwwwwww..",
    "wwwwwwwwww.",
    ".wwwwwwww..",
]
HILL = [
    "....nnnn....",
    "..nnnnnnnn..",
    ".nnnnnnnnnn.",
    "nnnnnnnnnnnn",
    "nnnNnnnnNnnn",
    "nnnnnnnnnnnn",
]

AS = 2
ART_W, ART_H = 288, 40
FRAME_W, FRAME_H = ART_W * AS, ART_H * AS
GROUND_TOP = 28          # art y of ground surface
PIPE_WX, GOOMBA_WX = 90, 202   # world-x of the two obstacles Mario hops (synced to scroll)

def ground_strip(extra_coins=0):
    """A seamless 288-wide art-tile of sky+ground+irregular decor that wraps left<->right.
    The pipe (PIPE_WX) and goomba (GOOMBA_WX) sit at known world-x so the run loop can time
    Mario's hops to clear them as they scroll under him. `extra_coins` sprinkles more coins for
    higher token tiers (more usage → more coins collected)."""
    t = Canvas(ART_W, ART_H, SKY)
    # ground body + surface highlight + mortar
    t.rect(0, GROUND_TOP, ART_W, ART_H - GROUND_TOP, GND)
    t.rect(0, GROUND_TOP, ART_W, 1, (252, 188, 120))
    t.rect(0, ART_H - 1, ART_W, 1, GND_K)
    for bx in range(0, ART_W, 8):
        t.rect(bx, GROUND_TOP + 1, 1, ART_H - GROUND_TOP - 1, GND_D)
    for by in range(GROUND_TOP + 4, ART_H, 4):
        t.rect(0, by, ART_W, 1, GND_D)
    # clouds + hill (irregular spacing so it doesn't read as a pattern)
    cl = sprite(CLOUD, PAL, 1)
    t.blit(cl, 36, 4); t.blit(cl, 158, 9); t.blit(cl, 244, 3)
    t.blit(sprite(HILL, PAL, 1), 138, GROUND_TOP - 6)
    # floating block clusters + coins (varied heights)
    q = sprite(QBLOCK, PAL, 1); br = sprite(BRICK, PAL, 1); co = sprite(COIN, PAL, 1)
    t.blit(q, 52, 10)
    t.blit(co, 54, 0)
    t.blit(br, 118, 8); t.blit(q, 126, 8); t.blit(br, 134, 8)
    t.blit(co, 128, 0)
    t.blit(q, 168, 13)
    t.blit(co, 232, 6); t.blit(co, 244, 4)
    # the two obstacles Mario hops over
    t.blit(sprite(PIPE_TOP, PAL, 1), PIPE_WX - 5, GROUND_TOP - 10)
    t.blit(sprite(GOOMBA, PAL, 1), GOOMBA_WX - 5, GROUND_TOP - 11)
    # extra coins for higher tiers
    for (cx, cy) in [(98, 2), (210, 1), (162, 16), (74, 15), (276, 7)][:extra_coins]:
        t.blit(co, cx, cy)
    return t


def jump_arc(i):
    """Upward offset (art px, >=0) for Mario at frame i — two parabolic hops per loop, each
    peaking when an obstacle is directly under him (scroll = 8*i, obstacle crosses x=26)."""
    h = 0.0
    for (a, b, hgt) in [(3, 13, 13), (17, 27, 13)]:   # peaks at i=8 (pipe) and i=22 (goomba)
        if a <= i <= b:
            t = (i - a) / (b - a)
            h = max(h, hgt * math.sin(math.pi * t))
    return h


def sparkles(fr, i, cx):
    """A few twinkling pixels around Mario (super/star powerup flair)."""
    for k, (x, y) in enumerate([(cx - 9, 5), (cx + 15, 7), (cx - 3, 1), (cx + 9, 17), (cx - 13, 13)]):
        if (i + k) % 3 == 0:
            fr.px(x, y, WHT); fr.px(x + 1, y, GOLD); fr.px(x, y + 1, GOLD)


def working_sheet(N=36, tier="small"):
    """N frames (3s @12fps): a seamless scrolling level, Mario running and HOPPING over the pipe
    then the goomba, coins + irregular decor scrolling past. `tier` selects the powerup form the
    token band maps to: small (classic), super (+sparkles), fire (white overalls + fireball), star
    (flashing recolor + sparkles). Higher tiers also scatter more coins."""
    tile = ground_strip(extra_coins=TIER_EXTRA_COINS[tier])
    sheet = Canvas(FRAME_W * N, FRAME_H)
    mario_x, mush_x = 24, 70
    for i in range(N):
        pal = FIRE_PAL if tier == "fire" else (STAR_PALS[(i // 2) % len(STAR_PALS)] if tier == "star" else PAL)
        ma, mb, mj = sprite(MARIO_A, pal, 1), sprite(MARIO_B, pal, 1), sprite(MARIO_JUMP, pal, 1)
        fr = Canvas(ART_W, ART_H, SKY)
        scroll = i * (ART_W // N)                       # 8 px/frame — wraps exactly at N
        for off in (-ART_W, 0, ART_W):
            fr.blit(tile, off - scroll, 0)
        # mushroom sprouts once (rookie only — higher tiers are already powered up)
        ph = i / N
        if tier == "small" and 0.6 <= ph <= 0.95:
            rise = int(min(9, max(0, (ph - 0.6) / 0.22 * 9)))
            bobm = -1 if (i // 3) % 2 else 0
            fr.blit(mush(rise), mush_x, GROUND_TOP - 9 + (9 - rise) + bobm)
        # Mario: hop arc (jump pose) or run cycle (legs every 4 frames, gentle bob)
        jy = jump_arc(i)
        if jy > 2:
            fr.blit(mj, mario_x, int(round(GROUND_TOP - 16 - jy)))
        else:
            leg = (i // 4) % 2
            bob = -1 if (i // 3) % 2 else 0
            fr.blit(ma if leg == 0 else mb, mario_x, GROUND_TOP - 16 + bob)
        # tier flair
        if tier in ("super", "star"):
            sparkles(fr, i, mario_x + 4)
        if tier == "fire":
            fbx = (mario_x + 18 + (i % 7) * 7) % (ART_W - 4)   # a fireball flies ahead
            fr.rect(fbx, GROUND_TOP - 9, 3, 3, (252, 120, 24)); fr.px(fbx + 1, GROUND_TOP - 8, (252, 232, 120))
        sheet.blit(scale_canvas(fr), FRAME_W * i, 0)
    return sheet, N


def scale_canvas(fr):
    dev = Canvas(FRAME_W, FRAME_H)
    for y in range(ART_H):
        for x in range(ART_W):
            idx = (y * ART_W + x) * 4
            c = tuple(fr.buf[idx:idx + 4])
            for sy in range(AS):
                for sx in range(AS):
                    dev.px(x * AS + sx, y * AS + sy, c)
    return dev


def text_blocky(c, s, x, y, col, sc=1):
    # tiny 3x5 font for short HUD words
    F = {
        'A': ["111", "101", "111", "101", "101"], 'C': ["111", "100", "100", "100", "111"],
        'E': ["111", "100", "111", "100", "111"], 'G': ["111", "100", "101", "101", "111"],
        'L': ["100", "100", "100", "100", "111"], 'M': ["101", "111", "111", "101", "101"],
        'O': ["111", "101", "101", "101", "111"], 'R': ["111", "101", "111", "110", "101"],
        'V': ["101", "101", "101", "101", "010"], 'P': ["111", "101", "111", "100", "100"],
        'U': ["101", "101", "101", "101", "111"], 'S': ["111", "100", "111", "001", "111"],
        'Z': ["111", "001", "010", "100", "111"], '!': ["1", "1", "1", "0", "1"],
        '?': ["111", "001", "011", "000", "010"], ' ': ["00", "00", "00", "00", "00"],
        'D': ["110", "101", "101", "101", "110"], 'N': ["101", "111", "111", "111", "101"],
        'I': ["1", "1", "1", "1", "1"], 'T': ["111", "010", "010", "010", "010"],
        'W': ["101", "101", "111", "111", "101"], 'Y': ["101", "101", "010", "010", "010"],
    }
    cx = x
    for ch in s:
        g = F.get(ch, F[' '])
        for gy, row in enumerate(g):
            for gx, b in enumerate(row):
                if b == '1':
                    for sy in range(sc):
                        for sx in range(sc):
                            c.px(cx + gx * sc + sx, y + gy * sc + sy, col)
        cx += (len(g[0]) + 1) * sc


def banner_wait_perm():
    fr = Canvas(ART_W, ART_H, SKY)
    fr.rect(0, GROUND_TOP, ART_W, ART_H - GROUND_TOP, GND)
    fr.rect(0, GROUND_TOP, ART_W, 1, (252, 188, 120))
    for bx in range(0, ART_W, 8):
        fr.rect(bx, GROUND_TOP + 1, 1, ART_H - GROUND_TOP - 1, GND_D)
    q = sprite(QBLOCK, PAL, 1)
    fr.blit(q, ART_W // 2 + 8, 3)
    fr.blit(sprite(MARIO_LOOK, PAL, 1), ART_W // 2 - 18, GROUND_TOP - 16)
    text_blocky(fr, "?", ART_W // 2 + 11, 12, K, 1)
    return scale_canvas(fr)


def banner_wait_turn():
    fr = Canvas(ART_W, ART_H, SKY)
    fr.rect(0, GROUND_TOP, ART_W, ART_H - GROUND_TOP, GND)
    fr.rect(0, GROUND_TOP, ART_W, 1, (252, 188, 120))
    for bx in range(0, ART_W, 8):
        fr.rect(bx, GROUND_TOP + 1, 1, ART_H - GROUND_TOP - 1, GND_D)
    fr.blit(sprite(MARIO_LOOK, PAL, 1), ART_W // 2 - 8, GROUND_TOP - 16)
    text_blocky(fr, "Z", ART_W // 2 + 10, 6, WHT, 1)
    text_blocky(fr, "Z", ART_W // 2 + 16, 2, WHT, 1)
    return scale_canvas(fr)


def banner_finished():
    fr = Canvas(ART_W, ART_H, SKY)
    fr.rect(0, GROUND_TOP, ART_W, ART_H - GROUND_TOP, GND)
    fr.rect(0, GROUND_TOP, ART_W, 1, (252, 188, 120))
    # flagpole + flag
    px = ART_W // 2 + 30
    fr.rect(px, 2, 1, GROUND_TOP - 2, GRY)
    fr.rect(px, 2, 1, 2, GRY_D)
    fr.rect(px - 9, 4, 9, 6, GRN)
    fr.rect(px - 9, 4, 9, 1, GRN_D)
    # castle blocks
    cx = ART_W // 2 + 44
    fr.rect(cx, GROUND_TOP - 10, 16, 10, BRK)
    fr.rect(cx + 6, GROUND_TOP - 6, 4, 6, K)
    # mario by the pole
    fr.blit(sprite(MARIO_A, PAL, 1), px - 24, GROUND_TOP - 16)
    text_blocky(fr, "CLEAR", 14, 6, WHT, 1)
    return scale_canvas(fr)


def banner_failed():
    fr = Canvas(ART_W, ART_H, (0, 0, 0, 255))
    text_blocky(fr, "GAME", ART_W // 2 - 44, 6, WHT, 2)
    text_blocky(fr, "OVER", ART_W // 2 + 8, 6, WHT, 2)
    return scale_canvas(fr)


def banner_idle():
    fr = Canvas(ART_W, ART_H, (24, 32, 56, 255))
    fr.rect(0, GROUND_TOP, ART_W, ART_H - GROUND_TOP, (60, 44, 24))
    fr.rect(0, GROUND_TOP, ART_W, 1, (110, 80, 40))
    fr.blit(sprite(MARIO_LOOK, PAL, 1), ART_W // 2 - 6, GROUND_TOP - 16)
    return scale_canvas(fr)


OUT = os.path.join(os.path.dirname(__file__), "mario")

TIERS = [("small", "level_run.png"), ("super", "run_super.png"),
         ("fire", "run_fire.png"), ("star", "run_star.png")]

def main():
    sheets = {}
    n = 0
    for tier, fname in TIERS:
        s, n = working_sheet(tier=tier)
        s.write_png(os.path.join(OUT, "sprites", fname))
        sheets[tier] = s
    banner_wait_perm().write_png(os.path.join(OUT, "images", "wait_permission.png"))
    banner_wait_turn().write_png(os.path.join(OUT, "images", "wait_turnend.png"))
    banner_finished().write_png(os.path.join(OUT, "images", "finished.png"))
    banner_failed().write_png(os.path.join(OUT, "images", "failed.png"))
    banner_idle().write_png(os.path.join(OUT, "images", "idle.png"))
    print("frames:", n, "frame_w:", FRAME_W, "frame_h:", FRAME_H, "tiers:", [t for t, _ in TIERS])

    # preview: each tier (frame 8 = mid-hop) stacked, then the state banners
    pad = 6
    prev = Canvas(FRAME_W + 2 * pad, (FRAME_H + pad) * 8 + pad, (40, 40, 40, 255))
    y = pad
    def put(canv):
        nonlocal y
        prev.blit(canv, pad, y)
        y += FRAME_H + pad
    for tier, _ in TIERS:
        f = Canvas(FRAME_W, FRAME_H)
        f.blit(sheets[tier], -FRAME_W * 8, 0)   # frame 8 = pipe hop
        put(f)
    put(banner_wait_perm())
    put(banner_wait_turn())
    put(banner_finished())
    put(banner_failed())
    prev.write_png(os.path.join(os.path.dirname(__file__), "_preview.png"))
    print("preview written")

main()
